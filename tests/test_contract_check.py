from pathlib import Path

import pytest

from conftest import git, sdlc

GOOD = """# Contract: 2026-10-14-fix-parser

## Purpose and relationship
The parser drops trailing fields. Fixing it unblocks the import work.

## Scope and return
Fix `parse_row` and add a regression test. No schema changes.

Reserved: none

## Authoritative inputs
[spec](docs/spec.md) section 3; D2.

## Execution arrangement
Writer in a worktree on the unit branch; may edit src/ and tests/ only.

Model: haiku

## Effort and stopping
Stop and report if the fix needs a schema change.

Turns: 30
Repairs: 2

## Acceptance and closure
The new test fails before and passes after. Review, then `sdlc integrate`.
"""


@pytest.fixture
def project(bare_repo):
    (bare_repo / "DOCUMENTS.md").write_text("# Documents\n\n| Doc | Purpose |\n|---|---|\n| [spec](docs/spec.md) | Spec |\n")
    (bare_repo / "DECISIONS.md").write_text(
        "# Decisions\n\n| # | Date | Decision |\n|---|---|---|\n"
        "| D1 | 2026-01-01 | One. |\n| ~~D2~~ | ~~2026-01-01~~ | ~~Two.~~ Superseded by D3. |\n| D3 | 2026-01-02 | Three. |\n")
    (bare_repo / "docs").mkdir()
    (bare_repo / "docs" / "spec.md").write_text("# spec\n")
    (bare_repo / "contracts").mkdir()
    return bare_repo


def write(project, text, name="2026-10-14-fix-parser.md", where="contracts"):
    p = project / where / name
    p.parent.mkdir(exist_ok=True)
    p.write_text(text)
    return p


def check(project, path, *flags):
    return sdlc(project, "contract", "check", str(path), *flags)


def test_good_contract_is_ready(project):
    p = write(project, GOOD.replace("D2", "D3"))
    r = check(project, p)
    assert r.returncode == 0, r.stderr
    assert "ready: 2026-10-14-fix-parser -> unit/2026-10-14-fix-parser" in r.stdout
    assert "turns=30 repairs=2" in r.stdout


def test_json_output_carries_what_dispatch_needs(project):
    import json
    p = write(project, GOOD.replace("D2", "D3"))
    data = json.loads(check(project, p, "--json").stdout)
    assert data["branch"] == "unit/2026-10-14-fix-parser"
    assert data["turns"] == 30 and data["repairs"] == 2
    assert data["docs"] == ["docs/spec.md"] and data["decisions"] == ["D3"]
    assert data["model"] == "haiku" and data["reserved"] == "none"


def test_superseded_decision_is_refused(project):
    p = write(project, GOOD)
    r = check(project, p)
    assert r.returncode == 2
    assert "D2 is superseded" in r.stderr


def test_unknown_decision_is_refused(project):
    p = write(project, GOOD.replace("D2", "D99"))
    r = check(project, p)
    assert r.returncode == 2 and "D99 is not in DECISIONS.md" in r.stderr


def test_uncanonical_doc_is_refused(project):
    p = write(project, GOOD.replace("D2", "D3").replace("docs/spec.md", "docs/notes.md"))
    r = check(project, p)
    assert r.returncode == 2 and "docs/notes.md is not listed in DOCUMENTS.md" in r.stderr


def test_no_citations_is_refused(project):
    text = GOOD.replace("[spec](docs/spec.md) section 3; D2.", "Just do it.")
    r = check(project, write(project, text))
    assert r.returncode == 2 and "cite nothing" in r.stderr


def test_template_copy_is_refused_with_every_gap_named(project):
    template = (Path(__file__).resolve().parent.parent / "templates" / "CONTRACT.md").read_text()
    r = check(project, write(project, template))
    assert r.returncode == 2
    assert "placeholders" in r.stderr
    assert "'## Purpose and relationship' has no content" in r.stderr
    assert "'## Acceptance and closure' has no content" in r.stderr


def test_missing_section_is_refused(project):
    text = GOOD.replace("D2", "D3").replace("## Effort and stopping\n", "## Effort\n")
    r = check(project, write(project, text))
    assert r.returncode == 2
    assert "Missing section '## Effort and stopping'" in r.stderr
    assert "No `Turns:` line" in r.stderr


def test_effort_lines_must_be_positive_integers(project):
    text = GOOD.replace("D2", "D3").replace("Turns: 30", "Turns: lots").replace("Repairs: 2", "Repairs: 0")
    r = check(project, write(project, text))
    assert r.returncode == 2
    assert "`Turns:` must be a positive integer" in r.stderr
    assert "`Repairs:` must be a positive integer" in r.stderr


def test_missing_reserved_line_is_refused(project):
    text = GOOD.replace("D2", "D3").replace("Reserved: none\n", "")
    r = check(project, write(project, text))
    assert r.returncode == 2 and "No `Reserved:` line" in r.stderr


def test_wrong_location_or_name_is_refused(project):
    r = check(project, write(project, GOOD.replace("D2", "D3"), where="docs"))
    assert r.returncode == 2 and "must live at" in r.stderr
    r = check(project, write(project, GOOD.replace("D2", "D3"), name="Fix_Parser.md"))
    assert r.returncode == 2 and "must live at" in r.stderr


def test_nonexistent_file_is_refused(project):
    r = check(project, project / "contracts" / "nope.md")
    assert r.returncode == 2 and "does not exist" in r.stderr
