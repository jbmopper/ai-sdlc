"""`sdlc integrate <unit>`: squash-merge a reviewed unit and clean up (D5, D10).

Gates, each a refusal with its resolution:

- runs from the main checkout on the integration branch with no modified
  tracked files, so the squash and the test run see only the unit;
- the latest verdict is a pass for the branch's current head;
- the branch changes no protected file against its base;
- the squash merge applies without conflict;
- the contract's test command passes on the merged tree.

With --apply it commits the squash with the unit id, the contract title, the
review summary, and the nonblocking findings as follow-ups; writes
`.sdlc/units/<id>/summary.md` (the one batched report Jules reads); removes
the worktree and deletes the branch; and records `integrated.json`.
Dry run reports the plan and runs nothing that changes the checkout.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import git
from .protected import INTEGRATION_BRANCHES, is_protected
from .review import find_record, past_reviews

REFUSE = 2


def gate(root: Path, unit: str) -> tuple[dict, dict, list[str], list[str]]:
    """Return (record, verdict, changed_paths, problems)."""
    problems: list[str] = []
    branch = git.current_branch(root)
    if branch not in INTEGRATION_BRANCHES:
        problems.append(f"integrate runs from the main checkout on main; this is {branch or 'a detached HEAD'}.")
    modified = [l for l in git.run(["status", "--porcelain", "--untracked-files=no"], root).splitlines() if l.strip()]
    if modified:
        problems.append(f"{len(modified)} modified tracked file(s) in the main checkout; commit or stash them so the merge and test run see only the unit.")

    record = find_record(root, unit)
    if not record.exists():
        return {}, {}, [], problems + [f"no unit record at {record}; dispatch the unit first."]
    rec = json.loads(record.read_text())
    if (record.parent / "integrated.json").exists():
        return rec, {}, [], problems + [f"unit {rec['unit']} is already integrated."]

    try:
        head = git.run(["rev-parse", rec["branch"]], root).strip()
    except git.GitError:
        return rec, {}, [], problems + [f"branch {rec['branch']} does not exist."]

    past = past_reviews(record)
    latest = past[-1] if past else None
    if latest is None:
        problems.append("no review on record; run `sdlc review` first.")
    elif latest["sha"] != head:
        problems.append(f"latest verdict is for {latest['sha'][:10]} but the branch is at {head[:10]}; review the current head.")
    elif latest["verdict"] == "decision":
        problems.append(f"the unit is waiting on a decision from Jules: {'; '.join(latest.get('waiting_on', []))}. Record it in DECISIONS.md, then review again.")
    elif latest["verdict"] != "pass":
        problems.append(f"latest verdict (round {latest['round']}) is FAIL; repair and review again.")

    changed = git.run(["diff", "--name-only", rec["base_sha"], head], root).split()
    for p in changed:
        if is_protected(p):
            problems.append(f"{p} is protected and changed on the branch; the writer cannot alter direction or its own approval.")
    if not changed:
        problems.append("the branch changes nothing.")
    rec["head"] = head
    return rec, latest or {}, changed, problems


def commit_message(rec: dict, verdict: dict, changed: list[str]) -> str:
    title = (Path(rec["root"]) / rec["contract"]).read_text().splitlines()[0].removeprefix("# Contract:").strip()
    lines = [f"unit {rec['unit']}: {title}", "", verdict.get("summary", "").strip(), ""]
    followups = [f for f in verdict.get("findings", []) if f["class"] in ("deferred", "suggestion")]
    needs = [f for f in verdict.get("findings", []) if f["class"] == "needs-decision"]
    if followups:
        lines += ["Follow-ups recorded, not fixed here:"] + [f"- [{f['class']}] {f['title']}: {f['detail']}" for f in followups] + [""]
    if needs:
        lines += ["Needs a decision from Jules:"] + [f"- {f['title']}: {f['detail']}" for f in needs] + [""]
    lines += [f"Contract: {rec['contract']}", f"Reviewed: round {verdict.get('round')} at {rec['head']}", f"Unit-Id: {rec['unit']}"]
    return "\n".join(lines) + "\n"


def summary_text(rec: dict, verdict: dict, changed: list[str], merge_sha: str, test_output: str) -> str:
    return "\n".join([
        f"# Unit {rec['unit']}: integrated", "",
        f"Squash commit {merge_sha[:10]} on {rec['base_branch']}. Branch {rec['branch']} and worktree removed.", "",
        "## Review summary", "", verdict.get("summary", ""), "",
        "## Findings", "",
        *([f"- [{f['class']}] {f['title']}: {f['detail']}" for f in verdict.get("findings", [])] or ["(none)"]), "",
        "## Tests", "", f"Establish: {verdict.get('tests', {}).get('establish', '')}", f"Miss: {verdict.get('tests', {}).get('miss', '')}", "",
        f"`{rec['tests']}` on the merged tree:", "", "```", test_output.strip()[-2000:] or "(no output)", "```", "",
        "## Changed files", "", *[f"- {p}" for p in changed], "",
    ])


def apply(root: Path, rec: dict, verdict: dict, changed: list[str]) -> tuple[str, str]:
    """Squash, test, commit, clean up. Returns (merge_sha, test_output). Raises on refusal, leaving main untouched."""
    try:
        git.run(["merge", "--squash", "--no-commit", rec["head"]], root)
    except git.GitError as e:
        git.run(["merge", "--abort"], root) if (root / ".git" / "MERGE_HEAD").exists() else git.run(["reset", "-q", "--hard", "HEAD"], root)
        raise git.GitError(f"squash merge conflicts with {rec['base_branch']}; rebase {rec['branch']} and review again. ({e})")
    test = subprocess.run(rec["tests"], shell=True, cwd=root, capture_output=True, text=True)
    output = test.stdout + test.stderr
    if test.returncode != 0:
        git.run(["reset", "-q", "--hard", "HEAD"], root)
        raise git.GitError(f"`{rec['tests']}` failed on the merged tree (exit {test.returncode}); main left untouched.\n{output.strip()[-1500:]}")
    subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=root, input=commit_message(rec, verdict, changed),
                   text=True, check=True, capture_output=True)
    merge_sha = git.run(["rev-parse", "HEAD"], root).strip()
    git.run(["worktree", "remove", "--force", rec["worktree"]], root)
    git.run(["branch", "-D", rec["branch"]], root)
    return merge_sha, output


def main(unit: str, do_apply: bool, cwd: Path | None = None) -> int:
    try:
        root = git.toplevel(cwd)
        rec, verdict, changed, problems = gate(root, unit)
    except (git.GitError, OSError, KeyError, json.JSONDecodeError) as e:
        print(f"sdlc integrate: cannot run the gate ({e}); refusing.", file=sys.stderr)
        return REFUSE
    if problems:
        print(f"sdlc integrate {unit}: refused.", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return REFUSE

    count = git.run(["rev-list", "--count", f"{rec['base_sha']}..{rec['head']}"], root).strip()
    if not do_apply:
        print(f"sdlc integrate {rec['unit']}: dry run (pass --apply to perform)")
        print(f"  would squash {count} commit(s) from {rec['branch']}@{rec['head'][:10]} onto {rec['base_branch']} ({len(changed)} file(s))")
        print(f"  would run `{rec['tests']}` on the merged tree and refuse if it fails")
        print(f"  would commit, write {find_record(root, unit).parent / 'summary.md'}, remove {rec['worktree']}, delete {rec['branch']}")
        return 0

    try:
        merge_sha, output = apply(root, rec, verdict, changed)
    except (git.GitError, subprocess.CalledProcessError) as e:
        print(f"sdlc integrate {rec['unit']}: refused. {e}", file=sys.stderr)
        return REFUSE
    record_dir = find_record(root, unit).parent
    (record_dir / "summary.md").write_text(summary_text(rec, verdict, changed, merge_sha, output))
    (record_dir / "integrated.json").write_text(json.dumps({
        "unit": rec["unit"], "merge_sha": merge_sha, "reviewed_sha": rec["head"], "round": verdict.get("round"),
        "integrated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=2) + "\n")
    print(f"sdlc integrate {rec['unit']}: merged as {merge_sha[:10]} on {rec['base_branch']}; {rec['branch']} and its worktree removed.")
    print(f"  summary: {record_dir / 'summary.md'}")
    return 0
