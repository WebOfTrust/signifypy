from pathlib import Path
import tomllib

from signify import __version__


def test_package_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject.open("rb") as handle:
        declared_version = tomllib.load(handle)["project"]["version"]

    assert __version__ == declared_version
    assert not __version__.startswith("v")
