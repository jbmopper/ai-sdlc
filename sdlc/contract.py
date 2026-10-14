"""`sdlc contract check`: the definition of ready for a work unit (D8, D18).

A contract passes when:

- it lives at `<project>/contracts/YYYY-MM-DD-slug.md`;
- every section 5 heading is present with real content, not the template's
  guidance line or a `{{placeholder}}`;
- Authoritative inputs cite at least one document listed in DOCUMENTS.md or
  one decision in DECISIONS.md, and every citation resolves (listed doc,
  existing and unsuperseded D-number);
- a `Reserved:` line names the choices that return to Jules (or "none");
- Effort and stopping carries `Turns:` and `Repairs:` as positive integers (D17).

The check prints what is missing and what would resolve it, and exits 2.
On success it prints the parsed unit summary that `dispatch` consumes.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import git

REFUSE = 2
HEADINGS = (
    "Purpose and relationship",
    "Scope and return",
    "Authoritative inputs",
    "Execution arrangement",
    "Effort and stopping",
    "Acceptance and closure",
)
FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9][a-z0-9-]*)\.md$")
TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "CONTRACT.md"


@dataclass
class Contract:
    path: str
    unit: str
    branch: str
    turns: int
    repairs: int
    reserved: str
    model: str | None
    docs: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            current = m.group(1)
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def guidance_lines() -> set[str]:
    """The template's one-line descriptions, which count as placeholders."""
    if not TEMPLATE.exists():
        return set()
    return {ln.strip() for ln in split_sections(TEMPLATE.read_text()).values()
            for ln in ln.splitlines() if ln.strip() and ":" not in ln.split()[0]}


def keyvalue(body: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.+?)\s*$", body, flags=re.MULTILINE | re.IGNORECASE)
    return m.group(1) if m else None


def listed_docs(root: Path) -> set[str]:
    index = root / "DOCUMENTS.md"
    if not index.exists():
        return set()
    return {m.group(1) for m in re.finditer(r"\]\(([^)#]+)\)", index.read_text())}


def decision_ids(root: Path) -> tuple[set[str], set[str]]:
    """(live, superseded) D-numbers from DECISIONS.md."""
    log = root / "DECISIONS.md"
    live, dead = set(), set()
    if not log.exists():
        return live, dead
    for line in log.read_text().splitlines():
        m = re.match(r"^\|\s*(~~)?(D\d+)(~~)?\s*\|", line)
        if m:
            (dead if m.group(1) else live).add(m.group(2))
    return live, dead


def citations(body: str) -> tuple[list[str], list[str]]:
    docs = [m.group(1) for m in re.finditer(r"\]\(([^)#\s]+\.md)\)", body)]
    docs += [m.group(1) for m in re.finditer(r"`([^`\s]+\.md)`", body)]
    decisions = re.findall(r"\bD\d+\b", body)
    return sorted(set(docs)), sorted(set(decisions))


def check(path: Path) -> tuple[Contract | None, list[str]]:
    problems: list[str] = []
    path = path.resolve()
    if not path.exists():
        return None, [f"{path} does not exist."]
    root = git.toplevel(path.parent)

    m = FILENAME.match(path.name)
    if path.parent != root / "contracts" or not m:
        problems.append(
            f"Contract must live at {root / 'contracts'}/YYYY-MM-DD-slug.md so dispatch can find it; got {path}.")
        unit = path.stem
    else:
        unit = path.stem

    text = path.read_text()
    if "{{" in text:
        problems.append("Template placeholders ({{...}}) remain; fill every one.")

    sections = split_sections(text)
    guidance = guidance_lines()
    for h in HEADINGS:
        if h not in sections:
            problems.append(f"Missing section '## {h}'.")
            continue
        content = [ln.strip() for ln in sections[h].splitlines()
                   if ln.strip() and ln.strip() not in guidance and not re.match(r"^\w+:\s", ln.strip())]
        if not content:
            problems.append(f"Section '## {h}' has no content beyond the template's guidance.")

    reserved = keyvalue(text, "Reserved")
    if reserved is None:
        problems.append("No `Reserved:` line. Name the choices that return to Jules, or write `Reserved: none`.")

    effort = sections.get("Effort and stopping", "")
    turns = keyvalue(effort, "Turns")
    repairs = keyvalue(effort, "Repairs")
    for name, val in (("Turns", turns), ("Repairs", repairs)):
        if val is None:
            problems.append(f"No `{name}:` line under Effort and stopping (D17).")
        elif not val.isdigit() or int(val) <= 0:
            problems.append(f"`{name}:` must be a positive integer; got {val!r}.")

    docs, decisions = citations(sections.get("Authoritative inputs", ""))
    if not docs and not decisions:
        problems.append("Authoritative inputs cite nothing. Cite at least one document listed in DOCUMENTS.md or one D-number.")
    listed = listed_docs(root)
    for d in docs:
        if d not in listed:
            problems.append(f"Cited document {d} is not listed in DOCUMENTS.md, so it is not canonical.")
    live, dead = decision_ids(root)
    for d in decisions:
        if d in dead:
            problems.append(f"{d} is superseded in DECISIONS.md; cite the decision that replaced it.")
        elif d not in live:
            problems.append(f"{d} is not in DECISIONS.md.")

    if problems:
        return None, problems
    return Contract(
        path=str(path), unit=unit, branch=f"unit/{unit}",
        turns=int(turns), repairs=int(repairs), reserved=reserved,
        model=keyvalue(text, "Model"), docs=docs, decisions=decisions,
    ), []


def main(file: str, as_json: bool = False) -> int:
    try:
        contract, problems = check(Path(file))
    except (git.GitError, OSError) as e:
        print(f"sdlc contract check: cannot run the gate ({e}); refusing.", file=sys.stderr)
        return REFUSE
    if problems:
        print(f"sdlc contract check: {file} is not ready.", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return REFUSE
    assert contract is not None
    if as_json:
        print(json.dumps(asdict(contract), indent=2))
    else:
        print(f"ready: {contract.unit} -> {contract.branch}; turns={contract.turns} repairs={contract.repairs}; "
              f"reserved={contract.reserved}; cites {len(contract.docs)} doc(s), {len(contract.decisions)} decision(s)")
    return 0
