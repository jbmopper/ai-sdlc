"""`sdlc sync <repo>`: bring an adopted project up to date with ai-sdlc.

`adopt` installs the substrate once and then keeps a project's files. `sync`
carries later template changes in without losing the project's own edits:
each substrate file is merged three ways with `git merge-file`, between

- base: the template as of the ai-sdlc commit the project last synced with,
  rendered the way the project rendered it;
- theirs: the template now, rendered for this machine;
- ours: the project's file.

The sync point is the `<!-- ai-sdlc: <sha> -->` marker at the end of
AGENTS.md. A project adopted before the marker existed has none; sync then
infers the base as the past template closest to the project's AGENTS.md and
says which commit it chose.

The git hooks, the Claude hook, and .gitignore are refreshed as `adopt` does.

Dry-run by default: prints each change as a diff. `--apply` writes the files
and the new marker; it does not commit. Refuses, writing nothing, when the
project is not on its integration branch (the substrate is protected), when
ai-sdlc's templates have uncommitted changes (the marker would not describe
them), when the sync point is unknown, or when any merge conflicts.
"""
from __future__ import annotations

import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from . import adopt, git
from .protected import INTEGRATION_BRANCHES

REFUSE = 2
MARKER_RE = re.compile(r"\n*<!-- ai-sdlc: ([0-9a-f]{7,40}) -->\n*\Z")
DESCRIPTION_RE = re.compile(r"^\*\*(?P<project>[^*]+)\*\* — (?P<description>.+)\. The operator is Jules\.$", re.M)
SDLC_PATH_RE = re.compile(r"`([^`\s]*bin/sdlc)[` ]")


class SyncError(RuntimeError):
    pass


def split_marker(text: str) -> tuple[str, str | None]:
    """The file without its marker, and the marker's commit, if any."""
    m = MARKER_RE.search(text)
    if not m:
        return text, None
    return text[: m.start()] + "\n", m.group(1)


def template_at(sha: str, name: str, source: Path) -> str | None:
    try:
        return git.run(["show", f"{sha}:templates/{name}"], source)
    except git.GitError:
        return None


def template_commits(source: Path) -> list[str]:
    """Commits that changed the templates, newest first."""
    return git.run(["log", "--format=%H", "--", "templates/"], source).split()


def distance(a: str, b: str) -> int:
    return sum(1 for line in difflib.ndiff(a.splitlines(), b.splitlines()) if line[:1] in "+-")


def merge3(ours: str, base: str, theirs: str, labels: tuple[str, str, str]) -> tuple[str, int]:
    """git merge-file; returns the merged text and the number of conflicts."""
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            p = Path(d) / name
            p.write_text(text)
            paths.append(str(p))
        r = subprocess.run(
            ["git", "merge-file", "-p", "-L", labels[0], "-L", labels[1], "-L", labels[2], *paths],
            capture_output=True, text=True)
    if r.returncode < 0 or r.returncode > 127:
        raise SyncError(f"git merge-file failed: {r.stderr.strip()}")
    return r.stdout, r.returncode


class Project:
    """How the project rendered its templates: name, description, sdlc path."""

    def __init__(self, root: Path, agents: str | None):
        self.root = root
        self.name = root.name
        self.description = None
        self.sdlc_path = adopt.sdlc_ref(shell=False)
        if agents:
            m = DESCRIPTION_RE.search(agents)
            if m:
                self.name, self.description = m.group("project"), m.group("description")
            p = SDLC_PATH_RE.search(agents)
            if p:
                self.sdlc_path = p.group(1)

    def render_base(self, text: str) -> str:
        return adopt.render_text(text, self.name, self.description, self.sdlc_path)

    def render_now(self, text: str) -> str:
        return adopt.render_text(text, self.name, self.description, adopt.sdlc_ref(shell=False))


def find_base(project: Project, agents_body: str, marker: str | None, source: Path) -> tuple[str, str]:
    """(sha, how) for the sync point."""
    if marker:
        try:
            sha = git.run(["rev-parse", "--verify", "-q", f"{marker}^{{commit}}"], source).strip()
        except git.GitError:
            raise SyncError(f"AGENTS.md records sync point {marker}, which is not in ai-sdlc's history at {source}. "
                            "Fetch ai-sdlc, or remove the marker to let sync infer the base.")
        return sha, "recorded in AGENTS.md"
    best: tuple[int, str] | None = None
    for sha in template_commits(source):
        old = template_at(sha, adopt.MARKED, source)
        if old is None:
            continue
        d = distance(project.render_base(old), agents_body)
        if best is None or d < best[0]:
            best = (d, sha)
    if best is None:
        raise SyncError(f"ai-sdlc at {source} has no template history to infer a sync point from.")
    return best[1], f"inferred: no marker in AGENTS.md; the closest past template differs by {best[0]} line(s)"


def plan(repo: Path, source: Path = adopt.HERE) -> tuple[list[tuple[str, Path, str, str]], str, str, list]:
    """Returns (file items, head sha, how the base was found, plumbing items).
    File items are (action, path, old text, new text); actions: create, merge, noop."""
    root = git.toplevel(repo)
    branch = git.current_branch(root)
    if branch not in INTEGRATION_BRANCHES:
        raise SyncError(f"{root.name} is on {branch or 'a detached HEAD'}. The substrate is protected, so sync runs "
                        f"on {' or '.join(INTEGRATION_BRANCHES)}. Switch to it and run sync again.")
    if git.run(["status", "--porcelain", "--", "templates"], source).strip():
        raise SyncError(f"ai-sdlc's templates at {source} have uncommitted changes, so no commit describes them. "
                        "Commit or stash them, then sync.")
    head = adopt.source_head(source)

    agents_path = root / adopt.MARKED
    agents_text = agents_path.read_text() if agents_path.exists() else None
    agents_body, marker = split_marker(agents_text) if agents_text is not None else (None, None)
    project = Project(root, agents_body)
    if agents_body is not None:
        base_sha, how = find_base(project, agents_body, marker, source)
    else:
        base_sha, how = head, "no AGENTS.md; it is created"

    items: list[tuple[str, Path, str, str]] = []
    conflicts: list[str] = []
    for name in adopt.SUBSTRATE:
        target = root / name
        theirs = project.render_now((source / "templates" / name).read_text())
        current = target.read_text() if target.exists() else None
        ours = agents_body if name == adopt.MARKED else current
        if ours is None:
            new = theirs
            action = "create"
        else:
            old = template_at(base_sha, name, source)
            base = project.render_base(old) if old is not None else ours
            new, n = merge3(ours, base, theirs, (f"{root.name}/{name}", f"ai-sdlc {base_sha[:10]}", f"ai-sdlc {head[:10]}"))
            if n:
                conflicts.append(f"{name}: {n} conflict(s)\n{new}")
                continue
        if name == adopt.MARKED:
            new = adopt.with_marker(new, head)
        if current is None:
            items.append(("create", target, "", new))
        else:
            items.append(("noop" if new == current else "merge", target, current, new))
    if conflicts:
        raise SyncError("template changes conflict with the project's edits; nothing was written. "
                        "Resolve by editing the project's file toward the template, then sync again.\n\n"
                        + "\n".join(conflicts))

    substrate = {str(root / n) for n in adopt.SUBSTRATE}
    plumbing = [i for i in adopt.plan(root, force=False, description=None) if i[1] not in substrate]
    return items, head, f"sync point {base_sha[:10]} ({how})", plumbing


def main(repo: str, apply: bool, source: Path = adopt.HERE) -> int:
    try:
        items, head, base_note, plumbing = plan(Path(repo), source)
    except (SyncError, git.GitError, OSError) as e:
        print(f"sdlc sync: {e}", file=sys.stderr)
        return REFUSE
    print(f"sdlc sync {repo}: {'applied' if apply else 'dry run (pass --apply to perform)'}")
    print(f"  {base_note}; templates now at {head[:10]}")
    for action, target, old, new in items:
        if action == "noop":
            print(f"  already current: {target}")
            continue
        print(f"  {'would ' if not apply else ''}{'create' if action == 'create' else 'merge template changes into'}"
              f"{'d' if apply and action == 'create' else ''}: {target}")
        if action == "merge":
            diff = difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        f"a/{target.name}", f"b/{target.name}")
            sys.stdout.writelines("    " + line if line.endswith("\n") else "    " + line + "\n" for line in diff)
    for action, target, _ in plumbing:
        print(f"  {adopt.VERBS[action][1 if apply else 0]}: {target}")
    if apply:
        for action, target, _, new in items:
            if action != "noop":
                target.write_text(new)
        adopt.execute(plumbing)
    return 0
