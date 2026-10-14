"""`sdlc adopt <repo>`: install the substrate and hooks into a project (D7).

Dry-run by default: prints one line per item saying what would happen.
`--apply` performs it. Existing files are kept unless `--force`, which still
never touches DOCUMENTS.md or DECISIONS.md: those are Jules's records. Existing git
hooks are chained after ours, never replaced: the old hook moves to
`<hook>.sdlc-chained` and our wrapper runs it after the gate passes. A second
run is a no-op.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import git

REFUSE = 2
HERE = Path(__file__).resolve().parent.parent
SDLC_BIN = HERE / "bin" / "sdlc"
TEMPLATES = HERE / "templates"
SUBSTRATE = ("CLAUDE.md", "AGENTS.md", "DOCUMENTS.md", "DECISIONS.md")
RECORDS_NEVER_OVERWRITTEN = ("DOCUMENTS.md", "DECISIONS.md")  # Jules's records; --force does not touch them
GIT_HOOKS = ("pre-commit", "pre-push")
MARKER = "# ai-sdlc hook"
CHAINED_SUFFIX = ".sdlc-chained"


def render_template(name: str, project: str, description: str | None) -> str:
    text = (TEMPLATES / name).read_text()
    text = text.replace("{{project}}", project).replace("@SDLC@", str(SDLC_BIN))
    if description:
        text = text.replace("{{one-line description}}", description)
    else:
        text = text.replace("**{{project}}** — {{one-line description}}.", f"**{project}**.")
        text = text.replace(f"**{project}** — {{{{one-line description}}}}.", f"**{project}**.")
    return text


def render_hook(name: str, chained: Path | None) -> str:
    text = (HERE / "hooks" / "git" / name).read_text()
    return text.replace("@SDLC@", str(SDLC_BIN)).replace("@CHAINED@", str(chained) if chained else "")


def hook_entry() -> dict:
    text = (HERE / "hooks" / "claude" / "settings.json").read_text().replace("@SDLC@", str(SDLC_BIN))
    return json.loads(text)["hooks"]["PreToolUse"][0]


def has_our_entry(settings: dict) -> bool:
    for entry in settings.get("hooks", {}).get("PreToolUse", []):
        for h in entry.get("hooks", []):
            if "check-protected --from-hook" in h.get("command", ""):
                return True
    return False


def plan(repo: Path, force: bool, description: str | None) -> list[tuple[str, str, object]]:
    """Return (action, target, payload) tuples. Actions: create, keep, overwrite, chain, merge, noop."""
    root = git.toplevel(repo)
    project = root.name
    items: list[tuple[str, str, object]] = []

    for name in SUBSTRATE:
        target = root / name
        content = render_template(name, project, description)
        if not target.exists():
            items.append(("create", str(target), content))
        elif target.read_text() == content:
            items.append(("noop", str(target), None))
        elif force and name not in RECORDS_NEVER_OVERWRITTEN:
            items.append(("overwrite", str(target), content))
        else:
            items.append(("keep", str(target), None))

    hooks_dir = Path(git.run(["rev-parse", "--git-path", "hooks"], root).strip())
    if not hooks_dir.is_absolute():
        hooks_dir = root / hooks_dir
    for name in GIT_HOOKS:
        target = hooks_dir / name
        chained_path = hooks_dir / (name + CHAINED_SUFFIX)
        if target.exists() and MARKER in target.read_text():
            desired = render_hook(name, chained_path if chained_path.exists() else None)
            items.append(("noop" if target.read_text() == desired else "overwrite", str(target), desired))
        elif target.exists():
            items.append(("chain", str(target), render_hook(name, chained_path)))
        else:
            items.append(("create", str(target), render_hook(name, None)))

    gitignore = root / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if any(line.strip() in (".sdlc", ".sdlc/") for line in existing.splitlines()):
        items.append(("noop", str(gitignore), None))
    else:
        sep = "" if not existing or existing.endswith("\n") else "\n"
        items.append(("append", str(gitignore), existing + sep + ".sdlc/\n"))

    settings_path = root / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    if has_our_entry(settings):
        items.append(("noop", str(settings_path), None))
    else:
        settings.setdefault("hooks", {}).setdefault("PreToolUse", []).append(hook_entry())
        items.append(("merge", str(settings_path), json.dumps(settings, indent=2) + "\n"))
    return items


def execute(items: list[tuple[str, str, object]]) -> None:
    for action, target, payload in items:
        t = Path(target)
        if action == "chain":
            t.rename(t.with_name(t.name + CHAINED_SUFFIX))
        if action in ("create", "overwrite", "merge", "chain", "append"):
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(payload)  # type: ignore[arg-type]
            if isinstance(payload, str) and payload.startswith("#!"):
                t.chmod(0o755)


VERBS = {
    "create": ("would create", "created"),
    "overwrite": ("would overwrite", "overwrote"),
    "keep": ("would keep (exists, differs; use --force to overwrite)", "kept (exists, differs; use --force to overwrite)"),
    "chain": (f"would chain existing hook as *{CHAINED_SUFFIX} after the gate", f"chained existing hook as *{CHAINED_SUFFIX} after the gate"),
    "merge": ("would add PreToolUse hook to", "added PreToolUse hook to"),
    "append": ("would add .sdlc/ to", "added .sdlc/ to"),
    "noop": ("already in place", "already in place"),
}


def main(repo: str, apply: bool, force: bool, description: str | None = None) -> int:
    try:
        items = plan(Path(repo), force, description)
    except (git.GitError, OSError, json.JSONDecodeError) as e:
        print(f"sdlc adopt: cannot plan ({e}); refusing.", file=sys.stderr)
        return REFUSE
    if apply:
        execute(items)
    print(f"sdlc adopt {repo}: {'applied' if apply else 'dry run (pass --apply to perform)'}")
    for action, target, _ in items:
        print(f"  {VERBS[action][1 if apply else 0]}: {target}")
    return 0
