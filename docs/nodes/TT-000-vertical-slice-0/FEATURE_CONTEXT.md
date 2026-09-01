# TT-000 Feature Context

## 1. Status and Gate C approval state

Approved — Gate C approved; prescriptive for Stage D milestone implementation.

- Gate A: approved by the human project owner.
- Gate B: approved by the human project owner on 2026-08-26.
- Gate B evidence: RESEARCH_REPORT.md.
- Gate C: Approved.
- Approved by: Human project owner.
- Approval date: 2026-08-26.
- Implementation: Stage D authorized on the approved feature branch.
- Git feature branch: feature/TT-000-vertical-slice-0.
- Node state: implementation in progress; neither validated nor unlocked.

This file is the approved, prescriptive architecture for Stage D milestone implementation. Gate C approval authorizes implementation on the named feature branch; it does not validate the node or approve Gate D. The substantive content of the approved RESEARCH_REPORT.md must not be changed to make implementation results appear consistent with this specification.

### 1.1 Corrective Gate C amendment

Gate D was not approved on 2026-09-01 after human reproduction confirmed missing WebSocket packaging, an inert launched runtime and commandless scheduler advancement without held-input physics.

The human project owner approved [FEATURE_CONTEXT_AMENDMENT_01.md](FEATURE_CONTEXT_AMENDMENT_01.md) on 2026-09-01. That amendment supplements this original context and is prescriptive wherever it addresses the integrated runtime owner, complete macro semantics, zero-order hold, ASGI lifecycle, live ingress, publications, snapshots, dependency packaging and corrective tests.

`docs/decisions/ADR-0002-integrated-runtime-owner-and-server-lifecycle.md` is accepted through that approval. Corrective Stage D is authorized on `feature/TT-000-vertical-slice-0`; the current requested developer assignment is R0 through R2 sequentially. Gate D remains not approved, and TT-000 remains unvalidated, unintegrated and locked.

## 2. Node identity and proposed Git branch

| Field | Selection |
|---|---|
| Node | TT-000 — Hierarchical Co-Simulation Vertical Slice 0 |
| Type | Mandatory trunk / architecture-learning vertical slice |
| Proposed implementation branch | feature/TT-000-vertical-slice-0 |
| Change class | Initial compatible extension; no existing executable behaviour or persistent data is migrated |
| Primary realms | Simulation kernel and time; physics and numerical models; control and automation; topology and protection boundary; SCADA and visualization; compliance and validation |
| Secondary realms | Data and historian boundary; typed in-process communications boundary |
| Explicitly unadvanced realms | Reliability and maintenance; cybersecurity; industrial-protocol interoperability; grid-code compliance |

After Gate C approval, all Stage D work must occur on the proposed branch. No implementation commit may be made directly to master.

## 3. Learning outcomes

Completion must provide evidence that the developer can explain and demonstrate:

1. Why logical time, wall-clock pacing and asynchronous observation are separate concerns, and how the same canonical input log produces the same logical result in fast-forward and paced execution.
2. How a 1 s macro controller interval coordinates exactly ten 0.1 s BESS child intervals using zero-order-held inputs, explicit reductions and deterministic interruption at child ticks.
3. How an ideal fallback BESS and a reduced-order detailed BESS share a stable lifecycle contract while preserving common state during fallback-to-detailed activation.
4. Why requested, accepted, controller-target and applied power are different owned values, and how commands, acknowledgements, telemetry, quality and alarms preserve their causal lineage.
5. Why graph connectivity and island labels are not electrical power-flow results, and why an island without an approved forming model must be classified as unsupported.
6. Which mutable state must be captured for deterministic restore, identical continuation and reproducible alternative continuation.
7. How HTTP/WebSocket and viewer adapters can observe and command the system without their arrival order, connection count or rendering rate becoming simulation truth.

The validation report must answer the seven learning questions in NODE_CONTEXT.md explicitly; passing tests without that synthesis is insufficient.

## 4. Current architecture and prerequisite evidence

The current architecture ledger records no implementation, package, canonical contract, clock, scheduler, model, solver, persistent schema or supported scenario. TT-000 therefore establishes the first executable trunk; it does not refactor an existing runtime.

| Prerequisite | Evidence | Gate C interpretation |
|---|---|---|
| Project constitution and invariants | MASTER_PROJECT_CONTEXT.md | Binding |
| North-star direction | NORTH_STAR.md | Directional, not an implementation mandate |
| Lifecycle and migration rules | DEVELOPMENT_PROTOCOL.md | Binding |
| Agent and stage rules | AGENTS.md | Binding |
| Live capability state | TECH_TREE.md | No node is active or unlocked |
| Current implementation state | ARCHITECTURE.md | Documentation bootstrap only |
| Approved node charter | NODE_CONTEXT.md and recorded Gate A approval | Binding scope and learning questions |
| Approved research | RESEARCH_REPORT.md and recorded Gate B approval | Evidence from which this design is selected |
| Accepted ADRs | None; only ADR-0000-template.md exists | No prior ADR constrains this node |

This context introduces long-lived time, event-ordering and snapshot semantics. DEVELOPMENT_PROTOCOL.md requires an ADR for those decisions. If Gate C approves the corresponding checklist item, Milestone 0 must transcribe sections 9–12 into ADR-0001 without changing their substance and record that the human Gate C approval is the acceptance evidence. If that item is not approved, implementation remains blocked until a separate ADR is approved.

## 5. Scope and explicit non-goals

### 5.1 In scope

- One deterministic, single-threaded, synchronous logical-time simulation owner.
- Integer base ticks of 0.1 s and macro boundaries every 10 ticks, or 1 s.
- One infinite-grid source label, GRID bus, LOCAL bus, switchable PCC branch, aggregate constant load and BESS terminal.
- Deterministic graph connectivity and island classification, separate from active-power accounting.
- One lossless ideal bounded fallback BESS.
- One reduced-order detailed BESS with separate charge/discharge efficiency, first-order active-power response, ramp limits and energy/nameplate limits.
- Fallback-to-detailed activation at a quiescent macro boundary with typed common handoff state and continuity evidence.
- One supervisory/local control path with explicit requested, accepted, target and applied values.
- Versioned canonical commands, acknowledgements, telemetry, quality, alarms, topology events, fidelity events, scenario data, traces and snapshots.
- One unsupported-island interlock and one UNSUPPORTED_ISLAND_POWER_IMBALANCE alarm lifecycle.
- In-memory strict-JSON snapshot bytes, restore, identical continuation and alternative continuation.
- Fast-forward and optional wall-clock pacing around the same core execution.
- A thin FastAPI/Uvicorn adapter and static single-line viewer using HTTP for reads/commands and WebSocket for publications.
- Automated unit, contract, invariant, integration, golden, replay, sensitivity and adapter-isolation evidence.
- Optional JSON evidence export through a port; filesystem persistence is not required for core correctness.

### 5.2 Explicit non-goals and nonclaims

TT-000 does not implement or claim:

- AC or DC power flow, optimal power flow, voltage, frequency, current, reactive power or phase quantities.
- EMT, switching/PWM, harmonics, three-phase imbalance or sub-cycle phenomena.
- Fault-current calculation, relay timing, protection coordination or production breaker behaviour.
- Grid-following or grid-forming inverter controls, droop, black start, stable island operation or resynchronization.
- Cell, equivalent-circuit or electrochemical battery models; thermal behaviour, degradation, SoH, auxiliaries or safety.
- Multiple feeders, substations or arbitrary clock ratios.
- Interpolation, adaptive stepping, root finding, optimistic rollback, distributed simulation or FMI integration.
- IEC 61850, Modbus, OPC UA, DNP3, CIM or any industrial-protocol interoperability.
- Production EMS, SCADA, historian, alarm rationalization, authentication, authorization, redundancy or cybersecurity.
- IEEE, IEC, ISA, OPC UA, FMI, grid-code, certification or production-suitability compliance.
- UI zoom or viewer activity as a direct trigger for model-fidelity change.
- Detailed-to-fallback runtime activation.
- PCC reclosing or any synchronization claim in the required scenario.

## 6. Selected model boundary, equations and cited basis

### 6.1 Evidence map

The selected boundary follows the approved RESEARCH_REPORT.md:

| Design choice | Evidence in RESEARCH_REPORT.md |
|---|---|
| Integer logical time, stable total order and pacing separation | Sections 2.A, 7 and 15 |
| Fixed-ratio 1 s / 0.1 s coupling and reductions | Sections 2.B, 8 and 15 |
| BESS signs, equations, limits and synthetic fixture | Sections 2.C, 5, 6 and 15 |
| One-way fidelity activation | Sections 2.D and 9 |
| Connectivity/electrical separation and unsupported island | Sections 2.E and 10 |
| Command, alarm and quality semantics | Sections 2.F and 11 |
| Snapshot completeness and replay | Sections 2.G and 12 |
| API/viewer isolation and selected stack | Sections 2.H, 13 and 14 |

The report in turn cites FMI 3.0.2, Gomes et al. on co-simulation, Lee on deterministic concurrency, Python 3.14 documentation, energy-residual research, Sandia/DOE BESS guidance, OPC UA and ISA alarm precedents, CloudEvents, RFC 8259 and official tool documentation. These are design bases only; no conformance claim is made.

### 6.2 Topology and balance boundary

The canonical topology contains buses GRID and LOCAL, branch PCC, and terminals for the infinite-grid label, aggregate load and BESS. Only branches whose actual state is CLOSED contribute adjacency. A sorted breadth-first traversal returns connected components and whether each component contains the infinite-grid source.

Connectivity owns reachability and island labels only. ActivePowerBalance owns these algebraic accounting signals:

- Grid connected: P_grid_import = P_load - P_ac.
- Unsupported island: P_imbalance = P_ac - P_load.

P_imbalance is a teaching and alarm proxy. It must never be converted into voltage, frequency, current, rotor acceleration or electrical stability.

### 6.3 Common BESS boundary

At the BESS AC terminal:

- P_ac greater than zero means discharge and injection into LOCAL.
- P_ac less than zero means charging and import from LOCAL.
- E is stored usable energy in MWh.
- SoC = E / E_nom.
- P_bat = -dE/dt is positive when stored energy is depleted.
- P_loss is non-negative.
- P_bat = P_ac + P_loss.

Both implementations expose identity/version/capabilities, initialize from typed configuration and common state, validate input, advance one declared interval, observe typed output, export/import common handoff state, snapshot/restore complete private state and report invariants.

### 6.4 Fallback BESS

The fallback is a lossless architectural model:

- eta_ch = eta_dis = 1.
- P_applied is the accepted value after nameplate and energy-feasible limiting.
- Power is constant during a child interval h.
- E_next = E_now - P_applied × h / 3600.

The feasible AC range is computed before the step. Stored energy must never be repaired by post-step clipping.

### 6.5 Detailed BESS

For a held target P_target, current endpoint P_k, child interval h and time constant tau:

- P_lag = P_target + (P_k - P_target) × exp(-h / tau).
- delta_P = clip(P_lag - P_k, -R_down × h, R_up × h).
- P_next = energy_and_nameplate_feasible_clip(P_k + delta_P).
- P_ac_mean = (P_k + P_next) / 2 for the interval energy calculation.

For P_ac_mean greater than or equal to zero:

- P_bat_mean = P_ac_mean / eta_dis.
- P_loss_mean = P_ac_mean × (1 / eta_dis - 1).

For P_ac_mean less than zero:

- P_bat_mean = eta_ch × P_ac_mean.
- P_loss_mean = (-P_ac_mean) × (1 - eta_ch).

Then E_next = E_now - P_bat_mean × h / 3600.

The chosen trapezoidal mean defines this discrete reduced-order actuator; it is not claimed to be an exact continuously rate-limited inverter. A half-step sensitivity test must quantify cap, sign-crossing and event-coupling effects. Feasible limiting must be computed before the energy update so E remains within bounds without post-update clipping.

Each child and macro interval reports:

- r_E = delta_E + integral(P_ac + P_loss) dt / 3600.
- r_H = E_macro_integral - sum(E_child_integral).

Residuals are evidence and must not be silently forced to zero.

### 6.6 Synthetic model fixture

| Parameter | Value | Interpretation |
|---|---:|---|
| E_nom | 2 MWh | Synthetic educational fixture |
| SoC initial | 0.50 | Synthetic fixture |
| SoC minimum / maximum | 0.10 / 0.90 | Test operating bounds, not chemistry limits |
| Charge / discharge rating | 1 MW / 1 MW | Synthetic rating |
| Detailed eta_ch / eta_dis | 0.95 / 0.95 | Synthetic one-way efficiencies |
| Detailed tau | 2 s | Visible response at the child step |
| R_up / R_down | 0.5 MW/s / 0.5 MW/s | Synthetic ramp limits |
| Aggregate load | 0.6 MW consumption | Constant reference load |
| Macro / child period | 1 s / 0.1 s | Fixed ratio 10 |
| Island alarm threshold | abs(P_imbalance) greater than 0.05 MW | Synthetic condition |
| Alarm on/off delay | 0 ticks / 0 ticks | Deterministic lifecycle fixture |

All values remain scenario parameters. They are not vendor ratings or accuracy claims.

### 6.7 Fidelity activation

Only fallback-to-detailed activation is executable in V0. At a quiescent macro boundary:

1. Export a typed common state from the fallback without mutating it.
2. Construct detailed private state in isolation.
3. Initialize detailed P_applied from fallback P_applied, not from the requested target.
4. Preview observation and limits.
5. Require exact identity/lineage compatibility and absolute discontinuities no greater than 1e-12 MWh for E, 1e-12 for SoC and 1e-12 MW for P_applied.
6. On failure, retain the complete fallback state and emit a correlated failure record.
7. On success, atomically change the active model and emit one transition record containing before/after versions and measured discontinuities.

The common handoff state includes asset identity; source and target model identity/version; logical tick; E, E_nom, SoC; requested, accepted and applied power; operating and energization state; topology version/component; quality; last command identity; and per-source sequence lineage.

### 6.8 Unsupported island policy

When PCC actual state opens, the current child interval ends at that tick. Topology and operating context are recomputed before command validation. LOCAL becomes ISLANDED_UNSUPPORTED because no forming model exists. The interlock sets controller target and applied BESS AC power to zero at the event boundary, emits the reason and makes no transient electrical claim. Stored energy does not jump at the zero-duration event.

The algebraic imbalance becomes -0.6 MW for the reference load, quality is UNCERTAIN/SIMPLIFIED_ISLAND_PROXY, and the alarm becomes active/unacknowledged. Energy and SoC remain valid bookkeeping values. No voltage or frequency signal is invented. PCC closing is excluded from the required scenario.

## 7. Units, sign conventions, time semantics and validity domain

| Quantity or concept | Rule |
|---|---|
| Logical time | Non-negative integer base ticks |
| Base tick | 0.1 s in the reference scenario |
| Macro boundary | Every 10 base ticks, equal to 1 s |
| Power | MW at the named boundary |
| Energy | MWh |
| SoC and efficiency | Dimensionless |
| BESS AC power sign | Positive discharges/injects; negative charges/imports |
| Load sign | P_load is non-negative consumption |
| Grid import sign | Positive means import from GRID into LOCAL |
| Loss sign | Non-negative |
| Event occurrence | Integer logical tick plus ordered phase/source/sequence |
| Wall time | Optional adapter/audit metadata only |
| Telemetry aggregation | END, MEAN, INTEGRAL, MIN or MAX with an explicit interval |
| Quality | GOOD, UNCERTAIN or BAD plus reason and since-tick |

The model is valid only for aggregate active-power and usable-energy bookkeeping over the configured bounds and for exercising architecture semantics. It is numerically validated against its own declared equations, invariants and deterministic scenarios, not against a physical BESS product or an electrical network.

## 8. Components, package boundaries and dependency direction

The target source layout is:

| Package | Responsibility | May depend on |
|---|---|---|
| energy_simlab.contracts | Frozen domain dataclasses, enums, units, versions and port protocols | Python standard library only |
| energy_simlab.kernel | Logical clock, phase scheduler, event queue, deterministic identifiers and run control | contracts |
| energy_simlab.models.bess | Common BESS lifecycle, fallback model, detailed model and transition mapper | contracts |
| energy_simlab.control | Command validation, authority resolution, accepted setpoint and controller target | contracts |
| energy_simlab.topology | Canonical topology, deterministic BFS and connectivity classification | contracts |
| energy_simlab.balance | Algebraic active-power accounting only | contracts |
| energy_simlab.alarms | Alarm definitions, occurrence state and acknowledgement lifecycle | contracts |
| energy_simlab.snapshots | Snapshot assembly, canonicalization, checksum, restore and compatibility policy | contracts plus domain snapshot ports |
| energy_simlab.application | Composition-independent orchestration of kernel, models, topology, control, alarms and publications | all domain packages and contracts |
| energy_simlab.adapters.serialization | Pydantic v2 ingress/egress DTOs and mapping to domain dataclasses | contracts and Pydantic |
| energy_simlab.adapters.api | FastAPI HTTP/WebSocket adapter and bounded viewer fan-out | application ports, contracts and serialization adapter |
| energy_simlab.adapters.persistence | In-memory snapshot/trace stores; optional JSON file adapter | snapshot/recorder ports and contracts |
| energy_simlab.viewer | Static single-line assets only | Published HTTP/WebSocket schemas |
| energy_simlab.bootstrap | The single composition root and CLI entry points | application and selected adapters |

Dependency rules:

- Physics, kernel, topology, control and alarm packages do not import FastAPI, Uvicorn, Pydantic, filesystem, graph-library, database or viewer types.
- Domain contracts are frozen standard-library dataclasses/enums. Pydantic models are serialization-edge DTOs and never become physical state.
- The application depends on inward-facing ports; adapters implement those ports.
- External-library objects never cross adapter boundaries.
- There is exactly one simulation owner. ASGI multi-worker execution and auto-reload are not valid evidence modes.
- Tests must enforce forbidden imports or equivalent dependency checks.

## 9. Canonical contracts, schema versions and ownership

Target initial semantic version for all new contracts is 1.0.0 after Gate C. During the unapproved draft, that version is proposed rather than released. Every persistent or process-boundary record carries its own schema_version. Incompatible meaning, units or required-field changes require a new major version and migration or explicit rejection.

Domain record IDs are deterministic within a run: stable source identity plus a monotonic source sequence. The reference scenario supplies fixed command IDs. Random UUID generation and wall-clock timestamps are excluded from canonical replay bytes.

| Contract | Owner/producer | Required semantics |
|---|---|---|
| CommandV1 | Requesting source | ID, source, target, kind, requested value/unit, apply tick, expiry, source sequence, optional expected versions and reason |
| AcknowledgementV1 | Command validator | Command correlation, ACCEPTED, ACCEPTED_WITH_LIMIT, REJECTED or DUPLICATE status, reason, effective tick, accepted value/unit and target versions |
| TelemetrySampleV1 | Model/application publisher | Signal/asset, typed value, unit, tick, sequence, aggregation kind/window, quality, model and topology versions |
| QualityV1 | Producing domain component | GOOD, UNCERTAIN or BAD; reason, detail, origin, since tick and retained-value flag |
| AlarmEventV1 / AlarmStateV1 | Alarm service | Condition key, occurrence ID, active and acknowledged axes, severity, transition, tick, source and correlation |
| TopologyEventV1 / TopologySnapshotV1 | Topology service | Requested/actual old/new branch state, cause, version change, sorted components and source/island labels |
| FidelityEventV1 / ModelHandoffV1 | Model registry/transition service | Before/after identity and versions, common state, discontinuities, result and cause |
| MacroPublicationV1 | Application publisher | End state, means, integrals, extrema, ordered discrete records and residuals |
| ScenarioV1 | Scenario loader | Resolved parameters, scheduled canonical inputs, time base, seed and content hash |
| TraceV1 | Deterministic trace recorder | Ordered canonical domain records and run lineage |
| SnapshotEnvelopeV1 | Snapshot service | Complete mutable state, compatibility metadata, canonicalization profile and checksum |

State ownership is fixed:

- A caller owns P_requested until validation.
- The validator owns P_accepted and its acknowledgement.
- The controller owns P_target.
- The active BESS model owns P_applied and E.
- Topology owns breaker actual state, component identity and topology_version.
- Alarm service owns occurrence and acknowledgement state.
- Telemetry is an immutable observation and never becomes a second source of truth.

Required inward-facing ports are CommandIngress, PublicationSink, TraceRecorder, SnapshotStore, Pacer, TopologyService and ActivePowerBalance. The reference implementations are in-process; future network, database, graph or solver adapters must preserve these semantics.

### 9.1 Command validation and authority

Validation order is schema/version, identity, deterministic ID/idempotency, source sequence, apply tick/expiry, finite value and unit, command kind/range, expected model/topology version, target availability and interlocks.

- NaN, infinity, wrong unit, past/current live apply tick, stale sequence, unknown target, wrong version and nameplate-out-of-range power are rejected.
- A syntactically valid in-range power request may become ACCEPTED_WITH_LIMIT only when current stored-energy feasibility is tighter; the acknowledgement contains requested and accepted values and a reason.
- Ramp and lag affect P_applied, not P_accepted.
- Topology-derived safe-zero interlock overrides the controller target and is published explicitly; it does not rewrite the historical acknowledgement.
- An exact duplicate returns the recorded acknowledgement and is never executed twice.

For conflicting commands at the same apply tick, the authority order is:

1. Safety/interlock actions derived from current topology and availability.
2. Scripted scenario/fault commands.
3. Operator/API commands.
4. Supervisory-controller scheduled requests.

Within one authority source, order by source sequence and then canonical command ID. A lower-authority conflicting command receives a deterministic SUPERSEDED_BY_HIGHER_AUTHORITY acknowledgement. Network arrival order is never a tie-breaker.

## 10. Clock, scheduling and event-ordering rules

### 10.1 Scheduler key and phases

Every scheduled item uses the total key (logical_tick, phase, source_order, insertion_sequence). insertion_sequence is monotonic, snapshotted and restored. Iteration order from dictionaries or sets may not determine domain order.

| Phase value | Phase | Required effect |
|---:|---|---|
| 10 | EXOGENOUS | Apply scheduled scenario/fault facts |
| 20 | TOPOLOGY | Change requested/actual breaker state and topology version |
| 30 | OPERATING_CONTEXT | Recompute components, energization, mode and interlocks |
| 40 | FIDELITY | Execute eligible atomic model activation |
| 50 | COMMAND | Validate, resolve authority and acknowledge commands |
| 60 | CONTROL | Compute controller target from accepted intent and interlocks |
| 70 | MODEL_ADVANCE | Advance the active child model for the next interval segment |
| 80 | AGGREGATION | Compute macro reductions, balance and residuals |
| 90 | ALARM | Evaluate condition and acknowledgement transitions |
| 100 | PUBLICATION | Assign canonical sequences and publish immutable records |
| 110 | SNAPSHOT | Capture/restore only at an eligible quiescent macro boundary |

New same-tick work may target only a later incomplete phase. Scheduling into a completed or equal phase is rejected as a causality error. The core quiesces all later-phase work before advancing. No domain callback executes concurrently.

### 10.2 Multi-rate execution

- H = 1 s, h = 0.1 s and ratio r = 10 for the reference scenario.
- Configuration rejects non-positive periods, non-integral ratios and off-grid physics events.
- At a macro boundary, events and commands are resolved; accepted input is held with zero-order hold.
- Exactly ten child intervals complete for an uninterrupted macro period.
- A scenario topology event may interrupt at a child tick; completed segment durations must still sum exactly to H.
- Live API commands are admitted only for a published future macro boundary and are drained only at that boundary.
- The supervisor receives the completed child reduction at the next macro boundary; this one-macro observation latency is explicit.
- End samples preserve E, SoC, P_applied, mode, topology and quality.
- Means preserve P_ac and loss power; integrals preserve AC energy, stored-energy change and losses; extrema preserve power and SoC; ordered lists preserve every discrete record.
- Modes, quality, topology and alarms are never averaged.

### 10.3 Pacing and asynchronous edges

Fast-forward executes without sleeping. Paced mode maps logical boundaries to monotonic wall-clock deadlines and may sleep or record overrun; it never changes dt, skips a step or reorders work. Pause takes effect only at an eligible boundary.

The core publishes immutable copies to adapters and never awaits a viewer, socket, file or database. Viewer connection state, frame rate and rendering are infrastructure state, not domain state.

## 11. Persistence, snapshot and replay implications

### 11.1 Required snapshot contents

SnapshotEnvelopeV1 must include:

- Snapshot ID, schema version, logical tick/phase and parent run lineage.
- Engine name/version/build, numerical runtime profile and supported compatibility range.
- Complete resolved ScenarioV1 plus scenario/configuration hashes.
- Canonical contract, model, topology and time-base versions.
- Scheduler current key, insertion/source/publication counters, complete pending queue and cancellation/tombstone state.
- Active and inactive model state needed for transitions.
- Controller state, timers, requested/accepted/target/applied values and command deduplication/source sequences.
- Topology, breaker, component, mode, energization and version state.
- Alarm active/acknowledged state, occurrence identity and timers.
- Injected RNG algorithm and state, even if the reference scenario is deterministic without draws.
- Canonical pending ingress already accepted by the core.
- Trace/publication sequence state.
- Canonicalization profile and checksum.
- An explicit list of excluded infrastructure state.

Sockets, connected viewers, fan-out queues, render state, wall-clock pacer origin, sleep history and HTTP connection metadata are excluded.

### 11.2 Capture and restore boundary

Capture occurs only at phase SNAPSHOT on a macro tick after the boundary has quiesced, normal publications have stable sequence numbers and no model step is in progress. Snapshot lifecycle records receive deterministic sequence numbers before bytes and checksum are finalized. The core does not wait for adapters to store or display the snapshot.

Restore validates the envelope completely before mutating a fresh runtime. Restore creates a new run ID with parent_snapshot_id; it does not splice a backwards logical-time jump into an existing run trace. Validation failure leaves the destination runtime unstarted and emits a structured incompatibility result.

### 11.3 Canonical bytes and checksum

The V1 profile is canonicalization_profile = python-json-v1:

- UTF-8 JSON.
- Sorted object keys.
- Compact separators.
- Stable string encodings for enums and identifiers.
- Semantically sorted lists where order is not itself domain data.
- Priority queue serialized by full semantic queue key, not backing-heap layout.
- NaN and infinity rejected.
- SHA-256 lowercase hexadecimal over canonical bytes with the checksum field omitted.

Exact byte replay is guaranteed only for CPython 3.14.7, the locked dependency set, the same model/schema versions and a recorded supported platform profile. Other runtimes or versions require an explicit migrator plus regression evidence or are rejected. Pickle and arbitrary executable deserialization are forbidden.

### 11.4 Stores and replay tests

An in-memory SnapshotStore and canonical JSON serializer are required. A filesystem JSON store may be added as an optional adapter but is not part of core correctness or the node Definition of Done.

Identical continuation: capture at T, execute suffix A, restore into a fresh runtime, replay suffix A and require byte-identical trace suffix plus exact final canonical snapshot.

Alternative continuation: restore the same immutable snapshot into fresh runtimes for suffix A and suffix B; require an exact common prefix through T, repeatability within each suffix and the first divergence to correlate to the first different command.

Historical observation replay is outside the requirement; resending stored telemetry is not a substitute for restoring and advancing the simulator.

## 12. Compatibility and migration plan

| Item | Policy |
|---|---|
| Existing executable behaviour | None; characterize repository bootstrap state in Milestone 0 |
| Existing contracts/data | None to migrate |
| New external/persistent formats | ScenarioV1, TraceV1 and SnapshotEnvelopeV1 are versioned from first use |
| Additive compatible change | Optional field with documented default and unchanged meaning/unit |
| Breaking change | New major schema version, explicit mapper/migrator, tests and ADR when consequential |
| Unit/sign change | Never silent; requires new major contract version |
| Model upgrade | New model identity/version behind the same lifecycle; do not overwrite the only fallback |
| Unknown snapshot major/model version | Reject before mutation |
| Parallel comparison | Fallback and detailed receive controlled shared-state fixtures; transition preview occurs before switch |
| Rollback | Keep fallback selectable; failed activation is atomic; revert to last passing milestone commit on the feature branch |
| Deprecation | No V1 format or model is removed in TT-000 |

No persistent data migration is required. An optional file adapter writes only the newest supported format and, if later implemented, must use atomic replacement. Contract or time-semantic deviations discovered during Stage D return to Gate C or require an approved ADR; they are not silently recorded as implementation details.

## 13. Sequential milestones

Milestones are strictly sequential. A later milestone may not begin until the prior exit gate passes and its evidence is recorded in PROGRESS.md.

| Milestone | Coherent increment | Prerequisite | Exit result |
|---|---|---|---|
| M0 — Foundations and decisions | Source layout, dependency lock, ADR-0001 transcription, V1 domain contracts, Pydantic edge mappings and architecture-boundary checks | Gate C approval and feature branch creation | Contracts serialize/validate deterministically and dependency direction is enforced |
| M1 — Deterministic kernel | Integer clock, phase scheduler, queue, deterministic IDs, fast-forward/pacer port and toy trace | M0 | Hand-authored event order and paced/fast toy traces pass |
| M2 — Grid-connected fallback slice | Two-bus closed topology, constant load, fallback BESS, command/ack/control path, macro publication and balance | M1 | A command produces acknowledged, energy-consistent grid-connected telemetry |
| M3 — Detailed multi-rate model and activation | Detailed BESS, ten-child reduction, residuals, common handoff and atomic fallback-to-detailed activation | M2 | Analytic, ramp, energy, sensitivity and transition gates pass |
| M4 — Topology event and alarm lifecycle | PCC opening, deterministic island classification, safe-zero interlock, quality and one alarm occurrence/acknowledgement lifecycle | M3 | Exact component, mode, imbalance, correlation and alarm-state tests pass |
| M5 — Snapshot and branching replay | Complete snapshot assembly, canonical JSON/checksum, in-memory store, fresh-runtime restore, identical and alternative continuation | M4 | Byte replay, final state, RNG and incompatibility tests pass |
| M6 — Asynchronous API and viewer | HTTP reads/commands, WebSocket publications, bounded fan-out and static single-line viewer | M5 | Viewer count/rate and slow-client tests cannot alter the canonical trace |
| M7 — Reference demonstration and validation package | Scripted golden scenario, full regression, run instructions, validation evidence and required project documents | M6 | Node-specific Definition of Done evidence is ready for Gate D review |

## 14. Required tests and gate for every milestone

### M0 gate

Required evidence:

- Contract round-trip for every V1 record.
- Rejection of wrong major version, NaN/infinity, wrong unit and missing causal fields.
- Deterministic serialization of equivalent domain values.
- Pydantic DTO-to-domain mapping without Pydantic objects entering physics packages.
- Dependency/forbidden-import test.
- Locked runtime/package versions and license inventory.
- ADR-0001 matches the Gate C-approved time, ordering and snapshot decisions.

Stop if the ADR requires a substantive choice not approved at Gate C.

### M1 gate

Required evidence:

- Exact hand-authored order across all phases.
- Equal-phase source and insertion tie tests.
- Rejection of scheduling into equal/completed phases.
- Queue cancellation/tombstone and counter state tests.
- Exact integer tick and 10:1 boundary count tests using a toy child.
- Fast-forward versus paced canonical toy trace equality after excluding wall diagnostics.
- Pacer overrun cannot change logical results.

### M2 gate

Required evidence:

- Closed-PCC components equal one sorted component containing GRID and LOCAL.
- Fallback constant charge/discharge analytic energy tests at 1e-12 relative and absolute MWh tolerance.
- Energy-bound commands never push E outside bounds by more than 1e-12 MWh.
- Static nameplate-out-of-range rejection and energy-feasible accepted-limit reasons.
- Valid, duplicate, stale-sequence, expired and wrong-version command tests.
- Requested, accepted, target and applied ownership fields remain distinct.
- Grid balance P_grid_import = P_load - P_ac and complete macro publication.

### M3 gate

Required evidence:

- Detailed 1 MW discharge for 1 h: delta E = -1.0526315789473684 MWh and loss = 0.0526315789473684 MWh within 1e-12 relative/absolute tolerance.
- Detailed -1 MW charge for 1 h: delta E = +0.95 MWh and loss = 0.05 MWh at the same tolerance.
- Uncapped lag from zero toward 1 MW: P at 2 s = 0.6321205588285577 MW and at 4 s = 0.8646647167633873 MW within 1e-12 relative/absolute tolerance.
- Ramp endpoint change no greater than R × h plus 1e-12 MW.
- Exactly ten child completions and exact duration sum per uninterrupted macro interval.
- r_E no greater than 1e-10 MWh per macro and 1e-9 MWh over the short reference run; r_H no greater than 1e-12 MWh.
- h = 0.05 s sensitivity: uncapped analytic endpoints match; capped/limited maximum delta P no greater than 1e-3 MW and absolute delta E no greater than 1e-6 MWh provisionally.
- Successful transition has exact discrete lineage and E/SoC/P discontinuities no greater than 1e-12 in their units.
- Failed transition leaves active model and complete state unchanged.

The provisional sensitivity tolerances become accepted only if the Gate C reviewer approves them and M3 evidence supports them. If they fail, classify the cause and return to Gate C; do not widen them silently.

### M4 gate

Required evidence:

- Closed components are {GRID, LOCAL}; open components are {GRID} and {LOCAL}, with exact deterministic IDs and topology versions.
- A command simultaneous with PCC opening is evaluated against post-opening topology.
- Unsupported island has exact operating and energization states.
- Interlock produces P_applied = 0 MW without an E jump at the event.
- With P_load = 0.6 MW, P_imbalance = -0.6 MW and quality = UNCERTAIN/SIMPLIFIED_ISLAND_PROXY.
- Alarm occurrence, acknowledge-while-active, clear-before-acknowledge and close-after-both transition sequences are exact.
- Correlation links topology event, interlock, imbalance and alarm occurrence.
- Dispatch in unsupported-island mode is rejected deterministically.

### M5 gate

Required evidence:

- Snapshot inventory test mutates every declared mutable state class and proves it restores.
- Queue, counters, dedupe state, alarm acknowledgement, inactive transition state and RNG survive restore.
- Unknown schema/model/runtime profile is rejected before destination mutation.
- Canonical snapshot equality is independent of map insertion and heap backing order.
- Identical continuation produces byte-identical suffix trace and exact final snapshot.
- Alternative continuation has an exact shared prefix, deterministic repeatability in both branches and causal first divergence.
- Checksum corruption is detected.

### M6 gate

Required evidence:

- HTTP request/ack and read schemas map through DTOs to canonical domain records.
- WebSocket publications carry logical sequence and version fields.
- Zero, one and multiple viewer connections produce byte-identical canonical domain traces for the same input log.
- Different render/read rates produce byte-identical canonical domain traces.
- Per-viewer queue capacity is 64 publication frames.
- Continuous telemetry coalesces to latest value per signal for a slow viewer.
- Discrete events are never silently discarded: if capacity remains exhausted after telemetry coalescing, the viewer is disconnected and must resynchronize.
- viewer_dropped_publications_total and disconnect reason are infrastructure diagnostics excluded from canonical physics evidence.
- Core evidence sink remains lossless and is never back-pressured.
- Configuration rejects multiple ASGI workers for the in-memory owner.

### M7 gate

Required evidence:

- The deterministic reference scenario in section 15 passes in fast-forward and paced modes with byte-identical canonical traces after wall diagnostics are excluded.
- The scenario passes with zero, one and multiple viewer connection patterns.
- All M0–M6 tests and applicable regressions pass from a clean environment.
- Golden trace includes commands, acknowledgements, fidelity, topology, alarm, publication and snapshot lifecycle records with versions and correlation.
- Validation report traces every claimed behaviour to approved research, implementation and test evidence.
- Demonstration and setup commands are repeatable.
- Unsupported phenomena and nonclaims are visible in user-facing documentation.
- Required documentation in section 17 is complete without marking the node unlocked before Gate D.

## 15. Deterministic reference scenario

Reference IDs and commands are fixed inputs, not generated from wall time.

| Tick | Time | Action | Required result |
|---:|---:|---|---|
| 0 | 0 s | Initialize run TT000-REF-V1 with PCC closed, fallback BESS, E = 1.0 MWh, load = 0.6 MW | One source-connected component; mode GRID_CONNECTED_AVAILABLE; no active alarm |
| 10 | 1 s | Scenario command CMD-P-001 requests +0.4 MW | ACCEPTED; fallback applies +0.4 MW; grid import becomes +0.2 MW |
| 30 | 3 s | Scenario command CMD-M-001 requests detailed-model activation | Atomic success; common E, SoC and P remain continuous within 1e-12; model version changes |
| 40 | 4 s | Scenario command CMD-P-002 requests -1.0 MW | ACCEPTED; detailed response exposes lag/ramp policy while respecting energy and rating bounds |
| 80 | 8 s | Scenario command CMD-PCC-001 opens PCC | Topology updates before command/control; LOCAL becomes unsupported island; safe-zero interlock applies; imbalance is -0.6 MW; alarm occurrence becomes active/unacknowledged |
| 90 | 9 s | Scenario command CMD-SNAP-001 requests snapshot S-TT000-090 | Snapshot captured after quiescence with alarm unacknowledged and complete scheduler/model/control/topology state |
| 100 | 10 s | Suffix A command CMD-ACK-001 acknowledges the alarm occurrence | Acknowledgement accepted; alarm becomes active/acknowledged |
| 120 | 12 s | End suffix A | State remains ISLANDED_UNSUPPORTED and deterministic; capture final A evidence |

Identical continuation restores S-TT000-090 into a fresh runtime and executes suffix A again; its suffix trace and final snapshot must be byte-identical.

Alternative continuation restores the same snapshot into a fresh runtime and uses:

| Tick | Time | Suffix B action | Required result |
|---:|---:|---|---|
| 100 | 10 s | Operator command CMD-P-ALT-001 requests +0.3 MW | REJECTED with TARGET_MODE_UNAVAILABLE; no power application |
| 120 | 12 s | End suffix B without alarm acknowledgement | Alarm remains active/unacknowledged; branch is repeatable and first divergence correlates to CMD-P-ALT-001 |

Suffixes share exact state and trace lineage through the snapshot. Their physical energy may remain equal; the command, acknowledgement and alarm state must diverge for an explicit causal reason. The scenario does not close the PCC or claim stable island operation.

Separate validation fixtures exercise full one-hour energy equations, energy bounds, alarm return-to-normal orderings, failed activation, corrupted snapshots and h = 0.05 s sensitivity; those are not forced into the short demonstration timeline.

## 16. Node-specific Definition of Done

TT-000 is ready for Gate D review only when:

- Every learning outcome in section 3 and every NODE_CONTEXT.md learning question is answered with evidence.
- The feature branch contains only Gate C-approved scope or separately approved deviations.
- All milestone gates in sections 13–14 pass sequentially and their exact commands/results are recorded in PROGRESS.md.
- The deterministic core has one owner, integer logical time, frozen phase order and no asynchronous domain callbacks.
- Fast-forward and paced execution produce identical canonical logical results.
- The 10:1 macro/child coupling, reductions, residuals and sensitivity gate pass.
- Fallback and detailed models satisfy their declared equations, signs, units, bounds and validity limits.
- Fallback-to-detailed activation is atomic and continuous within the approved tolerances; failed activation rolls back completely.
- Connectivity and active-power accounting remain distinct; unsupported island behaviour makes no electrical-stability claim.
- Commands, acknowledgements, telemetry, topology, fidelity, quality and alarms use versioned canonical contracts with explicit ownership and causality.
- Snapshot restore reproduces all mutable state, canonical byte replay and RNG continuation under the declared profile.
- The alternative continuation is deterministic and causally explained.
- Viewer/API connection count, rendering rate and slow-client behaviour do not alter canonical domain results.
- The reference scenario and all regression tests pass from a clean locked environment.
- Claims are traceable to sources, implementation and tests; unsupported claims are explicitly rejected.
- ARCHITECTURE.md, REFERENCES.md, CHANGELOG.md, VALIDATION_REPORT.md and RETROSPECTIVE.md are complete as required.
- TECH_TREE.md is not updated to unlocked until the human Gate D review validates the node.
- No branch is merged merely because code exists.

## 17. Required documentation updates

### During implementation

- Create ADR-0001 from the Gate C-approved time, event-ordering, command-authority and snapshot semantics before behavioural implementation.
- Update PROGRESS.md after each milestone with commit/reference, test command, result and any deviation.
- Add developer setup, deterministic scenario and viewer run instructions to README.md or a dedicated linked guide.
- Keep this FEATURE_CONTEXT.md unchanged after approval unless a human-approved Gate C amendment is recorded.
- Do not alter substantive approved-research conclusions to fit implementation.

### At validation/integration, and only when supported by evidence

- Populate VALIDATION_REPORT.md with learning-question answers, traceability, test results, tolerances, replay results, limitations and rejected claims.
- Update ARCHITECTURE.md to record implemented components, contracts, clocks, models, ports, dependencies, snapshots and supported scenario.
- Register accepted sources and exact versions in REFERENCES.md.
- Update CHANGELOG.md.
- Complete RETROSPECTIVE.md.
- Update TECH_TREE.md only after Gate D approval; record only validated capability and evidence, then reassess nearby non-binding candidates.
- Preserve TT-000 as not active/unlocked until the applicable governance record authorizes the state change.

## 18. Risks, stop conditions and rollback strategy

| Risk | Stop condition | Required response / rollback |
|---|---|---|
| Event semantics are ambiguous in code | Two valid executions can order the same inputs differently | Stop M1; correct specification or return to Gate C; revert to last passing M0 commit |
| Async ingress affects logical order | Connection or arrival timing changes canonical trace | Stop M6; isolate ingress at future macro boundaries; disable adapter |
| Numerical residual or sensitivity gate fails | M3 tolerance exceeded | Stop; classify discretization, sign, limiting or equation error; do not widen tolerance silently |
| Fidelity activation mutates source before validation | Failed activation changes any state | Stop M3; restore atomic preview/switch design; keep fallback active |
| Island output implies electrical support | Voltage/frequency is invented or island called stable | Stop M4; remove claim/output and restore unsupported classification |
| Snapshot is incomplete | Any mutation class or replay suffix diverges | Stop M5; expand inventory/version and rerun all replay tests |
| Runtime/profile mismatch | Exact replay requested under unsupported versions | Reject restore clearly; require migrator and new evidence |
| Adapter/library object crosses domain boundary | FastAPI, Pydantic, graph or store type appears in core state | Stop current milestone; move mapping behind adapter |
| Multi-worker server duplicates owner | More than one in-memory simulator can run | Reject configuration; use one worker |
| Required package/runtime cannot be locked or licensed | Reproducible clean install or license inventory fails | Stop M0 and return to Gate C for stack revision |
| Approved research is contradicted | Evidence invalidates a selected model or tolerance | Stop at current milestone and return to Gate B or C as appropriate |
| Scope expands into a deferred candidate | Work requires unapproved physics/protocol/security capability | Do not implement; record as a candidate learning question |

Rollback is milestone-based on the feature branch. Revert only the failing milestone's commits without destructive Git operations or loss of unrelated work. The fallback model remains a selectable, tested implementation. Detailed activation is transactional. Adapters can be disabled without changing the core. No rollback rewrites approved evidence or marks the node validated.

## 19. Candidate learning questions exposed but outside scope

These are non-binding candidates, receive no permanent node ID here and must not be implemented under TT-000:

- What fidelity transition policy can support detailed-to-fallback changes without hiding transient-state loss?
- When do arbitrary ratios, interpolation, adaptive stepping or root-found events become necessary?
- How should a real electrical solver consume topology while preserving canonical identities and deterministic scheduling?
- What model boundary and validation evidence are needed for voltage/frequency, reactive power and grid-forming island operation?
- How should a device-calibrated or PyBaMM-based battery model map to the aggregate AC lifecycle?
- What FMI capability negotiation, rollback and coupling algorithms are required for external co-simulation units?
- Which historian requirements justify DuckDB, Parquet or another store, and how should schema evolution work?
- How should IEC 61850, Modbus or other protocol adapters map quality, command and event semantics?
- What alarm shelving, suppression, flood-management and rationalization behaviour is educationally valuable?
- How should authentication, authorization, segmentation, audit and communication-failure models attach without contaminating physics?
- What breaker travel, interlock and protection models are required before PCC reclosing or resynchronization can be demonstrated?

## Gate C checklist for human approval

The human project owner approved each item explicitly on 2026-08-26:

- [x] The approved status is understood: TT-000 enters Stage D but remains neither validated nor unlocked.
- [x] The branch feature/TT-000-vertical-slice-0 is approved for Stage D implementation.
- [x] The learning outcomes, scope and explicit non-goals are approved.
- [x] The fallback and detailed BESS equations, signs, limits, synthetic fixture and validity domain are approved.
- [x] The 1 s macro / 0.1 s child periods, 10:1 coupling and provisional half-step tolerances are approved.
- [x] The ordered phases, topology-before-command rule and command-authority policy are approved.
- [x] The unsupported-island safe-zero policy, algebraic imbalance nonclaim and alarm definition are approved.
- [x] The one-way fallback-to-detailed transition and continuity tolerances are approved.
- [x] The package boundaries, standard-library domain contracts, Pydantic edge DTOs and dependency direction are approved.
- [x] The V1 schema ownership, command lifecycle, deterministic IDs and viewer queue/loss policy are approved.
- [x] The snapshot inventory, python-json-v1 canonicalization, SHA-256 checksum and same-profile replay guarantee are approved.
- [x] The eight (0 - 7) sequential implementation milestones and every milestone test gate are approved.
- [x] The deterministic reference scenario, identical replay and alternative continuation are approved.
- [x] The node-specific Definition of Done, documentation duties, risks, stop conditions and rollback policy are approved.
- [x] Gate C approval also authorizes ADR-0001 to transcribe these approved time, event-ordering, command-authority and snapshot decisions without introducing new choices.
- [x] Gate C is approved by the human project owner on 2026-08-26 and recorded in PROGRESS.md.
