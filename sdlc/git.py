"""Thin git helpers. Every call fails closed: a git error raises GitError."""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def run(args: list[str], cwd: Path | None = None) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    except FileNotFoundError as e:
        raise GitError("git is not installed") from e
    except subprocess.CalledProcessError as e:
        raise GitError(e.stderr.strip() or f"git {' '.join(args)} failed") from e
    return r.stdout


def toplevel(cwd: Path | None = None) -> Path:
    return Path(run(["rev-parse", "--show-toplevel"], cwd).strip())


def current_branch(cwd: Path | None = None) -> str | None:
    """Branch name, or None when HEAD is detached."""
    try:
        return run(["symbolic-ref", "--short", "-q", "HEAD"], cwd).strip() or None
    except GitError:
        return None


def staged_paths(cwd: Path | None = None) -> list[str]:
    out = run(["diff", "--cached", "--name-only", "--no-renames", "-z"], cwd)
    return [p for p in out.split("\0") if p]
