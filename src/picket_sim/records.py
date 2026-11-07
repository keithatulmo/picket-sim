"""Immutable experiment run records and provenance (ADR-0006)."""

from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import __version__

__all__ = ["git_state", "software_versions", "RunDirectory", "sha256_file", "DirtyTreeError"]


class DirtyTreeError(RuntimeError):
    pass


def _git(args, cwd):
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_state(repo_dir) -> dict:
    """Commit hash and dirty flag of the repository containing ``repo_dir`` (None if not a repo)."""
    commit = _git(["rev-parse", "HEAD"], repo_dir)
    if commit is None:
        return {"git_commit": None, "git_dirty": None, "git_status": None}
    status = _git(["status", "--porcelain", "--untracked-files=no"], repo_dir) or ""
    return {"git_commit": commit, "git_dirty": bool(status), "git_status": status.splitlines()}


def software_versions() -> dict:
    import matplotlib
    import numpy
    import yaml

    return {
        "picket_sim": __version__,
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "matplotlib": matplotlib.__version__,
        "pyyaml": yaml.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
    }


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class RunDirectory:
    """A run directory assembled in a temporary location and moved into place on success.

    The final directory must not already exist; nothing is ever overwritten.
    """

    def __init__(self, output_root, run_id: str):
        self.output_root = Path(output_root)
        self.run_id = run_id
        self.final = self.output_root / run_id
        if self.final.exists():
            raise FileExistsError(f"run directory already exists, refusing to overwrite: {self.final}")
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=self.output_root))
        (self.tmp / "tables").mkdir()
        (self.tmp / "figures").mkdir()

    def path(self, *parts) -> Path:
        return self.tmp.joinpath(*parts)

    def finalize(self, record: dict) -> Path:
        files = sorted(p for p in self.tmp.rglob("*") if p.is_file())
        record["outputs"] = [
            {"path": str(p.relative_to(self.tmp)), "sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in files
        ]
        with open(self.tmp / "record.json", "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, sort_keys=True, default=_json_default)
            fh.write("\n")
        if self.final.exists():
            raise FileExistsError(f"run directory appeared during the run, refusing to overwrite: {self.final}")
        os.replace(self.tmp, self.final)
        self._append_index(record)
        return self.final

    def abort(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _append_index(self, record: dict):
        idx = self.output_root / "RUN_INDEX.csv"
        new = not idx.exists()
        with open(idx, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["run_id", "experiment_id", "created_utc", "config_path", "config_sha256",
                            "git_commit", "git_dirty", "picket_sim_version", "status"])
            sw = record.get("software", {})
            w.writerow([record["run_id"], record.get("experiment_id"), record.get("created_utc"),
                        record.get("config_path"), record.get("config_sha256"), sw.get("git_commit"),
                        sw.get("git_dirty"), sw.get("picket_sim"), record.get("status")])


def utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)


def make_run_id(when: _dt.datetime, config_sha: str, git_commit: str | None) -> str:
    return f"{when:%Y%m%dT%H%M%SZ}_{config_sha[:8]}_{(git_commit or 'nogit')[:7]}"


def _json_default(o):
    import numpy as np

    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    return str(o)
