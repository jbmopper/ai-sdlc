import json
from pathlib import Path

import pytest

from conftest import git, sdlc
from test_contract_check import GOOD

CONTRACT = GOOD.replace("D2", "D3")


@pytest.fixture
def project(bare_repo):
    (bare_repo / "DOCUMENTS.md").write_text("# Documents\n\n| Doc | Purpose |\n|---|---|\n| [spec](docs/spec.md) | Spec |\n")
    (bare_repo / "DECISIONS.md").write_text("# Decisions\n\n| # | Date | Decision |\n|---|---|---|\n| D3 | 2026-01-02 | Three. |\n")
    (bare_repo / "docs").mkdir()
    (bare_repo / "docs" / "spec.md").write_text("# spec\n")
    (bare_repo / "contracts").mkdir()
    (bare_repo / "contracts" / "2026-10-14-fix-parser.md").write_text(CONTRACT)
    git(bare_repo, "add", "-A")
    git(bare_repo, "commit", "-q", "-m", "contract")
    return bare_repo


def contract_path(project):
    return str(project / "contracts" / "2026-10-14-fix-parser.md")


def test_dry_run_prints_package_and_creates_nothing(project, tmp_path):
    r = sdlc(project, "dispatch", contract_path(project))
    assert r.returncode == 0, r.stderr
    assert "dry run" in r.stdout
    assert "branch:   unit/2026-10-14-fix-parser from main@" in r.stdout
    assert str(tmp_path / "proj.units" / "2026-10-14-fix-parser") in r.stdout
    assert "turns=30 repairs=2 model=haiku" in r.stdout
    assert not git(project, "branch", "--list", "unit/2026-10-14-fix-parser").strip()
    assert not (tmp_path / "proj.units").exists()
    assert not (project / ".sdlc").exists()


def test_apply_creates_branch_worktree_and_record(project, tmp_path):
    r = sdlc(project, "dispatch", contract_path(project), "--apply")
    assert r.returncode == 0, r.stderr
    wt = tmp_path / "proj.units" / "2026-10-14-fix-parser"
    assert (wt / "contracts" / "2026-10-14-fix-parser.md").exists()
    assert git(wt, "symbolic-ref", "--short", "HEAD").strip() == "unit/2026-10-14-fix-parser"
    assert "unit/2026-10-14-fix-parser" in git(project, "worktree", "list")
    rec = json.loads((project / ".sdlc" / "units" / "2026-10-14-fix-parser" / "dispatch.json").read_text())
    assert rec["base_sha"] == git(project, "rev-parse", "HEAD").strip()
    assert rec["turns"] == 30 and rec["repairs"] == 2 and rec["worktree"] == str(wt)
    assert rec["dispatched_at"]
    assert git(project, "symbolic-ref", "--short", "HEAD").strip() == "main"


def test_json_output(project):
    data = json.loads(sdlc(project, "dispatch", contract_path(project), "--json").stdout)
    assert data["branch"] == "unit/2026-10-14-fix-parser" and data["docs"] == ["docs/spec.md"]


def test_worktrees_dir_override(project, tmp_path):
    custom = tmp_path / "elsewhere"
    r = sdlc(project, "dispatch", contract_path(project), "--apply", "--worktrees-dir", str(custom))
    assert r.returncode == 0, r.stderr
    assert (custom / "2026-10-14-fix-parser" / "README.md").exists()


def test_writer_in_worktree_cannot_touch_the_contract(project):
    sdlc(project, "adopt", str(project), "--apply")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "adopt")
    sdlc(project, "dispatch", contract_path(project), "--apply")
    wt = Path(json.loads((project / ".sdlc" / "units" / "2026-10-14-fix-parser" / "dispatch.json").read_text())["worktree"])
    (wt / "contracts" / "2026-10-14-fix-parser.md").write_text("relaxed\n")
    git(wt, "add", "contracts")
    import subprocess
    r = subprocess.run(["git", "-C", str(wt), "commit", "-q", "-m", "relax"], capture_output=True, text=True)
    assert r.returncode != 0 and "contracts/2026-10-14-fix-parser.md is protected" in r.stderr


def test_uncommitted_contract_is_refused(project):
    (project / "contracts" / "2026-10-14-fix-parser.md").write_text(CONTRACT.replace("Turns: 30", "Turns: 99"))
    r = sdlc(project, "dispatch", contract_path(project))
    assert r.returncode == 2 and "uncommitted changes" in r.stderr


def test_untracked_contract_is_refused(project):
    p = project / "contracts" / "2026-10-14-other.md"
    p.write_text(CONTRACT.replace("2026-10-14-fix-parser", "2026-10-14-other"))
    r = sdlc(project, "dispatch", str(p))
    assert r.returncode == 2 and "is not committed" in r.stderr


def test_unready_contract_is_refused_with_its_reasons(project):
    p = project / "contracts" / "2026-10-14-fix-parser.md"
    p.write_text(CONTRACT.replace("Repairs: 2\n", ""))
    git(project, "commit", "-qam", "break it")
    r = sdlc(project, "dispatch", str(p))
    assert r.returncode == 2 and "contract is not ready: No `Repairs:` line" in r.stderr


def test_second_dispatch_is_refused(project):
    sdlc(project, "dispatch", contract_path(project), "--apply")
    r = sdlc(project, "dispatch", contract_path(project), "--apply")
    assert r.returncode == 2
    assert "already exists" in r.stderr and "unit record" in r.stderr


def test_dispatch_from_a_work_branch_is_refused(project):
    git(project, "checkout", "-q", "-b", "unit/other")
    r = sdlc(project, "dispatch", contract_path(project))
    assert r.returncode == 2 and "runs from the main checkout on main or master; this is unit/other" in r.stderr
