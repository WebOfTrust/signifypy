"""Signify package metadata."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib


def _source_tree_version() -> str:
    """Read the package version from pyproject.toml in a source checkout."""
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject.open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


try:
    __version__ = version("signifypy")
except PackageNotFoundError:
    __version__ = _source_tree_version()
