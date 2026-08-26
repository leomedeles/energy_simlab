# TT-000 M0 Runtime and Dependency Inventory

## Evidence profile

- Inventory date: 2026-08-27
- Runtime: CPython 3.14.7, Windows x86-64
- Project lock: `requirements.lock`
- Build backend: setuptools 84.0.0
- Direct domain/edge dependency: Pydantic 2.13.4
- Direct API dependencies: FastAPI 0.141.1 and Uvicorn 0.52.4
- Direct test dependency: pytest 9.1.1

The versions below are the complete installed dependency set produced from the
approved direct versions. The license expressions come from installed package
metadata; Colorama uses its bundled BSD license file and BSD classifier. This
inventory establishes reproducible implementation evidence, not a security or
legal-compliance certification.

| Package/runtime | Version | Relationship | Declared license |
|---|---:|---|---|
| CPython | 3.14.7 | Runtime | PSF License |
| annotated-doc | 0.0.5 | FastAPI transitive | MIT |
| annotated-types | 0.8.0 | Pydantic transitive | MIT |
| anyio | 4.14.2 | Starlette transitive | MIT |
| click | 8.5.0 | Uvicorn transitive | BSD-3-Clause |
| colorama | 0.4.6 | pytest/click Windows transitive | BSD |
| FastAPI | 0.141.1 | Direct API adapter | MIT |
| h11 | 0.16.0 | Uvicorn transitive | MIT |
| idna | 3.19 | AnyIO transitive | BSD-3-Clause |
| iniconfig | 2.3.0 | pytest transitive | MIT |
| packaging | 26.3 | pytest transitive | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.6.0 | pytest transitive | MIT |
| Pydantic | 2.13.4 | Direct serialization edge | MIT |
| pydantic-core | 2.46.4 | Pydantic transitive | MIT |
| Pygments | 2.21.0 | pytest transitive | BSD-2-Clause |
| pytest | 9.1.1 | Direct test tool | MIT |
| setuptools | 84.0.0 | Locked build backend | MIT |
| Starlette | 1.6.0 | FastAPI transitive | BSD-3-Clause |
| typing-extensions | 4.16.0 | FastAPI/Pydantic transitive | PSF-2.0 |
| typing-inspection | 0.4.4 | FastAPI/Pydantic transitive | MIT |
| Uvicorn | 0.52.4 | Direct API runtime adapter | BSD-3-Clause |

## Boundary decisions

- Domain packages import only the Python standard library and
  `energy_simlab.contracts`.
- Pydantic is confined to `energy_simlab.adapters.serialization`.
- FastAPI and Uvicorn are confined to `energy_simlab.adapters.api` and the
  composition root.
- pytest and its support packages are test/build dependencies only.
- No package in this inventory establishes protocol interoperability,
  standards conformance, electrical-model validity, or production suitability.

