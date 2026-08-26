# TT-000 Progress

## Current stage

Stage D — Milestone Implementation

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Gate A — learning charter | Approved by human project owner | `NODE_CONTEXT.md` |
| Gate B — research | Approved by human project owner on 2026-08-26 | `RESEARCH_REPORT.md` |
| Gate C — feature architecture | Approved by human project owner on 2026-08-26 | `FEATURE_CONTEXT.md` |
| Implementation milestones | M0 passed; M1 in progress | Approved `FEATURE_CONTEXT.md` and milestone evidence below |
| Gate D — validation | Blocked pending completed implementation and validation | No validation review |

## Implementation state

- Implementation branch: `feature/TT-000-vertical-slice-0`
- Active milestone: M1 — Deterministic kernel
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

## Active work

M1 — Deterministic kernel. Its prerequisite M0 passed and is recorded below.

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

## Decisions and deviations

- Gate B evidence: `RESEARCH_REPORT.md`.
- Gate C evidence: `FEATURE_CONTEXT.md`.
- Gate C approval: Human project owner, 2026-08-26.
- Approved implementation branch: `feature/TT-000-vertical-slice-0`.
- The substantive content of the approved research report remains unchanged.
- ADR-0001 transcribes the Gate C-approved contract, time, event-ordering, command-authority and snapshot decisions without adding a new design choice.
- Domain contracts are frozen standard-library dataclasses/enums; generated Pydantic DTOs and JSON mapping remain in `adapters.serialization`.
- The exact approved CPython 3.14.7 runtime was absent initially and was provisioned at user scope from the verified Python package source.
- No architecture or scope deviations recorded. The only failed M0 test was the corrected whitespace-sensitive documentation assertion described above.

## Next permitted action

Implement only M1, run every M1 gate test plus applicable M0 regressions, and continue to M2 only if the M1 gate passes.
