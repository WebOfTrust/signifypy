#!/usr/bin/env python
"""Synchronize pinned source repos and virtualenvs for live integration tests."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SIGNIFYPY_ROOT = Path(__file__).resolve().parents[1]
CONSTRAINTS = SIGNIFYPY_ROOT / ".github" / "constraints" / "integration.txt"
SIGNIFYPY_VENV_PYTHON = SIGNIFYPY_ROOT / "venv" / "bin" / "python"

sys.path.insert(0, str(SIGNIFYPY_ROOT))
from tests.integration.dependencies import INTEGRATION_DEPENDENCIES, KERIA, KERIPY, VLEI  # noqa: E402


def run(*args: str, cwd: Path | None = None) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=cwd, check=True)


def sync_repo(root: Path, repo: str, ref: str) -> None:
    if not root.exists():
        root.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", repo, str(root))
    else:
        run("git", "-C", str(root), "remote", "set-url", "origin", repo)

    run("git", "-C", str(root), "fetch", "--tags", "--force", "origin")
    run("git", "-C", str(root), "fetch", "origin")
    run("git", "-C", str(root), "checkout", "--detach", ref)


def ensure_venv(venv: Path) -> Path:
    python = venv / "bin" / "python"
    if not python.exists():
        run(sys.executable, "-m", "venv", str(venv))
    return python


def pip_install(python: Path, *args: str) -> None:
    run(str(python), "-m", "pip", *args)


def install_signifypy_runtime(deps_root: Path) -> None:
    if not SIGNIFYPY_VENV_PYTHON.exists():
        raise RuntimeError(
            f"SignifyPy venv is missing at {SIGNIFYPY_VENV_PYTHON}. "
            "Run `make sync` before `make sync-integration-deps`."
        )

    keripy_root = deps_root / KERIPY.path_name
    pip_install(SIGNIFYPY_VENV_PYTHON, "install", "--upgrade", "pip", "setuptools", "wheel")
    pip_install(SIGNIFYPY_VENV_PYTHON, "install", "-c", str(CONSTRAINTS), "hio==0.6.14")
    pip_install(SIGNIFYPY_VENV_PYTHON, "install", "-c", str(CONSTRAINTS), "-e", str(keripy_root))


def install_keria_runtime(deps_root: Path) -> None:
    python = ensure_venv(deps_root / KERIA.path_name / "venv")
    keripy_root = deps_root / KERIPY.path_name
    keria_root = deps_root / KERIA.path_name
    pip_install(python, "install", "--upgrade", "pip", "setuptools", "wheel")
    pip_install(python, "install", "-c", str(CONSTRAINTS), "hio==0.6.14")
    pip_install(python, "install", "-c", str(CONSTRAINTS), "-e", str(keripy_root), "-e", str(keria_root))


def install_vlei_runtime(deps_root: Path) -> None:
    python = ensure_venv(deps_root / VLEI.path_name / "venv")
    keripy_root = deps_root / KERIPY.path_name
    vlei_root = deps_root / VLEI.path_name
    pip_install(python, "install", "--upgrade", "pip", "setuptools", "wheel")
    pip_install(python, "install", "-c", str(CONSTRAINTS), "hio==0.6.14")
    pip_install(python, "install", "-c", str(CONSTRAINTS), "-e", str(keripy_root), "-e", str(vlei_root))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deps-root",
        default=str(SIGNIFYPY_ROOT / ".integration-deps"),
        help="directory where pinned integration source repos should be stored",
    )
    args = parser.parse_args()

    deps_root = Path(args.deps_root).expanduser().resolve()
    for dependency in INTEGRATION_DEPENDENCIES:
        sync_repo(deps_root / dependency.path_name, dependency.repo, dependency.ref)

    install_signifypy_runtime(deps_root)
    install_keria_runtime(deps_root)
    install_vlei_runtime(deps_root)


if __name__ == "__main__":
    main()
