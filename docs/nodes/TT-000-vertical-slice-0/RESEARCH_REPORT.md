# TT-000 Research Report

## Status

Research complete — Gate B evidence package

- Research date: 2026-08-26
- Node: `TT-000 — Hierarchical Co-Simulation Vertical Slice 0`
- Stage boundary: research only; this report is not a feature architecture, milestone plan, implementation approval, compliance claim, or validation result.
- Source policy: primary standards, official documentation, national-laboratory reports, and peer-reviewed work are preferred. Tool versions are current stable releases observed on the research date.

### Evidence labels

- **Cited fact / normative source** — supported by the adjacent reference.
- **Engineering inference** — a conclusion derived from cited evidence and the approved TT-000 charter.
- **Proposed project choice** — a recommendation for the feature architect to accept or reject at Gate C.
- **Unresolved** — evidence is insufficient or the decision belongs to feature architecture.

---

## 1. Executive recommendation

**Proposed project choice.** TT-000 should prove the architecture with one synchronous, deterministic, in-process simulation core using integer logical ticks, a stable total order for simultaneous work, a 1 s macro period, and ten 0.1 s child steps per macro period. Wall-clock pacing is an optional adapter around that same logical execution. The viewer and API must consume copies of published domain data and submit canonical commands through a deterministic boundary; they must never be awaited by, nor directly call, the physics step.

**Proposed project choice.** The fallback BESS should be an ideal bounded active-power/energy model. The detailed BESS should add separate charge/discharge efficiencies, a discrete first-order active-power response, a ramp cap, operating modes, and explicit power/energy limits. Both models use the same AC-side sign convention and common handoff state. Neither is a cell model, EMT inverter, RMS network model, grid-forming control, degradation model, thermal model, or safety model.

**Proposed project choice.** The two-bus topology should be represented by canonical buses, one switchable PCC branch, asset terminals, and a small deterministic breadth-first search. Connectivity identifies islands; a separate calculation computes only an algebraic active-power balance. When the PCC opens, V0 has no validated voltage/frequency-forming source, so the local island becomes `ISLANDED_UNSUPPORTED` (or equivalently de-energized/degraded), applied BESS power is driven to a safe zero target, and a correlated alarm is raised. No voltage, frequency, reactive-power, protection, or resynchronization claim is made.

**Proposed project choice.** Only fallback-to-detailed activation is required in V0. The reverse mapping is documented but deferred from the demonstration because a memoryless fallback cannot preserve the detailed model's transient trajectory without adding another transition policy.

**Proposed project choice.** Use Python 3.14, standard-library scheduling and graph traversal, Pydantic v2 for canonical boundary schemas, pytest for evidence, and a thin FastAPI/Uvicorn adapter plus a static single-line viewer. Defer NetworkX, PyBaMM, FMI integration, DuckDB, and Parquet. Preserve ports that permit those later replacements.

**Gate B verdict: READY FOR ARCHITECTURE.** The evidence is sufficient to choose an honest V0 model boundary and validation method. The unresolved items in section 19 are Gate C design choices, not missing scientific evidence. Gate B does not approve implementation.

---

## 2. Direct answers to every learning question

### A. Deterministic simulation semantics

#### A1. Scheduling model

**Cited fact.** Superdense time represents an instant as physical/logical time plus a microstep, permitting ordered changes without advancing ordinary time; deterministic discrete-event work benefits from such an explicit ordering model ([Lee, *Deterministic Concurrency*](https://ptolemy.berkeley.edu/~eal/books/DC/DeterministicConcurrency_Digital_05.pdf)). Python's heap documentation also warns that a heap is not stable and recommends a unique entry counter as a tie-breaker for equal priorities ([Python 3.14 `heapq`](https://docs.python.org/3.14/library/heapq.html#priority-queue-implementation-notes)).

**Proposed project choice.** Use a conservative single-threaded hybrid scheduler with an integer key:

`(logical_tick, phase_priority, source_order, insertion_sequence)`.

No domain callback runs concurrently. Events created while processing an instant receive a later phase or microstep; a same-or-earlier key is rejected. This is a small, inspectable scheduler rather than a general DEVS or FMI master.

#### A2. Logical time, pacing, and fast-forward

**Cited fact.** Co-simulation literature distinguishes simulated time from wall-clock time and assigns the orchestrator responsibility for advancing simulation time and exchanging data ([Gomes et al., *Co-simulation: a Survey*](https://doi.org/10.1145/3179993)).

**Proposed project choice.** The core advances only logical ticks. `fast_forward` performs no sleeping. `paced` computes a wall-clock deadline for each logical boundary and may sleep or report overrun, but never changes `dt`, skips steps, or reorders events. The canonical domain trace for a fixed canonical input log must be identical in both modes; wall-clock diagnostics are kept outside that trace.

#### A3. Simultaneous-event priority

**Proposed project choice.** At a logical boundary, apply the following total order:

1. exogenous scenario/fault conditions;
2. breaker/topology state transitions;
3. connectivity, energization, and operating-mode derivation;
4. fidelity lifecycle transitions;
5. command validation, acceptance/rejection, and acknowledgement;
6. supervisory/local controller evaluation;
7. child-model advancement to the next boundary;
8. macro aggregation and power/energy residual calculation;
9. alarm condition/state transitions;
10. telemetry/event publication and eligible snapshot capture.

The purpose is semantic, not merely computational: a command simultaneous with PCC opening is validated against the post-opening topology; telemetry never reports a pre-alarm state as though it were the completed boundary. The architect should freeze this in an ADR because `DEVELOPMENT_PROTOCOL.md` treats time/event semantics as long-lived architecture.

#### A4. State required for exact reproduction

**Cited fact.** FMI 3.0.2 requires a captured FMU state to contain all information needed to continue without additional API calls, and explicitly supports get/set and serialized state where the FMU declares the capability ([FMI 3.0.2, FMU state](https://fmi-standard.org/docs/3.0.2/#get-set-fmu-state)). Python's RNG exposes `getstate()`/`setstate()` for the same continuation purpose ([Python 3.14 `random`](https://docs.python.org/3.14/library/random.html#bookkeeping-functions)).

**Proposed project choice.** Capture logical tick/phase, scheduler counters and full pending event queue, all active/inactive model states needed for transition, controller states and timers, topology and breaker state, command deduplication/sequence state, requested/accepted/applied values, alarm and acknowledgement state, RNG algorithm/state, pending canonicalized commands, publication sequence counters, scenario/configuration hashes, schema/model/snapshot versions, and numerical-runtime metadata. Socket connections, viewer state, and wall-clock pacing state are excluded.

### B. Multi-rate coupling

#### B1. Smallest correct fixed-ratio algorithm

**Cited fact.** FMI Co-Simulation exchanges data at communication points, leaves internal advancement to the simulation unit, and makes the master responsible for time advancement, exchange, and events; FMI deliberately does not prescribe the master algorithm ([FMI 3.0.2, Co-Simulation concepts](https://fmi-standard.org/docs/3.0.2/#co-simulation)).

**Proposed project choice.** Let macro period `H = 1 s`, child period `h = 0.1 s`, and ratio `r = H/h = 10`. Use integer microticks. At each macro boundary: resolve events and commands, hold accepted macro inputs, execute exactly ten child transitions (interrupting only on a scheduled microtick event), accumulate outputs, then publish one macro result. Reject non-integral ratios and off-grid physics events in V0.

#### B2. Input holding/interpolation/interruption

**Cited fact.** FMI states that discrete inputs retain their value between communication points; continuous inputs require an explicit assumption, and discontinuous changes need event handling ([FMI 3.0.2, smoothness and discontinuity](https://fmi-standard.org/docs/3.0.2/#smoothness-continuity-and-discontinuity)).

**Proposed project choice.** Use zero-order hold for accepted setpoints, load, limits, and mode inputs. Use no interpolation in V0 because no smooth profile requires it. Scenario topology events may interrupt a macro interval only at a child tick. Live API commands apply at a macro boundary, never midway through an already executing child step. Linear interpolation is deferred for future sampled profiles and must carry an explicit interpolation policy.

#### B3. Output reduction

**Proposed project choice.** Preserve:

- end sample: SoC/energy, applied power, mode, breaker/connectivity, quality;
- time-weighted mean: applied AC power and loss power;
- integral: AC energy, battery-energy change, and losses;
- extrema: min/max applied power and SoC;
- ordered list: every discrete event, acknowledgement, and alarm transition with its tick.

Do not average modes, quality, topology, or alarms.

#### B4. Energy conservation and coupling residuals

**Cited fact.** Explicit co-simulation can introduce artificial interface energy, so energy residuals are useful diagnostics even where an exact monolithic reference is unavailable ([Moshagen, *On meeting Energy Balance Errors in Cosimulations*](https://arxiv.org/abs/1706.07273); [Rodríguez et al., energy-based monitoring](https://doi.org/10.1007/s11044-021-09819-0)).

**Proposed project choice.** At each child and macro interval calculate the BESS residual

`r_E = ΔE_stored + ∫(P_ac + P_loss) dt / 3600`,

with MW, seconds, and MWh. Also calculate coupling closure `r_H = E_macro_integral - Σ E_child_integral`. Report signed and absolute residuals; never silently force them to zero after calculation.

#### B5. Initial time steps

**Proposed project choice.** Use `H = 1 s`, `h = 0.1 s`, ratio 10, and a synthetic detailed-model lag `τ = 2 s`. This supplies 20 child samples per time constant and ten child transitions per supervisory decision while remaining easy to inspect. The lag update should use the exact zero-order-hold factor `exp(-h/τ)` when the ramp cap is inactive, so this step is selected for pedagogical visibility and coupling evidence, not because it represents a vendor bandwidth.

**Unresolved.** Gate C must retain these as scenario parameters and require a half-step sensitivity run; research cannot claim a universally correct BESS step size without a specified device model and bandwidth.

#### B6. Unrepresented phenomena

**Proposed project choice.** The steps and equations do not represent AC waveforms, sub-cycle events, switching/PWM, harmonics, electromagnetic transients, fault current, relay timing/coordination, inner current/voltage loops, PLL dynamics, DC-link dynamics, cell electrochemistry, thermal gradients, or communication latency. These are explicit nonclaims.

### C. BESS model hierarchy

#### C1. Fallback model

**Proposed project choice.** A bounded, lossless AC active-power source with state `E_stored` (MWh), immediate application of an accepted `P_set` (MW), nameplate/SoC limits, and exact rectangular energy integration. It is a deterministic architectural fallback, not a realistic battery.

#### C2. Smallest meaningful detailed model

**Cited fact.** Real BESS data/control architectures distinguish the battery/BMS, PCS, meters, and supervisory/site controller ([Sandia/EPRI storage data guidelines](https://www.sandia.gov/ess-ssl/wp-content/uploads/2021/07/SNL-EPRI-Data-Guide-SAND-V2.pdf)). Battery equivalent-circuit tools may include OCV, resistance, RC and thermal elements, showing how much physical scope lies beyond an aggregate energy model ([PyBaMM Thevenin model](https://docs.pybamm.org/en/latest/source/api/models/equivalent_circuit/thevenin.html)).

**Proposed project choice.** Add charge/discharge efficiency, `P_applied` state, first-order lag, ramp limit, availability/mode state, accepted-vs-applied separation, and energy-feasible limits. Keep the battery and PCS aggregated at the AC boundary. Do not add voltage, current, OCV, resistance, temperature, degradation, reactive power, or grid-forming dynamics.

#### C3. State, parameters, units, signs, ranges

**Proposed project choice.** State: `E_stored [MWh]`, `P_applied [MW]`, operating mode, active-model identity/version, last accepted command/setpoint, and sequence/timer state. Parameters: `E_nom [MWh]`, `soc_min/max [-]`, `P_charge_max/P_discharge_max [MW]`, `η_ch/η_dis [-]`, `τ [s]`, ramp up/down `[MW/s]`, and child period `[s]`. Enforce finite values, `0 ≤ soc_min < soc_max ≤ 1`, `0 < η ≤ 1`, positive ratings, `τ > 0`, and integer clock ratio. The proposed fixture values in section 6 are synthetic, not equipment ratings.

#### C4. Power/loss/energy signs

**Cited fact.** DOE storage-data guidance distinguishes DC battery power, PCS power, auxiliary power, transformer power, and grid power, demonstrating that the measurement boundary must be explicit ([DOE ROVI flow-system data guidance](https://www.energy.gov/sites/default/files/2023-09/Guidance%20for%20Data%20Collection%20from%20Flow%20Systems.pdf)).

**Proposed project choice.** At the BESS AC terminal, `P_ac > 0` means discharge/injection into the local bus; `P_ac < 0` means charging/import. Define `P_bat = -dE_stored/dt` positive when stored energy is depleted and `P_loss ≥ 0`; then `P_bat = P_ac + P_loss`. Section 6 gives the piecewise equations.

#### C5. Droop in V0

**Cited fact.** Grid-forming resources actively regulate voltage/frequency, and practical islanded demonstrations use droop with inner current and outer voltage controls; tuning can create stability issues ([NREL GFM roadmap](https://www.nrel.gov/docs/fy21osti/79761.pdf); [NREL multi-microgrid black-start study](https://www.nrel.gov/docs/fy23osti/83956.pdf)). IEEE 1547 addresses interconnection, reactive-power/voltage functions, abnormal response, and islanding, not a trivial scalar energy-balance substitute ([IEEE 1547-2018 scope](https://standards.ieee.org/standard/1547-2018.html)).

**Engineering inference.** Frequency-power or voltage-reactive-power droop without voltage/frequency states, network equations, source strength, current limits, or validation would create false physical meaning.

**Proposed project choice.** Defer all droop. V0 detects an unsupported island, computes an algebraic power imbalance for teaching/alarms, and makes no claim that the island is electrically sustained.

### D. Fidelity transition

#### D1. Lifecycle interface

**Proposed project choice.** Interchangeable models need lifecycle capabilities equivalent to: declare identity/version/capabilities; initialize from typed configuration and common state; validate inputs; advance over a declared logical interval; observe typed state/output; export/import common handoff state; snapshot/restore complete private state; and evaluate invariants. This is a semantic contract, not an implementation signature.

#### D2. Fallback to detailed

**Proposed project choice.** At a quiescent macro boundary map `E_stored`, `P_applied`, requested and accepted setpoints, topology-derived mode, quality, and sequence lineage. Initialize the detailed lag state to the fallback's current `P_applied`, not to the requested target. Re-evaluate detailed-model limits before the next advance. Emit one auditable transition event with before/after model versions and measured discontinuities.

#### D3. Detailed to fallback

**Proposed project choice (documented, deferred).** Collapse to the same common state: retain `E_stored`, `P_applied`, requested/accepted values, mode, and lineage; discard detailed-only lag/ramp internals explicitly. A subsequent fallback control evaluation may jump because the fallback is ideal, so reverse activation requires a stated transient policy and is not required in V0.

#### D4. Discontinuities to measure

**Proposed project choice.** Measure `ΔE_stored [MWh]`, `ΔSoC [-]`, `ΔP_applied [MW]`, requested/accepted setpoint difference, change in mode/availability, energy-residual impulse, output quality change, and any alarm transition. Identity/version changes are expected; physical-state jumps are not.

#### D5. Honest transition tolerances

**Proposed project choice.** At activation require exact equality for discrete identity/lineage and `abs(ΔE) ≤ 1e-12 MWh`, `abs(ΔSoC) ≤ 1e-12`, `abs(ΔP) ≤ 1e-12 MW` for the proposed numerical scale. These are numerical round-off guards, not physical accuracy claims. Python documents tolerance comparison as `abs(a-b) ≤ max(rel_tol*scale, abs_tol)` ([Python 3.14 `math.isclose`](https://docs.python.org/3.14/library/math.html#math.isclose)).

#### D6. Directions supported

**Proposed project choice.** Require only fallback-to-detailed activation in V0. Preserve reverse mapping in the contract/research, but defer its executable scenario and acceptance gate.

### E. Topology and islanding

#### E1. Minimum canonical topology

**Proposed project choice.** Two buses (`GRID`, `LOCAL`), one branch (`PCC`) with breaker requested/actual state, and terminals attaching the grid equivalent, aggregate load, and BESS to buses. IDs, terminal direction, branch endpoints, equipment type, state, and version are typed. Assets are not arbitrary graph dictionaries.

#### E2. Connectivity versus electrical calculation

**Proposed project choice.** A topology service returns connected components, source-containing components, and island labels. A separate balance service consumes the resulting energized/island context and asset powers. Connectivity never computes voltage/current/power flow; the balance service never decides graph reachability.

#### E3. NetworkX

**Cited fact.** NetworkX 3.6.1 computes undirected connected components by BFS in `O(n+m)` ([NetworkX `connected_components`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.connected_components.html)).

**Engineering inference.** For two buses and one branch, a deterministic adjacency map plus BFS teaches the same boundary with less dependency and serialization surface.

**Proposed project choice.** Do not depend on NetworkX in V0. Define a topology port and contract tests so a later NetworkX adapter can replace the traversal without leaking NetworkX objects.

#### E4. PCC opening effects

**Proposed project choice.** Change breaker actual state; emit topology event; increment topology version; recompute components; mark `LOCAL` disconnected from the infinite-grid source; derive `ISLANDED_UNSUPPORTED`; reject/limit incompatible active-power commands; drive BESS target to zero; calculate `P_imbalance = P_BESS - P_load` as an explicitly non-electrical proxy; update quality if signals become not meaningful; and activate a correlated island/power-imbalance alarm. Do not calculate fault current, voltage, or frequency.

### F. Contracts and control flow

#### F1. Minimum schemas

**Cited fact.** CloudEvents 1.0.2 requires `id`, `source`, `specversion`, and `type`, and treats incompatible data-schema changes as a reason to change `dataschema` ([CloudEvents 1.0.2](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md)). OPC UA distinguishes value, source timestamp, server timestamp, and a status whose severity conveys Good/Uncertain/Bad usability ([OPC UA Part 4, DataValue](https://reference.opcfoundation.org/specs/OPC-10000-4/7.11)).

**Proposed project choice.** Define canonical `Command`, `Acknowledgement`, `TelemetrySample`, `AlarmEvent/AlarmState`, `TopologyEvent`, and `Quality` records. Section 11 lists required fields. Use the standards as design precedents only; do not claim CloudEvents or OPC UA conformance.

#### F2. Correlation, identity, time, sequence, version

**Proposed project choice.** Every record carries `schema_version`, record `id`, `correlation_id` where causal linkage exists, `source_id`, target/subject identity, integer `logical_tick`, source-local monotonic `sequence`, and model version where values depend on a model. External ingress may also record wall time as audit metadata, but domain ordering uses logical fields only.

#### F3. State ownership

**Proposed project choice.** API/operator owns a request; command validator owns acceptance/rejection and the accepted setpoint; controller owns actuator target; model owns applied actuator value and physical state; telemetry is an immutable observation, not a second owner. Each field has a distinct name and timestamp.

#### F4. Command validation and alarm lifecycle

**Cited fact.** ISA-18.2 organizes alarm management as a lifecycle, while OPC UA models active/inactive and acknowledged/unacknowledged states separately ([ISA-18 series](https://www.isa.org/standards-and-publications/isa-standards/isa-18-series-of-standards); [OPC UA Part 9 Annex A](https://reference.opcfoundation.org/Core/Part9/v105/docs/A)).

**Proposed project choice.** Validate schema/version, identity, authorization placeholder, uniqueness/idempotency, source sequence, scheduling horizon, command kind, numeric finiteness/units/range, target mode/availability, and interlocks. Always return a correlated acknowledgement. Minimal alarm state is condition active/inactive × acknowledgement unacknowledged/acknowledged, with occurrence, return-to-normal, and acknowledgement events. No shelving, suppression, confirmation, flood management, or ISA/IEC conformance claim.

### G. Snapshot and replay

#### G1. Snapshot contents

**Proposed project choice.** Capture every item listed in A4, including inactive transition state if needed, scheduler tombstones/cancellations, alarm acknowledgement, command dedupe state, and pending canonical input. Omission of any mutable state is a failed snapshot design.

#### G2. Versioned strategy

**Cited fact.** JSON is a language-independent text format, but permits neither application-specific schema evolution nor snapshot completeness by itself ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)).

**Proposed project choice.** At a quiescent macro boundary, serialize a typed snapshot envelope to strict finite-number JSON with `snapshot_schema_version`, engine build, scenario/config hashes, model versions, and checksum. Write/read through a snapshot port. Reject unknown major versions; allow explicit, tested migrations only. JSON is selected for inspectability, not long-term universal portability.

#### G3. Identical and alternative continuation tests

**Proposed project choice.** Identical continuation: snapshot at tick T, run input suffix S, restore, replay S, and require byte-identical canonical events plus exact final serialized state. Alternative continuation: restore the same snapshot, use suffix A and B, require a common prefix through T, deterministic repeatability within each suffix, and a documented causal divergence after the first different command.

#### G4. Portability limits

**Engineering inference.** Exact floating results can depend on runtime, platform math libraries, dependency versions, and changed algorithms even when JSON loads successfully.

**Proposed project choice.** Guarantee replay initially only for the same declared engine/model/schema versions and supported platform profile. Across versions, require a migrator plus regression evidence or reject with a clear incompatibility error. Never deserialize arbitrary executable objects/pickle as a portable snapshot format.

### H. API, viewer, and persistence boundary

#### H1. Smallest API/viewer

**Cited fact.** FastAPI is built on typed Python/Pydantic and OpenAPI; Uvicorn is an ASGI server supporting HTTP and WebSockets ([FastAPI features](https://fastapi.tiangolo.com/features/); [Uvicorn](https://uvicorn.dev/)).

**Proposed project choice.** Supply read-only current state/topology, command submission with acknowledgement, snapshot/restore actions gated to valid boundaries, and a telemetry/event stream. A static single-line page shows grid, PCC, bus, load, BESS, active model, SoC/power/mode, and alarms. The adapter receives immutable publications through a bounded fan-out buffer. Slow clients drop/coalesce telemetry or disconnect; they never back-pressure the core. Discrete events/alarms use a separately lossless test sink inside the core evidence path.

#### H2. Wall-clock command ingress

**Engineering inference.** Arbitrary live interaction is an external input; two runs receiving different inputs or cut-off timing cannot be expected to match.

**Proposed project choice.** The API validates and canonicalizes a command, assigns/validates an explicit logical apply tick, and hands it to a thread-safe ingress port. The core drains ingress only at a defined macro boundary. Commands without an allowed apply tick are rejected or scheduled to a published future boundary under one frozen policy. Replay uses the resulting canonical command log. At the same apply tick, order by source priority, source sequence, then command ID—not network arrival order.

#### H3. DuckDB/Parquet

**Cited fact.** DuckDB targets in-process analytical/OLAP workloads ([DuckDB design](https://duckdb.org/why_duckdb)); Parquet is a column-oriented bulk storage format optimized for efficient storage/retrieval ([Apache Parquet overview](https://parquet.apache.org/docs/overview/)).

**Engineering inference.** TT-000 needs deterministic replay evidence and a small trace, not analytical query performance or a historian.

**Proposed project choice.** Defer both. Use in-memory canonical traces and optional strict JSON evidence files behind a recorder port. A later historian node may evaluate DuckDB/Parquet with schema-evolution and query requirements.

#### H4. Replaceable ports

**Proposed project choice.** Define inward-facing ports for command ingress, publication sink, snapshot store, topology service, clock/pacer, and optional trace recorder. FastAPI/Uvicorn, static visualization, filesystem, and future database/protocol implementations are adapters. Domain packages never import web, database, graph-library, or protocol types.

### I. Open-source tools and validation

#### I1. Smallest justified stack

**Proposed project choice.** Python standard library + Pydantic + pytest for the core/contracts/evidence; FastAPI + Uvicorn only in the asynchronous adapter/viewer. Use no numerical array library unless measurements show a need. Section 14 records current versions and boundaries.

#### I2. Current versions

**Cited fact.** On 2026-08-26 the observed stable releases are Python 3.14.7 documentation, Pydantic 2.13.4, FastAPI 0.141.1, Uvicorn 0.52.4, pytest 9.1.1, and NetworkX 3.6.1 ([Python 3.14.7 docs](https://docs.python.org/3.14/); [Pydantic PyPI](https://pypi.org/project/pydantic/); [FastAPI PyPI](https://pypi.org/project/fastapi/); [Uvicorn PyPI](https://pypi.org/project/uvicorn/); [pytest PyPI](https://pypi.org/project/pytest/); [NetworkX PyPI](https://pypi.org/project/networkx/)). Pin exact versions in implementation evidence; recheck at Gate C rather than treating this report as a permanent lockfile.

#### I3. Validation references

**Proposed project choice.** Use closed-form constant-power energy changes, first-order step response, graph-component truth tables, explicit event-order goldens, conservation residuals, transition invariants, and snapshot/replay identity. Section 15 supplies numbers and tolerances. External tools are not needed to validate these deliberately simple equations.

#### I4. Tolerances

**Proposed project choice.** Use exact equality for discrete states, ordering, IDs, and canonical replay bytes; tight scale-aware floating tolerances for analytically exact equations; explicit residual thresholds for energy; and a mandatory half-step sensitivity comparison. These tolerances validate the implemented simplified model, not real equipment.

#### I5. Risks

**Engineering inference.** Main risks are hidden scheduler state, unstable ties, nondeterministic async intake, incomplete snapshots, floating/version drift, schema/model version confusion, telemetry back-pressure, dependency leakage, and mistaking an open-source model's availability for evidence that it is valid for V0. Permissive licenses reduce integration friction but do not establish interoperability, determinism, correctness, or standards compliance.

---

## 3. Concepts and glossary

| Term | Meaning in TT-000 |
|---|---|
| Logical time | Integer simulation tick that determines domain evolution. |
| Wall-clock time | Real execution time used only by pacing/audit adapters. |
| Superdense ordering | Additional phase/microstep order for multiple changes at one logical time. |
| Macro period `H` | Supervisory communication/control interval, proposed as 1 s. |
| Child period `h` | BESS local-model interval, proposed as 0.1 s. |
| Communication boundary | Tick at which held inputs may change and reduced outputs are exchanged. |
| ZOH | Zero-order hold: an input remains constant over an interval. |
| Fallback model | Minimal ideal bounded power/energy implementation. |
| Detailed model | Aggregate reduced-order model adding efficiency and response dynamics. |
| Common handoff state | Small technology-independent state used for a fidelity transition. |
| PCC | Point of common coupling; represented by one switchable branch. |
| Island | Connected component no longer connected to the infinite-grid source. |
| Energized | Topological/source classification only in V0; not a solved voltage. |
| Requested setpoint | Operator/supervisor intent before validation. |
| Accepted setpoint | Validator/controller-owned feasible target. |
| Applied power | Model-owned value actually used in energy integration. |
| Quality | Usability metadata (`GOOD`, `UNCERTAIN`, `BAD`) plus reason. |
| Snapshot | Versioned complete mutable domain state captured at a quiescent boundary. |
| Canonical trace | Ordered, versioned domain records excluding wall-clock/render metadata. |

---

## 4. Real-world architecture and behaviour versus V0

**Cited fact.** A real BESS comprises more than stored energy: battery racks/cells and BMS, bidirectional PCS/inverter and often transformer/switchgear, plant or site controller/EMS, meters, thermal and safety systems. DOE describes PCS as conversion, conditioning, control, and protection equipment, while Sandia separates BMS, PCS, EMS, and site functions ([DOE BESS report](https://www.energy.gov/sites/default/files/2025-01/Battery-Energy-Storage-Systems-Report.pdf); [Sandia storage overview](https://www.sandia.gov/app/uploads/sites/273/2024/06/1_Passell_Howard_SNL_ICC_Session1_11-16-2021.pdf)).

| Real-system concern | Honest V0 representation | Explicit omission/nonclaim |
|---|---|---|
| Grid source and network | Infinite energized source, two buses, PCC connectivity | No impedance, voltage, current, phases, power flow, short circuit |
| Breaker | Requested/actual boolean state and ordered event | No mechanism, arc, operation time distribution, protection rating |
| Load | Constant aggregate active power | No voltage/frequency dependence, motor dynamics, profile uncertainty |
| Battery/BMS | Usable energy bounds and availability mode | No cells, OCV, current, temperature, SoH, balancing, safety |
| PCS/inverter | AC active-power target, lag, ramp, limits, efficiency | No switching, PLL, current loop, reactive power, DC link, EMT |
| EMS/site controller | Requested/accepted setpoint and mode validation | No optimization, forecast, market, dispatch stack |
| Island operation | Connectivity classification and unsupported-island alarm | No grid-forming voltage/frequency, droop, black start, resynchronization |
| SCADA/API | Typed commands, acknowledgements, telemetry, alarms | No industrial protocol, redundancy, access-control certification |
| Historian | In-memory canonical evidence trace | No historian performance, retention, SQL/columnar analytics |

**Engineering inference.** This boundary is operationally meaningful because it exposes ownership, sequencing, energy accounting, topology change, alarms, replay, and replaceability—the TT-000 learning goals—without confusing those lessons with unvalidated electrical fidelity.

---

## 5. V0 model candidates

### 5.1 Infinite grid

**Proposed project choice.** A boundary object with identity, `available=true`, and `energizes_component=true` while connected. It has no continuous state and does not solve or publish voltage/frequency beyond an optional nominal label clearly marked as configuration.

### 5.2 Aggregate load

**Proposed project choice.** Constant `P_load ≥ 0 MW` consumption on the local bus, ZOH over a macro interval. Optional scenario events may change it only on a scheduled child tick. No load equation depends on voltage or frequency.

### 5.3 Fallback BESS

**Proposed project choice.** State `(E_stored, P_applied, mode)`. Accepted power is immediately clipped by nameplate and energy-feasible limits. Efficiency is exactly one and `P_applied` is constant over a child step.

### 5.4 Detailed BESS

**Proposed project choice.** Same common state and boundary, plus separate efficiencies and a discrete actuator response:

- first-order ZOH lag when unconstrained;
- per-step ramp cap;
- energy- and nameplate-feasible clipping;
- modes `OFF`, `AVAILABLE_GRID_CONNECTED`, `ISLANDED_UNSUPPORTED`, `LIMITED`, `TRIPPED` (exact enum is Gate C work);
- typed limit/alarm reasons.

### 5.5 Island behaviour candidates

| Candidate | Assessment |
|---|---|
| Keep dispatching active power with no voltage/frequency state | Reject: implies an energized AC island without a forming model. |
| Add scalar frequency droop | Defer: unsupported by network/inverter states and validation. |
| Immediately classify unsupported and target zero power | Recommend: honest, deterministic, sufficient for topology/alarm learning. |
| Trip instantaneously on PCC opening | Acceptable alternative, but hides the distinction between island detection and subsequent control action. |

---

## 6. Equations, state variables, units, signs, and fixture values

### 6.1 Common definitions

| Symbol | Meaning | Unit/sign |
|---|---|---|
| `E` | stored usable energy state | MWh |
| `E_nom` | nominal energy base | MWh |
| `SoC = E/E_nom` | normalized stored energy | 0…1 |
| `P_req` | requested AC active power | MW; + discharge/injection |
| `P_set` | accepted AC target | MW; same sign |
| `P_ac` | applied AC terminal power | MW; + discharge/injection |
| `P_bat = -dE/dt` | power leaving stored-energy state | MW; + depletion |
| `P_loss` | conversion loss | MW; non-negative |
| `η_ch`, `η_dis` | one-way efficiencies | dimensionless, `(0,1]` |
| `τ` | response time constant | s |
| `R_up`, `R_down` | ramp limits | MW/s |

### 6.2 Energy and loss equations

For `P_ac ≥ 0` (discharge):

`P_bat = P_ac / η_dis`

`P_loss = P_ac(1/η_dis - 1)`

For `P_ac < 0` (charge):

`P_bat = η_ch P_ac`

`P_loss = (-P_ac)(1 - η_ch)`

Thus in both directions:

`P_bat = P_ac + P_loss`

and for a constant child-step mean power:

`E_(k+1) = E_k - (h/3600) P_bat,mean`.

**Proposed project choice.** Clamp through an energy-feasible AC range before applying the step:

`P_dis,E = (E_k - E_min) 3600 η_dis / h`

`P_ch,E = (E_max - E_k) 3600 / (η_ch h)`

`P_ac ∈ [-min(P_charge_max, P_ch,E), +min(P_discharge_max, P_dis,E)]`.

This prevents post-update clipping from silently destroying energy. At exact bounds, only movement back into the allowed region is accepted.

### 6.3 Detailed active-power response

For target `P_target` held over child interval `h`, first compute the unconstrained ZOH lag endpoint:

`P_lag = P_target + (P_k - P_target) exp(-h/τ)`.

Then apply a discrete ramp cap and feasibility limits:

`ΔP = clip(P_lag - P_k, -R_down h, +R_up h)`

`P_(k+1) = feasible_clip(P_k + ΔP)`.

**Proposed project choice.** Treat this as the definition of a discrete reduced-order actuator, not as an exact solution of a continuously rate-limited inverter. Use the trapezoidal mean `(P_k + P_(k+1))/2` for the energy step; compare against half-step execution to quantify its discretization effect. When no ramp/feasibility cap is active, the endpoint must match the analytic exponential.

### 6.4 Bus balance proxy

Grid-connected:

`P_grid_import = P_load - P_ac`.

Unsupported island:

`P_imbalance = P_ac - P_load`.

**Proposed project choice.** `P_imbalance` is an algebraic accounting signal only. It is not converted to `df/dt`, frequency, voltage, current, or load shedding in V0.

### 6.5 Synthetic reference fixture

| Parameter | Proposed value | Status/basis |
|---|---:|---|
| `E_nom` | 2 MWh | Synthetic educational fixture |
| `SoC_0` | 0.50 | Synthetic fixture |
| `SoC_min`, `SoC_max` | 0.10, 0.90 | Operational test bounds, not chemistry limits |
| `P_charge_max`, `P_discharge_max` | 1 MW, 1 MW | Synthetic 0.5C-like energy/power ratio; no vendor claim |
| `η_ch`, `η_dis` detailed | 0.95, 0.95 | Synthetic; gives 90.25% modeled round trip |
| `τ` | 2 s | Chosen to be visible at 0.1 s child steps |
| `R_up`, `R_down` | 0.5 MW/s | Synthetic ramp fixture |
| `P_load` | 0.6 MW | Synthetic fixture |
| `H`, `h` | 1 s, 0.1 s | Architectural coupling experiment |

**Cited fact.** Published aggregate Li-ion round-trip values vary with system and cycling conditions; an Argonne report lists a reference-system round-trip value of 0.86 and warns that capacity/efficiency depend on conditions ([ANL-21/31](https://publications.anl.gov/anlpubs/2021/09/170551.pdf)).

**Engineering inference.** The fixture's 90.25% is plausible enough for energy-accounting exercises but is not validated against a product. The report therefore treats it only as a transparent parameterized test case.

### 6.6 Validity boundary

The equations are valid only as an aggregate active-power/usable-energy bookkeeping and response model over the configured range. They do not predict terminal voltage, current, cell SoC, temperature, aging, availability probability, overload duration, converter fault response, efficiency maps, auxiliary consumption, reactive power, grid strength, voltage/frequency stability, or any certification quantity.

---

## 7. Time, scheduling, and event semantics

### 7.1 Time representation

**Proposed project choice.** Store time as an integer count of the smallest admitted tick (`0.1 s` initially), never as a cumulative binary float. Duration conversions occur at model boundaries. Event records include both tick and declared time-base version.

### 7.2 Queue and determinism

The queue key is `(tick, phase, source_order, insertion_sequence)`. `insertion_sequence` is monotonic and snapshotted. Event payloads are immutable typed values. Cancellation marks an entry and snapshots the tombstone or rebuilds a canonical queue at a permitted boundary. Iteration over sets/maps never determines domain order; identities are explicitly sorted.

### 7.3 Boundary algorithm

1. Pop all work for the current key in total order.
2. Reject attempts to schedule into an already completed phase.
3. Quiesce the instant: process newly emitted same-tick later-phase work until none remains.
4. If advancement is enabled, step to the next scheduled child tick.
5. Aggregate only at a completed macro boundary.
6. Snapshot only after quiescence and before the next advance.

### 7.4 Event interruption

**Cited fact.** FMI 3.0.2 permits early return when an internal event changes outputs discontinuously or another part requires an earlier communication point ([FMI 3.0.2, early return](https://fmi-standard.org/docs/3.0.2/#early-return)).

**Proposed project choice.** V0 borrows the principle, not FMI: scheduled scenario events can end a macro subinterval at a child tick, apply event phases, and continue the remaining child ticks. Arbitrary sub-child event location and root finding are out of scope.

### 7.5 Pacing

The pacer maps a logical origin to a monotonic-clock origin. It may sleep until a deadline; if late, it records overrun and continues without changing logical semantics. Pausing freezes advancement at a valid boundary. Viewer connect/disconnect and render frequency cannot call advance or alter the pacer.

---

## 8. Multi-rate coupling

### 8.1 Recommended Jacobi-like one-way interval coupling

There is one supervisory-to-asset setpoint path and an asset-to-supervisor reduction path; no algebraic loop is required. Macro inputs are resolved once, then held while the child advances. The supervisor sees reductions only at the next macro boundary. This intentional one-macro latency must be documented.

### 8.2 Aggregation formulas

For child intervals `j = 0…r-1`, each duration `h_j` and child mean `P̄_j`:

`E_ac,macro = Σ(P̄_ac,j h_j / 3600)`

`P̄_ac,macro = (1/H) Σ(P̄_ac,j h_j)`

`P_min/max = min/max of all interval endpoints and event-side values`

`ΔE_macro = E_end - E_start`

`r_H = E_ac,macro - P̄_ac,macro H/3600`.

### 8.3 Event handling inside a macro period

If the PCC opens at child tick `j`, close the preceding interval, process topology/mode/command phases at that tick, update the held feasible target, and continue. The macro event list retains the exact tick. A simple end-of-macro sample is insufficient evidence because it can hide the transition.

### 8.4 Coupling acceptance

Require exactly ten child completions in an uninterrupted macro interval; when interrupted, require child-duration segments to sum exactly to `H` in integer ticks. Validate endpoint state, integral, mean, extrema, events, and residual separately.

---

## 9. Fidelity-transition contract and mapping

### 9.1 Common handoff state

| Field | Reason it is common |
|---|---|
| `asset_id` | Stable identity across implementations |
| `from_model_id/version`, `to_model_id/version` | Audit and compatibility |
| `logical_tick` | Transition boundary |
| `E_stored_MWh`, `E_nom_MWh`, `SoC` | Conserved physical/accounting state |
| `P_requested_MW` | Control intent lineage |
| `P_accepted_MW` | Validation/controller state |
| `P_applied_MW` | Output continuity and detailed lag initialization |
| `operating_mode`, `availability` | Behavioural continuity |
| `topology_version`, `component_id` | Context used to derive mode |
| `quality` | Usability through transition |
| `last_command_id`, `source_sequences` | Idempotency and causality |

### 9.2 Activation transaction

**Proposed project choice.** Treat transition as an atomic domain transaction at a quiescent macro boundary:

1. export and validate common state from fallback;
2. construct detailed private state without mutating the active model;
3. compute a preview observation;
4. compare energy, SoC, applied power, mode, quality, and limits;
5. reject and keep fallback if invariants fail;
6. otherwise switch the active registry pointer and emit one transition event;
7. include the event and both model versions in the next publication/snapshot.

### 9.3 Activation edge cases

- If the mapped power is outside detailed nameplate limits, reject activation rather than silently clip at the boundary.
- If energy is exactly at a bound, activation is allowed only if the applied power is zero or moves inward.
- If the topology-derived mode is unsupported island, initialize the detailed model with the current applied power for continuity but target zero; subsequent response follows the declared transition policy.
- If schema/model versions are incompatible, require an explicit mapper; do not infer by matching field names.
- A failed transition emits a correlated failure event/alarm without changing the active implementation.

### 9.4 Reverse transition

The reverse common-state export is well-defined, but detailed-only transient state is lost. To implement detailed-to-fallback later, select one of: immediate ideal response on the next control phase; a one-boundary hold; or a stateful fallback ramp. That is a consequential behaviour choice and should not be smuggled into V0 as a convenience.

---

## 10. Topology and islanding

### 10.1 Canonical data

`Bus`: identity and optional nominal labels. `Branch`: identity, endpoints, equipment type, requested/actual state, and state-change sequence. `Terminal`: asset-to-bus attachment. `TopologySnapshot`: schema version, topology version, tick, sorted buses/branches/terminals, connected-component IDs, source flags, and quality.

### 10.2 Deterministic connectivity

Build adjacency from branches whose actual state is closed. Traverse buses in sorted canonical ID order and neighbours in sorted order. Assign component identity deterministically (for example, minimum bus ID plus topology version). A component is grid-connected if it contains the `GRID` source bus; otherwise it is an island. This calculation is exact for the declared boolean graph and says nothing about electrical feasibility.

### 10.3 Breaker state and events

Keep requested and actual breaker state separate even if V0 applies them at the same logical tick. This preserves the future seam for travel time, interlocks, failure-to-open/close, and protection. A topology event includes old/new requested and actual state, cause, correlation ID, tick, sequence, and resulting topology version.

### 10.4 Island state machine

Recommended minimal states:

- `GRID_CONNECTED`: local bus is in the source component.
- `ISLANDED_UNSUPPORTED`: local bus is disconnected and no approved forming model exists.
- `DEENERGIZED` (optional separate presentation state): applied active-power target is zero and measurements requiring an energized AC reference are bad/uncertain.

Reconnection/resynchronization is outside V0. Closing the PCC in the scripted scenario may restore the connectivity label only if the feature architect explicitly defines the state preconditions; it must not claim synchronization.

### 10.5 Why no general solver

There is only one algebraic active-power balance and no voltage-dependent element. Introducing a power-flow package would add buses/units/results whose meaning V0 cannot validate. The topology and balance ports should nevertheless make a later solver adapter possible without changing canonical asset identities.

---

## 11. Commands, acknowledgements, telemetry, alarms, topology events, and quality

### 11.1 Common envelope fields

| Field | Requirement |
|---|---|
| `schema_version` | Required semantic schema version |
| `id` | Unique record identity within source |
| `source_id` | Stable producer identity |
| `subject_id` / `target_id` | Stable domain identity |
| `logical_tick` | Domain occurrence/effective tick |
| `sequence` | Monotonic per-source sequence |
| `correlation_id` | Required where caused by a command/event |
| `causation_id` | Immediate causal parent where useful |
| `model_id/version` | Required for model-dependent state/output |
| `topology_version` | Required for topology-dependent interpretation |
| `wall_time_utc` | Optional ingress/audit metadata; never domain ordering |

**Engineering inference.** CloudEvents is a useful envelope precedent, but adopting its wire format now would couple the in-process domain model to an external event specification without an interoperability goal. Preserve a mapping adapter instead.

### 11.2 Command

Minimum payload: command kind, target, requested value with explicit unit, requested logical apply tick, expected target/topology/model version if optimistic concurrency is used, source sequence, expiry tick, and optional reason/operator text. V0 command kinds should be closed enums: BESS active-power request, PCC open, model activation, alarm acknowledge, snapshot, restore, and run-control actions if approved.

### 11.3 Acknowledgement

Required: acknowledgement ID, command ID/correlation, accepted/rejected status, reason code and human-readable detail, accepted/effective tick, accepted value/unit (which may differ from request only under a documented clipping policy), target version, and source sequence. Separate `ACCEPTED` from `EXECUTED/APPLIED`; if V0 implements only one acknowledgement plus telemetry, say so explicitly and do not imply execution merely from acceptance.

### 11.4 Telemetry

Required: signal identity, asset/source, typed value, unit, logical tick, sequence, quality, model/topology version, and aggregation kind (`END`, `MEAN`, `INTEGRAL`, `MIN`, `MAX`). Never mix instantaneous MW with interval MWh or omit the aggregation window.

### 11.5 Quality

Recommended fields: `validity ∈ {GOOD, UNCERTAIN, BAD}`, reason code, detail, origin/source, since tick, and whether the last value is retained. OPC UA's Good/Uncertain/Bad structure is a precedent, not a compatibility claim ([OPC UA Part 8 status codes](https://reference.opcfoundation.org/specs/OPC-10000-8/7.3)).

Examples:

- `GOOD/NORMAL`: computed under supported V0 assumptions.
- `UNCERTAIN/SIMPLIFIED_ISLAND_PROXY`: algebraic imbalance retained but no electrical state exists.
- `BAD/DEENERGIZED_OR_UNSUPPORTED`: value such as bus voltage/frequency is unavailable; do not invent a numeric zero.
- `BAD/STALE_OR_MODEL_ERROR`: model did not advance successfully.

### 11.6 Alarm

Minimum definition fields: condition key, source/asset, category, fixed severity/priority, threshold or boolean condition, on/off delay (zero is allowed), deadband if numeric, message, and operator guidance text. Runtime state includes active flag, acknowledged flag, occurrence ID, active-since tick, return tick, acknowledge tick/source, last transition sequence, and correlation.

Recommended transitions:

1. inactive/acknowledged baseline;
2. active/unacknowledged on condition occurrence;
3. active/acknowledged on operator acknowledgement;
4. inactive/unacknowledged if condition clears before acknowledgement, preserving the occurrence for acknowledgement;
5. inactive/acknowledged/closed after both clear and acknowledgement.

**Proposed project choice.** For V0, one `UNSUPPORTED_ISLAND_POWER_IMBALANCE` alarm is sufficient. Its condition is PCC-open island plus absolute algebraic imbalance above the declared threshold. It is an educational lifecycle demonstration, not a rationalized production alarm.

### 11.7 Topology event

Required: branch/breaker identity, requested/actual old/new state, trigger kind, command/cause correlation, tick, sequence, topology version before/after, affected component IDs, and derived grid-connected/island status.

### 11.8 Command conflict policy

At a common tick, safety/scenario topology state dominates active-power dispatch validation. Duplicate `(source_id, command_id)` returns the recorded acknowledgement without re-execution. A lower or repeated source sequence is rejected unless it is the exact duplicate. Conflicting valid commands from different sources require an architect-approved authority order; lexical IDs alone should not encode operator authority.

---

## 12. Snapshot and replay

### 12.1 Snapshot envelope

Recommended top-level data:

- snapshot ID, schema version, creation logical tick/phase;
- engine name/version/build and supported compatibility range;
- scenario ID/version/hash and complete resolved parameters;
- canonical contract versions;
- active model IDs/versions/capabilities;
- scheduler state and event queue;
- model/controller/topology/command/alarm/RNG/publication state;
- canonical pending ingress already accepted by the core;
- checksum over a canonical serialization;
- explicit list of excluded infrastructure state.

### 12.2 Capture boundary

Capture only when the current tick is quiescent: all phases for the boundary are complete, no model step is in progress, publications for the boundary have stable sequence numbers, and the next interval has not started. The core must not wait for viewers to consume those publications.

### 12.3 Canonical serialization

Use sorted object keys and stable enum/string encodings; reject NaN and infinities because they are not interoperable JSON numbers. Serialize the priority queue in canonical key order, not backing-heap array order. Include pending event insertion sequences. Hash bytes after canonicalization. The snapshot store handles atomic file replacement if filesystem persistence is approved; the domain produces/consumes bytes through a port.

### 12.4 Replay scope

Two notions must remain separate:

- **Logical replay:** same canonical inputs produce the same ordered domain records and state under the declared compatible runtime.
- **Historical observation replay:** resend previously recorded telemetry/events without advancing physics.

TT-000 requires logical replay. It may use the canonical trace for observation, but must not confuse replaying a log with restoring a simulator.

### 12.5 Alternative continuation

The snapshot remains immutable. Branch A and B each restore into a fresh runtime, receive explicitly versioned command suffixes, and generate separate trace/run IDs linked to the parent snapshot. Alternative continuation is not a Git branch and does not mutate the saved baseline.

---

## 13. API, viewer, and persistence boundaries

### 13.1 Minimal operations

| Operation | Direction | Deterministic rule |
|---|---|---|
| Read current published state/topology | core → API | Reads immutable latest publication only |
| Stream telemetry/events | core → viewer | Subscription cannot block core; carries logical sequence |
| Submit command | API → core | Typed validation, explicit future apply tick, canonical ingress |
| Acknowledge alarm | API → core | Canonical command with occurrence ID |
| Request snapshot/restore | API → core | Schedules action at eligible boundary; never executes inline |
| Connect/disconnect viewer | infrastructure only | No domain event unless explicitly audited outside physics |

### 13.2 Back-pressure and loss policy

Continuous telemetry may be coalesced to the newest state per slow viewer and a dropped-count diagnostic exposed. Alarm/topology/acknowledgement evidence must be retained by the deterministic in-core trace sink regardless of viewer delivery. A WebSocket is a convenience transport, not the evidence store.

### 13.3 Command cut-off

The API publishes the next admissible apply tick and minimum lead. An accepted live command cannot target the current or past tick. In fast-forward, the core may outrun a human; interactive operation therefore uses pacing or pause, while scripted fast-forward injects a predeclared logical command schedule. This is an honest limitation, not a synchronization bug.

### 13.4 Persistence recommendation

Keep snapshots and canonical traces as optional versioned JSON files for V0 demonstrations/tests. Do not make filesystem persistence necessary for core correctness. Defer historian queries, retention, compaction, and columnar export. If JSON evidence is committed, record engine/version hashes and avoid timestamps that make golden files change needlessly.

---

## 14. Open-source tool assessment, boundaries, and replacement analysis

### 14.1 Recommended/deferred matrix

| Tool (stable observed 2026-08-26) | V0 decision | Boundary and reason | Replacement/risk |
|---|---|---|---|
| CPython 3.14.7 | Recommend runtime | Integer/float semantics, stdlib heap/RNG/JSON/async edges | Pin patch for evidence; cross-runtime floating replay not guaranteed; PSF license |
| Pydantic 2.13.4 | Recommend at canonical serialization/API boundaries | Validation and JSON Schema; domain semantics remain plain typed records/ports | Keep Pydantic models from leaking into physics if replacement is desired; MIT license |
| pytest 9.1.1 | Recommend | Unit, contract, invariant, integration, golden, replay tests | Test framework only; MIT license |
| FastAPI 0.141.1 | Recommend adapter only | Small typed HTTP/WebSocket API and OpenAPI | Domain must not import it; MIT license |
| Uvicorn 0.52.4 | Recommend runtime adapter only | ASGI serving | Worker/thread/process settings must not multiply simulation cores; BSD-3-Clause license |
| NetworkX 3.6.1 | Defer | Two-node connectivity does not justify dependency | Later adapter behind topology port; BSD-3-Clause license |
| PyBaMM 26.8.0.0 | Defer | Valuable battery-model library, but its Thevenin/electrochemical scope does not validate TT-000's aggregate AC model | Future battery-physics adapter; CalVer may contain breaking changes; BSD license ([PyBaMM release policy](https://pypi.org/project/pybamm/)) |
| FMI 3.0.2 tooling | Defer integration; use as interface evidence | Standard model exchange/co-simulation boundary is larger than V0 | Future FMI adapter/master requires capability negotiation and its own validation; FMI specification is available under its published terms |
| DuckDB 1.5.5 | Defer | OLAP/historian need absent | Later recorder/query adapter; MIT license; release cadence/versioned storage need evaluation ([DuckDB releases](https://duckdb.org/release_calendar.html)) |
| Apache Parquet format | Defer | Columnar bulk storage need absent | Later export adapter; cross-implementation feature support must be tested; Apache-2.0 ecosystem |

### 14.2 Why Pydantic is justified but not domain truth

Pydantic validates syntax, types, ranges, and serialization shape. It does not prove unit correctness, scheduler semantics, physical validity, or interoperability. Canonical contracts require semantic tests in addition to generated JSON Schema. Pydantic 2.13.4 is the stable release; 2.14.0 beta observed on PyPI is not recommended for the initial evidence baseline ([Pydantic releases](https://pypi.org/project/pydantic/)).

### 14.3 Why no NumPy/SciPy initially

The state is scalar and the recommended lag has a closed-form factor. Standard-library `math.exp`, accurate summation where needed, and transparent loops are enough. Adding array/solver dependencies before a vector/network/electrochemical requirement would obscure rather than teach the scheduling and coupling logic.

### 14.4 FastAPI/Uvicorn process risk

Do not use multiple ASGI workers around an in-memory simulator: each worker could own a divergent simulation. V0 should have exactly one simulation owner and one adapter process/runtime, or an explicit external domain service boundary (the latter is out of scope). Auto-reload must not be used as normal execution evidence.

### 14.5 Licensing and maintenance

The recommended packages use permissive open-source licenses, but Gate C should record exact package/license files and transitive dependencies in the lock/evidence. Version pins aid reproducibility; they do not remove security/maintenance obligations. No selected library establishes IEEE, IEC, ISA, OPC UA, FMI, or grid-code compliance.

---

## 15. Validation cases, reference values, and tolerances

### 15.1 Tolerance principles

1. Exact equality for discrete state, event order, IDs, sequences, versions, and canonical serialized replay.
2. Both relative and absolute tolerance for floating comparisons; near zero requires a positive absolute tolerance ([Python `math.isclose`](https://docs.python.org/3.14/library/math.html#math.isclose)).
3. Derive expected values independently from the transition under test where practical.
4. Separate numerical conformance to the simplified equation from validation against reality; TT-000 provides the former only.
5. Perform a child half-step sensitivity run even where the chosen analytic update is exact, because ramp/limit/event coupling is discrete.

### 15.2 Validation matrix

| Case | Independent reference/method | Proposed acceptance |
|---|---|---|
| Event tie order | Hand-authored expected list for all phases and equal-priority insertion ties | Exact ordered equality |
| Fast-forward vs paced | Same scenario/command log; remove wall diagnostics | Byte-identical canonical trace and final snapshot |
| Viewer independence | 0, 1, and multiple connect/disconnect/render rates | Byte-identical canonical domain trace |
| Macro/child count | `H=1`, `h=0.1`, ratio 10 | Exact tick/count equality; durations sum exactly in ticks |
| Fallback constant discharge | `E1 = E0 - P h/3600` | `rel≤1e-12`, `abs≤1e-12 MWh` |
| Detailed discharge efficiency | 1 MW for 1 h, unconstrained: `ΔE=-1/0.95=-1.0526315789473684 MWh`, loss `0.0526315789473684 MWh` | `rel≤1e-12`, `abs≤1e-12 MWh` |
| Detailed charge efficiency | `P_ac=-1 MW` for 1 h: `ΔE=+0.95 MWh`, loss `0.05 MWh` | Same |
| First-order lag | `P0=0`, target 1 MW, `τ=2 s`: `P(2)=0.6321205588285577`, `P(4)=0.8646647167633873` when ramp inactive | `rel≤1e-12`, `abs≤1e-12 MW` |
| Ramp cap | Synthetic sequence with target jump and `R=0.5 MW/s`; each endpoint delta bounded by `Rh` | Exact inequality plus `1e-12 MW` guard |
| Energy bounds | Commands into/out of both bounds | Never exceed bound by more than `1e-12 MWh`; accepted/applied reason exact |
| Energy residual | Recompute from independently accumulated AC energy, loss, and stored delta | `abs(r_E)≤1e-10 MWh` per macro and `≤1e-9 MWh` over the short reference run |
| Coupling closure | Integral versus time-weighted mean and child sum | `abs(r_H)≤1e-12 MWh` |
| Half-step sensitivity | Repeat at `h=0.05 s` with identical event times representable on both grids | Exact for uncapped analytic lag; capped/limited scenario `max|ΔP|≤1e-3 MW`, `|ΔE|≤1e-6 MWh` provisionally |
| Fidelity activation | Compare common state immediately before/after | Discrete exact; `|ΔE|, |ΔSoC|, |ΔP|≤1e-12` in their units |
| Failed activation | Deliberately incompatible/out-of-range state | Active model and full state unchanged; exact failure event |
| PCC components | Closed: `{GRID,LOCAL}`; open: `{GRID}`, `{LOCAL}` | Exact sets, labels, and topology versions |
| Unsupported island | Open PCC with 0.6 MW load | Exact mode; imbalance `-0.6 MW` once BESS applied power is zero; alarm correlation exact |
| Command lifecycle | valid, duplicate, stale sequence, past tick, out-of-range, wrong mode | Exact reason/status and one execution per unique command |
| Alarm lifecycle | occurrence, acknowledgement, return in both orders | Exact state-transition/event sequence |
| Snapshot identical continuation | Save T; execute suffix S twice from save | Byte-identical trace suffix and final serialized state |
| Alternative continuation | Same T; suffix A vs B | Exact common prefix; repeatability per branch; first divergence tied to different command |
| RNG continuation | Draw before/after snapshot using injected RNG | Exact repeated sequence after restore |

### 15.3 Basis and limits of proposed tolerances

The `1e-12` point tolerances are appropriate only for a short scalar calculation using closed-form updates and binary64-scale values near 1; they are not measurement tolerances. The looser cumulative residual accounts for repeated arithmetic. The half-step thresholds are provisional engineering acceptance values intended to catch gross coupling mistakes; Gate C should confirm them by running the defined sensitivity study before freezing the Definition of Done. If observed differences exceed them, do not widen tolerances without classifying the cause.

### 15.4 Reference trace requirements

A golden trace should include every command, acknowledgement, topology event, fidelity event, alarm transition, macro telemetry publication, and snapshot/restore event. Include logical tick, phase-derived sequence, model/topology/schema versions, and correlation. Exclude wall time, network connection IDs, and rendering metadata.

---

## 16. Failure modes and common modelling traps

| Failure/trap | Consequence | Required defence |
|---|---|---|
| Floating cumulative time | Missed/equal events drift | Integer ticks and declared time base |
| Heap key lacks tie-breaker | Runtime-dependent or incomparable ties | Stable source/insertion sequence |
| Same-tick work scheduled backward | Causality loop/hidden reordering | Reject completed phases; quiescence rule |
| UI directly calls model step | Rendering becomes physics | Command/publication ports only |
| Core awaits viewer/storage | Client speed changes execution | Non-blocking bounded adapter buffers |
| Live arrival order becomes priority | Network jitter changes result | Explicit logical apply tick and source sequence |
| Requested = accepted = applied | Hides validation/dynamics | Separate ownership and telemetry fields |
| SoC clipped after integration | Artificial energy deletion/creation | Pre-compute energy-feasible power |
| Efficiency applied twice or wrong direction | Incorrect energy/loss balance | One sign convention and residual tests |
| Round-trip efficiency used as each-way efficiency | Squares the intended efficiency | Separate `η_ch`, `η_dis`; publish product |
| Endpoint power used as interval energy blindly | Coupling error | Explicit mean/integral policy |
| Average discrete modes/quality | Invented states | End sample + ordered events, never average |
| Topological island called electrically stable | False realism | `ISLANDED_UNSUPPORTED`; no voltage/frequency claim |
| Droop without network/forming dynamics | Meaningless frequency/voltage | Defer droop |
| Fidelity initializes lag to target | Power jump at transition | Initialize from applied power |
| Reverse transition discards transient silently | Hidden discontinuity | Defer or define explicit policy |
| Snapshot omits counters/queue/RNG/alarm ack | Replay divergence | Completeness inventory and mutation tests |
| Snapshot serializes heap backing order | Noncanonical evidence | Sort by semantic queue key |
| Pickle used as portable contract | Unsafe/version-fragile | Typed finite JSON and explicit versions |
| Multi-worker in-memory API | Divergent parallel simulations | Exactly one simulation owner |
| Library object crosses boundary | Replacement becomes migration | Canonical records and adapters |
| Plausible plot accepted as validation | False confidence | Analytic/invariant/golden evidence |

---

## 17. Recommended V0 model boundary

### Included

- One deterministic, synchronous logical-time core.
- Integer 0.1 s base tick, 1 s macro boundary, fixed ratio 10.
- Explicit total event order and quiescent synchronization boundary.
- Infinite-source label, two buses, one PCC breaker, one constant active load.
- Deterministic connectivity/island detection and separate active-power accounting.
- Ideal fallback BESS and reduced-order detailed BESS defined in sections 5–6.
- Fallback-to-detailed activation with common state and continuity evidence.
- Supervisory request, validation/acknowledgement, model-owned application.
- Typed telemetry, quality, topology events, and one alarm lifecycle.
- Complete versioned snapshots, identical replay, and alternative continuation.
- Optional pacing around identical logical execution.
- Thin asynchronous API/viewer adapters that cannot back-pressure the core.
- In-memory evidence plus optional versioned JSON trace/snapshot files.

### Explicit nonclaims

No AC/RMS power flow, voltage, frequency, current, reactive power, phases, waveform/EMT, switching, harmonics, imbalance, fault current, relay/protection coordination, grid-forming/grid-following control, droop, black start, resynchronization, cell electrochemistry, thermal/degradation/safety, industrial-protocol interoperability, cybersecurity, historian capability, grid-code/IEEE/IEC/ISA/OPC/FMI compliance, certification, or production suitability.

### Replacement seams

| Current V0 element | Stable boundary | Possible maturation |
|---|---|---|
| Internal scheduler | Model lifecycle + canonical event contract | FMI/co-simulation master or richer hybrid kernel |
| Scalar BESS | Asset/model lifecycle + common state | PyBaMM/device-calibrated/PCS dynamic adapter |
| Small BFS | Topology service contract | NetworkX or solver topology adapter |
| Algebraic balance | Electrical-solver port | power flow/RMS dynamics |
| In-process commands | Command/ack contracts | protocol adapters |
| JSON/in-memory trace | Publication/recorder port | DuckDB/Parquet/historian |
| Static viewer | API/publication contracts | operational HMI/SCADA views |

---

## 18. Alternatives rejected or deferred

### Rejected for TT-000

- UI zoom directly switches fidelity: violates the project invariant that fidelity change is a controlled domain event.
- Async physics/models in the core: unnecessary concurrency and nondeterministic completion risk.
- Arbitrary dictionaries for messages/snapshots: hides units, versions, and ownership.
- Direct commits to a technology-specific topology or solver object: breaks replacement boundaries.
- Declaring an island energized/stable based only on graph connectivity and active-power equality.
- Treating a software package's model catalog as validation evidence.

### Deferred with a preserved seam

- Detailed-to-fallback runtime activation.
- Arbitrary clock ratios and adaptive time steps.
- Off-grid/root-found events and optimistic rollback.
- Interpolation/extrapolation of smooth exchanged variables.
- FMI import/export and distributed co-simulation.
- NetworkX and a general electrical solver.
- Voltage/frequency states, reactive power, GFL/GFM, droop, and protection.
- Cell/equivalent-circuit/electrochemical and thermal/degradation models.
- External protocols and communication delay/loss models.
- DuckDB, Parquet, historian queries/retention, and full event sourcing.
- Alarm shelving, suppression, confirmation, rationalization metrics, and standards alignment.
- Production authentication/authorization, redundancy, deployment, and cybersecurity.

---

## 19. Unresolved decisions for the feature architect

These choices are bounded by the evidence and do not block Gate B:

1. Freeze the exact phase enumeration and whether fidelity activation precedes or follows topology derivation when both occur at one tick; the report recommends topology first.
2. Decide the authority order for simultaneous commands from scenario, operator, and controller sources.
3. Choose reject-versus-clip for out-of-range active-power commands. Recommendation: reject impossible requests; allow an explicitly reported accepted limit only for dynamic energy feasibility.
4. Freeze the exact operating-mode enum and whether `DEENERGIZED` is separate from `ISLANDED_UNSUPPORTED`.
5. Define whether PCC close is demonstrated; if so, restrict it to topology relabelling without synchronization claims.
6. Confirm whether snapshots are memory-only plus test fixture or also optional atomic JSON files.
7. Choose canonical JSON rules/checksum method and supported runtime/platform replay profile.
8. Decide whether `Pydantic` types are canonical domain contracts or serialization-edge DTOs around standard dataclasses. Recommendation: preserve a domain/serialization separation even if both are generated together.
9. Decide FastAPI telemetry transport (WebSocket versus server-sent events); command submission should remain request/ack HTTP or an equivalent typed operation.
10. Define bounded per-viewer queue sizes and telemetry coalescing diagnostics without affecting evidence sinks.
11. Confirm the synthetic fixture, alarm threshold/delay, command timings, snapshot tick, and alternative suffixes.
12. Run/inspect the proposed `h=0.05 s` sensitivity reference before freezing the provisional capped-response tolerance.
13. Decide whether an ADR is created at Gate C for time/event/snapshot semantics, as required by `DEVELOPMENT_PROTOCOL.md` for long-lived choices.
14. State the exact model/version compatibility policy for restore and transition failures.

---

## 20. Exact reference list suitable for `REFERENCES.md`

1. Modelica Association Project FMI. **Functional Mock-up Interface Specification 3.0.2**. 2024-11-27. <https://fmi-standard.org/docs/3.0.2/>. Accessed 2026-08-26.
2. Gomes, C.; Thule, C.; Broman, D.; Larsen, P. G.; Vangheluwe, H. **Co-simulation: a Survey**. *ACM Computing Surveys* 51(3), Article 49, 2018. DOI: <https://doi.org/10.1145/3179993>.
3. Lee, E. A. **Deterministic Concurrency**. Ptolemy Project / UC Berkeley, digital edition observed 2026. <https://ptolemy.berkeley.edu/~eal/books/DC/DeterministicConcurrency_Digital_05.pdf>. Accessed 2026-08-26.
4. Moshagen, T. **On meeting Energy Balance Errors in Cosimulations**. arXiv:1706.07273, 2017. <https://arxiv.org/abs/1706.07273>.
5. Rodríguez, B. et al. **Energy-based monitoring and correction to enhance explicit co-simulation**. *Multibody System Dynamics*, 2022. DOI: <https://doi.org/10.1007/s11044-021-09819-0>.
6. Ponciroli, R. et al. **Development of Electro-chemical Battery Model for Plug-and-Play Eco-system Library**. Argonne National Laboratory, ANL-21/31, 2021. <https://publications.anl.gov/anlpubs/2021/09/170551.pdf>.
7. U.S. Department of Energy. **Battery Energy Storage Systems Report**. January 2025. <https://www.energy.gov/sites/default/files/2025-01/Battery-Energy-Storage-Systems-Report.pdf>.
8. Sandia National Laboratories / EPRI. **Electrical Energy Storage Data Submission Guidelines, Version 2**. 2021. <https://www.sandia.gov/ess-ssl/wp-content/uploads/2021/07/SNL-EPRI-Data-Guide-SAND-V2.pdf>.
9. U.S. Department of Energy, Rapid Operational Validation Initiative. **Guidance for Data Collection from Flow Systems**. 2023. <https://www.energy.gov/sites/default/files/2023-09/Guidance%20for%20Data%20Collection%20from%20Flow%20Systems.pdf>.
10. Denholm, P. et al. **Stabilizing the Power System in 2035 and Beyond: Evolving from Grid-Following to Grid-Forming Distributed Inverter Controllers**. NREL/TP-5D00-79761, 2021. <https://www.nrel.gov/docs/fy21osti/79761.pdf>.
11. Fix, E. et al. **Investigating Multi-Microgrid Black Start Methods Using Grid-Forming Inverters and Protective Relays**. NREL/CP-5D00-83956, 2023. <https://www.nrel.gov/docs/fy23osti/83956.pdf>.
12. IEEE Standards Association. **IEEE Std 1547-2018 — Standard for Interconnection and Interoperability of Distributed Energy Resources with Associated Electric Power Systems Interfaces**. <https://standards.ieee.org/standard/1547-2018.html>. Accessed 2026-08-26.
13. OPC Foundation. **OPC Unified Architecture Part 4: Services, 7.11 DataValue**. <https://reference.opcfoundation.org/specs/OPC-10000-4/7.11>. Accessed 2026-08-26.
14. OPC Foundation. **OPC Unified Architecture Part 8: Data Access, 7.3 Status Codes**. <https://reference.opcfoundation.org/specs/OPC-10000-8/7.3>. Accessed 2026-08-26.
15. OPC Foundation. **OPC Unified Architecture Part 9: Alarms and Conditions, Annex A**. Version 1.05. <https://reference.opcfoundation.org/Core/Part9/v105/docs/A>. Accessed 2026-08-26.
16. International Society of Automation. **ISA-18 Series of Standards**; includes ANSI/ISA-18.2-2016. <https://www.isa.org/standards-and-publications/isa-standards/isa-18-series-of-standards>. Accessed 2026-08-26.
17. Cloud Native Computing Foundation. **CloudEvents Specification v1.0.2**. <https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md>. Accessed 2026-08-26.
18. Bray, T., ed. **RFC 8259 — The JavaScript Object Notation (JSON) Data Interchange Format**. IETF, 2017. <https://www.rfc-editor.org/rfc/rfc8259>.
19. Python Software Foundation. **Python 3.14.7 Documentation: `heapq`, `random`, `math`, `sys`**. <https://docs.python.org/3.14/>. Accessed 2026-08-26.
20. NetworkX Developers. **NetworkX 3.6.1 Documentation: Connected Components**. <https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.connected_components.html>. Accessed 2026-08-26.
21. Pydantic Team. **Pydantic 2.13.4 package and release metadata**. <https://pypi.org/project/pydantic/>. Accessed 2026-08-26.
22. Ramírez, S. / FastAPI contributors. **FastAPI 0.141.1 documentation and release metadata**. <https://fastapi.tiangolo.com/> and <https://pypi.org/project/fastapi/>. Accessed 2026-08-26.
23. Uvicorn contributors. **Uvicorn 0.52.4 documentation and release metadata**. <https://uvicorn.dev/> and <https://pypi.org/project/uvicorn/>. Accessed 2026-08-26.
24. pytest contributors. **pytest 9.1.1 documentation and release metadata**. <https://docs.pytest.org/> and <https://pypi.org/project/pytest/>. Accessed 2026-08-26.
25. PyBaMM Team. **PyBaMM 26.8.0.0 documentation; Thevenin Equivalent Circuit Model**. <https://docs.pybamm.org/en/latest/source/api/models/equivalent_circuit/thevenin.html> and <https://pypi.org/project/pybamm/>. Accessed 2026-08-26.
26. DuckDB Foundation. **Why DuckDB; Release Calendar (1.5.5 current stable observed)**. <https://duckdb.org/why_duckdb> and <https://duckdb.org/release_calendar.html>. Accessed 2026-08-26.
27. Apache Software Foundation. **Apache Parquet Overview and File Format**. <https://parquet.apache.org/docs/overview/> and <https://parquet.apache.org/docs/file-format/>. Accessed 2026-08-26.

---

## 21. Gate B verdict

### READY FOR ARCHITECTURE

The report provides enough evidence to select:

- a deterministic logical-time and simultaneous-event policy;
- a fixed-ratio macro/child coupling method and initial steps;
- transparent fallback and detailed BESS equations with signs/units/limits;
- an honest unsupported-island boundary;
- a one-way V0 fidelity transition with measurable continuity;
- canonical command/state/event/alarm requirements;
- complete snapshot/replay semantics;
- an asynchronous adapter boundary that cannot become accidental physics;
- a minimal open-source stack and explicit deferrals;
- analytic, invariant, sensitivity, and replay validation cases with proposed tolerances.

Unsupported realism claims have been removed or explicitly rejected. The architect must resolve section 19 and convert the selected choices into `FEATURE_CONTEXT.md` only after this Gate B report is reviewed. No implementation branch or code is authorized by this verdict.
