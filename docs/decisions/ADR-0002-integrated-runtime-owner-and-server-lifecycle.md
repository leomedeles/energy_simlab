# ADR-0002 — Integrated Runtime Owner and Server Lifecycle

## Status

Proposed — awaiting human approval of `FEATURE_CONTEXT_AMENDMENT_01.md`.

This ADR is not implementation authorization. If the amendment is approved, this decision becomes accepted for TT-000 corrective Stage D work. Until then, the original Gate C architecture remains the last approved design and implementation is blocked.

## Date

2026-09-01

## Context

TT-000 requires a deterministic synchronous simulation core with one owner, fixed logical time, exact phase ordering, 1 s macro periods containing ten 0.1 s child intervals, zero-order-held accepted inputs, future-boundary live command ingress and immutable publications to an asynchronous viewer.

The component implementation at baseline commit `f5ca22e28bdf6a32324c7d10021ff24f3d34ba85` passed 180 developer tests and the scripted suffix A/B demonstrations. Human Gate D reproduction nevertheless confirmed:

1. the locked installation contains Uvicorn but no usable WebSocket backend;
2. the launched server accepts HTTP commands but has no owner loop that advances time, drains commands or publishes;
3. `ReplayRuntime.run_until()` can cross a macro boundary by advancing the scheduler without advancing BESS physics under the held input.

The current CLI demonstration acts as an external conductor by calling operations directly. The API tests likewise drain and execute admitted commands manually. Those paths prove component behavior but not the launched operational composition.

A decision is required because the correction establishes a long-lived ownership and lifecycle boundary between deterministic domain execution and asynchronous ASGI infrastructure.

## Decision

### 1. One synchronous runtime owner

Create one application-layer runtime owner. It is the sole authority that may advance logical time and invoke mutable domain operations during a run.

The owner exposes synchronous operations, including one complete macro advance. The deterministic core remains non-async and executes no concurrent domain callbacks.

Existing `ReplayRuntime` responsibilities may be retained, extracted or composed behind the owner, but no second service may independently move the scheduler or model.

### 2. Semantic advancement is atomic at macro level

A complete macro operation executes all approved phases through a quiescent boundary. It drains eligible commands, applies authority and interlocks, advances the model for all required child intervals, aggregates, evaluates alarms, records trace and publishes.

A macro with no newly eligible command still advances physics using the held target. Scheduler-only movement is an internal mechanism, not a public substitute for simulation advancement.

If `run_until(T)` remains public, its meaning is full semantic execution through T. A low-level queue/scheduler drain must be private or explicitly named as non-physical.

### 3. ASGI lifespan owns one pacing task

The interactive server uses one ASGI lifespan-managed asynchronous pacing task and exactly one ASGI worker.

At startup:

1. compose one runtime owner;
2. compose immutable read/publication edges and the command-ingress mailbox;
3. start one pacing task.

During operation:

1. the pacing task asynchronously waits for the next monotonic wall deadline;
2. when due, it synchronously invokes one complete macro operation;
3. while it is awaiting, HTTP handlers may validate and enqueue immutable commands and viewers may consume immutable publications;
4. no HTTP or WebSocket handler invokes domain advancement.

At shutdown:

1. signal the pacing task;
2. if a macro has started, allow it to reach its quiescent boundary;
3. await task completion;
4. close infrastructure resources.

Wall-clock overrun may be diagnosed but cannot change logical duration, child count or phase order.

### 4. Ingress is a mailbox, not execution

HTTP 202 means admitted for future deterministic processing. It is not the final domain acknowledgement.

The edge validates and enqueues an immutable canonical command. At the eligible macro boundary, the owner drains and canonically sorts commands under the approved authority/source/sequence/ID rules. Every processed command produces a final canonical acknowledgement.

External arrival order is not a domain tie-breaker.

### 5. Publications are owner output

The owner produces one canonical macro publication for every completed macro, including commandless macros. The lossless evidence sink receives every publication. Viewer fan-out remains bounded and best effort under the existing loss policy.

Connecting, disconnecting or slowing a viewer cannot trigger, pause or alter physics.

### 6. Fast and paced modes share the owner

Fast-forward code repeatedly calls the same synchronous complete-macro operation without waiting. Paced server execution calls it through the lifespan task. Scenario scripting supplies scheduled inputs; it does not manually reproduce the phase sequence.

Canonical results must match for identical inputs after excluding wall-clock diagnostics.

### 7. WebSocket transport is explicit

Declare `wsproto` as the direct Uvicorn WebSocket backend and pin a CPython 3.14.7-compatible version in the complete lock. Record its license.

The exact pinned version is selected during corrective milestone R0 through a clean Windows x86-64 resolution. Failure to obtain a reproducible compatible version stops R0 and returns the choice to Gate C.

### 8. Snapshot boundary

Canonical owner state that affects continuation is included or derived from the existing snapshot inventory. Infrastructure lifecycle state is excluded.

A restored owner begins stopped at a quiescent macro boundary. Starting fast-forward or paced execution is an explicit infrastructure action after successful restore.

## Consequences

### Positive

- The launched server becomes the real TT-000 composition rather than a static API shell.
- Scripted, fast-forward and paced executions share one semantic path.
- Commandless intervals cannot silently skip physics.
- HTTP admission and final domain acknowledgement remain distinct and testable.
- Async infrastructure remains outside deterministic domain ordering.
- Startup and shutdown ownership are explicit.
- The clean installation can support the documented viewer.

### Costs and risks

- The application layer gains a new orchestration abstraction and lifecycle tests.
- Existing golden traces or snapshots may change when previously skipped macro work is executed; every change requires classification.
- Synchronous macro work briefly occupies the ASGI event loop. TT-000's tiny model is expected to keep this bounded; if measurements contradict that assumption, the design must return to Gate C rather than introduce concurrent domain mutation.
- Shutdown needs an explicit quiescence rule.
- Snapshot inventory must be re-audited after owner extraction.

## Alternatives considered

### Keep scripted orchestration as the reference owner

Rejected. It cannot make the launched API/viewer operational and duplicates phase order in caller code.

### Execute a command directly inside the HTTP POST handler

Rejected. Network arrival timing would become execution timing, HTTP 202 would collapse admission into domain acknowledgement, and commandless macros would still not advance.

### Let each model or phase run in its own asynchronous task

Rejected. Concurrent callbacks would violate the approved single-owner deterministic semantics and make ordering depend on infrastructure scheduling.

### Advance the scheduler independently and call physics only when commands arrive

Rejected. It is the behavior reproduced by GD-003 and violates the approved ZOH and child-count contract.

### Use a dedicated operating-system thread for the domain owner

Not selected for TT-000. A thread adds synchronization and shutdown complexity without evidence that the tiny synchronous macro blocks the event loop materially. Reconsider only through a Gate C amendment supported by measurements.

### Install `uvicorn[standard]` without declaring its resolved extras

Rejected. It hides additional runtime dependencies and does not preserve the project's explicit direct-version and license discipline. A single declared WebSocket backend is sufficient.

### Derive physics `dt` from wall-clock elapsed time

Rejected. Wall time is pacing only and may never become accidental simulation physics.

## Validation

Acceptance requires all tests in `FEATURE_CONTEXT_AMENDMENT_01.md` section 10, including:

- consecutive commandless macro energy advancement;
- real-owner phase order;
- real ASGI lifespan liveness;
- POST-to-final-acknowledgement without manual drain/execute calls;
- WebSocket tick/publication progression;
- viewer-count/read-rate independence;
- fast/paced canonical equality;
- clean quiescent shutdown;
- clean locked WebSocket installation;
- snapshot/restore coverage for new canonical state;
- full regression.

The pre-correction 180-test result and golden suffix hashes remain characterization evidence, not acceptance of this ADR.

## Rollback

All work remains on `feature/TT-000-vertical-slice-0`. Preserve the pre-correction commit and revert only the failing corrective milestone through non-destructive commits if necessary.

The synchronous owner must remain independently executable if the ASGI lifecycle adapter is disabled. No correction may update `TECH_TREE.md` or mark TT-000 validated before Gate D passes.

## Conditions for reconsideration

Reconsider through a new Gate C amendment or superseding ADR if:

- measured macro execution cannot safely share the ASGI event loop;
- an external solver requires blocking isolation or rollback;
- distributed ownership becomes an approved node;
- arbitrary/adaptive clocks replace the fixed ratio;
- a canonical contract or snapshot major version must change;
- the selected WebSocket backend cannot be reproducibly supported.
