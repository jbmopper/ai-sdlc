import json
import subprocess
import sys
from pathlib import Path

import pytest

SDLC = Path(__file__).resolve().parent.parent / "bin" / "sdlc"


def git(repo, *args, stdin=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, input=stdin).stdout


def sdlc(repo, *args, stdin=""):
    return subprocess.run([sys.executable, str(SDLC), "check-protected", *args],
                          cwd=repo, capture_output=True, text=True, input=stdin)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "t")
    for name in ("AGENTS.md", "DECISIONS.md", "DOCUMENTS.md", "CLAUDE.md", "README.md"):
        (r / name).write_text(f"# {name}\n")
    (r / "contracts").mkdir()
    (r / "contracts" / "2026-10-14-x.md").write_text("# x\n")
    (r / "src").mkdir()
    (r / "src" / "a.py").write_text("x = 1\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r


def stage(repo, relpath, text="changed\n"):
    (repo / relpath).write_text(text)
    git(repo, "add", relpath)


# --- pre-commit mode: staged paths -------------------------------------------

def test_on_main_anything_is_allowed(repo):
    stage(repo, "DECISIONS.md")
    r = sdlc(repo)
    assert r.returncode == 0, r.stderr


def test_work_branch_refuses_staged_decisions(repo):
    git(repo, "checkout", "-q", "-b", "unit/2026-10-14-x")
    stage(repo, "DECISIONS.md")
    r = sdlc(repo)
    assert r.returncode == 2
    assert "DECISIONS.md is protected on branch unit/2026-10-14-x" in r.stderr
    assert "needs-decision" in r.stderr


def test_work_branch_refuses_contracts_and_sdlc_dir(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    stage(repo, "contracts/2026-10-14-x.md")
    (repo / ".sdlc").mkdir()
    stage(repo, ".sdlc/verdict.md")
    r = sdlc(repo)
    assert r.returncode == 2
    assert "contracts/2026-10-14-x.md is protected" in r.stderr
    assert ".sdlc/verdict.md is protected" in r.stderr


def test_work_branch_allows_ordinary_files(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    stage(repo, "src/a.py")
    stage(repo, "README.md")
    r = sdlc(repo)
    assert r.returncode == 0, r.stderr


def test_nested_file_named_like_protected_is_not_protected(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    (repo / "src" / "AGENTS.md").write_text("sub\n")
    git(repo, "add", "src/AGENTS.md")
    assert sdlc(repo).returncode == 0


def test_staged_deletion_of_protected_file_is_refused(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    git(repo, "rm", "-q", "DOCUMENTS.md")
    r = sdlc(repo)
    assert r.returncode == 2
    assert "DOCUMENTS.md" in r.stderr


def test_detached_head_counts_as_work_branch(repo):
    git(repo, "checkout", "-q", "--detach")
    stage(repo, "AGENTS.md")
    r = sdlc(repo)
    assert r.returncode == 2
    assert "detached HEAD" in r.stderr


def test_explicit_paths_override_staged_set(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    assert sdlc(repo, "src/a.py").returncode == 0
    assert sdlc(repo, "DECISIONS.md").returncode == 2


def test_outside_a_git_repo_refuses(tmp_path):
    r = sdlc(tmp_path, "x.md")
    assert r.returncode == 2
    assert "cannot run the gate" in r.stderr


# --- pre-push mode ------------------------------------------------------------

def push_line(remote_ref, local_ref="refs/heads/unit/x"):
    return f"{local_ref} {'a' * 40} {remote_ref} {'b' * 40}\n"


def test_push_to_main_from_unit_branch_is_refused(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--push", stdin=push_line("refs/heads/main"))
    assert r.returncode == 2
    assert "Refusing to push refs/heads/main from branch unit/x" in r.stderr


def test_push_of_unit_branch_is_allowed(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--push", stdin=push_line("refs/heads/unit/x"))
    assert r.returncode == 0, r.stderr


def test_push_to_main_from_main_is_allowed(repo):
    r = sdlc(repo, "--push", stdin=push_line("refs/heads/main", "refs/heads/main"))
    assert r.returncode == 0, r.stderr


def test_push_branch_deletion_lines_are_ignored(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--push", stdin="(delete) 0000 refs/heads/unit/y 0000\n")
    assert r.returncode == 0


# --- Claude Code PreToolUse mode ---------------------------------------------

def hook_json(repo, tool, **tool_input):
    return json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(repo)})


def test_hook_refuses_edit_to_protected_file(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--from-hook", stdin=hook_json(repo, "Edit", file_path=str(repo / "DECISIONS.md")))
    assert r.returncode == 2
    assert "DECISIONS.md is protected" in r.stderr


def test_hook_allows_edit_to_ordinary_file(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--from-hook", stdin=hook_json(repo, "Write", file_path=str(repo / "src" / "a.py")))
    assert r.returncode == 0, r.stderr


def test_hook_allows_protected_edit_on_main(repo):
    r = sdlc(repo, "--from-hook", stdin=hook_json(repo, "Edit", file_path=str(repo / "DECISIONS.md")))
    assert r.returncode == 0, r.stderr


def test_hook_allows_file_outside_repo(repo, tmp_path):
    git(repo, "checkout", "-q", "-b", "unit/x")
    outside = tmp_path / "elsewhere" / "DECISIONS.md"
    r = sdlc(repo, "--from-hook", stdin=hook_json(repo, "Edit", file_path=str(outside)))
    assert r.returncode == 0, r.stderr


def test_hook_checks_multiedit_paths(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    payload = json.dumps({"tool_name": "MultiEdit", "tool_input": {
        "edits": [{"file_path": str(repo / "src" / "a.py")}, {"file_path": str(repo / "contracts" / "2026-10-14-x.md")}]}})
    r = sdlc(repo, "--from-hook", stdin=payload)
    assert r.returncode == 2
    assert "contracts/2026-10-14-x.md" in r.stderr


def test_hook_with_malformed_json_refuses(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--from-hook", stdin="{not json")
    assert r.returncode == 2
    assert "cannot run the gate" in r.stderr


def test_hook_with_no_path_proceeds(repo):
    git(repo, "checkout", "-q", "-b", "unit/x")
    r = sdlc(repo, "--from-hook", stdin=hook_json(repo, "Edit"))
    assert r.returncode == 0
