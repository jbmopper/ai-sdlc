import json
import os
from pathlib import Path

from conftest import git, sdlc

SDLC_BIN = Path(__file__).resolve().parent.parent / "bin" / "sdlc"


def hooks_dir(repo):
    p = Path(git(repo, "rev-parse", "--git-path", "hooks").strip())
    return p if p.is_absolute() else Path(repo) / p


def test_dry_run_changes_nothing(bare_repo):
    r = sdlc(bare_repo, "adopt", str(bare_repo))
    assert r.returncode == 0, r.stderr
    assert "dry run" in r.stdout
    assert "would create" in r.stdout
    assert not (bare_repo / "AGENTS.md").exists()
    assert not (bare_repo / ".claude").exists()
    assert not (hooks_dir(bare_repo) / "pre-commit").exists()


def test_apply_installs_substrate_hooks_and_settings(bare_repo):
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply", "--description", "a test project")
    assert r.returncode == 0, r.stderr
    for name in ("CLAUDE.md", "AGENTS.md", "DOCUMENTS.md", "DECISIONS.md"):
        assert (bare_repo / name).exists(), name
    agents = (bare_repo / "AGENTS.md").read_text()
    assert "**proj** — a test project." in agents and "{{" not in agents
    assert f"`{SDLC_BIN} contract check`" in agents and "@SDLC@" not in agents
    for name in ("pre-commit", "pre-push"):
        hook = hooks_dir(bare_repo) / name
        text = hook.read_text()
        assert str(SDLC_BIN) in text and "@SDLC@" not in text and 'CHAINED=""' in text
        assert os.access(hook, os.X_OK)
    settings = json.loads((bare_repo / ".claude" / "settings.json").read_text())
    cmd = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert cmd == f"{SDLC_BIN} check-protected --from-hook"


def test_sdlc_records_dir_is_gitignored(bare_repo):
    (bare_repo / ".gitignore").write_text("*.pyc")  # no trailing newline
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    assert (bare_repo / ".gitignore").read_text() == "*.pyc\n.sdlc/\n"
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    assert (bare_repo / ".gitignore").read_text() == "*.pyc\n.sdlc/\n"


def test_without_description_the_placeholder_is_dropped(bare_repo):
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    agents = (bare_repo / "AGENTS.md").read_text()
    assert "**proj**." in agents and "{{" not in agents


def test_installed_hooks_actually_gate_commits(bare_repo):
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    git(bare_repo, "add", "-A")
    git(bare_repo, "commit", "-q", "-m", "adopt")  # on main: allowed
    git(bare_repo, "checkout", "-q", "-b", "unit/x")
    (bare_repo / "DECISIONS.md").write_text("tampered\n")
    git(bare_repo, "add", "DECISIONS.md")
    import subprocess
    r = subprocess.run(["git", "-C", str(bare_repo), "commit", "-q", "-m", "bad"], capture_output=True, text=True)
    assert r.returncode != 0 and "DECISIONS.md is protected" in r.stderr


def test_second_run_is_a_noop(bare_repo):
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    assert r.returncode == 0
    assert "created" not in r.stdout and "chained" not in r.stdout and "added" not in r.stdout
    assert r.stdout.count("already in place") == 8


def test_existing_differing_file_is_kept_unless_forced(bare_repo):
    (bare_repo / "AGENTS.md").write_text("# mine\n")
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    assert "kept (exists, differs" in r.stdout
    assert (bare_repo / "AGENTS.md").read_text() == "# mine\n"
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply", "--force")
    assert "Instructions for every agent" in (bare_repo / "AGENTS.md").read_text()


def test_force_never_overwrites_records(bare_repo):
    (bare_repo / "DECISIONS.md").write_text("| D1 | 2026-01-01 | Mine. |\n")
    (bare_repo / "DOCUMENTS.md").write_text("# mine\n")
    (bare_repo / "AGENTS.md").write_text("# old\n")
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply", "--force")
    assert (bare_repo / "DECISIONS.md").read_text() == "| D1 | 2026-01-01 | Mine. |\n"
    assert (bare_repo / "DOCUMENTS.md").read_text() == "# mine\n"
    assert "Instructions for every agent" in (bare_repo / "AGENTS.md").read_text()
    assert r.stdout.count("kept (exists, differs") == 2


def test_existing_hook_is_chained_and_still_runs(bare_repo):
    hd = hooks_dir(bare_repo)
    hd.mkdir(parents=True, exist_ok=True)
    marker = bare_repo / "chained-ran"
    old = hd / "pre-commit"
    old.write_text(f"#!/bin/sh\ntouch {marker}\n")
    old.chmod(0o755)
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    assert "chained existing hook" in r.stdout
    assert (hd / "pre-commit.sdlc-chained").read_text().startswith("#!/bin/sh\ntouch")
    assert str(hd / "pre-commit.sdlc-chained") in (hd / "pre-commit").read_text()
    (bare_repo / "x.txt").write_text("x\n")
    git(bare_repo, "add", "x.txt")
    git(bare_repo, "commit", "-q", "-m", "ok")
    assert marker.exists()


def test_chained_hook_is_not_run_when_gate_refuses(bare_repo):
    hd = hooks_dir(bare_repo)
    hd.mkdir(parents=True, exist_ok=True)
    marker = bare_repo / "chained-ran"
    (hd / "pre-commit").write_text(f"#!/bin/sh\ntouch {marker}\n")
    (hd / "pre-commit").chmod(0o755)
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    git(bare_repo, "add", "-A")
    git(bare_repo, "commit", "-q", "-m", "adopt")
    marker.unlink()
    git(bare_repo, "checkout", "-q", "-b", "unit/x")
    (bare_repo / "AGENTS.md").write_text("tampered\n")
    git(bare_repo, "add", "AGENTS.md")
    import subprocess
    r = subprocess.run(["git", "-C", str(bare_repo), "commit", "-q", "-m", "bad"], capture_output=True, text=True)
    assert r.returncode != 0 and not marker.exists()


def test_existing_settings_are_merged_not_replaced(bare_repo):
    (bare_repo / ".claude").mkdir()
    (bare_repo / ".claude" / "settings.json").write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]},
        "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}]}}))
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    s = json.loads((bare_repo / ".claude" / "settings.json").read_text())
    assert s["permissions"] == {"allow": ["Bash(ls)"]}
    assert len(s["hooks"]["PreToolUse"]) == 2
    assert s["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo hi"


def test_not_a_git_repo_refuses(tmp_path):
    r = sdlc(tmp_path, "adopt", str(tmp_path))
    assert r.returncode == 2 and "cannot plan" in r.stderr
