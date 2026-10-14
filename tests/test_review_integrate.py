"""End to end: adopt, contract, dispatch, write, review (fake reviewer), integrate."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import git, sdlc
from test_contract_check import GOOD

FAKE = f"{sys.executable} {Path(__file__).resolve().parent / 'fake_reviewer.py'}"
UNIT = "2026-10-14-fix-parser"
# The contract's test command: passes unless the tree contains a file named FAIL.
TESTS = f"{sys.executable} -c \"import sys,os; sys.exit(1 if os.path.exists('FAIL') else 0)\""
CONTRACT = GOOD.replace("D2", "D3").replace("Tests: python -m pytest -q", f"Tests: {TESTS}")


@pytest.fixture
def project(bare_repo, monkeypatch):
    monkeypatch.setenv("SDLC_REVIEWER", FAKE)
    sdlc(bare_repo, "adopt", str(bare_repo), "--apply")
    (bare_repo / "DOCUMENTS.md").write_text("# Documents\n\n| Doc | Purpose |\n|---|---|\n| [spec](docs/spec.md) | Spec |\n")
    (bare_repo / "DECISIONS.md").write_text("# Decisions\n\n| # | Date | Decision |\n|---|---|---|\n| D3 | 2026-01-02 | Three. |\n")
    (bare_repo / "docs").mkdir()
    (bare_repo / "docs" / "spec.md").write_text("# spec\n")
    (bare_repo / "contracts").mkdir()
    (bare_repo / "contracts" / f"{UNIT}.md").write_text(CONTRACT)
    (bare_repo / "src").mkdir()
    (bare_repo / "src" / "a.py").write_text("x = 1\n")
    git(bare_repo, "add", "-A")
    git(bare_repo, "commit", "-q", "-m", "contract")
    r = sdlc(bare_repo, "dispatch", str(bare_repo / "contracts" / f"{UNIT}.md"), "--apply")
    assert r.returncode == 0, r.stderr
    return bare_repo


def worktree(project):
    return Path(json.loads((project / ".sdlc" / "units" / UNIT / "dispatch.json").read_text())["worktree"])


def write_change(project, text="x = 2\n", msg="fix parser", extra=None):
    wt = worktree(project)
    (wt / "src" / "a.py").write_text(text)
    if extra:
        for name, content in extra.items():
            (wt / name).write_text(content)
    git(wt, "add", "-A")
    git(wt, "commit", "-q", "-m", msg)
    return git(wt, "rev-parse", "HEAD").strip()


def reviews(project):
    return sorted((project / ".sdlc" / "units" / UNIT / "reviews").glob("*.json"))


# --- review -------------------------------------------------------------------

def test_review_pass_stores_verdict_keyed_to_sha(project, tmp_path, monkeypatch):
    capture = tmp_path / "pkg.md"
    monkeypatch.setenv("FAKE_REVIEWER_CAPTURE", str(capture))
    head = write_change(project)
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 0, r.stderr
    assert f"round 1/3 at {head[:10]}: PASS" in r.stdout
    [v] = reviews(project)
    assert v.name == f"01-{head[:12]}.json"
    data = json.loads(v.read_text())
    assert data["sha"] == head and data["verdict"] == "pass" and data["test_exit"] == 0
    pkg = capture.read_text()
    assert "# Contract" in pkg and "Turns: 30" in pkg
    assert "# Decision record" in pkg and "D3" in pkg
    assert "+x = 2" in pkg and "- " in pkg and "fix parser" in pkg
    assert "# Test output" in pkg and "exit 0" in pkg
    assert "independent reviewer" in pkg
    assert (v.parent / f"01-{head[:12]}.package.md").exists()


def test_review_accepts_unit_prefix_and_claude_envelope(project):
    write_change(project, "x = 2  # WRAPPED\n")
    r = sdlc(project, "review", f"unit/{UNIT}")
    assert r.returncode == 0, r.stderr
    assert json.loads(reviews(project)[0].read_text())["verdict"] == "pass"


def test_review_fail_on_blocking_finding(project):
    write_change(project, "x = 2  # BLOCKER\n")
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 1
    assert "FAIL" in r.stdout and "[blocking] Does not meet contract (src/a.py:1)" in r.stdout


def test_review_forces_fail_when_model_lies_about_blocking(project):
    write_change(project, "x = 2  # LIE\n")
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 1
    assert "forced fail: blocking findings present" in r.stdout


def test_review_forces_fail_when_tests_fail(project):
    write_change(project, extra={"FAIL": ""})
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 1
    assert "forced fail: test command exited 1" in r.stdout


def test_needs_decision_passes_when_nothing_reserved(project):
    write_change(project, "x = 2  # DECIDE\n")
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[needs-decision] Which format?" in r.stdout


def test_needs_decision_fails_when_choices_are_reserved(bare_repo, monkeypatch):
    monkeypatch.setenv("SDLC_REVIEWER", FAKE)
    # build a project whose contract reserves a choice
    p = bare_repo
    (p / "DOCUMENTS.md").write_text("# Documents\n\n| Doc | Purpose |\n|---|---|\n| [spec](docs/spec.md) | Spec |\n")
    (p / "DECISIONS.md").write_text("# Decisions\n\n| # | Date | Decision |\n|---|---|---|\n| D3 | 2026-01-02 | Three. |\n")
    (p / "docs").mkdir(); (p / "docs" / "spec.md").write_text("# spec\n")
    (p / "contracts").mkdir(); (p / "src").mkdir(); (p / "src" / "a.py").write_text("x = 1\n")
    (p / "contracts" / f"{UNIT}.md").write_text(CONTRACT.replace("Reserved: none", "Reserved: output format"))
    git(p, "add", "-A"); git(p, "commit", "-q", "-m", "c")
    sdlc(p, "dispatch", str(p / "contracts" / f"{UNIT}.md"), "--apply")
    write_change(p, "x = 2  # DECIDE\n")
    r = sdlc(p, "review", UNIT)
    assert r.returncode == 1 and "needs-decision finding on a unit with reserved choices" in r.stdout


def test_review_refuses_same_sha_twice(project):
    write_change(project)
    assert sdlc(project, "review", UNIT).returncode == 0
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 2 and "was already reviewed (round 1)" in r.stderr
    assert len(reviews(project)) == 1


def test_rounds_exhaust_and_stop_report_is_written(project):
    for i in range(3):
        write_change(project, f"x = {i}  # BLOCKER\n", msg=f"attempt {i}")
        r = sdlc(project, "review", UNIT)
        assert r.returncode == 1, (i, r.stderr)
    assert "STOPPED: no rounds left" in r.stdout
    stop = project / ".sdlc" / "units" / UNIT / "STOP.md"
    assert stop.exists() and "Does not meet contract" in stop.read_text()
    write_change(project, "x = 9\n", msg="one more")
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 2 and "is stopped after 3 failed rounds" in r.stderr


def test_garbage_reviewer_output_spends_no_round(project):
    write_change(project, "x = 2  # GARBAGE\n")
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 2 and "No round was spent" in r.stderr
    assert reviews(project) == []


def test_review_refuses_nothing_to_review(project):
    r = sdlc(project, "review", UNIT)
    assert r.returncode == 2 and "no commits beyond base" in r.stderr


def test_review_refuses_from_worktree(project):
    write_change(project)
    r = sdlc(worktree(project), "review", UNIT)
    assert r.returncode == 2 and "run from the main checkout" in r.stderr


def test_reviewer_flag_and_config_precedence(project, tmp_path):
    write_change(project)
    cfg = project / ".sdlc" / "config.json"
    cfg.write_text(json.dumps({"reviewer": "false"}))  # would fail
    r = sdlc(project, "review", UNIT, "--reviewer", FAKE)  # flag wins
    assert r.returncode == 0, r.stderr
    assert json.loads(reviews(project)[0].read_text())["reviewer"] == FAKE


# --- integrate ----------------------------------------------------------------

def test_integrate_dry_run_then_apply(project):
    head = write_change(project, "x = 2  # DEFER\n")
    assert sdlc(project, "review", UNIT).returncode == 0
    r = sdlc(project, "integrate", UNIT)
    assert r.returncode == 0, r.stderr
    assert "dry run" in r.stdout and "would squash 1 commit(s)" in r.stdout
    assert git(project, "rev-parse", "HEAD").strip() != head
    assert git(project, "branch", "--list", f"unit/{UNIT}").strip()

    r = sdlc(project, "integrate", UNIT, "--apply")
    assert r.returncode == 0, r.stderr
    assert "merged as" in r.stdout
    assert (project / "src" / "a.py").read_text() == "x = 2  # DEFER\n"
    msg = git(project, "log", "-1", "--format=%B")
    assert msg.startswith(f"unit {UNIT}: {UNIT}")
    assert "Follow-ups recorded, not fixed here:" in msg and "[deferred] Corner case" in msg
    assert f"Reviewed: round 1 at {head}" in msg and f"Unit-Id: {UNIT}" in msg
    assert git(project, "rev-list", "--count", "HEAD").strip() == "3"  # init, contract, squash
    assert not git(project, "branch", "--list", f"unit/{UNIT}").strip()
    assert not worktree(project).exists()
    assert f"unit/{UNIT}" not in git(project, "worktree", "list")
    rec = project / ".sdlc" / "units" / UNIT
    assert (rec / "integrated.json").exists()
    summary = (rec / "summary.md").read_text()
    assert "integrated" in summary and "[deferred] Corner case" in summary and "src/a.py" in summary
    r = sdlc(project, "integrate", UNIT, "--apply")
    assert r.returncode == 2 and "already integrated" in r.stderr


def test_integrate_refuses_without_review(project):
    write_change(project)
    r = sdlc(project, "integrate", UNIT)
    assert r.returncode == 2 and "no review on record" in r.stderr


def test_integrate_refuses_failed_verdict(project):
    write_change(project, "x = 2  # BLOCKER\n")
    sdlc(project, "review", UNIT)
    r = sdlc(project, "integrate", UNIT)
    assert r.returncode == 2 and "is FAIL" in r.stderr


def test_integrate_refuses_commits_after_review(project):
    write_change(project)
    sdlc(project, "review", UNIT)
    write_change(project, "x = 3\n", msg="sneaky")
    r = sdlc(project, "integrate", UNIT)
    assert r.returncode == 2 and "review the current head" in r.stderr


def test_integrate_refuses_dirty_main(project):
    write_change(project)
    sdlc(project, "review", UNIT)
    (project / "README.md").write_text("dirty\n")
    r = sdlc(project, "integrate", UNIT)
    assert r.returncode == 2 and "modified tracked file" in r.stderr


def test_integrate_refuses_when_tests_fail_on_merged_tree(project):
    write_change(project)
    sdlc(project, "review", UNIT)
    # main moves on: a FAIL marker lands on main, so the merged tree fails tests
    (project / "FAIL").write_text("")
    git(project, "add", "FAIL")
    git(project, "commit", "-q", "-m", "main moves")
    before = git(project, "rev-parse", "HEAD").strip()
    r = sdlc(project, "integrate", UNIT, "--apply")
    assert r.returncode == 2 and "failed on the merged tree" in r.stderr
    assert git(project, "rev-parse", "HEAD").strip() == before
    assert not git(project, "status", "--porcelain", "--untracked-files=no").strip()
    assert git(project, "branch", "--list", f"unit/{UNIT}").strip()


def test_integrate_refuses_conflict_and_leaves_main_clean(project):
    write_change(project, "x = 2\n")
    sdlc(project, "review", UNIT)
    (project / "src" / "a.py").write_text("x = 3\n")
    git(project, "commit", "-qam", "conflicting change on main")
    before = git(project, "rev-parse", "HEAD").strip()
    r = sdlc(project, "integrate", UNIT, "--apply")
    assert r.returncode == 2 and "conflicts" in r.stderr
    assert git(project, "rev-parse", "HEAD").strip() == before
    assert not git(project, "status", "--porcelain", "--untracked-files=no").strip()
