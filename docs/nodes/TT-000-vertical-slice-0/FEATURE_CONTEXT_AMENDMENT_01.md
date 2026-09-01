# TT-000 Feature Context Amendment 01 — Integrated Runtime Owner

## 1. Status and authority

**Draft — awaiting human Gate C amendment approval. Corrective Stage D implementation is blocked.**

- Original Gate C approval: 2026-08-26.
- Gate D review attempt: 2026-09-01.
- Gate D result: not approved; corrective work required.
- Reviewed implementation baseline: `f5ca22e28bdf6a32324c7d10021ff24f3d34ba85`.
- Tracking issue: [#1](https://github.com/leomedeles/energy_simlab/issues/1).
- Proposed decision record: `docs/decisions/ADR-0002-integrated-runtime-owner-and-server-lifecycle.md`.
- Implementation branch after approval: `feature/TT-000-vertical-slice-0`.

This amendment is append-only governance evidence. It does not erase or retroactively revoke the original Gate C approval, the historical developer test results, or the completed component implementations. If approved, it supplements the original `FEATURE_CONTEXT.md` wherever the integrated runtime path, server lifecycle, commandless advancement, WebSocket packaging, or end-to-end evidence is concerned. All original requirements not explicitly amended remain binding.

No implementation code, dependency change, generated lock update, or node unlock is authorized by this draft. The human project owner must approve the checklist in section 13 before corrective Stage D work begins.

## 2. Reason for reopening Gate C

The original Feature Context already requires one synchronous owner, the eleven-phase order, exact 10:1 macro/child coupling, zero-order-held accepted inputs, future-boundary live ingress, immutable publications, and an operational API/viewer boundary. Gate D manual validation nevertheless showed that isolated components and scripted call order could satisfy the developer tests while the launched composition remained inert.

The correction therefore needs both:

1. implementation fixes for behavior that was already required; and
2. a more explicit integrated execution and acceptance contract so the same class of omission cannot pass again.

This is a narrow corrective architecture amendment within TT-000. It does not introduce a new tech-tree node or expand the approved physical model.

## 3. Confirmed Gate D findings

| ID | Confirmed observation | Required behavior contradicted |
|---|---|---|
| GD-001 | The locked installation starts Uvicorn but lacks a supported WebSocket backend; the viewer upgrade fails until `wsproto` is installed manually. | Repeatable operational viewer from the clean locked environment |
| GD-002 | With WebSocket connectivity restored, the launched server accepts two future commands with HTTP 202 but never produces acknowledgements, trace entries, tick advancement, or publications. | One owner, future-boundary ingress drain, phase execution, acknowledgement, publication and live observation |
| GD-003 | After one +0.4 MW macro, `run_until(30)` moves logical time from tick 20 to 30 while stored energy remains unchanged. | ZOH across commandless macros and exactly ten child advances per uninterrupted macro |

The 180 passing tests and suffix A/B golden hashes remain truthful historical evidence for the paths they exercised. They are insufficient evidence for the integrated launched path.

## 4. Learning questions and Definition-of-Done impact

The findings block satisfactory answers to learning questions 1, 2 and 7:

- logical time and paced interactive execution are not integrated through one operational path;
- fixed-ratio coupling and held inputs are not executed for every elapsed macro;
- the asynchronous API/viewer cannot command and observe a continuously operating deterministic core.

The original node-specific Definition of Done remains unmet until this amendment's corrective milestones and tests pass and Gate D is performed again.

## 5. Integrated runtime architecture

### 5.1 Single domain owner

Introduce one application-layer runtime owner as the only component permitted to advance logical time or invoke mutable domain operations during an active run.

The owner must encapsulate the scheduler, active model registry, controller, command validator, topology, balance, alarm service, trace recorder, publication sequence and snapshot-relevant state already held by `ReplayRuntime`. Existing services may be composed or refactored behind this owner, but there must be one explicit entry point for completing a macro interval.

No HTTP handler, WebSocket handler, viewer task, publication sink or wall-clock callback may call model advancement or execute a domain phase independently.

### 5.2 Complete macro operation

The owner must expose a synchronous operation equivalent to `advance_one_macro()`. One call must complete the approved eleven phases in their existing order and finish at a quiescent macro boundary.

For every uninterrupted 1 s macro, including a macro with no new command:

1. eligible exogenous work and topology changes are resolved;
2. operating context and interlocks are recomputed;
3. eligible fidelity work is resolved;
4. live and scripted commands eligible for the boundary are canonically ordered, validated and acknowledged;
5. the controller computes the target;
6. the active model completes exactly ten 0.1 s child intervals under the current target;
7. reductions, active-power balance, residuals and alarms are computed;
8. one immutable canonical macro publication is committed and fanned out;
9. eligible snapshot work runs only after the boundary is quiescent.

The detailed phase values and same-tick causality rules in the original `FEATURE_CONTEXT.md` section 10 remain unchanged.

A public operation named `run_until(T)` may not advance across a macro boundary by moving the scheduler alone. It must execute all semantic macro work through T. Any low-level scheduler-only operation must be private or explicitly named so it cannot be mistaken for simulation advancement.

### 5.3 Zero-order hold

After a power command is accepted, its accepted value remains the controller's held intent across later macro intervals until another accepted command replaces it or an approved control/safety rule overrides the target.

Command `expiry_tick` controls whether the command is eligible for acceptance at its intended boundary; it does not silently erase an already accepted value in later commandless macros.

Requested, accepted, target and applied power remain distinct:

- requested and accepted values preserve command history;
- the controller target reflects the held accepted intent and active interlocks;
- the model-applied value reflects dynamics and limits;
- an active safe-zero interlock may override target/applied power without rewriting the historical accepted value.

Physics still advances during an override or zero target; “no new command” never means “skip the model.”

### 5.4 Live ingress ownership

HTTP admission validates edge schema and queues an immutable canonical command only. Admission returns HTTP 202 and is not the final command acknowledgement.

The ASGI edge must not directly execute the command. At each future macro boundary the single runtime owner drains all eligible ingress, sorts it by the approved authority/source/sequence/ID rules, executes it during the COMMAND phase, and records the final canonical acknowledgement.

A command admitted for a valid future boundary must become either an accepted, limited, rejected, superseded or duplicate acknowledgement at that boundary. It may not remain indefinitely admitted without a final result while the run continues.

### 5.5 Server lifecycle and pacing

The interactive server must use exactly one ASGI worker and one lifespan-managed asynchronous pacing task.

- ASGI startup constructs one runtime owner and starts one pacing task.
- The pacing task is the sole caller of the owner's synchronous macro-advance operation.
- The task waits asynchronously for monotonic wall deadlines; the domain core remains synchronous.
- Wall-clock delay or overrun never changes logical `dt`, phase order or child count.
- HTTP and WebSocket work may run while the pacing task is awaiting the next deadline, but it may only enqueue ingress or consume immutable observations.
- Shutdown signals the task, allows any already-started macro to reach its quiescent boundary, awaits the task and leaves no orphan runtime activity.
- Multiple workers and auto-reload remain rejected.

Fast-forward CLI execution invokes the same synchronous owner operation without wall waiting. Scripted demonstrations may schedule reference inputs, but may not reproduce the phase sequence through bespoke direct calls that bypass the integrated owner.

### 5.6 Publication and viewer behavior

A canonical `MacroPublicationV1` must be produced after every completed macro, whether or not a command arrived. The lossless evidence sink receives it before or independently of best-effort viewer delivery.

A connected WebSocket viewer must observe increasing logical ticks and publication sequences as paced macros complete. Zero, one or multiple viewers, slow readers, disconnects and reconnects must not change canonical domain results.

The viewer remains an observer and command-admission edge; it is never the trigger that causes physics to advance.

### 5.7 WebSocket dependency

The API installation profile must declare and the lock must pin one Uvicorn-supported WebSocket backend. `wsproto` is the selected direct backend because it restored the approved WebSocket route during the manual reproduction without requiring the full unrelated Uvicorn “standard” extras.

The exact `wsproto` version must be resolved and locked under CPython 3.14.7 on Windows x86-64 during corrective milestone R0. A clean installation using only the committed project metadata and lock must accept the viewer WebSocket without an additional manual `pip install`.

If a compatible pinned version cannot be reproduced or licensed, stop R0 and return to Gate C; do not silently substitute an unrecorded package.

## 6. Snapshot and infrastructure state

New mutable state that can affect canonical continuation must be included in the existing snapshot inventory or made derivable from already captured canonical state. This includes the next logical boundary, held accepted intent, pending canonical ingress, phase/quiescence state and all deterministic counters.

ASGI task handles, sockets, connected viewers, fan-out queues, monotonic wall origins, sleep history, server stop events and WebSocket implementation state are infrastructure and remain excluded.

Snapshots remain legal only at a quiescent macro boundary. Restore creates a fresh stopped runtime owner; fast-forward code or the server lifecycle may then start it explicitly.

## 7. Change classification

| Work | Classification |
|---|---|
| Extracting one runtime-owner interface from existing application services without changing contracts | Refactor |
| Making macro advancement execute held-input physics and all phases | Corrective behavioral change |
| Starting/stopping the owner through ASGI lifespan | Corrective integration change |
| Declaring and pinning `wsproto` | Compatible dependency/configuration correction |
| Replacing scripted/manual orchestration with the shared owner path | Corrective behavioral integration |
| Adding real composition/liveness tests | Test-gap correction |
| Canonical schema change, if unexpectedly required | Contract migration requiring separate approval |

Do not describe the overall correction as behavior-preserving refactoring.

## 8. Stable boundaries and compatibility

- V1 command, acknowledgement, telemetry, publication, trace and snapshot meanings remain stable unless a separately approved contract migration becomes necessary.
- The 0.1 s base tick, 1 s macro, phase values, command authority order, BESS equations, topology semantics, alarm policy and one-way fidelity activation remain unchanged.
- Existing valid scenarios and snapshots should remain readable if the complete runtime state can be derived. Any incompatibility must be detected before mutation and documented with a migration or explicit rejection.
- Existing golden changes are not automatically accepted. Each changed byte or numerical value must be classified as correction of the previously skipped behavior, unintended regression or approved migration.

## 9. Corrective milestones

### R0 — Characterize and repair the executable profile

- Preserve the current 180-test result and suffix A/B hashes as pre-correction evidence.
- Add a regression test proving the locked API profile includes a functioning WebSocket backend.
- Declare and lock `wsproto`; update the license inventory and setup documentation.
- Capture failing tests for GD-002 and GD-003 before implementing their fixes.

Exit: a clean CPython 3.14.7 Windows x86-64 environment installs from committed metadata/lock and can accept the publication WebSocket.

### R1 — Integrated deterministic runtime owner

- Introduce or extract the single owner and synchronous complete-macro operation.
- Make commandless macros advance exactly ten child intervals under ZOH.
- Route `run_until` and the reference demonstration through the complete semantic path.
- Preserve phase order, authority, residual, replay and snapshot invariants.

Exit: direct integrated tests prove consecutive commandless macros change energy exactly as required and no public simulation-advance method skips semantic phases.

### R2 — Operational ASGI composition

- Add the lifespan-managed pacing task and clean shutdown.
- Restrict HTTP to admission/read behavior and drain ingress only through the owner.
- Deliver a final acknowledgement at the apply boundary.
- Publish every macro to the evidence sink and WebSocket fan-out.

Exit: the real composed application advances while idle, executes a POSTed future command, exposes its acknowledgement and trace, updates the connected viewer, and stops cleanly.

### R3 — Regression and Gate D package

- Run affected M0, M1, M3, M6 and M7 suites plus the full suite from a clean locked environment.
- Run fast-forward versus paced canonical comparison.
- Run zero/one/multiple and slow-viewer independence tests through the integrated owner.
- Repeat the human live-server and commandless-macro reproductions.
- Update README, PROGRESS and VALIDATION_REPORT with post-correction evidence.
- Explain any golden changes; do not update `TECH_TREE.md` or validated `ARCHITECTURE.md` before Gate D passes.

Exit: evidence is ready for a new Gate D review. Passing developer tests does not approve Gate D.

Milestones R0–R3 are sequential. Stop on failure and record the deviation before continuing.

## 10. Required corrective tests

At minimum, the corrected branch must include:

1. clean-lock WebSocket startup test;
2. two consecutive fallback macros under held +0.4 MW with the expected cumulative energy change;
3. detailed-model commandless macro child-count, energy and residual test;
4. integrated phase-order test using the real owner rather than hand-authored caller order;
5. real ASGI lifespan liveness test proving idle tick/publication advancement;
6. POST-to-final-acknowledgement test with no manual `drain_for_tick` or command execution;
7. WebSocket publication test showing increasing tick and sequence;
8. zero/one/multiple/slow-viewer canonical equality through the live composition;
9. clean shutdown test proving no partial macro and no orphan task;
10. snapshot/restore test for all newly introduced canonical owner state;
11. fast-forward/paced canonical equality using the same owner path;
12. complete M0–M7 and full-regression rerun.

A mock-only API mapping test cannot satisfy items 5–9.

## 11. Rollback strategy

Corrective work remains on `feature/TT-000-vertical-slice-0`. Preserve the pre-correction baseline commit and do not rewrite its history.

- R0 dependency changes can be reverted independently.
- R1 owner extraction should keep existing canonical contracts stable.
- R2 ASGI lifecycle can be disabled without changing the synchronous core.
- If R1 or R2 requires a contract/time-semantic change beyond this amendment, stop and return to Gate C.
- Do not merge, unlock TT-000, populate the canonical technology frontier, or delete the sidequest branch as part of this correction.

## 12. Documentation duties

During corrective implementation:

- update `PROGRESS.md` after every R milestone;
- keep issue #1 open until post-fix evidence is reviewed;
- update `ADR-0002` only through the approved decision and a superseding ADR if later changed;
- update dependency and license documents in R0;
- update README operational instructions in R2/R3;
- preserve the failed Gate D evidence in `VALIDATION_REPORT.md`;
- append revalidation evidence rather than replacing the failed observations.

## 13. Human Gate C amendment checklist

Before corrective Stage D begins, the human project owner must explicitly approve:

- [x] The failed Gate D evidence and return to corrective Stage C are accepted.
- [x] The correction remains TT-000 scope and does not create a new node.
- [x] One synchronous runtime owner and one ASGI lifespan-managed pacing task are approved.
- [x] Complete macro semantics, including commandless ZOH advancement, are approved.
- [x] HTTP admission, future-boundary drain and final acknowledgement semantics are approved.
- [x] Publication on every completed macro and viewer independence are approved.
- [x] `wsproto` is approved as the explicitly declared and locked WebSocket backend.
- [x] Snapshot inclusions/exclusions for the runtime owner are approved.
- [x] Corrective milestones R0–R3 and their required tests are approved.
- [x] Change classification, compatibility and rollback policy are approved.
- [x] Gate D remains not approved and TT-000 remains locked until successful revalidation.

Approval record:

- Approved by: Leo  
- Approval date: 01.09.2026
- Approval statement/reference: Looks fine

Until this checklist is approved and recorded in `PROGRESS.md`, implementation remains blocked.
