from __future__ import annotations

import ast
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "energy_simlab"

EXPECTED_PACKAGES = {
    "contracts",
    "kernel",
    "models/bess",
    "control",
    "topology",
    "balance",
    "alarms",
    "snapshots",
    "application",
    "adapters/serialization",
    "adapters/api",
    "adapters/persistence",
    "viewer",
    "bootstrap",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
    return names


def test_approved_source_layout_exists():
    missing = [name for name in sorted(EXPECTED_PACKAGES) if not (PACKAGE / name / "__init__.py").is_file()]
    assert missing == []


@pytest.mark.parametrize("path", sorted(PACKAGE.rglob("*.py")))
def test_external_dependencies_are_confined_to_approved_adapters(path: Path):
    relative = path.relative_to(PACKAGE).as_posix()
    for imported in _imports(path):
        root = imported.split(".", 1)[0]
        if root == "pydantic":
            assert relative.startswith("adapters/serialization/")
        if root in {"fastapi", "uvicorn"}:
            assert relative.startswith("adapters/api/") or relative.startswith("bootstrap/")


@pytest.mark.parametrize(
    "domain_package",
    ["contracts", "kernel", "models", "control", "topology", "balance", "alarms", "snapshots"],
)
def test_domain_packages_import_only_stdlib_or_canonical_contracts(domain_package: str):
    package_path = PACKAGE / domain_package
    violations: list[str] = []
    for path in package_path.rglob("*.py"):
        for imported in _imports(path):
            root = imported.split(".", 1)[0]
            if root in sys.stdlib_module_names or root == "energy_simlab":
                continue
            violations.append(f"{path.relative_to(ROOT)} imports {imported}")
    assert violations == []


@pytest.mark.parametrize(
    "domain_package",
    ["kernel", "models", "control", "topology", "balance", "alarms", "snapshots"],
)
def test_domain_dependency_direction_allows_only_contracts(domain_package: str):
    violations: list[str] = []
    package_path = PACKAGE / domain_package
    for path in package_path.rglob("*.py"):
        for imported in _imports(path):
            if imported.startswith("energy_simlab") and not imported.startswith("energy_simlab.contracts"):
                violations.append(f"{path.relative_to(ROOT)} imports {imported}")
    assert violations == []


def test_domain_source_contains_no_arbitrary_dictionary_contract_annotations():
    violations: list[str] = []
    for path in (PACKAGE / "contracts").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in {"dict", "Dict"}:
                violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert violations == []
