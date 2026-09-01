# Hierarchical Energy Co-Simulation Lab

This learning-first laboratory now contains the implementation of the approved TT-000 vertical slice on `feature/TT-000-vertical-slice-0`. The implementation is not yet validated, integrated, or unlocked; it is being prepared for a separate Gate D review.

TT-000 demonstrates deterministic logical time, two BESS fidelity levels, topology and unsupported-island handling, typed commands/telemetry/alarms, complete snapshots with branching replay, and an isolated HTTP/WebSocket viewer edge.

Corrective Stage D milestones R0–R3 are implemented on the feature branch and the post-correction evidence package is ready for human review. This is not Gate D approval: TT-000 remains unvalidated, unintegrated, inactive and locked, and GitHub issue #1 remains open.

## Developer setup

The exact replay profile is CPython 3.14.7 on Windows x86-64. From PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

`requirements.lock` contains the complete transitive environment used for evidence. Exact direct versions and licenses are recorded in `pyproject.toml` and `docs/nodes/TT-000-vertical-slice-0/DEPENDENCY_LICENSES.md`.
The locked API profile includes `wsproto`; no separate WebSocket package install is required.

## Deterministic reference scenario

Run suffix A in fast-forward mode:

```powershell
.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix A
```

Run the same scenario with real wall-clock pacing (about 12 seconds), or print the full canonical trace:

```powershell
.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode paced --suffix A
.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix A --trace
```

The alternative deterministic continuation is:

```powershell
.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix B
```

The approved scenario applies +0.4 MW to the fallback model, activates the detailed model, requests -1.0 MW, opens PCC, captures at tick 90, then either acknowledges the active island alarm (suffix A) or rejects an island dispatch with `TARGET_MODE_UNAVAILABLE` (suffix B). Golden hashes and outcomes are asserted in `tests/m7/test_reference_demonstration.py`.

The corrective owner executes every elapsed macro. The current same-profile suffix-A trace/final-snapshot hashes are `53650f4800bf07fe37fc50a9a5525fd16d047b6f8dc4a4fb3b7aa170623d1993` / `98453c1efd2773d1cf9d3633f95dcda49cfdf54a9edc6400d38a208a78f4516d`; suffix B is `98c17a30e824810d81eaf614902cc14b8bfaed48d34559a3c65a9b53213f843d` / `7992c44ce5cb6af438e27b373b6b12c03978e3a51cbfd4c3aa1588388ddb8bec`. The pre-correction hashes remain preserved in `PROGRESS.md` and `VALIDATION_REPORT.md` as failed Gate D evidence.

## HTTP/WebSocket viewer

Launch the single-owner adapter:

```powershell
.\.venv\Scripts\python.exe -m energy_simlab.bootstrap --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/`. The static single-line viewer reads canonical HTTP schemas, admits operator commands only for future macro boundaries, and observes canonical publications on `/api/v1/publications`. HTTP admission returns 202; the final canonical acknowledgement is read separately after deterministic boundary processing.

The ASGI lifespan starts one paced owner task. With the default profile it completes one logical 1 s macro per wall-clock second, publishes while idle, drains admitted commands only at their apply boundary, and finishes any started macro before shutdown. The viewer updates its command field to the next future macro tick after every publication. `--pace-seconds` may shorten or lengthen wall pacing for diagnostics without changing logical duration, phase order, child count, or canonical results.

The in-memory owner supports exactly one ASGI worker and rejects auto-reload. Viewer queues hold 64 publication frames. Slow telemetry is coalesced by signal; discrete overflow disconnects that viewer with a resynchronization reason. Viewer connections, render rate, queues, drops, and wall-clock diagnostics cannot change canonical simulation results.

## Implemented boundaries

- `energy_simlab.contracts`: frozen standard-library V1 records, enums, units, and ports.
- `energy_simlab.kernel`: synchronous integer-time scheduler and pacing seam.
- `energy_simlab.models.bess`: bounded fallback and reduced-order detailed BESS models with atomic one-way activation.
- `energy_simlab.topology`, `balance`, `control`, and `alarms`: deterministic connectivity, algebraic active-power bookkeeping, command ownership, safe-zero interlock, and alarm lifecycle.
- `energy_simlab.snapshots` and adapters: complete state inventory, compatibility policy, canonical JSON, SHA-256 integrity, and fresh-runtime restore.
- `energy_simlab.adapters.api` and `viewer`: typed HTTP/WebSocket mappings and bounded observation-only fan-out.

## Explicit limitations

TT-000 is an educational aggregate active-power and usable-energy model. It does not implement or claim voltage, frequency, current, reactive power, AC/DC power flow, electrical island stability, grid-forming control, protection-grade behavior, physical breaker travel, device-calibrated battery behavior, degradation, thermal behavior, industrial-protocol interoperability, cybersecurity, standards compliance, or production suitability. PCC reclosing and detailed-to-fallback activation are outside the approved scope.

## Project reading order

1. [`MASTER_PROJECT_CONTEXT.md`](MASTER_PROJECT_CONTEXT.md) — project constitution and invariants.
2. [`NORTH_STAR.md`](NORTH_STAR.md) — long-term direction.
3. [`DEVELOPMENT_PROTOCOL.md`](DEVELOPMENT_PROTOCOL.md) — gated lifecycle.
4. [`TECH_TREE.md`](TECH_TREE.md) — validated live capability state; TT-000 remains locked pending Gate D.
5. [`ARCHITECTURE.md`](ARCHITECTURE.md) — validated architecture ledger; implementation evidence is not entered there before Gate D.
6. [`docs/nodes/TT-000-vertical-slice-0/FEATURE_CONTEXT.md`](docs/nodes/TT-000-vertical-slice-0/FEATURE_CONTEXT.md) — approved TT-000 specification.
7. [`docs/nodes/TT-000-vertical-slice-0/PROGRESS.md`](docs/nodes/TT-000-vertical-slice-0/PROGRESS.md) — sequential implementation evidence.

Codex and other implementation agents must also read [`AGENTS.md`](AGENTS.md).
