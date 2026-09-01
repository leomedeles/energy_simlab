# TT-000 Progress

## Current stage

Stage D — Corrective Milestone Implementation

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Gate A — learning charter | Approved by human project owner | `NODE_CONTEXT.md` |
| Gate B — research | Approved by human project owner on 2026-08-26 | `RESEARCH_REPORT.md` |
| Gate C — original feature architecture | Approved by human project owner on 2026-08-26 | `FEATURE_CONTEXT.md` |
| Original implementation milestones | M0–M7 developer gates historically passed; evidence preserved but insufficient for integrated completion | Milestone evidence below; 180-test and suffix results |
| Gate D — validation | **Not approved on 2026-09-01; corrective evidence ready for re-review** | `VALIDATION_REPORT.md`; GitHub issue #1; manual and post-correction evidence |
| Corrective Gate C amendment | **Approved by human project owner on 2026-09-01** | `FEATURE_CONTEXT_AMENDMENT_01.md`; accepted `ADR-0002` |
| Corrective implementation | R0–R3 developer gates passed; human review pending | Approved amendment; corrective commits and evidence below |

## Implementation state

- Implementation branch: `feature/TT-000-vertical-slice-0`
- Preserved pre-correction baseline: `f5ca22e28bdf6a32324c7d10021ff24f3d34ba85`
- Corrective Gate C approval: Human project owner, 2026-09-01
- Accepted corrective decision: `ADR-0002-integrated-runtime-owner-and-server-lifecycle.md`
- Active milestone: None — corrective developer work stopped for human review
- Current developer authorization: R0 through R3 completed sequentially
- Implementation status: Corrective evidence package ready for human review; Gate D not approved
- Node status: Unvalidated, unintegrated, inactive and locked

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
- [x] M3 — Detailed multi-rate model and activation passed its approved gate.
- [x] M4 — Topology event and alarm lifecycle passed its approved gate.
- [x] M5 — Snapshot and branching replay passed its approved gate.
- [x] M6 — Asynchronous API and viewer passed its approved gate.
- [x] M7 — Reference demonstration and validation package passed its approved developer gate.
- [x] Human Gate D manual review reproduced the locked WebSocket dependency defect.
- [x] Human Gate D manual review reproduced admitted-but-unprocessed live commands, an empty trace and no tick/publication advancement.
- [x] Human Gate D manual review reproduced scheduler-only commandless advancement without held-input physics.
- [x] Gate D was not approved on 2026-09-01.
- [x] Stage C was reopened without rewriting the original approval or implementation history.
- [x] Drafted `FEATURE_CONTEXT_AMENDMENT_01.md` and accepted `ADR-0002`.
- [x] Human project owner reviewed and approved the corrective Gate C amendment on 2026-09-01.
- [x] ADR-0002 accepted through the corrective Gate C approval.
- [x] Corrective Stage D milestones R0–R3 authorized by the approved amendment.
- [x] R0 — Characterize and repair the executable profile passes.
- [x] R1 — Integrated deterministic runtime owner passes.
- [x] R2 — Operational ASGI composition passes.
- [x] R3 — Regression and Gate D package passes.
- [ ] Gate D revalidation passes.

## Active work

Corrective Stage D developer work is complete through R3 and has stopped for human review. Passing corrective developer gates does not approve Gate D. No integration, tree/architecture-ledger update, issue closure, merge or next-node work is authorized.

## Corrective Gate D loop

### Corrective implementation preflight

- Audit date: 2026-09-01
- Branch before corrective implementation: `feature/TT-000-vertical-slice-0`
- Commit before corrective implementation: `de961caa13d41c22b9de1c9ffe7e3a51ad5b04d3`
- Working-tree status before corrective implementation: clean (`git status --short` produced no output)
- Preserved failed Gate D baseline: `f5ca22e28bdf6a32324c7d10021ff24f3d34ba85`; its 180-test result, suffix hashes and GD-001 through GD-003 observations below remain unchanged.
- Governance commits between the failed baseline and the corrective implementation commit contain only the approved amendment, ADR and failed-validation records; `git diff --name-status f5ca22e..de961ca` showed no implementation-file changes.
- The project `.venv` contained the reviewer's diagnostic `wsproto 1.3.2`; it was treated as modified diagnostic state, not clean-lock evidence.

### Reviewer baseline

- Review date: 2026-09-01
- Reviewer: Human project owner
- Reviewed baseline: `f5ca22e28bdf6a32324c7d10021ff24f3d34ba85`
- Runtime profile: CPython 3.14.7, Windows x86-64
- Full regression: 180 passed in 7.25 s
- Suffix A trace/snapshot: `ee7552f36e05b795ac76562443dbd5e205f0ddec307f2a5d38e467f9f0f5b2c4` / `b084af87407376735a1ab5b0b772943cf8296e6c1e5e6812c38cbdc121f30dc9`
- Suffix B trace/snapshot: `0bfe2d25db59135006993e6a3b438ace74e3b2eef4d40ae7e0b605e9d853a302` / `e8d0dfca3a8d96a08e56ee79e744816fbfc7835f1df42630bebb669f8029ca69`

### Confirmed blockers

| Finding | Evidence | Disposition |
|---|---|---|
| GD-001 — WebSocket backend absent from locked profile | Uvicorn rejected the upgrade; manual `wsproto` installation restored connection | Declare, pin, license and clean-install test the backend in R0 |
| GD-002 — live server has no operating runtime owner | Two HTTP-202 commands remained without acknowledgements; trace empty; connected viewer stayed at tick/sequence 0 | Implement the approved owner/lifecycle path in R1–R2 |
| GD-003 — commandless macro skips physics | Tick reached 30 while energy remained `0.9998888888888889 MWh` instead of `0.9997777777777779 MWh` | Enforce complete macro semantics and ZOH in R1 |

The manual `wsproto` installation was a diagnostic modification to the review environment, not an approved project dependency change.

### Historical evidence interpretation

The original M0–M7 commands and results below are retained exactly as developer evidence. “Passed” means the specified tests passed at that time. Gate D demonstrated that the coverage did not prove the launched integrated composition, so those results may not be used alone to claim implementation completion or Gate D readiness.

## Corrective milestone evidence

### R0 — Characterize and repair the executable profile

- Status: Passed
- Implementation commit: `a400367` (`fix(TT-000): repair R0 WebSocket profile`)
- Starting commit/worktree: `de961caa13d41c22b9de1c9ffe7e3a51ad5b04d3`, clean
- Selected backend: `wsproto==1.3.2`, resolved under CPython 3.14.7 on Windows x86-64; MIT license; requires the already locked `h11>=0.16.0,<1`

Commands and results:

1. `git branch --show-current`, `git rev-parse HEAD`, `git status --short`, and `git diff --name-status f5ca22e..de961ca`
   - Passed: correct feature branch, governance HEAD recorded, empty status, and no implementation changes since the preserved failed Gate D baseline.
2. `.\.venv\Scripts\python.exe -m pytest -q`, followed by both fast suffix commands and the GD-003 reproduction script.
   - Characterization passed: 180 tests in 8.36 s; suffix A/B hashes remained exactly as recorded; GD-003 remained reproducible at tick 30 with unchanged energy `0.9998888888888889 MWh` instead of `0.9997777777777779 MWh`.
3. `.\.venv\Scripts\python.exe -m pip index versions wsproto` and installed metadata inspection.
   - Passed: `1.3.2` was the current compatible release; metadata reported MIT and `h11>=0.16.0,<1`.
4. `.\.venv\Scripts\python.exe -m pytest tests/r0 tests/m0 -q`
   - Passed: 123 passed, 2 expected characterization xfails in 2.95 s. The real Uvicorn process returned HTTP 101 for the publication WebSocket. GD-002 and GD-003 tests remain strict expected failures until their corrective milestones.
5. Fresh temporary CPython 3.14.7 environment: `python -m pip install -r requirements.lock`, `python -m pip install --no-deps .`, `python -m pip check`, then `python -m pytest tests/r0 tests/m0 -q`.
   - Passed: clean lock installed `wsproto 1.3.2` without a manual package addition; `pip check` reported no broken requirements; 123 passed and the 2 expected characterization xfails completed in 3.01 s; the real WebSocket upgrade test passed.
6. `.\.venv\Scripts\python.exe -m compileall -q src tests` and `git diff --check`.
   - Passed.

Gate coverage:

- The pre-correction full-suite result and suffix hashes remain preserved in this file and `VALIDATION_REPORT.md`.
- The API optional profile, full lock and license inventory now explicitly contain `wsproto 1.3.2`.
- Uvicorn selects `uvicorn.protocols.websockets.wsproto_impl` from the locked profile.
- A real subprocess server accepts `/api/v1/publications` with an HTTP 101 WebSocket upgrade.
- Fresh-lock evidence proves no diagnostic/manual dependency installation is needed.
- Strict expected-failure tests capture GD-002 and GD-003 before their implementations change.

Decisions and deviations:

- The exact `wsproto` version approved for selection in R0 resolved to `1.3.2`; no substitute package or Uvicorn extra was introduced.
- The existing project `.venv` was not used as clean-install evidence because it already contained the reviewer's diagnostic `wsproto` installation.
- No canonical contract, time semantic, model equation or golden evidence changed in R0.

### R1 — Integrated deterministic runtime owner

- Status: Passed
- Implementation commit: `1364e25` (`fix(TT-000): implement R1 integrated runtime owner`)
- Prerequisite: R0 passed at `a400367`; R0 evidence recorded at `af15398`

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/r1 tests/r0 tests/m1 tests/m3 tests/m0 -q`
   - Passed during owner integration: 154 passed and the single remaining GD-002 strict expected failure in 3.70 s.
2. `.\.venv\Scripts\python.exe -m pytest -q` during migration of legacy callers.
   - Characterization run: 13 tests failed because M5–M7 fixtures still invoked removed scheduler-only/public component conductors. Those fixtures and the demonstration were migrated to the real owner; no compatibility wrapper that could bypass semantics was added.
3. `.\.venv\Scripts\python.exe -m pytest tests/m5/test_branching_replay.py -q`
   - First integrated branch run exposed a pre-command publication difference caused only by assigning A/B run IDs at restore. The continuation now runs through tick 100 with a common restored lineage, assigns the branch ID at the first distinct suffix command, and passed 2 tests in 1.56 s with causal first divergence preserved.
4. `.\.venv\Scripts\python.exe -m pytest tests/r1 tests/r0 tests/m1 tests/m3 tests/m5 tests/m7 -q`
   - Passed: 43 passed and the one remaining GD-002 strict expected failure in 8.29 s.
5. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 189 passed and the one remaining GD-002 strict expected failure in 14.03 s.
6. `.\.venv\Scripts\python.exe -m pip check`, `.\.venv\Scripts\python.exe -m compileall -q src tests`, and `git diff --check`.
   - Passed: no broken requirements, compilation errors or patch-integrity errors.
7. `.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix A` and suffix B.
   - Passed through the shared owner. Post-correction suffix A: trace `53650f4800bf07fe37fc50a9a5525fd16d047b6f8dc4a4fb3b7aa170623d1993`, snapshot `2ceff36d401be4449f4b5e19814d86845e3a02ca52b9726d6aa05542476426c0`. Suffix B: trace `98c17a30e824810d81eaf614902cc14b8bfaed48d34559a3c65a9b53213f843d`, snapshot `bb092858f76a70deda480ee3464bc293c066c40fa511e2436989dc76de9d8dd7`. Both end at `1.000037170499217 MWh` and emit 12 macro publications.

Gate coverage:

- `IntegratedRuntimeOwner.advance_one_macro()` is the sole public operational advancement method and executes all eleven approved phases through a quiescent boundary.
- `IntegratedRuntimeOwner.run_until(T)` repeatedly invokes complete macros; `ReplayRuntime` exposes no public scheduler-only `run_until`.
- Every fallback and detailed macro completes exactly ten 0.1 s child intervals, including zero-target and commandless macros.
- Two held +0.4 MW fallback macros produce cumulative energy `1.0 - 2 × 0.4 / 3600 MWh` within the approved tolerance.
- Detailed commandless macros advance energy with per-macro energy residual at most `1e-10 MWh` and coupling residual at most `1e-12 MWh`.
- The reference demonstration, snapshot/replay fixtures and viewer-invariance fixture all use the integrated owner rather than reproducing phase order externally.
- Fast and fake-wall paced execution use the same owner path and produce byte-identical canonical traces.
- Held requested/accepted/target state, pending ingress, scheduler boundary, publication sequence and branch lineage remain captured or derived from the existing V1 snapshot inventory; no schema field changed.

Decisions and deviations:

- The correction is intentionally behavioral, not a behavior-preserving refactor: every previously skipped macro now advances physics and publishes.
- Historical failed Gate D hashes remain unchanged above. New golden hashes changed because the approved ZOH now executes the formerly omitted 20→30, 30→40, 50→80 and post-restore macro intervals. The model equations, time base and contracts did not change.
- Final energy changed from `0.9998446478818566 MWh` to `1.000037170499217 MWh`: +0.4 MW remains held through its commandless intervals, then the accepted -1.0 MW request remains held until the tick-80 safe-zero interlock; this is the approved correction rather than a tolerance or model migration.
- A restored continuation uses a common deterministic pre-branch run lineage through tick 100, then assigns A/B lineage immediately before the first different command. This preserves separate final run IDs and the approved causal first-divergence property despite mandatory tick-100 publication.
- No V1 canonical schema, sign convention, phase value, command authority, snapshot version or model identity changed.

### R2 — Operational ASGI composition

- Status: Passed
- Implementation commit: `1cb4b9b` (`fix(TT-000): operate R2 ASGI runtime lifecycle`)
- Prerequisite: R1 passed at `1364e25`; R1 evidence recorded at `738a684`

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/r2 -q`
   - Passed: 4 tests in 3.63 s, including a real Uvicorn/wsproto process and live HTTP/WebSocket interaction.
2. First affected-regression run after explicitly expanding the snapshot infrastructure-exclusion inventory.
   - Result: 169 passed and 2 M7 golden snapshot assertions failed. Canonical traces and numerical results were unchanged; only snapshot bytes changed because the envelope now explicitly names ASGI task, stop-event, server-sleep and WebSocket protocol state as excluded infrastructure. The snapshot hashes were re-characterized without changing a schema or tolerance.
3. `.\.venv\Scripts\python.exe -m pytest tests/r0 tests/r1 tests/r2 tests/m0 tests/m1 tests/m3 tests/m6 tests/m7 -q`
   - Passed after classification: 171 tests in 17.12 s.
4. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 195 tests in 20.46 s.
5. `.\.venv\Scripts\python.exe -m pip check`, `.\.venv\Scripts\python.exe -m compileall -q src tests`, and `git diff --check`.
   - Passed: no broken requirements, compilation errors or patch-integrity errors.

Gate coverage:

- FastAPI lifespan starts exactly one `RuntimePacingLifecycle` task around exactly one integrated owner.
- The pacing task is the only ASGI-side caller of `advance_one_macro`; HTTP handlers only validate/admit or read immutable/canonical state, and the facade exposes no drain/execute operation.
- Idle startup produces increasing ticks, canonical publication sequences and lossless evidence publications.
- A real ASGI POST returns HTTP 202, then becomes an `ACCEPTED` final acknowledgement at its apply boundary without any test/manual drain or domain call.
- A real Uvicorn process using locked `wsproto 1.3.2` accepts `/api/v1/publications`, emits increasing ticks/sequences, accepts a future HTTP command, exposes its final acknowledgement and trace, and includes the acknowledgement in its macro publication.
- Zero, one, three and slow live viewer patterns preserve byte-identical canonical trace prefixes through the same logical boundary.
- Shutdown signals and awaits the pacing task; the task reference is cleared, no macro remains in progress, the scheduler is quiescent and logical time ends on a macro boundary.
- A late wall deadline records an infrastructure overrun and resets the next wall deadline without changing logical `dt`, child count or domain ordering.
- The viewer now advances its command form to the next future macro tick after each publication.

Decisions and deviations:

- `--pace-seconds` is an infrastructure diagnostic/pacing option only. It never enters canonical state or changes the 1 s logical macro duration.
- The async task, stop event, wall origin/sleep history, viewer queues and WebSocket protocol state are explicitly excluded from snapshots; the scheduler boundary, held intent, pending canonical ingress and publication sequence remain included.
- Post-R2 trace hashes remain the R1 hashes because lifecycle state is noncanonical. Snapshot hashes changed only through the expanded explicit exclusion list: tick-90 `774f3ee674dcb4af153015b4af7783f9754f221a18e0488077d891e87ff841d9`; suffix-A final `98453c1efd2773d1cf9d3633f95dcda49cfdf54a9edc6400d38a208a78f4516d`; suffix-B final `7992c44ce5cb6af438e27b373b6b12c03978e3a51cbfd4c3aa1588388ddb8bec`.
- No canonical contract migration, worker/thread expansion, concurrent domain callback or new physical behavior was introduced.

### R3 — Regression and Gate D package

- Status: Passed (developer evidence gate only; human Gate D review pending)
- Evidence/package commit: `c7ccc71` (`docs(TT-000): package R3 corrective review evidence`)
- Prerequisite: R2 passed at `1cb4b9b`; R2 evidence recorded at `27aa642`

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m0 tests/m1 tests/m3 tests/m6 tests/m7 tests/r0 tests/r1 tests/r2 -q`
   - Passed: 171 tests in 13.41 s.
2. `.\.venv\Scripts\python.exe -m pytest tests/m7/test_reference_demonstration.py tests/m7/test_reference_viewer_patterns.py tests/r2/test_asgi_lifecycle.py tests/r2/test_live_server.py -q`
   - Passed: 8 integrated fast/paced, viewer and real-server tests in 7.76 s.
3. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 195 tests in 20.95 s.
4. `.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix A`, the same command with `--mode paced`, and fast suffix B.
   - Passed: fast and actual-wall-paced suffix A emitted identical outcome JSON, trace `53650f4800bf07fe37fc50a9a5525fd16d047b6f8dc4a4fb3b7aa170623d1993` and final snapshot `98453c1efd2773d1cf9d3633f95dcda49cfdf54a9edc6400d38a208a78f4516d`. Fast suffix B emitted trace `98c17a30e824810d81eaf614902cc14b8bfaed48d34559a3c65a9b53213f843d` and final snapshot `7992c44ce5cb6af438e27b373b6b12c03978e3a51cbfd4c3aa1588388ddb8bec`. Both end at `1.000037170499217 MWh`.
5. Corrected commandless-macro reproduction through `IntegratedRuntimeOwner`.
   - Passed: tick 30; energy at tick 20 `0.9998888888888893 MWh`; energy at tick 30 `0.9997777777777785 MWh`; independent expected value `0.9997777777777782 MWh`; advancement true; `1e-12` comparison true; publication sequence 3.
6. `.\.venv\Scripts\python.exe -m pytest tests/r2/test_live_server.py -q`
   - Passed: 1 real Uvicorn/wsproto live-server reproduction in 1.67 s.
7. Fresh temporary CPython 3.14.7 Windows x86-64 environment: install `requirements.lock`, build/install the project wheel with `--no-deps`, run `pip check`, full pytest, and print runtime/wsproto versions.
   - Passed: lock installed without manual additions; `pip check` clean; 195 tests in 18.05 s; CPython 3.14.7 and `wsproto 1.3.2`; temporary evidence environment removed afterward.
8. After the R3 README/validation append: `.\.venv\Scripts\python.exe -m pytest tests/m0 tests/m7 -q` and `git diff --check`.
   - Passed: 127 tests in 5.62 s and no patch-integrity errors.

Gate coverage:

- Every required R0–R2 corrective behavior is covered in the affected and full regression suites.
- Fast and real-wall paced modes share the owner and reproduce identical canonical suffix-A evidence.
- Zero, one, multiple and slow viewers remain canonical observers in both synchronous owner and live lifespan tests.
- The real launched server establishes the locked WebSocket, advances while idle, executes admitted ingress, exposes the final acknowledgement/trace, publishes to the viewer and shuts down cleanly.
- The corrected GD-003 reproduction proves held-input commandless advancement and publication on every macro.
- A fresh clean-lock wheel install reproduces the full corrected suite.
- `README.md` and `VALIDATION_REPORT.md` contain post-correction commands, hashes, blocker disposition, deviations and risks while retaining the failed Gate D baseline.

Decisions, deviations and remaining risks:

- R3 introduced no domain behavior, canonical contract, model, phase, timing or dependency change; it packages evidence from commits `a400367`, `1364e25` and `1cb4b9b`.
- Historical failed Gate D results/hashes remain preserved. Corrected golden changes are classified in the R1/R2 sections and `VALIDATION_REPORT.md` rather than treated as implicit acceptance.
- Remaining risks are the approved synchronous-ASGI-loop scalability boundary, live future-tick cut-off usability, same-profile byte portability limit, need for independent reproduction of new hashes, and all original physical/noncompliance limitations.
- `TECH_TREE.md`, `ARCHITECTURE.md`, issue #1, the retrospective and Gate D state were not changed.

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

### M3 — Detailed multi-rate model and activation

- Status: Passed
- Implementation commit: `13f118e` (`feat(TT-000): implement M3 detailed multi-rate model`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m3 tests/m2 tests/m1 tests/m0 -q`
   - Passed: 133 tests in 1.38 s, including all M0–M2 regressions.
2. `.\.venv\Scripts\python.exe -m pytest -q` after strengthening dependency-direction checks.
   - Passed: 140 tests in 1.43 s.
3. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
4. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
5. `git diff --check`
   - Passed.

Gate coverage:

- A constant 1 MW detailed discharge for 1 h produces -1.0526315789473684 MWh stored-energy change and 0.0526315789473684 MWh loss within 1e-12 relative/absolute tolerance.
- A constant -1 MW detailed charge for 1 h produces +0.95 MWh stored-energy change and 0.05 MWh loss within the same tolerance.
- Uncapped exact-ZOH lag reaches 0.6321205588285577 MW at 2 s and 0.8646647167633873 MW at 4 s within 1e-12.
- Every ramp-limited endpoint change is at most `R × h + 1e-12 MW`.
- Fixed-ratio macro advancement completes exactly ten 0.1 s children totaling 1.0 s.
- Per-macro energy residual is at most 1e-10 MWh, short-run cumulative residual at most 1e-9 MWh, and coupling closure at most 1e-12 MWh.
- Half-step uncapped endpoints match analytically; the capped 0.1/0.05 s comparison remains within 1e-3 MW and 1e-6 MWh.
- Successful activation preserves exact lineage and E/SoC/P within 1e-12; failed activation retains the fallback as active and leaves captured registry/model state unchanged.
- Strengthened architecture tests enforce that kernel, model, control, topology, balance, alarm and snapshot packages import only canonical contracts across domain boundaries.

### M4 — Topology event and alarm lifecycle

- Status: Passed
- Implementation commit: `ecd98a8` (`feat(TT-000): implement M4 island and alarm lifecycle`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m4 tests/m3 tests/m2 tests/m1 tests/m0 -q`
   - Passed: 149 tests in 2.10 s, including all M0–M3 regressions.
2. `.\.venv\Scripts\python.exe -m pytest -q` after adding explicit imbalance correlation/causation.
   - Passed: 149 tests in 1.54 s.
3. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
4. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
5. `git diff --check`
   - Passed.

Gate coverage:

- Closed components are `(GRID, LOCAL)`; opening PCC produces exact `GRID@1` and `LOCAL@1` components and topology version 1.
- A simultaneous dispatch is validated after topology/operating-context changes: an old expected topology version is rejected, and otherwise unsupported mode is rejected with `TARGET_MODE_UNAVAILABLE`.
- Safe-zero sets controller target and model-applied power to 0 MW without changing stored energy at the event boundary.
- With a 0.6 MW load, island imbalance is exactly -0.6 MW with `UNCERTAIN/SIMPLIFIED_ISLAND_PROXY` quality.
- The topology event, typed interlock event, balance and alarm occurrence share explicit correlation/causation lineage.
- Alarm occurrence, acknowledge-while-active, return/close, clear-before-acknowledge and acknowledge/close sequences are exact on separate active/acknowledged axes.

### M5 — Snapshot and branching replay

- Status: Passed
- Implementation commit: `323660d` (`feat(TT-000): implement M5 snapshot and branching replay`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m0 -q`
   - Initial regression run: 112 passed, 1 failed. The new shared phase-priority declaration used a dictionary annotation in the contracts package, which the approved no-arbitrary-dictionary boundary check rejected. It was replaced with a closed-enum priority function; no scheduler order changed.
   - Rerun passed: 113 tests in 1.35 s.
2. `.\.venv\Scripts\python.exe -m pytest tests/m5 -q`
   - Passed: 7 tests in 2.11 s.
3. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 161 tests in 3.31 s, including all M0–M4 regressions.
4. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
5. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
6. `git diff --check`
   - Passed.

Gate coverage:

- The mutation inventory restores scheduler key/queue/tombstones/counters, publication sequence, active and inactive model state, controller ownership, validator receipts/dedupe/source sequences, topology/mode, acknowledged alarm occurrence, pending ingress, trace state and injected MT19937 state.
- V1 snapshots use compact sorted finite JSON and a lowercase SHA-256 checksum over the envelope with the checksum field empty; byte corruption is detected.
- Unknown envelope major schema, model identity/version and numerical runtime profile are rejected before a fresh destination becomes started.
- Scheduler events serialize by the approved numeric semantic phase order regardless of backing-heap layout; receipts, counters, model states and ingress are canonically sorted independent of insertion order.
- Two fresh same-branch continuations produce byte-identical trace suffixes and exact final canonical snapshot bytes, including RNG continuation.
- Alternative suffixes share the exact trace prefix through `S-TT000-090`, repeat byte-for-byte within each branch, and first diverge at `CMD-ACK-001` versus `CMD-P-ALT-001`; the latter is causally rejected with `TARGET_MODE_UNAVAILABLE`.
- Restore creates a new deterministic run lineage with `parent_snapshot_id`; snapshot capture/restore lifecycle records are included in the canonical trace.

### M6 — Asynchronous API and viewer

- Status: Passed
- Implementation commit: `bc2ef0d` (`feat(TT-000): isolate M6 API and viewer adapters`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m6 -q`
   - Passed: 7 tests in 2.50 s.
2. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 174 tests in 6.59 s, including all M0–M5 regressions.
3. `.\.venv\Scripts\python.exe -m pip check`
   - Passed: no broken requirements.
4. `.\.venv\Scripts\python.exe -m compileall -q src tests`
   - Passed.
5. `git diff --check`
   - Passed.

Gate coverage:

- Real ASGI HTTP requests validate `CommandV1` through generated Pydantic DTOs, return canonical admitted-command and acknowledgement schemas, and map topology reads back to frozen domain records.
- WebSocket publication frames carry canonical `logical_tick`, `sequence` and `schema_version` fields.
- Zero, one and three viewer patterns, plus fast, slow and mixed drain rates, produce byte-identical canonical domain traces for the same ordered input log.
- Every per-viewer queue has the approved capacity of 64 publication frames.
- On telemetry saturation, queued continuous frames coalesce to the latest sample per `(subject_id, signal_id)`; the infrastructure drop counter records replaced frames.
- When 64 discrete frames leave no capacity after telemetry coalescing, the viewer is disconnected with `SLOW_VIEWER_RESYNC_REQUIRED`; the lossless evidence sink still retains every publication.
- Viewer drop counts, queue state and disconnect reasons remain infrastructure diagnostics and do not enter the canonical trace.
- Live ingress accepts only future exact macro boundaries and sorts eligible commands canonically before draining, independent of asynchronous arrival order.
- Server configuration rejects more than one ASGI worker and rejects auto-reload for the in-memory owner.

### M7 — Reference demonstration and validation package

- Status: Passed (developer gate; independent validation pending)
- Implementation commit: `7cc9194` (`feat(TT-000): package M7 reference demonstration evidence`)

Commands and results:

1. `.\.venv\Scripts\python.exe -m pytest tests/m7 -q`
   - Passed: 4 tests in 3.23 s; final rerun passed in 3.05 s.
2. `.\.venv\Scripts\python.exe -m pytest -q`
   - Passed: 180 tests in 8.22 s, including every M0–M6 regression.
3. First isolated-install attempt: create a CPython 3.14.7 venv, then install with `pip install --require-hashes -r requirements.lock`.
   - Stopped before tests: the version-pinned lock intentionally contains no artifact hashes, so `--require-hashes` was incompatible. This flag had been introduced only in the new README command, not in the approved M0 install procedure. The README was corrected to `pip install -r requirements.lock`.
4. Corrected isolated CPython 3.14.7 environment: `python -m pip install -r requirements.lock`, `python -m pip install --no-deps .`, `python -m pip check`, then `python -m pytest -q`.
   - Passed: exact locked packages installed, project wheel built/installed, no broken requirements, and 180 tests passed in 10.19 s.
5. Installed-wheel asset check: `python -c "from energy_simlab.viewer import viewer_html; print(len(viewer_html()))"` in the isolated environment.
   - Passed: packaged static viewer loaded (4,868 characters).
6. `.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix A`
   - Passed: final mode `ISLANDED_UNSUPPORTED`, applied power 0 MW, energy `0.9998446478818566 MWh`, alarm active/acknowledged, trace SHA-256 `ee7552f36e05b795ac76562443dbd5e205f0ddec307f2a5d38e467f9f0f5b2c4`, final snapshot SHA-256 `b084af87407376735a1ab5b0b772943cf8296e6c1e5e6812c38cbdc121f30dc9`.
7. `.\.venv\Scripts\python.exe -m energy_simlab.bootstrap.demonstration --mode fast --suffix B`
   - Passed: final mode `ISLANDED_UNSUPPORTED`, applied power 0 MW, energy `0.9998446478818566 MWh`, alarm active/unacknowledged, trace SHA-256 `0bfe2d25db59135006993e6a3b438ace74e3b2eef4d40ae7e0b605e9d853a302`, final snapshot SHA-256 `e8d0dfca3a8d96a08e56ee79e744816fbfc7835f1df42630bebb669f8029ca69`.
8. `.\.venv\Scripts\python.exe -m compileall -q src tests`, `.\.venv\Scripts\python.exe -m pip check`, and `git diff --check`.
   - Passed.

Gate coverage:

- The fixed tick 0–120 reference scenario is available as a repeatable CLI and a typed composition function.
- Fast-forward and fake-wall paced suffix-A executions produce byte-identical canonical traces, tick-90 snapshots and final snapshots; wall pacing diagnostics remain excluded.
- The scenario produces identical canonical trace/final snapshot bytes with zero viewers, one fast viewer, one slow viewer and three mixed-rate viewers.
- The golden trace includes V1 command, acknowledgement, fidelity, topology, alarm, publication and snapshot capture/restore records with correlation/causation fields.
- The tick-90 snapshot retains the active/unacknowledged alarm; suffix A acknowledges it and suffix B rejects `CMD-P-ALT-001` with `TARGET_MODE_UNAVAILABLE` while physical energy remains equal.
- `README.md` contains the exact setup, locked install, fast/paced/alternative demonstration and single-owner viewer commands plus visible unsupported phenomena and nonclaims.
- `VALIDATION_REPORT.md` contains developer-supplied traceability, comparisons, replay evidence, limitations and reproduction data, while explicitly reserving verdict and Gate D for an independent reviewer.
- `ARCHITECTURE.md`, `REFERENCES.md`, `CHANGELOG.md` and `TECH_TREE.md` remain unchanged because their approved updates occur only during validation/integration. `RETROSPECTIVE.md` remains unpopulated as instructed.

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
- The detailed endpoint is selected from the intersection of rating, ramp and energy-feasible constraints before trapezoidal energy integration.
- The model registry constructs and validates a detailed candidate before atomically changing the active pointer; only fallback-to-detailed activation exists.
- M4 adds the approved explicit safe-zero publication as `InterlockEventV1`; it carries target/applied power and energy before/after plus topology/correlation lineage.
- Alarm state retains occurrence identity after return until acknowledgement and emits `CLOSED` only when both condition-clear and acknowledged are true.
- M5 keeps checksum/DTO code in the serialization adapter, compatibility policy in the inward snapshot package and heap/domain mapping in application orchestration; no adapter object enters domain state.
- M5 derives topology-event identity from the snapshotted topology version, eliminating an otherwise hidden event counter while retaining the exact M4 event identity.
- M6 tests established HTTP 202 admission and a separate acknowledgement read when boundary processing was invoked manually; Gate D showed that the launched server never performs that boundary processing.
- M6 fan-out publishes to the lossless core evidence sink before bounded per-viewer observation work; viewer delivery performs no awaited callback into the synchronous owner.
- M7 records actual numerical residuals in reference publications and hard-codes same-profile golden hashes only after the analytic, invariant, snapshot and adapter gates passed.
- The M7 evidence package does not make a validation verdict. Validated architecture/reference/changelog/tech-tree updates and the retrospective remain reserved for later authorized stages.
- The first M7 isolated-install command added an unsupported `--require-hashes` flag; after correcting the README to the approved version-pinned install command, the isolated full suite passed. This was a documentation-command defect, not an approved dependency or architecture change.
- Gate D confirmed an integrated runtime architecture/test gap. The correction remains within TT-000 and is governed by `FEATURE_CONTEXT_AMENDMENT_01.md` and accepted `ADR-0002`.

## Next permitted action

The human project owner may review and independently reproduce the appended R0–R3 evidence for a new Gate D decision. Developer work stops here.

Until a separate human decision authorizes otherwise, do not approve Gate D, close issue #1, mark TT-000 validated/integrated/active/unlocked, populate the retrospective, update `TECH_TREE.md` or the validated architecture ledger, merge the feature branch, or begin another node.
