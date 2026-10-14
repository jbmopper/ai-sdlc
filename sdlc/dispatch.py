"""`sdlc dispatch <contract>`: open a work unit (D8, D18).

Gates, each a refusal with its resolution:

- the contract passes `sdlc contract check`;
- the contract is committed on the integration branch with no local change,
  so the writer is held to what the coordinator approved;
- the command runs in the main checkout on the integration branch;
- the unit's branch and worktree do not already exist.

With --apply it creates branch `unit/<id>` from HEAD, a worktree at
`<parent>/<project>.units/<id>`, and the unit record
`.sdlc/units/<id>/dispatch.json` in the main checkout. Writers never receive
`.sdlc/`; review and integrate read it. The record plus the printed package
is what the coordinator hands the writer: worktree, contract, the documents
to read, and the effort limits.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import contract as contract_mod
from . import git
from .protected import INTEGRATION_BRANCHES

REFUSE = 2
RECORDS = ".sdlc"


def units_dir(root: Path) -> Path:
    return root.parent / f"{root.name}.units"


def record_path(root: Path, unit: str) -> Path:
    return root / RECORDS / "units" / unit / "dispatch.json"


def plan(contract_file: str, worktrees_dir: str | None) -> tuple[dict, list[str]]:
    problems: list[str] = []
    c, contract_problems = contract_mod.check(Path(contract_file))
    if contract_problems:
        return {}, [f"contract is not ready: {p}" for p in contract_problems]
    assert c is not None
    root = git.toplevel(Path(c.path).parent)
    rel = Path(c.path).relative_to(root).as_posix()

    branch = git.current_branch(root)
    if branch not in INTEGRATION_BRANCHES:
        problems.append(f"dispatch runs from the main checkout on {' or '.join(INTEGRATION_BRANCHES)}; this is {branch or 'a detached HEAD'}.")

    try:
        git.run(["ls-files", "--error-unmatch", rel], root)
    except git.GitError:
        problems.append(f"{rel} is not committed. Commit the contract on {branch or 'main'} before dispatch, so the writer is held to the approved text.")
    else:
        if git.run(["status", "--porcelain", "--", rel], root).strip():
            problems.append(f"{rel} has uncommitted changes. Commit the approved contract before dispatch.")

    if git.run(["branch", "--list", c.branch], root).strip():
        problems.append(f"branch {c.branch} already exists. The unit was dispatched already, or the branch is stale; integrate or delete it first.")

    worktree = (Path(worktrees_dir) if worktrees_dir else units_dir(root)) / c.unit
    if worktree.exists():
        problems.append(f"worktree path {worktree} already exists. Remove it or pick --worktrees-dir.")

    rec = record_path(root, c.unit)
    if rec.exists():
        problems.append(f"unit record {rec} already exists. The unit was dispatched already.")

    head = git.run(["rev-parse", "HEAD"], root).strip()
    package = {
        **asdict(c),
        "contract": rel,
        "root": str(root),
        "base_branch": branch,
        "base_sha": head,
        "worktree": str(worktree),
        "record": str(rec),
    }
    return package, problems


def execute(package: dict) -> None:
    root = Path(package["root"])
    git.run(["worktree", "add", "-q", "-b", package["branch"], package["worktree"], package["base_sha"]], root)
    rec = Path(package["record"])
    rec.parent.mkdir(parents=True, exist_ok=True)
    package["dispatched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rec.write_text(json.dumps(package, indent=2) + "\n")


def main(contract_file: str, apply: bool, worktrees_dir: str | None = None, as_json: bool = False) -> int:
    try:
        package, problems = plan(contract_file, worktrees_dir)
    except (git.GitError, OSError) as e:
        print(f"sdlc dispatch: cannot run the gate ({e}); refusing.", file=sys.stderr)
        return REFUSE
    if problems:
        print(f"sdlc dispatch: {contract_file} cannot be dispatched.", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return REFUSE
    if apply:
        try:
            execute(package)
        except (git.GitError, OSError) as e:
            print(f"sdlc dispatch: failed while creating the unit ({e}).", file=sys.stderr)
            return REFUSE
    if as_json:
        print(json.dumps(package, indent=2))
        return 0
    verb = "dispatched" if apply else "dry run (pass --apply to perform)"
    print(f"sdlc dispatch {package['unit']}: {verb}")
    print(f"  branch:   {package['branch']} from {package['base_branch']}@{package['base_sha'][:10]}")
    print(f"  worktree: {package['worktree']}")
    print(f"  contract: {package['contract']}")
    print(f"  read:     DECISIONS.md, {', '.join(package['docs']) or '(no docs cited)'}")
    print(f"  limits:   turns={package['turns']} repairs={package['repairs']}" + (f" model={package['model']}" if package['model'] else ""))
    print(f"  record:   {package['record']}")
    return 0
