import shutil
import sys
from pathlib import Path

import pytest

from conftest import git, sdlc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sdlc import adopt, sync  # noqa: E402

TOOL = Path(__file__).resolve().parent.parent
HOME = TOOL.parents[1]


@pytest.fixture(autouse=True)
def tools_under_home(monkeypatch):
    monkeypatch.setenv("HOME", str(HOME))


def commit_all(repo, msg):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def source(tmp_path):
    """A stand-in ai-sdlc checkout holding the real templates, to evolve in tests."""
    s = tmp_path / "ai-sdlc"
    shutil.copytree(TOOL / "templates", s / "templates")
    git(s, "init", "-q", "-b", "main", "--template=")
    git(s, "config", "user.email", "t@example.com")
    git(s, "config", "user.name", "t")
    commit_all(s, "templates A")
    return s


def render(source, name, description="a test project", marker=True):
    text = adopt.render_text((source / "templates" / name).read_text(), "proj", description, adopt.sdlc_ref(shell=False))
    if marker and name == adopt.MARKED:
        text = adopt.with_marker(text, adopt.source_head(source))
    return text


def adopt_from(source, repo, marker=True):
    for name in adopt.SUBSTRATE:
        (repo / name).write_text(render(source, name, marker=marker))
    commit_all(repo, "adopt")


def edit(path, old, new):
    text = path.read_text()
    assert old in text, old
    path.write_text(text.replace(old, new))


def test_freshly_adopted_project_is_current(bare_repo):
    r = sdlc(bare_repo, "adopt", str(bare_repo), "--apply", "--description", "a test project")
    assert r.returncode == 0, r.stderr
    assert "<!-- ai-sdlc: " in (bare_repo / "AGENTS.md").read_text()
    r = sdlc(bare_repo, "sync", str(bare_repo))
    assert r.returncode == 0, r.stderr
    assert "recorded in AGENTS.md" in r.stdout
    assert "merge template changes" not in r.stdout
    for name in adopt.SUBSTRATE:
        assert f"already current: {bare_repo / name}" in r.stdout


def test_template_changes_merge_and_project_edits_survive(bare_repo, source):
    adopt_from(source, bare_repo)
    edit(bare_repo / "AGENTS.md", "## Rules\n", "## Rules\n\n- **Project rule.** Kept by sync.\n")
    with (bare_repo / "DOCUMENTS.md").open("a") as f:
        f.write("| [SPEC.md](SPEC.md) | The project's spec |\n")
    with (bare_repo / "DECISIONS.md").open("a") as f:
        f.write("| D1 | 2026-11-10 | A project decision. |\n")
    commit_all(bare_repo, "project edits")

    edit(source / "templates" / "AGENTS.md", "- **Don't clutter.**", "- **New template rule.** Arrives by sync.\n- **Don't clutter.**")
    edit(source / "templates" / "DOCUMENTS.md", "Canonical docs.", "Canonical docs, revised.")
    head = commit_all(source, "templates B")

    before = {n: (bare_repo / n).read_text() for n in adopt.SUBSTRATE}
    assert sync.main(str(bare_repo), apply=False, source=source) == 0
    assert {n: (bare_repo / n).read_text() for n in adopt.SUBSTRATE} == before, "dry run wrote"

    assert sync.main(str(bare_repo), apply=True, source=source) == 0
    agents = (bare_repo / "AGENTS.md").read_text()
    assert "- **Project rule.** Kept by sync." in agents
    assert "- **New template rule.** Arrives by sync." in agents
    assert "**proj** — a test project." in agents
    assert agents.endswith(f"<!-- ai-sdlc: {head} -->\n") and agents.count("<!-- ai-sdlc:") == 1
    docs = (bare_repo / "DOCUMENTS.md").read_text()
    assert "Canonical docs, revised." in docs and "| [SPEC.md](SPEC.md) | The project's spec |" in docs
    assert "A project decision." in (bare_repo / "DECISIONS.md").read_text()


def test_conflict_refuses_and_writes_nothing(bare_repo, source, capsys):
    adopt_from(source, bare_repo)
    edit(bare_repo / "AGENTS.md", "- **Don't clutter.** Create a file only when it's needed.", "- **Don't clutter.** The project's wording.")
    commit_all(bare_repo, "project edits the rule")
    edit(source / "templates" / "AGENTS.md", "- **Don't clutter.** Create a file only when it's needed.", "- **Don't clutter.** The template's wording.")
    commit_all(source, "template edits the same rule")
    before = (bare_repo / "AGENTS.md").read_text()
    assert sync.main(str(bare_repo), apply=True, source=source) == 2
    assert (bare_repo / "AGENTS.md").read_text() == before
    err = capsys.readouterr().err
    assert "conflict" in err and "nothing was written" in err


def test_without_a_marker_the_base_is_inferred(bare_repo, source, capsys):
    adopt_from(source, bare_repo, marker=False)
    a = adopt.source_head(source)
    edit(source / "templates" / "AGENTS.md", "- **Don't clutter.**", "- **New template rule.** Arrives by sync.\n- **Don't clutter.**")
    commit_all(source, "templates B")
    assert sync.main(str(bare_repo), apply=True, source=source) == 0
    assert f"sync point {a[:10]} (inferred" in capsys.readouterr().out
    assert "- **New template rule.** Arrives by sync." in (bare_repo / "AGENTS.md").read_text()


def test_off_the_integration_branch_refuses(bare_repo, source, capsys):
    adopt_from(source, bare_repo)
    git(bare_repo, "switch", "-q", "-c", "unit/x")
    assert sync.main(str(bare_repo), apply=True, source=source) == 2
    assert "runs on main" in capsys.readouterr().err


def test_uncommitted_template_changes_refuse(bare_repo, source, capsys):
    adopt_from(source, bare_repo)
    edit(source / "templates" / "AGENTS.md", "- **Don't clutter.**", "- **Uncommitted.**\n- **Don't clutter.**")
    assert sync.main(str(bare_repo), apply=True, source=source) == 2
    assert "uncommitted changes" in capsys.readouterr().err


def test_unknown_recorded_sync_point_refuses(bare_repo, source, capsys):
    adopt_from(source, bare_repo)
    edit(bare_repo / "AGENTS.md", adopt.source_head(source), "0" * 40)
    commit_all(bare_repo, "bogus marker")
    assert sync.main(str(bare_repo), apply=True, source=source) == 2
    assert "not in ai-sdlc's history" in capsys.readouterr().err
