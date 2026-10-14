import subprocess
import sys
from pathlib import Path

SDLC = Path(__file__).resolve().parent.parent / "bin" / "sdlc"


def run(*args):
    return subprocess.run([sys.executable, str(SDLC), *args], capture_output=True, text=True)


def test_help_lists_every_workflow_tool():
    out = run("--help").stdout
    for name in ("adopt", "contract", "dispatch", "check-protected", "review", "integrate"):
        assert name in out


def test_no_command_is_an_error():
    assert run().returncode == 2
