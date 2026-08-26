from __future__ import annotations

from importlib import metadata
from pathlib import Path
import re
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[2]
LOCK_LINE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s]+)$")


def _normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _locked() -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in (ROOT / "requirements.lock").read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCK_LINE.fullmatch(line)
        assert match is not None, f"unlocked or malformed requirement: {line}"
        result[_normalized(match.group(1))] = match.group(2)
    return result


def test_runtime_profile_is_exact():
    assert sys.version_info[:3] == (3, 14, 7)
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.14.7"


def test_approved_direct_versions_are_exact_and_installed():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["requires-python"] == ">=3.14.7,<3.15"
    assert pyproject["project"]["dependencies"] == ["pydantic==2.13.4"]
    assert pyproject["project"]["optional-dependencies"]["api"] == [
        "fastapi==0.141.1",
        "uvicorn==0.52.4",
    ]
    assert pyproject["project"]["optional-dependencies"]["test"] == ["pytest==9.1.1"]

    lock = _locked()
    expected = {
        "pydantic": "2.13.4",
        "fastapi": "0.141.1",
        "uvicorn": "0.52.4",
        "pytest": "9.1.1",
        "setuptools": "84.0.0",
    }
    for package, version in expected.items():
        assert lock[package] == version
        assert metadata.version(package) == version


def test_every_locked_distribution_is_installed_at_the_locked_version():
    for package, version in _locked().items():
        assert metadata.version(package) == version


def test_license_inventory_covers_runtime_and_every_locked_distribution():
    inventory = (ROOT / "docs/nodes/TT-000-vertical-slice-0/DEPENDENCY_LICENSES.md").read_text(encoding="utf-8")
    assert "CPython | 3.14.7" in inventory
    for package, version in _locked().items():
        assert package in inventory.lower()
        assert version in inventory

