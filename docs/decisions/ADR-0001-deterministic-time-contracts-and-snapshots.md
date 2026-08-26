# ADR-0001: Deterministic time, command authority, contracts and snapshots

- Status: accepted
- Date: 2026-08-26
- Accepted by: Human project owner through TT-000 Gate C approval
- Related node: TT-000 — Hierarchical Co-Simulation Vertical Slice 0
- Source decision: `docs/nodes/TT-000-vertical-slice-0/FEATURE_CONTEXT.md`, sections 9–12
- Supersedes: none
- Superseded by: none

## Context

TT-000 establishes the first executable architecture. Logical-time ordering,
command authority, canonical contracts and snapshot compatibility will be
long-lived boundaries. Leaving any of them to callback order, network arrival,
dictionary iteration, wall time or implementation-specific serialization would
make replay nondeterministic and make later model or adapter replacement a
contract migration.

Gate C approved the decisions below as one prescriptive set. This ADR
transcribes those decisions without adding implementation choices.

## Decision drivers

- Deterministic logical replay from the same canonical input log.
- Separation of synchronous physics from pacing and asynchronous I/O.
- Stable typed contracts whose units, time, source and quality are explicit.
- Atomic model activation and restore before destination mutation.
- Inspectable, versioned snapshot bytes with an explicit compatibility profile.
- Replaceable models, topology implementations, transports and stores.

## Considered options

### Approved option: integer logical time and typed canonical state

Use a single synchronous simulation owner, integer base ticks, a total event
order, standard-library frozen domain records, Pydantic only at serialization
edges, deterministic source sequences and strict finite JSON snapshots.

### Rejected option: infrastructure-driven or implicit semantics

Do not use wall-clock arrival, concurrent callbacks, dictionary/set iteration,
random UUIDs, Pydantic/FastAPI objects in domain state, heap backing order,
pickle or viewer delivery state as domain truth. These mechanisms either make
ordering accidental or leak a replaceable technology across a stable boundary.

## Decision

### Canonical contracts and ownership

All process-boundary or persistent records begin at semantic version 1.0.0 and
carry `schema_version`. An incompatible meaning, required field, sign or unit
change requires a new major version and an explicit mapper/migrator or clear
rejection. Deterministic record identity is stable source identity plus a
monotonic source sequence. The reference scenario provides fixed command IDs;
wall-clock timestamps and random UUIDs are excluded from canonical replay.

The canonical V1 surface comprises commands, acknowledgements, telemetry,
quality, alarm events/state, topology events/snapshots, model handoff/fidelity
events, macro publications, scenarios, traces and snapshot envelopes. Units,
logical tick, sequence, model version, topology version, correlation and
causation are mandatory where their semantics apply.

State ownership is fixed:

1. A caller owns requested power until validation.
2. The validator owns accepted power and its acknowledgement.
3. The controller owns target power.
4. The active BESS model owns applied power and stored energy.
5. Topology owns breaker actual state, components and topology version.
6. The alarm service owns occurrence and acknowledgement state.
7. Telemetry is immutable observation and is never a second source of truth.

Domain records are frozen standard-library dataclasses/enums. Pydantic DTOs
map only at serialization edges and do not enter physics, kernel, topology,
control or alarm state. The approved inward-facing ports are CommandIngress,
PublicationSink, TraceRecorder, SnapshotStore, Pacer, TopologyService and
ActivePowerBalance.

### Command validation and authority

Validation order is schema/version, identity, deterministic ID/idempotency,
source sequence, apply tick/expiry, finite value and unit, command kind/range,
expected model/topology version, target availability and interlocks.

NaN, infinity, wrong unit, past/current live apply tick, stale sequence,
unknown target, wrong version and nameplate-out-of-range requests are rejected.
An in-range power request may be accepted with a reported limit only when
stored-energy feasibility is tighter. Lag/ramp affect applied power rather than
accepted power. A topology safe-zero interlock overrides controller target
without rewriting historical acknowledgement. Exact duplicates return their
recorded acknowledgement and execute no more than once.

Conflicts at one apply tick use this authority order:

1. Safety/interlock actions derived from topology and availability.
2. Scripted scenario/fault commands.
3. Operator/API commands.
4. Supervisory-controller scheduled requests.

Within one authority source, source sequence then canonical command ID decides
order. A lower-authority conflict receives
`SUPERSEDED_BY_HIGHER_AUTHORITY`. Network arrival is never a tie-breaker.

### Logical clock and total event order

The reference time base is 0.1 seconds per integer tick. A macro boundary is
every ten ticks (1 second). Configuration rejects non-positive periods,
non-integral ratios and off-grid physics events.

Every queued item has the total key
`(logical_tick, phase, source_order, insertion_sequence)`. The insertion
sequence is monotonic and is captured/restored. Dictionary and set iteration
do not determine domain order. Phase values and meanings are frozen:

| Value | Phase | Meaning |
|---:|---|---|
| 10 | EXOGENOUS | Apply scheduled scenario/fault facts |
| 20 | TOPOLOGY | Change requested/actual breaker state and topology version |
| 30 | OPERATING_CONTEXT | Recompute components, energization, mode and interlocks |
| 40 | FIDELITY | Execute eligible atomic model activation |
| 50 | COMMAND | Validate, resolve authority and acknowledge commands |
| 60 | CONTROL | Compute controller target from accepted intent and interlocks |
| 70 | MODEL_ADVANCE | Advance the active child model for the next segment |
| 80 | AGGREGATION | Compute macro reductions, balance and residuals |
| 90 | ALARM | Evaluate condition and acknowledgement transitions |
| 100 | PUBLICATION | Sequence and publish immutable records |
| 110 | SNAPSHOT | Capture/restore at an eligible quiescent macro boundary |

Same-tick work may target only a later incomplete phase. Equal/completed-phase
scheduling is a causality error. All later-phase work quiesces before time
advances, and no domain callback executes concurrently.

Macro inputs are resolved at a boundary and held by zero-order hold. An
uninterrupted macro period completes exactly ten child intervals. A scheduled
topology event may interrupt only on a child tick, while completed segment
durations still sum to the macro period. Live API commands target a published
future macro boundary and drain only there. The supervisor observes completed
child reductions at the next macro boundary.

End samples preserve state; means, integrals and extrema preserve their stated
continuous quantities; ordered lists preserve discrete records. Modes,
quality, topology and alarms are never averaged.

Fast-forward does not sleep. Pacing maps logical boundaries to monotonic
wall-clock deadlines but never changes step, skips work or reorders events.
The core publishes immutable copies and never awaits a viewer, socket, file or
database.

### Snapshot boundary, inventory and canonical bytes

SnapshotEnvelopeV1 contains snapshot/run lineage; logical tick/phase; engine,
build, numerical runtime and compatibility metadata; complete resolved
scenario and hashes; contract/model/topology/time-base versions; scheduler
current key, counters, queue and cancellation state; active and inactive model
state; controller/timer/command/deduplication state; topology/mode state; alarm
occurrence/acknowledgement/timers; injected RNG state; pending canonical
ingress; trace/publication sequence state; canonicalization profile, checksum;
and an explicit excluded-infrastructure list.

Sockets, viewer/fan-out/render state, pacer wall-clock origin and sleep history,
and HTTP connection metadata are excluded.

Capture occurs only at SNAPSHOT on a quiescent macro tick after normal
publications have stable sequences and no model step is active. Snapshot
lifecycle records receive deterministic sequences before checksum finalization.
The core does not wait for storage or display.

Restore validates the complete envelope before mutating a fresh runtime and
creates a new run ID linked through `parent_snapshot_id`; it does not move an
existing run backwards. An incompatibility leaves the destination unstarted.

The `python-json-v1` canonicalization profile is UTF-8 JSON with sorted object
keys, compact separators, stable enum/identifier strings, semantic ordering of
unordered lists, queue ordering by full semantic key, and rejection of NaN and
infinity. The SHA-256 lowercase hexadecimal checksum covers canonical bytes
with the checksum field omitted. Pickle and executable deserialization are
forbidden.

Exact byte replay is guaranteed only for CPython 3.14.7, the locked dependency
set, identical model/schema versions and the recorded supported platform
profile. Other profiles need an explicit migrator and regression evidence or
are rejected. The required store is in-memory; filesystem JSON is optional.

Identical continuation restores a snapshot into a fresh runtime and requires a
byte-identical suffix trace and exact final canonical snapshot for the same
suffix. Alternative continuation restores the same immutable snapshot into
fresh runtimes, requires an exact shared prefix and repeatability per suffix,
and ties the first divergence to the first different command.

## Consequences

### Positive

- Domain behavior is inspectable and independent of UI/network timing.
- Event ties, command conflicts and restores have explicit deterministic rules.
- External libraries remain replaceable behind adapters.
- Snapshot compatibility failures occur before state mutation.

### Negative and risks

- Every mutable state class and source counter must be inventoried explicitly.
- Exact byte replay initially has a narrow runtime/platform profile.
- Live fast-forward interaction requires pacing/pause or a predeclared input log.
- Contract evolution requires versioning and migration rather than silent edits.

## Compatibility and migration

- Stable boundaries: V1 contracts, lifecycle ports and canonical logical trace.
- Contracts changed: initial V1 introduction; no pre-existing contract changes.
- Data migration: none for TT-000.
- Parallel-run plan: transition preview and shared-state fallback/detailed tests.
- Rollback plan: keep fallback selectable; reject before activation/restore
  mutation; revert only the failing milestone on the feature branch.
- Deprecation period: no V1 contract or model is removed in TT-000.

## Validation

M0 proves deterministic contract serialization, DTO/domain separation,
wrong-major/non-finite/unit/causality rejection, dependency direction and ADR
correspondence. M1 proves phase ordering and paced/fast logical equality. M2–M6
exercise ownership, transitions, topology, alarms, snapshots and adapter
isolation. M7 runs the approved golden scenario and full regression package.

## Conditions for reconsideration

Review this ADR through a new approved ADR or Gate C amendment if evidence
requires adaptive/off-grid events, arbitrary clock ratios, concurrent domain
execution, a new command-authority model, cross-runtime replay, external
co-simulation rollback or a breaking canonical contract change.

