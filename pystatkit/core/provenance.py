"""Run provenance: captures Git commit, timestamps, and data hashes.

Every output includes this metadata so results can always be traced back
to the exact code and data that produced them.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pystatkit import __version__


@dataclass
class RunMetadata:
    """Metadata recorded alongside every analysis output."""

    pystatkit_version: str
    timestamp: str
    git_commit: str
    git_dirty: bool
    python_version: str
    platform: str
    data_hash: str
    config_path: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "pystatkit_version": self.pystatkit_version,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "python_version": self.python_version,
            "platform": self.platform,
            "data_hash": self.data_hash,
            "config_path": self.config_path,
        }


def _get_git_info(repo_path: Path | None = None) -> tuple[str, bool]:
    """Return (short commit hash, dirty flag). Returns ('unknown', False) if not a repo."""
    cwd = repo_path or Path.cwd()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return commit, bool(status)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown", False


def get_run_metadata(
    data_hash: str, config_path: str | Path, repo_path: Path | None = None
) -> RunMetadata:
    """Collect all provenance metadata for the current run.

    Parameters
    ----------
    data_hash : str
        Hash of the input DataFrame (from `hash_data`).
    config_path : str or Path
        Path to the config file used for this run.
    repo_path : Path, optional
        Path to the Git repository (defaults to current working directory).

    Returns
    -------
    RunMetadata
        Populated metadata dataclass.
    """
    commit, dirty = _get_git_info(repo_path)
    return RunMetadata(
        pystatkit_version=__version__,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        git_commit=commit,
        git_dirty=dirty,
        python_version=platform.python_version(),
        platform=platform.platform(),
        data_hash=data_hash,
        config_path=str(config_path),
    )
