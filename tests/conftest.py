import subprocess
import sys
from pathlib import Path

import pytest

SDLC = Path(__file__).resolve().parent.parent / "bin" / "sdlc"


def git(repo, *args, stdin=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, input=stdin).stdout


def sdlc(cwd, *args, stdin=""):
    return subprocess.run([sys.executable, str(SDLC), *args], cwd=cwd, capture_output=True, text=True, input=stdin)


@pytest.fixture
def bare_repo(tmp_path):
    """An initialized git repo with one commit and no substrate."""
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main", "--template=")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "t")
    (r / "README.md").write_text("# proj\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r
