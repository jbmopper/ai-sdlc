"""`sdlc review <unit>`: independent review of a dispatched unit (section 6).

Assembles the package the reviewer may see (contract, DECISIONS.md, diff
against base, branch commit messages, test output), runs the reviewer
command with the package on stdin, parses the JSON verdict, enforces the
rules the model may not bend, and stores the verdict under the unit record
keyed to the reviewed commit. Writers never receive `.sdlc/`.

Gates:

- the unit record exists and its branch has commits beyond the base;
- the branch head has not already been reviewed (a round costs effort);
- the unit has rounds left: the first review plus `Repairs` repair rounds.
  When the last allowed round fails, a stop report is written and further
  review is refused until Jules decides.

The reviewer command comes from --reviewer, $SDLC_REVIEWER, the project's
`.sdlc/config.json` ("reviewer"), or the default `claude -p` with tools off
and a JSON schema. Any command that reads stdin and prints the verdict JSON
(bare, or wrapped in a Claude CLI result) works, so the reviewer is swappable.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import git
from .protected import INTEGRATION_BRANCHES

REFUSE = 2
HERE = Path(__file__).resolve().parent.parent
CLASSES = ("blocking", "deferred", "suggestion", "needs-decision")
SCHEMA = {
    "type": "object",
    "required": ["verdict", "summary", "tests", "findings"],
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "fail"]},
        "summary": {"type": "string"},
        "tests": {
            "type": "object",
            "required": ["establish", "miss"],
            "properties": {"establish": {"type": "string"}, "miss": {"type": "string"}},
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["class", "title", "detail"],
                "properties": {
                    "class": {"type": "string", "enum": list(CLASSES)},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "location": {"type": "string"},
                },
            },
        },
    },
}
DEFAULT_REVIEWER = "claude -p --output-format json --tools \"\" --json-schema {schema}"


def find_record(root: Path, unit: str) -> Path:
    unit = unit.removeprefix("unit/")
    return root / ".sdlc" / "units" / unit / "dispatch.json"


def reviews_dir(record: Path) -> Path:
    return record.parent / "reviews"


def past_reviews(record: Path) -> list[dict]:
    d = reviews_dir(record)
    if not d.exists():
        return []
    return [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))]


def reviewer_command(root: Path, override: str | None) -> str:
    if override:
        return override
    if os.environ.get("SDLC_REVIEWER"):
        return os.environ["SDLC_REVIEWER"]
    cfg = root / ".sdlc" / "config.json"
    if cfg.exists():
        v = json.loads(cfg.read_text()).get("reviewer")
        if v:
            return v
    return DEFAULT_REVIEWER


def build_package(rec: dict, root: Path, head: str, test_result: subprocess.CompletedProcess) -> str:
    base = rec["base_sha"]
    contract = (root / rec["contract"]).read_text()
    decisions = (root / "DECISIONS.md").read_text() if (root / "DECISIONS.md").exists() else "(no DECISIONS.md)"
    log = git.run(["log", "--format=- %h %s%n%b", f"{base}..{head}"], root)
    stat = git.run(["diff", "--stat", base, head], root)
    diff = git.run(["diff", base, head], root)
    tests = (test_result.stdout + test_result.stderr).strip()
    return "\n".join([
        (HERE / "templates" / "REVIEWER.md").read_text(),
        "",
        f"# Unit {rec['unit']}",
        f"Branch {rec['branch']} at {head}, base {base}. Reserved choices: {rec['reserved']}.",
        "",
        "# Contract", "", contract,
        "# Decision record", "", decisions,
        "# Work record (commit messages)", "", log or "(no commits)",
        "# Diff summary", "", stat,
        "# Diff", "", "```diff", diff, "```",
        f"# Test output (`{rec['tests']}`, exit {test_result.returncode})", "", "```", tests or "(no output)", "```",
    ])


def parse_verdict(stdout: str) -> dict:
    """Accept a bare verdict, a Claude CLI result wrapper, or a fenced block."""
    text = stdout.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
        if not m:
            raise ValueError("reviewer output is not JSON")
        data = json.loads(m.group(1))
    if isinstance(data, dict) and "structured_output" in data:
        data = data["structured_output"]
    elif isinstance(data, dict) and "result" in data and "verdict" not in data:
        return parse_verdict(data["result"] if isinstance(data["result"], str) else json.dumps(data["result"]))
    if not isinstance(data, dict) or data.get("verdict") not in ("pass", "fail"):
        raise ValueError("reviewer output lacks a pass/fail verdict")
    findings = data.get("findings") or []
    for f in findings:
        if f.get("class") not in CLASSES:
            raise ValueError(f"finding has unknown class {f.get('class')!r}")
    data["findings"] = findings
    return data


def enforce(verdict: dict, test_exit: int, reserved: str) -> dict:
    """Rules the model may not bend. Returns the verdict with reasons appended."""
    forced = []
    if any(f["class"] == "blocking" for f in verdict["findings"]):
        forced.append("blocking findings present")
    if test_exit != 0:
        forced.append(f"test command exited {test_exit}")
    if reserved.strip().lower() != "none" and any(f["class"] == "needs-decision" for f in verdict["findings"]):
        forced.append("needs-decision finding on a unit with reserved choices")
    if forced and verdict["verdict"] == "pass":
        verdict["verdict"] = "fail"
        verdict["forced_fail"] = forced
    return verdict


def run_reviewer(command: str, package: str, cwd: Path) -> subprocess.CompletedProcess:
    cmd = command.replace("{schema}", shlex.quote(json.dumps(SCHEMA)))
    return subprocess.run(cmd, shell=True, cwd=cwd, input=package, capture_output=True, text=True)


def main(unit: str, reviewer: str | None = None, cwd: Path | None = None) -> int:
    try:
        root = git.toplevel(cwd)
        if git.current_branch(root) not in INTEGRATION_BRANCHES:
            print("sdlc review: run from the main checkout on main; the writer's worktree is not the place for its own review.", file=sys.stderr)
            return REFUSE
        record = find_record(root, unit)
        if not record.exists():
            print(f"sdlc review: no unit record at {record}. Dispatch the unit first.", file=sys.stderr)
            return REFUSE
        rec = json.loads(record.read_text())
        head = git.run(["rev-parse", rec["branch"]], root).strip()
        if head == rec["base_sha"]:
            print(f"sdlc review: {rec['branch']} has no commits beyond base; nothing to review.", file=sys.stderr)
            return REFUSE

        past = past_reviews(record)
        stop = record.parent / "STOP.md"
        if stop.exists():
            print(f"sdlc review: unit {rec['unit']} is stopped after {len(past)} failed rounds. See {stop}. Jules decides what happens next.", file=sys.stderr)
            return REFUSE
        if any(r["sha"] == head for r in past):
            print(f"sdlc review: {head[:10]} was already reviewed (round {[r['round'] for r in past if r['sha']==head][0]}). Repair first; a round costs effort.", file=sys.stderr)
            return REFUSE
        allowed = rec["repairs"] + 1
        round_no = len(past) + 1
        if round_no > allowed:
            print(f"sdlc review: no rounds left ({allowed} allowed: first review plus {rec['repairs']} repairs).", file=sys.stderr)
            return REFUSE

        worktree = Path(rec["worktree"])
        if not worktree.exists():
            print(f"sdlc review: worktree {worktree} is missing; cannot run `{rec['tests']}`.", file=sys.stderr)
            return REFUSE
        test_result = subprocess.run(rec["tests"], shell=True, cwd=worktree, capture_output=True, text=True)
        package = build_package(rec, root, head, test_result)
        command = reviewer_command(root, reviewer)
        reviews_dir(record).mkdir(parents=True, exist_ok=True)
        stem = f"{round_no:02d}-{head[:12]}"
        (reviews_dir(record) / f"{stem}.package.md").write_text(package)

        result = run_reviewer(command, package, record.parent)
        if result.returncode != 0:
            print(f"sdlc review: reviewer command failed (exit {result.returncode}): {result.stderr.strip()[:500]}", file=sys.stderr)
            return REFUSE
        verdict = enforce(parse_verdict(result.stdout), test_result.returncode, rec["reserved"])
    except (git.GitError, OSError, ValueError, KeyError) as e:
        print(f"sdlc review: cannot complete the review ({e}); refusing. No round was spent.", file=sys.stderr)
        return REFUSE

    stored = {
        "unit": rec["unit"], "round": round_no, "sha": head, "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reviewer": command, "test_exit": test_result.returncode, **verdict,
    }
    (reviews_dir(record) / f"{stem}.json").write_text(json.dumps(stored, indent=2) + "\n")

    print(f"sdlc review {rec['unit']}: round {round_no}/{allowed} at {head[:10]}: {verdict['verdict'].upper()}")
    if verdict.get("forced_fail"):
        print(f"  forced fail: {'; '.join(verdict['forced_fail'])}")
    print(f"  {verdict['summary']}")
    for f in verdict["findings"]:
        loc = f" ({f['location']})" if f.get("location") else ""
        print(f"  [{f['class']}] {f['title']}{loc}: {f['detail']}")
    print(f"  tests establish: {verdict['tests'].get('establish', '')}")
    print(f"  tests miss: {verdict['tests'].get('miss', '')}")

    if verdict["verdict"] == "fail" and round_no >= allowed:
        blocking = [f for f in verdict["findings"] if f["class"] == "blocking"]
        stop.write_text("\n".join([
            f"# Unit {rec['unit']} stopped", "",
            f"Failed review round {round_no} of {allowed} at {head}. No repair rounds remain (Repairs: {rec['repairs']}).",
            "Jules decides: extend the allowance, change the contract, or abandon the unit.", "",
            "## Open blocking findings", "",
            *([f"- {f['title']}: {f['detail']}" for f in blocking] or ["(none; failed on tests or forced rules)"]),
            "", f"Verdicts: {reviews_dir(record)}", "",
        ]))
        print(f"  STOPPED: no rounds left. Report at {stop}")
    return 0 if verdict["verdict"] == "pass" else 1
