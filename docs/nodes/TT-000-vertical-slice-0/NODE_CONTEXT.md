# TT-000 — Hierarchical Co-Simulation Vertical Slice 0

## Status

Approved

This charter defines the learning problem. It does not approve implementation choices, equations, time steps or technology selections.

## 1. Node identity

- Node ID: TT-000
- Working title: Hierarchical Co-Simulation Vertical Slice 0
- Type: mandatory trunk / architecture-learning slice
- Prerequisites: documentation bootstrap only

## 2. Affected realms

Primary:

- simulation kernel and time;
- physics and numerical models;
- control and automation;
- topology and protection;
- SCADA and visualization;
- compliance and validation.

Secondary:

- data and historian;
- communications and interoperability through typed in-process contracts only.

Not advanced by this node:

- reliability and maintenance;
- cybersecurity;
- industrial protocol interoperability;
- grid-code compliance.

## 3. Current-system limitation

No executable system exists. The project has not yet demonstrated that its central architectural ideas—deterministic logical time, hierarchical coupling, model-fidelity substitution, bidirectional state/control propagation, topology change, snapshot restore and UI independence—can coexist in one minimal vertical slice.

## 4. Central learning question

Can a small deterministic energy simulation coordinate a supervisory layer and a higher-rate asset model, exchange typed control and telemetry in both directions, change topology, transition between fallback and detailed models, and reproduce results after restore without allowing UI or infrastructure timing to become accidental physics?

## 5. Learning questions

1. How should logical simulation time, event ordering and wall-clock execution be separated so that fast-forward and interactive runs remain logically equivalent?
2. What is the smallest correct contract for synchronizing one macro clock with one fixed-ratio micro clock, including input holding, output aggregation and interruption events?
3. How can a fallback BESS model and a more detailed reduced-order BESS model exchange state at a synchronization boundary without artificial energy, power or mode discontinuities?
4. Which typed commands, acknowledgements, telemetry, alarms and quality metadata are necessary to demonstrate downward control and upward state propagation?
5. How should connectivity and island detection be represented without confusing graph topology with electrical power-flow calculation?
6. What state must a snapshot capture to reproduce scheduler, model, controller, topology, event-queue and random behaviour?
7. How can an asynchronous API/viewer observe and command the system without changing deterministic results merely by connecting, disconnecting or rendering at a different rate?

## 6. Intended capability

After completion, the repository should run one documented deterministic scenario through:

- a logical-time kernel;
- one macro execution rate and one child rate;
- a tiny switchable electrical topology;
- one BESS represented by two interchangeable fidelity levels;
- supervisory and local control;
- canonical commands, acknowledgements, telemetry and alarms;
- snapshot, restore and alternative continuation;
- a minimal read/control viewer;
- automated validation evidence.

## 7. Proposed reference system

The research and architecture stages should evaluate this minimal system:

- an infinite-grid equivalent;
- a point-of-common-coupling breaker;
- one local AC bus;
- one aggregate load;
- one BESS;
- one supervisory controller;
- one local BESS/controller boundary;
- one minimal single-line viewer.

Only the BESS is expected to have two fidelity implementations in V0:

- fallback hypothesis: bounded ideal active-power response plus SoC integration;
- detailed hypothesis: SoC and efficiency plus reduced-order inverter response, limits and a deliberately simplified island response.

These are research hypotheses, not approved equations.

## 8. North-star vector

TT-000 establishes the replaceable trunk needed by later branches:

- higher-fidelity physics can replace model implementations;
- additional assets can implement the same lifecycle and contracts;
- external solvers can replace algebraic calculations behind a solver boundary;
- protocols can replace or supplement in-process transport through adapters;
- richer SCADA and historians can consume stable external contracts;
- protection, security and reliability can later act through defined state, event and message boundaries.

## 9. Scope

- One deterministic scenario configuration.
- One macro rate and one fixed-ratio child rate.
- One topology-changing breaker.
- Connectivity and island detection only; no general network solver.
- One aggregate load model.
- Two reduced-order BESS implementations sharing a canonical model contract.
- Explicit state mapping between BESS fidelity levels.
- Minimal command, acknowledgement, telemetry and alarm contracts.
- Snapshot and restore at a documented synchronization boundary.
- Fast-forward execution and optional wall-clock pacing with identical logical results.
- Minimal API/viewer sufficient to observe topology and send approved commands.
- Tests and a validation report.

## 10. Non-goals

TT-000 will not claim or implement:

- AC power flow or optimal power flow;
- electromagnetic transients or switching waveforms;
- harmonics or three-phase imbalance;
- fault-current calculation or relay coordination;
- grid-code compliance;
- production-quality GFL/GFM inverter controls;
- IEC 61850, Modbus, OPC UA, DNP3 or other industrial protocols;
- CIM conformance;
- cybersecurity attacks or IEC 62443 compliance;
- TSO/DSO institutional replication;
- multiple substations or feeders;
- automatic fidelity switching caused by UI zoom;
- arbitrary clock ratios;
- distributed microservices;
- production EMS, protection or safety behaviour.

## 11. Expected reference scenario

The scenario should, subject to research and architecture approval:

1. start grid-connected with the fallback BESS model;
2. send and acknowledge an active-power command;
3. activate the detailed BESS model at a synchronization boundary;
4. apply a setpoint change that exposes dynamic response or limits;
5. open the PCC breaker and detect an island;
6. create a load/power imbalance and raise a typed alarm;
7. create a snapshot;
8. continue to a defined trip or degraded state;
9. restore the snapshot;
10. apply an alternative command and produce a different, reproducible continuation.

Exact timings, equations and expected numerical results must come from the research and feature context.

## 12. Expected validation

At minimum, research should determine defensible methods for testing:

- deterministic event ordering;
- equality of logical results between fast-forward and paced execution;
- macro/micro synchronization;
- energy and SoC invariants;
- state continuity during fidelity transition;
- topology/island detection;
- command lifecycle and alarm correlation;
- snapshot equivalence for identical continuation;
- UI connection independence;
- documented numerical tolerances.

## 13. Unknowns research must resolve

- Suitable clock semantics and event-priority rules.
- Appropriate initial macro/micro rates and their numerical justification.
- Minimum BESS equations and controller states required for the learning goals.
- Boundary variables and aggregation method between rates.
- State-mapping equations and acceptable continuity tolerances.
- Minimum topology representation and island semantics.
- Snapshot contents and serialization/versioning strategy.
- Whether persistence belongs in V0 or should remain an in-memory validation fixture.
- Minimum viewer/API boundary needed to test asynchronous independence.
- Which proposed libraries are necessary in V0 and which should be deferred.

## 14. Risks of implementing too early

- Encoding arbitrary equations as if they were validated physics.
- Making UI zoom control model fidelity directly.
- Coupling domain models to FastAPI, NetworkX or storage objects.
- Building a complex scheduler before specifying event semantics.
- Storing incomplete snapshots that appear reproducible but omit hidden state.
- Adding multiple services before proving deterministic in-process behaviour.
- Using RMS averaging without defining what is preserved at the coupling boundary.

## Gate A — Human approval

Before research begins, confirm:

- [x] The central learning question is correct.
- [x] The seven supporting questions are worth learning now.
- [x] The proposed reference system is small enough for V0.
- [x] The scope is sufficient to prove the project thesis.
- [x] The non-goals are accepted.
- [x] V0 may be revised if research shows that one proposed mechanism is premature.
