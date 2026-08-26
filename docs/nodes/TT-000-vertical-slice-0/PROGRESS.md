# TT-000 Progress

## Current stage

Stage D — Milestone Implementation

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Gate A — learning charter | Approved by human project owner | `NODE_CONTEXT.md` |
| Gate B — research | Approved by human project owner on 2026-08-26 | `RESEARCH_REPORT.md` |
| Gate C — feature architecture | Approved by human project owner on 2026-08-26 | `FEATURE_CONTEXT.md` |
| Implementation milestones | M0–M2 passed; M3 in progress | Approved `FEATURE_CONTEXT.md` and milestone evidence below |
| Gate D — validation | Blocked pending completed implementation and validation | No validation review |

## Implementation state

- Implementation branch: `feature/TT-000-vertical-slice-0`
- Active milestone: M3 — Detailed multi-rate model and activation
- Implementation status: In progress

## Completed

- [x] Created and approved the V0 learning charter.
- [x] Created and executed the V0 deep-research prompt.
- [x] Produced `RESEARCH_REPORT.md`.
- [x] Gate B approved by the human project owner on 2026-08-26.
- [x] Entered Stage C — Feature Architecture.
- [x] Replaced the blocked `FEATURE_CONTEXT.md` placeholder with a Stage C draft and Gate C checklist.
- [x] Gate C approved by the human project owner on 2026-08-26.
- [x] Created and switched to `feature/TT-000-vertical-slice-0`.
- [x] Entered Stage D — Milestone Implementation.
- [x] M0 — Foundations and decisions passed its approved gate.
- [x] M1 — Deterministic kernel passed its approved gate.
- [x] M2 — Grid-connected fallback slice passed its approved gate.

## Active work

M3 — Detailed multi-rate model and activation. Its prerequisite M2 passed and is recorded below.

## Test evidence

### M0 — Foundations and decisions

- Status: Passed
- Implementation commit: `f89c793` (`feat(TT-000): establish M0 contracts and boundaries`)
- Runtime provisioned and verified: CPython 3.14.7, Windows x86-64
- Locked direct versions: Pydantic 2.13.4, FastAPI 0.141.1, Uvicorn 0.52.4 and pytest 9.1.1
- Complete transitive lock: `requirements.lock`
- License evidence: `DEPENDENCY_LICENSES.md`
- Architecture decision: `docs/decisions/ADR-0001-deterministic-time-contracts-and-snapshots.md`

Commands and results:

1. `py -3.14 -c "import sys; print(sys.version); print(sys.executable)"`
   - Passed: CPython 3.14.7 selected.
2. `.\.venv\Scripts\python.exe -m pytest tests/m0 -q`
   - Initial run: 81 passed, 1 failed. The failure was an ADR test that compared a phrase across a Markdown line wrap; the ADR already contained the approved decision. The assertion was normalized for whitespace.
   - Gate rerun: 82 passed in 1.74 s.
3. Fresh temporary CPython 3.14.7 environment: install `requirements.lock`, install the project with `--no-deps`, then `.\Scripts\python.exe -m pytest tests/m0 -q`.
   - Passed: 82 tests in 1.29 s from the clean locked environment.
4. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
5. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
6. `git diff --check`
   - Passed.

Gate coverage:

- Every registered V1 domain record round-trips through its Pydantic edge DTO and canonical JSON.
- Wrong major version, NaN/infinity, wrong active-power unit and absent/empty causal fields are rejected.
- Equivalent values serialize deterministically with sorted finite JSON.
- DTO mapping returns only frozen standard-library domain state; Pydantic is confined to the serialization adapter.
- Forbidden-import and approved package-layout checks pass.
- Exact runtime/direct versions, all locked transitive distributions and license inventory are checked.
- ADR-0001 is accepted through Gate C and contains the approved phase order, authority order and snapshot policy.

### M1 — Deterministic kernel

- Status: Passed
- Implementation commit: `a4ed9c5` (`feat(TT-000): implement deterministic M1 kernel`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m1 tests/m0 -q`
   - Passed: 102 tests in 1.36 s, including all M0 regressions.
2. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
3. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
4. `git diff --check`
   - Passed.

Gate coverage:

- Hand-authored exact order passes across all eleven approved phases.
- Equal-phase work orders by source order and then insertion sequence.
- Same-tick later-phase scheduling succeeds; equal/completed-phase and closed-tick scheduling fail deterministically.
- Cancellation tombstones, semantic queue order, insertion counter and per-source deterministic ID counters survive export/restore.
- The fixed-ratio toy completes exact integer ticks with ten child completions per macro period.
- Fast-forward and paced toy traces are byte-identical after wall diagnostics are excluded.
- A forced pacer overrun records infrastructure diagnostics without altering logical trace or final tick.

### M2 — Grid-connected fallback slice

- Status: Passed
- Implementation commit: `197fe25` (`feat(TT-000): deliver M2 fallback vertical slice`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m2 tests/m1 tests/m0 -q`
   - Passed: 120 tests in 1.47 s, including all M0–M1 regressions.
2. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 120 tests in 1.37 s.
3. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
4. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
5. `git diff --check`
   - Passed.

Gate coverage:

- Closed PCC connectivity is one sorted component containing GRID and LOCAL and the infinite source.
- Lossless fallback charge/discharge follows the analytic energy equation within 1e-12 relative/absolute MWh tolerance.
- Pre-step feasible limiting prevents either energy bound from being exceeded by more than 1e-12 MWh.
- Nameplate-out-of-range requests are rejected; tighter energy feasibility produces `ACCEPTED_WITH_LIMIT` and an explicit reason.
- Valid, exact duplicate, stale-source-sequence, expired and wrong model/topology version cases are deterministic.
- Requested, accepted, controller target and model-applied power remain separate owned fields.
- Grid import equals `P_load - P_ac`; the macro publication includes end, mean and integral values, quality, versions, acknowledgement and residual.

## Decisions and deviations

- Gate B evidence: `RESEARCH_REPORT.md`.
- Gate C evidence: `FEATURE_CONTEXT.md`.
- Gate C approval: Human project owner, 2026-08-26.
- Approved implementation branch: `feature/TT-000-vertical-slice-0`.
- The substantive content of the approved research report remains unchanged.
- ADR-0001 transcribes the Gate C-approved contract, time, event-ordering, command-authority and snapshot decisions without adding a new design choice.
- Domain contracts are frozen standard-library dataclasses/enums; generated Pydantic DTOs and JSON mapping remain in `adapters.serialization`.
- The exact approved CPython 3.14.7 runtime was absent initially and was provisioned at user scope from the verified Python package source.
- M1 uses typed scheduler events rather than callbacks or arbitrary payload dictionaries; handlers execute synchronously in the sole owner.
- M2 connectivity uses a deterministic sorted BFS and returns typed topology records; active-power balance remains a separate service.
- The fallback BESS computes energy-feasible power before integration and does not repair energy by post-step clipping.
- No architecture or scope deviations recorded. The only failed test to date was the corrected M0 whitespace-sensitive documentation assertion described above.

## Next permitted action

Implement only M3, run every M3 gate test plus applicable M0–M2 regressions, and continue to M4 only if the M3 gate passes.
