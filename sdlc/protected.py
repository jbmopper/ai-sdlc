"""`sdlc check-protected`: refuse changes to protected files on a work branch.

Protected files hold Jules's direction or the record of a unit's approval. On
an integration branch (main) they are edited by Jules or the coordinator. On
any other branch, or with a detached HEAD, a change to them is refused.

Three callers, one gate:

- git pre-commit (no arguments): checks the staged paths.
- git pre-push (`--push`): refuses a push to an integration branch unless the
  pusher is on that branch, so a unit branch cannot push itself to main.
- Claude Code PreToolUse (`--from-hook`): reads the hook's JSON on stdin and
  checks the file the tool is about to write. The repository is found from
  the file's own location, not the process's working directory, so scratch
  files outside any repository are allowed: there is nothing to protect.

Exit 0 proceeds. Exit 2 refuses and prints what is protected and what would
resolve it. Any error also exits 2: a gate that cannot run must not pass.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

from . import git

PROTECTED_FILES = ("AGENTS.md", "CLAUDE.md", "DECISIONS.md", "DOCUMENTS.md")
PROTECTED_DIRS = ("contracts", ".sdlc")
INTEGRATION_BRANCHES = ("main", "master")

REFUSE = 2


def is_protected(relpath: str) -> bool:
    p = PurePosixPath(relpath)
    if not p.parts:
        return False
    if p.name in PROTECTED_FILES and len(p.parts) == 1:
        return True
    return p.parts[0] in PROTECTED_DIRS


def relative_to_repo(path: str, root: Path) -> str | None:
    """Repo-relative POSIX path, or None when the path is outside the repo."""
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    try:
        rel = p.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return None
    return rel.as_posix()


def why_protected(relpath: str, branch: str | None) -> str:
    where = f"branch {branch}" if branch else "a detached HEAD"
    if relpath == "DECISIONS.md":
        fix = "Propose the entry in the unit's needs-decision list; Jules records it on main."
    elif relpath.startswith("contracts/"):
        fix = "The contract is the specification you are held to. Scope changes return through planning."
    elif relpath.startswith(".sdlc/"):
        fix = "Verdicts are written by `sdlc review`, never by the writer."
    else:
        fix = "Propose the change in the unit's summary; it lands on main under review."
    return f"{relpath} is protected on {where}. {fix}"


def check_paths(paths: list[str], root: Path, branch: str | None) -> list[str]:
    """Return refusal messages for protected paths. Empty means proceed."""
    if branch in INTEGRATION_BRANCHES:
        return []
    msgs = []
    for p in paths:
        rel = relative_to_repo(p, root) if Path(p).is_absolute() else p
        if rel is not None and is_protected(rel):
            msgs.append(why_protected(rel, branch))
    return msgs


def check_push(stdin_lines: list[str], branch: str | None) -> list[str]:
    """pre-push stdin: `<local ref> <local sha> <remote ref> <remote sha>` per line."""
    msgs = []
    for line in stdin_lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        remote_ref = parts[2]
        target = remote_ref.removeprefix("refs/heads/")
        if target in INTEGRATION_BRANCHES and branch != target:
            where = f"branch {branch}" if branch else "a detached HEAD"
            msgs.append(
                f"Refusing to push {remote_ref} from {where}. "
                f"Integration is `sdlc integrate` after review, never a push from a unit branch."
            )
    return msgs


def repo_of(path: str) -> tuple[Path, str | None] | None:
    """(toplevel, branch) of the repository containing `path`, or None if none does."""
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    probe = p if p.is_dir() else p.parent
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        root = git.toplevel(probe)
    except git.GitError:
        return None
    return root, git.current_branch(root)


def check_hook_paths(paths: list[str]) -> list[str]:
    msgs = []
    for p in paths:
        found = repo_of(p)
        if found is None:
            continue
        root, branch = found
        msgs += check_paths([str(Path(p) if Path(p).is_absolute() else Path.cwd() / p)], root, branch)
    return msgs


def paths_from_hook_json(payload: str) -> list[str]:
    data = json.loads(payload) if payload.strip() else {}
    tool_input = data.get("tool_input") or {}
    paths = []
    for key in ("file_path", "notebook_path"):
        if tool_input.get(key):
            paths.append(tool_input[key])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and edit.get("file_path"):
            paths.append(edit["file_path"])
    return paths


def main(paths: list[str], push: bool, from_hook: bool, stdin=sys.stdin, cwd: Path | None = None) -> int:
    try:
        if from_hook:
            msgs = check_hook_paths(paths_from_hook_json(stdin.read()))
        else:
            root = git.toplevel(cwd)
            branch = git.current_branch(cwd)
            if push:
                msgs = check_push(stdin.read().splitlines(), branch)
            else:
                msgs = check_paths(paths or git.staged_paths(cwd), root, branch)
    except (git.GitError, ValueError, OSError) as e:
        print(f"sdlc check-protected: cannot run the gate ({e}); refusing.", file=sys.stderr)
        return REFUSE
    for m in msgs:
        print(f"sdlc check-protected: {m}", file=sys.stderr)
    return REFUSE if msgs else 0
