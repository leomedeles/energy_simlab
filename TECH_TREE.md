# Live Technology Tree — Disposable TT-000 Provisional Frontier Preview

> [!CAUTION]
> **DISPOSABLE SIDEQUEST PREVIEW — NEVER MERGE THIS BRANCH INTO 'main'.**
>
> This document is based on the **unvalidated** TT-000 implementation observed on
> 'feature/TT-000-vertical-slice-0' at commit
> 'f5ca22e28bdf6a32324c7d10021ff24f3d34ba85' on 2026-08-27.
> Gate D has not been performed or approved. No capability in this version may be
> treated as canonically unlocked. Every maturity assessment and frontier candidate
> below is provisional. The canonical next action remains independent TT-000
> validation. Every proposed future node is conditional on TT-000 eventually passing
> Gate D or being corrected in response to Gate D findings.

## Preview status and authority

| Field | Provisional value |
|---|---|
| Preview kind | Disposable, noncanonical analytical sidequest |
| Source branch | 'feature/TT-000-vertical-slice-0' |
| Exact observation commit | 'f5ca22e28bdf6a32324c7d10021ff24f3d34ba85' |
| Preview branch | 'sidequest/tt-000-provisional-frontier' |
| Preview date | 2026-08-27 |
| TT-000 implementation status observed | M0–M7 recorded complete by developer; separate Gate D review pending |
| Canonical unlock status | None |
| Canonical next action | Perform TT-000 Gate D validation |

This file deliberately bypasses the normal timing of a technology-tree update only
inside this disposable branch. It does not perform Stage E validation, Stage F
integration, node selection, architecture approval, or an unlock. The canonical
'TECH_TREE.md' remains the version outside this branch.

## Evidence and classification rules

- **Implemented and supported by existing automated tests** means code and relevant
  developer-authored tests exist. It does not mean the tests or capability have been
  independently validated.
- **Implemented but not yet independently validated** means the end-to-end capability
  is present and developer evidence exists, while Gate D is still absent.
- **Partially implemented**, **specified but not implemented**, **absent**, and
  **uncertain from available evidence** retain their literal meanings.

'PROGRESS.md' records 180 tests passing from the locked CPython 3.14.7 profile and a
repeatable M7 demonstration. This preview treats those as existing evidence only; it
does not convert them into an independent reproduction or Gate D verdict.

## Provisional maturity scale

| Label | Provisional meaning |
|---|---|
| P0 — absent | No relevant implementation is present. |
| P1 — specified | A boundary or intended capability is documented but not implemented. |
| P2 — partial | A narrow implementation or seam exists, without an end-to-end realm capability. |
| P3 — implemented / developer-tested | The V0 capability and automated tests exist, but independent validation is absent. |
| P4 — integrated / developer-tested | The capability participates in the M7 slice and has developer evidence, but independent validation is absent. |

No provisional label means validated, integrated into 'main', unlocked,
standards-conformant, or production-ready.

## Current-system capability assessment

| Capability | Classification | Observed implementation | Existing evidence | Important gap |
|---|---|---|---|---|
| V1 canonical records and edge DTOs | Implemented and supported by existing automated tests | Frozen domain records, semantic validation, Pydantic mapping and canonical JSON | M0 contract/serialization/dependency tests | Vocabulary is TT-000-shaped; no compatibility evidence beyond V1/same profile |
| Deterministic logical-time scheduler | Implemented and supported by existing automated tests | Integer ticks, eleven phases, stable ties, cancellation and restorable counters | M1 scheduler tests; M5 snapshot tests; ADR-0001 | The integrated demonstration still invokes several domain actions directly rather than through generic scheduled handlers |
| Fast-forward/pacing separation | Implemented and supported by existing automated tests | No-op and wall pacers wrap the same logical run | M1 toy tests; M7 fast/fake-wall equality | Real wall-clock load/overrun behaviour has not been independently characterized |
| Fixed 10:1 BESS coupling | Implemented and supported by existing automated tests | Ten child steps with reductions and residuals | M3 analytic/residual/sensitivity tests | Runner accepts 'DetailedBess' directly; arbitrary ratios, interruption and external units are absent |
| Fallback BESS | Implemented and supported by existing automated tests | Lossless bounded power/energy bookkeeping | M2 analytic and bound tests | Synthetic aggregate model only |
| Detailed BESS | Implemented and supported by existing automated tests | Efficiency, first-order response, ramp and energy/nameplate limits | M3 tests | Synthetic AC-boundary model; no device validation |
| Fallback-to-detailed activation | Implemented and supported by existing automated tests | Atomic handoff and continuity checks | M3 transition tests | Registry and snapshots are BESS-specific |
| Detailed-to-fallback activation | Specified but not implemented | Reverse handoff is documented | Deferred research/feature scope | Transient-loss policy unresolved |
| Boolean topology | Implemented and supported by existing automated tests | Typed sorted BFS and deterministic component IDs | M2/M4 tests | Operations/application code hard-code GRID, LOCAL and PCC |
| Electrical network solution | Absent | Algebraic active-power balance only | Tests cover grid import and proxy imbalance | No voltage, frequency, reactive power, flow, fault current or dynamics |
| Command/ack/control ownership | Implemented and supported by existing automated tests | Deterministic validation, dedupe, authority and requested/accepted/target/applied values | M2/M4/M6/M7 tests | Targets and execution routes are TT-000-specific |
| Unsupported-island safe zero | Implemented and supported by existing automated tests | PCC opening, unsupported mode, zero target/power, proxy imbalance and correlated alarm | M4/M7 tests | Explicitly not energized island operation, protection or resynchronization |
| Alarm lifecycle | Implemented and supported by existing automated tests | One active/acknowledged two-axis alarm | M4/M7 tests | No alarm configuration, shelving, suppression or flood handling |
| Snapshot/restore/branching replay | Implemented and supported by existing automated tests | Complete V1 envelope, canonical JSON, checksum and same-profile continuation | M5/M7 tests | State owners are enumerated manually; compatibility is hard-coded to one runtime profile and known BESS models |
| HTTP/WebSocket and fan-out | Implemented and supported by existing automated tests | Command/read endpoints, publications, lossless evidence sink, coalescing and slow-viewer disconnect | M6/M7 tests | No authentication, durable resync or multi-owner deployment |
| Static single-line viewer | Implemented but not yet independently validated | Hard-coded GRID–PCC–LOCAL/load/BESS page | M6/M7 packaging tests | No topology-driven rendering, alarm list or event navigation |
| Trace/snapshot persistence | Partially implemented | Canonical in-memory trace and store ports | M5/M6 tests | No durable historian, retention, queries, migrations or observation replay |
| Industrial interoperability | Absent | In-process records plus HTTP/WebSocket only | Explicit non-goal | No IEC 61850, Modbus, OPC UA, DNP3, CIM or conformance evidence |
| Reliability and maintenance | Absent | No failure, repair, degradation or maintenance model | Explicitly unadvanced | No generic availability boundary |
| Cybersecurity | Absent | No identity, authorization, segmentation or audit policy | Explicitly unadvanced | Caller-supplied authority is trusted at the API edge |
| Compliance/independent validation | Partially implemented | Developer traceability, tests, golden hashes and nonclaims | M7 package | Gate D absent; references not canonically registered; no compliance claim |

## Provisional realm maturity

| Realm | Observed implementation | Existing evidence | Provisional maturity | Missing Gate D evidence | Limitation or exposed gap |
|---|---|---|---|---|---|
| Simulation kernel and time | Integer ticks, ordered events, fixed-ratio runner, pacing and scheduler snapshots | M1/M3/M5/M7 developer tests | **Provisional P4 — integrated / developer-tested** | Independent ordering, pacing, snapshot and tolerance reproduction | Runtime and multi-rate execution remain specialized |
| Physics and numerical models | Two aggregate BESS fidelities and algebraic bookkeeping | M2/M3/M7 tests | **Provisional P3 — implemented / developer-tested** | Independent equation/reference and claim-boundary review | No electrical state or device calibration |
| Control and automation | Command lifecycle, authority, ownership and safe-zero interlock | M2/M4/M6/M7 tests | **Provisional P3 — implemented / developer-tested** | Independent simultaneous-event and causal-lineage review | Hard-coded to one BESS and PCC |
| Topology and protection | Two-bus connectivity, PCC open and island classification | M2/M4/M7 tests | **Provisional P2 — partial** | Independent topology/event review | Protection, breaker travel, faults, reclosing and resynchronization absent |
| Communications and interoperability | Typed in-process contracts and HTTP/WebSocket edges | M0/M6 tests | **Provisional P2 — partial** | Independent isolation/back-pressure/mapping review | No industrial protocol or impairment model |
| SCADA and visualization | Static single-line viewer and command/read/publication edges | M6/M7 tests | **Provisional P2 — partial** | Independent operational workflow review | Scenario-specific, no operational alarm/event workflow |
| Data and historian | In-memory trace, snapshots and logical branching replay | M5/M7 tests | **Provisional P2 — partial** | Independent integrity/completeness/replay review | No durable historian or observation replay |
| Reliability and maintenance | None | None | **Provisional P0 — absent** | Confirm realm was not advanced accidentally | No failure/repair/availability semantics |
| Cybersecurity | None | None | **Provisional P0 — absent** | Confirm no security claim is implied by the API | No identity, permissions, audit or segmentation |
| Compliance and validation | Developer evidence package and explicit nonclaims | M0–M7 developer evidence | **Provisional P2 — partial** | Entire independent Gate D and human verdict | Passing tests is not validation; nothing is unlocked |

## Architectural seams actually observed

| Seam | Observed strength | Pressure revealed |
|---|---|---|
| Contracts/serialization adapter | Strong in V0 | New assets/solver results need controlled contract evolution |
| Scheduler/pacer | Strong for the tested scenario | Generic action dispatch, interruption and external units remain untested |
| BESS model boundary | Moderate | Lifecycle used by runtime is wider than 'BessPowerModel'; runner/registry/snapshots use concrete classes |
| Topology service | Moderate | Recompute is generic, but PCC/local operations are hard-coded |
| Active-power balance port | Weak-to-moderate | Signature accepts one load and one BESS rather than arbitrary typed injections or solver results |
| Command ingress/ack | Moderate | Admission is isolated; validation/execution is command- and target-specific |
| Snapshot store/envelope | Strong for exact TT-000 inventory | Every new owner/model pressures envelope, compatibility and restore assembly |
| Publication/fan-out | Strong for isolation | Durable replay/resynchronization and operational views are absent |

These seams make replaceability/extensibility a plausible hypothesis with good V0
developer evidence, not yet a demonstrated general property.

## Provisional frontier candidates

Candidate names are deliberately unnumbered. None is selected or authorized.

### Simulation kernel and time

#### Candidate: Reversible fidelity lifecycle

- **Realms:** Simulation kernel and time; physics and numerical models.
- **Observed trigger:** Registry supports only fallback-to-detailed; reverse handoff is documented but deferred.
- **Why adjacent:** Common state, atomic preview/switch and snapshots already exist.
- **Learning question:** How can a richer model be replaced without hiding discarded transient state or creating an unexplained jump?
- **Possible unlock:** Controlled detailed-to-fallback transition and reversible comparison.
- **Prerequisite evidence:** Gate D; validated handoff, snapshot and model invariants.
- **Dependencies:** Approved immediate-response, one-boundary-hold or stateful-fallback policy.
- **Architectural pressure:** General lifecycle port, transition event, inactive-state snapshot and contract tests.
- **Complexity:** Medium.
- **Uncertainty:** Whether fallback must gain state, changing its meaning.
- **Pursue/defer:** Pursue early as a narrow backbone test; defer if Gate D finds current handoff/snapshot defects.

#### Candidate: External FMI co-simulation unit

- **Realms:** Kernel/time; interoperability; physics.
- **Observed trigger:** FMI informed the design, but no external unit, negotiation, early return or rollback exists.
- **Why adjacent:** Logical-time and model boundaries offer an adapter insertion point.
- **Learning question:** Which FMI step/state/failure semantics preserve canonical determinism?
- **Possible unlock:** One external model behind a canonical adapter.
- **Prerequisite evidence:** Gate D; generic lifecycle; external-state snapshot policy.
- **Dependencies:** FMI tool, supported subset and independently checkable FMU.
- **Architectural pressure:** Step negotiation, interruption, binary state, errors, versioning and differential tests.
- **Complexity:** Extra large.
- **Uncertainty:** External determinism, portability and rollback support.
- **Pursue/defer:** Defer until a smaller in-process generalization succeeds.

### Physics and numerical models

#### Candidate: Extensible multi-asset composition with PV and profiled load

- **Realms:** Physics; control; topology; kernel/time.
- **Observed trigger:** Runtime, commands, balance, snapshots, publications and viewer repeatedly hard-code BESS, LOAD, LOCAL and PCC.
- **Why adjacent:** Terminals, commands, telemetry, snapshots and a composition root already exist.
- **Learning question:** Can a second source and time-varying consumer use the same lifecycle, control, balance, snapshot and publication paths without breaking V0?
- **Possible unlock:** Scenario-defined multi-asset microgrids and a foundation for PV, wind, genset and flexible loads.
- **Prerequisite evidence:** Gate D; V0 characterization tests; contract compatibility policy.
- **Dependencies:** Generic asset lifecycle, injection/consumption record, routing and snapshot registration.
- **Architectural pressure:** Replace target-specific conditionals/scalars with deterministic registries and collections.
- **Complexity:** Large.
- **Uncertainty:** How to avoid prematurely designing a universal asset abstraction.
- **Pursue/defer:** Strong early candidate; restrict scope to one PV profile and one load profile.

#### Candidate: Electrical power-flow solver adapter

- **Realms:** Physics; topology/protection; validation.
- **Observed trigger:** Scalar balance provides no electrical state while a solver port is a stated maturation seam.
- **Why adjacent:** Typed topology, deterministic scheduling and quality already exist.
- **Learning question:** How should canonical topology/assets map to a solver without leaking tool objects or confusing connectivity with electrical results?
- **Possible unlock:** Validated steady-state voltage, flow, losses and constraint observations for a small network.
- **Prerequisite evidence:** Gate D; generic injections; authoritative small reference case/tolerances.
- **Dependencies:** Solver choice, per-unit/base rules, reactive-power records and failure-quality policy.
- **Architectural pressure:** Solver-result contracts, mappings, differential tests and scalar-balance replacement.
- **Complexity:** Extra large.
- **Uncertainty:** Honest educational boundary without planning/grid-code overclaims.
- **Pursue/defer:** High value; follow or pair with a tightly scoped generic injection model.

#### Candidate: Grid-forming island dynamics

- **Realms:** Physics; control; topology/protection.
- **Observed trigger:** V0 deliberately enters unsupported island and forces zero because voltage/frequency-forming behaviour is absent.
- **Why adjacent:** The unsupported boundary identifies the missing evidence and gives a deterministic extension scenario.
- **Learning question:** What minimum voltage/frequency state, limits and dynamics justify supported-island claims?
- **Possible unlock:** Bounded island-capable microgrid operation.
- **Prerequisite evidence:** Gate D; electrical model boundary; validated forming reference/stability criteria.
- **Dependencies:** Solver/dynamics, PCS control, load dependence and disturbance cases.
- **Architectural pressure:** New timescale, mode state, telemetry/quality, hierarchy, tolerances and snapshots.
- **Complexity:** Extra large.
- **Uncertainty:** Risk of another plausible but weakly grounded model.
- **Pursue/defer:** Defer until the electrical solver/model boundary is validated.

### Topology and protection

#### Candidate: Breaker lifecycle and protection-driven isolation

- **Realms:** Topology/protection; control; reliability.
- **Observed trigger:** PCC requested/actual states change simultaneously; no travel, interlock, failure or relay decision exists.
- **Why adjacent:** Typed events, phase ordering and causal alarms already exist.
- **Learning question:** How should sensing, relay decision, trip, breaker travel/failure and recomputation be ordered?
- **Possible unlock:** Representative protection-driven isolation and sequence-of-events evidence.
- **Prerequisite evidence:** Gate D; defensible disturbance quantity and relay/breaker reference.
- **Dependencies:** Electrical/fault proxy, breaker timers/states and protection contracts.
- **Architectural pressure:** Finer events, requested/actual ownership, failure paths and SOE volume.
- **Complexity:** Large.
- **Uncertainty:** Whether a proxy trip is meaningful before fault-current calculation.
- **Pursue/defer:** Bound to a state-machine nonclaim or defer coordination until solver quantities exist.

### Communications and interoperability

#### Candidate: IEC 61850 MMS adapter for selected V1 records

- **Realms:** Interoperability; control; SCADA.
- **Observed trigger:** Canonical commands/telemetry/quality/alarms/topology exist, but only HTTP/WebSocket mappings exist.
- **Why adjacent:** Stable internal semantics permit a real adapter test.
- **Learning question:** How should a narrow IEC model map values, quality and controls while preserving ownership and logical apply ticks?
- **Possible unlock:** Lab-tested MMS read/control for a selected BESS/PCC subset.
- **Prerequisite evidence:** Gate D; generic routing; approved data model and independent client plan.
- **Dependencies:** Server/client stack, SCL scope, mapping, licensing and explicit conformance nonclaims.
- **Architectural pressure:** Configuration, timestamps, control reconciliation, failures and audit.
- **Complexity:** Extra large.
- **Uncertainty:** Successful lab exchange is not conformance.
- **Pursue/defer:** Strong portfolio candidate; defer until internal routing is generic.

#### Candidate: Deterministic communication impairment adapter

- **Realms:** Interoperability; reliability; cybersecurity.
- **Observed trigger:** Ingress is deterministic but delay/loss/duplicate/corruption/stale/disconnection are not modeled.
- **Why adjacent:** Command/publication boundaries and snapshot-aware RNG are insertion points.
- **Learning question:** How can impairments affect messages without uncontrolled arrival order becoming physics?
- **Possible unlock:** Reproducible degraded-communication scenarios.
- **Prerequisite evidence:** Gate D; declared impairment and random-state policies.
- **Dependencies:** Message clock, queues, timeouts, quality and trace records.
- **Architectural pressure:** Future delivery, retry/idempotency and queue snapshots.
- **Complexity:** Large.
- **Uncertainty:** Domain truth versus infrastructure diagnostic boundary.
- **Pursue/defer:** Pursue when an adapter needs failure semantics; defer cyber-attack interpretation.

### SCADA and visualization

#### Candidate: Operational HMI alarm and event workflow

- **Realms:** SCADA; control; data.
- **Observed trigger:** Viewer is a static TT-000 single-line; alarm state, acknowledgements, topology and trace already exist.
- **Why adjacent:** Existing isolated viewer boundary can expose whether contracts support operator workflows.
- **Learning question:** What minimum indication, confirmation, alarm list and SOE workflow is operationally legible without implying production SCADA?
- **Possible unlock:** Topology-driven view, alarm acknowledgement and deterministic event inspection.
- **Prerequisite evidence:** Gate D; stable read models and command transitions.
- **Dependencies:** UI state, alarm/event query, reconnect and human-factor references.
- **Architectural pressure:** Current state/history separation, generic rendering, stale quality and resync.
- **Complexity:** Large.
- **Uncertainty:** How much realism is useful before historian/multi-asset work.
- **Pursue/defer:** Good adjacent option; pair with a small historian boundary.

### Data and historian

#### Candidate: Versioned historian and observation replay

- **Realms:** Data/historian; SCADA; validation.
- **Observed trigger:** Versioned trace/publication/store ports exist only in memory; durable queries and observation replay were deferred.
- **Why adjacent:** Actual records now reveal storage/query needs.
- **Learning question:** Which schema, ordering, retention and migration rules preserve evidence while separating observation from physics replay?
- **Possible unlock:** Durable runs, SOE/trend queries and observation replay.
- **Prerequisite evidence:** Gate D; frozen persistence semantics and representative workload.
- **Dependencies:** Store evaluation, migrations, atomic ingestion, lineage and integrity.
- **Architectural pressure:** Back-pressure isolation, append layout, indexes and API read models.
- **Complexity:** Large.
- **Uncertainty:** DuckDB/Parquet versus simpler append-only storage.
- **Pursue/defer:** Strong evidence-path candidate; precede rich historical HMI work.

### Reliability and maintenance

#### Candidate: Deterministic component failure and repair injection

- **Realms:** Reliability/maintenance; control; topology.
- **Observed trigger:** Availability is fixed except safe zero; no failure, repair, derating or maintenance state exists.
- **Why adjacent:** Replay, alarms and snapshots can support availability events after multi-asset registration.
- **Learning question:** How should failure/repair ownership affect commands, quality, topology and replay?
- **Possible unlock:** Repeatable availability scenarios.
- **Prerequisite evidence:** Gate D; generic registry and multiple resources/components.
- **Dependencies:** Failure taxonomy, repair state, availability records and scripted/probabilistic policy.
- **Architectural pressure:** Cross-realm ownership, controller fallback and RNG/snapshot completeness.
- **Complexity:** Large.
- **Uncertainty:** Defensible rates; scripted failures may be better initially.
- **Pursue/defer:** Defer until multi-asset composition exists.

### Cybersecurity

#### Candidate: Operator identity, authorization and audit boundary

- **Realms:** Cybersecurity; interoperability; SCADA.
- **Observed trigger:** API trusts caller-supplied source and authority.
- **Why adjacent:** Correlation and traces can map authenticated identity into trusted provenance.
- **Learning question:** Where should identity and permissions be enforced without contaminating physics?
- **Possible unlock:** Role-scoped commands and auditable denials/actions.
- **Prerequisite evidence:** Gate D; threat boundary, role model and identity adapter.
- **Dependencies:** Authentication, authorization, configuration and audit retention.
- **Architectural pressure:** Untrusted ingress versus canonical command, provenance, secrets and denial records.
- **Complexity:** Large.
- **Uncertainty:** Educational model must not imply IEC 62443 compliance.
- **Pursue/defer:** Defer until a real multi-user/external surface exists.

### Compliance and validation

No competing candidate is ranked here. Independent TT-000 Gate D is the mandatory
canonical prerequisite, not an optional frontier candidate. Later traceability
automation must be derived from Gate D findings rather than used to avoid review.

## Transparent provisional priority calculation

Inputs are 0–5: learning value L, adjacency A, north-star alignment N, blocker
removal B, cross-realm leverage X, backbone challenge value E, complexity C and
uncertainty U.

**Provisional priority = 2L + A + N + 2B + X + E - C - U**

These values are decision aids, not objective truth.

| Rank | Candidate | L | A | N | B | X | E | C | U | Calculation | Score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | Multi-asset PV/profiled-load composition | 5 | 5 | 5 | 5 | 5 | 5 | 4 | 3 | 2×5+5+5+2×5+5+5−4−3 | **33** |
| 2 | Electrical power-flow adapter | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 4 | 2×5+4+5+2×5+5+5−5−4 | **30** |
| 3= | Reversible fidelity lifecycle | 4 | 5 | 4 | 4 | 3 | 5 | 3 | 3 | 2×4+5+4+2×4+3+5−3−3 | **27** |
| 3= | Grid-forming island dynamics | 5 | 3 | 5 | 5 | 5 | 4 | 5 | 5 | 2×5+3+5+2×5+5+4−5−5 | **27** |
| 3= | Breaker/protection lifecycle | 5 | 4 | 5 | 4 | 4 | 4 | 4 | 4 | 2×5+4+5+2×4+4+4−4−4 | **27** |
| 3= | Operational HMI workflow | 4 | 5 | 5 | 3 | 4 | 4 | 3 | 2 | 2×4+5+5+2×3+4+4−3−2 | **27** |
| 7= | IEC 61850 MMS adapter | 5 | 3 | 5 | 3 | 5 | 5 | 5 | 4 | 2×5+3+5+2×3+5+5−5−4 | **25** |
| 7= | Historian and observation replay | 4 | 4 | 5 | 3 | 5 | 4 | 4 | 3 | 2×4+4+5+2×3+5+4−4−3 | **25** |
| 9 | Communication impairments | 4 | 4 | 4 | 3 | 4 | 4 | 3 | 3 | 2×4+4+4+2×3+4+4−3−3 | **24** |
| 10 | Identity/authorization/audit | 4 | 4 | 4 | 3 | 4 | 3 | 4 | 3 | 2×4+4+4+2×3+4+3−4−3 | **22** |
| 11 | External FMI unit | 5 | 3 | 4 | 2 | 5 | 5 | 5 | 5 | 2×5+3+4+2×2+5+5−5−5 | **21** |
| 12 | Failure and repair injection | 4 | 3 | 4 | 2 | 4 | 4 | 4 | 4 | 2×4+3+4+2×2+4+4−4−4 | **19** |

### Evidence behind each score

- **Multi-asset:** all positive inputs are 5 because it attacks repeated hard-coding,
  uses nearly every seam and directly approaches the north-star DER mix. C4/U3
  acknowledge cross-cutting contracts, routing, balance and snapshots.
- **Power flow:** L/N/B/X/E are 5 because missing electrical state is the dominant
  physics/topology blocker and solver replacement is central. A4 reflects existing
  topology/balance seams; C5/U4 reflect units, reactive power and validation.
- **Reversible fidelity:** A5/B4/E5 reflect the exact missing direction beside the
  existing handoff. L4/N4/X3 are narrower; C3/U3 reflect transient-loss policy.
- **Grid forming:** L/N/B/X are 5 because unsupported islanding is a major north-star
  gap. A3/E4 reflect the existing boundary but missing electrical state; C5/U5
  penalize scientific risk.
- **Breaker/protection:** L5/A4/N5/B4/X4/E4 follow from existing breaker/event seams.
  C4/U4 reflect absent fault quantities and proxy risk.
- **HMI:** A5/U2 reflect an existing viewer/API. L4/N5/B3/X4/E4 reward operational
  learning and contract pressure; C3 reflects bounded UI/read-model work.
- **IEC 61850:** L/N/X/E are 5 for interoperability/backbone value. A3/B3 reflect
  missing generic routing; C5/U4 reflect protocol and conformance complexity.
- **Historian:** L4/A4/N5/B3/X5/E4 follow from existing records/ports. C4/U3 reflect
  storage, migration, query and back-pressure choices.
- **Impairments:** L4/A4/N4/B3/X4/E4 follow from ingress, queues and RNG. C3/U3 reflect
  subtle domain-versus-infrastructure semantics.
- **Identity/audit:** L4/A4/N4/B3/X4/E3 reflect the exposed unauthenticated edge.
  C4/U3 reflect threat-model and secure-configuration work.
- **FMI:** L/X/E are 5, but A3/N4/B2 show it is not the nearest blocker. C5/U5 cover
  negotiation, rollback, determinism and portability.
- **Reliability:** L/N/X/E are 4, but A3/B2 show the missing multi-asset substrate.
  C4/U4 cover ownership and evidence choices.

Highest score is not automatic selection. Large solver/grid-forming scores come with
large complexity/uncertainty; a smaller reversible-fidelity node may be the better
controlled experiment.

## Strongest candidate in each relevant realm

| Realm | Strongest provisional candidate | Reason |
|---|---|---|
| Kernel/time | Reversible fidelity lifecycle | Closest controlled lifecycle/snapshot replacement test |
| Physics | Multi-asset PV/profiled-load composition | Tests extension before a much larger solver leap |
| Control | Multi-asset PV/profiled-load composition | Forces generic routing/ownership across asset types |
| Topology/protection | Breaker lifecycle/protection-driven isolation | Extends requested/actual/event seam with bounded claims |
| Interoperability | IEC 61850 MMS adapter | Strongest canonical-to-industrial mapping test |
| SCADA | Operational HMI workflow | Directly adjacent to viewer and alarm/trace records |
| Data/historian | Historian and observation replay | Direct maturation of trace/publication/store ports |
| Reliability | Failure and repair injection | Direct availability/repair learning, after multi-asset work |
| Cybersecurity | Identity/authorization/audit | Attaches at untrusted API edge |
| Compliance/validation | None ranked | Gate D is mandatory first |

## Coherent cross-realm advancement options

### Option A — Challenge the backbone first

1. Multi-asset PV/profiled-load composition.
2. Reversible fidelity lifecycle.
3. Electrical power-flow adapter.

This is the strongest sequence for answering whether V0 is a firm, versatile
backbone before adding operational infrastructure.

### Option B — Build the operational evidence path

1. Versioned historian and observation replay.
2. Operational HMI alarm/event workflow.
3. IEC 61850 MMS adapter for a narrow record set.

Historian should precede rich historical HMI features; generic routing should precede
the protocol adapter.

### Option C — Advance toward supported islanding

1. Electrical power-flow adapter.
2. Breaker/protection lifecycle.
3. Grid-forming island dynamics.

This follows the largest north-star physics gap but has the highest scientific risk.
Each item needs its own charter and validation gate.

## Candidates to defer provisionally

- Grid-forming dynamics until an electrical model/reference basis exists.
- External FMI until in-process lifecycle/runner/snapshots use a generic port.
- IEC 61850 implementation until command/asset routing is generic.
- Failure/repair until multi-asset composition makes availability coordination useful.
- Identity/authorization until a threat boundary and real multi-user/external surface exist.
- Full protection coordination/resynchronization; these are not current candidates
  without fault/electrical and synchronization evidence.

## Dependencies that could change the ranking

- Any Gate D defect in ordering, snapshots, serialization, residuals, causality or
  viewer isolation lowers every dependent candidate and makes correction first.
- A breaking V1 migration for generic assets raises multi-asset complexity; reversible
  fidelity may become the safer first experiment.
- A solver with clean mapping and an authoritative small case lowers power-flow C/U.
- A large reactive-power/per-unit redesign raises solver C/U and favors multi-asset or historian work.
- A concrete IEC 61850 lab objective and available stack raise adapter adjacency, but
  do not remove Gate D/routing prerequisites.
- If exact-platform snapshots are too brittle, portability/migration may outrank all expansion.

## Gate D findings that could invalidate or reorder this preview

| Possible finding | Effect |
|---|---|
| Ordering or fast/paced equivalence not reproduced | Block scheduler-dependent candidates; correct/revalidate |
| Snapshot inventory/replay incomplete | Defer reversible fidelity, multi-asset, FMI, historian and failures |
| Equations/signs/residuals wrong | Reassess physics maturity, transitions and solver proposals |
| V1 contracts cannot evolve cleanly | Insert approved contract-migration work before protocols/historian/multi-asset |
| Viewer/API affects canonical results | Correct async ownership before HMI/data/comms/security |
| Hard-coded identities mean demonstration code, not trunk | Increase multi-asset priority; reduce backbone-maturity claims |
| Existing ports judged intentionally sufficient | Reduce multi-asset blocker score; reversible fidelity/historian may lead |
| Locked-profile evidence not independently reproducible | TT-000 remains blocked; no candidate is canonically selectable |
| Unsupported claims/documentation gaps found | Correct claims/evidence and rescore maturity/frontier |

## Provisional conclusion

TT-000 is a substantial developer-tested vertical slice across deterministic time,
typed boundaries, two BESS fidelities, topology, alarms, replay and async observation.
It is a plausible V0 backbone, but several seams remain specialized to the one
reference system. The strongest provisional experiment is therefore to prove that a
second asset type and time-varying load can traverse the same lifecycle, routing,
balance, snapshot and publication machinery without breaking TT-000 golden behaviour.

This conclusion is disposable and conditional. TT-000 remains unvalidated, no node is
unlocked, and the canonical next action remains Gate D.
