# Master Project Context

## Status and authority

This document is the project constitution. It defines stable philosophy, terminology, invariants and governance. It does not describe the current implementation, prescribe the entire future technology tree or replace a node-specific feature specification.

Changes to this document require an Architecture Decision Record when they alter an invariant or materially change the project mission.

## 1. Mission

Build an interactive, modular, hierarchical Model-in-the-Loop energy simulation laboratory for learning how modern electrical systems are modelled, controlled, automated, monitored, integrated, operated, validated and secured.

Learning is the primary objective. The software is both an executable laboratory and a record of the reasoning, references, assumptions, experiments and validation that produced each capability.

The mature system should become operationally representative of real power-system architectures using open-source tools wherever practicable. Early slices intentionally use lightweight models and synthetic substitutes. Every substitute must state its limits and, where maturation is expected, expose a credible replacement boundary.

## 2. Governing principles

### 2.1 Learning before feature accumulation

Every tech-tree node begins with explicit learning questions and ends by answering them. Code alone does not unlock a node. A capability requires evidence, validation and a record of remaining uncertainty.

### 2.2 Vertical slices before horizontal expansion

A slice should exercise a complete path through the system before new breadth is added. New assets, protocols, solvers or operational layers are introduced only when the existing trunk can integrate and validate them.

### 2.3 Maturity is multidimensional

The project matures across independent realms:

- simulation kernel and time;
- physics and numerical models;
- control and automation;
- topology and protection;
- communications and interoperability;
- SCADA and visualization;
- data and historian;
- reliability and maintenance;
- cybersecurity;
- compliance and validation.

A node may advance one or several realms. No single global fidelity label may conceal weaknesses in another realm.

### 2.4 The tech tree is emergent

`TECH_TREE.md` records validated capabilities, current maturity and nearby candidates revealed by the latest work. It is descriptive, not a frozen roadmap. Proposed nodes are non-binding and may be revised, combined, reordered or discarded.

### 2.5 The north star supplies direction, not fixed implementation

`NORTH_STAR.md` defines the final-boss reference topology, representative operational scenario and desired realism dimensions. It does not freeze libraries, service boundaries, models or numerical methods.

### 2.6 Observable contracts outlive implementations

Canonical state, command, telemetry, alarm, event, topology, scenario and lifecycle contracts should remain more stable than the technologies behind them. External libraries, solvers, transports, databases and frontends belong behind explicit boundaries.

### 2.7 Simplifications must be technically honest

Every model or subsystem declares:

- what it represents;
- what it deliberately omits;
- its equations or behavioural rules;
- units and sign conventions;
- applicable operating range;
- validation evidence;
- maturity and known limitations;
- intended upgrade direction, when one exists.

Plausible-looking output is not validation. Standards alignment, conformance, protection-grade timing, certification and production suitability may not be claimed without corresponding evidence.

### 2.8 Deterministic logical time is separate from execution time

Simulation results are governed by logical time, ordered events, explicit inputs and recorded random state. Wall-clock synchronization is an execution mode, not a source of physical truth. A UI connection, rendering rate or operator navigation must not silently change simulation behaviour.

### 2.9 Fidelity changes are controlled simulation events

UI zoom may reveal additional detail or request a fidelity change, but it does not directly alter physics. Model activation or replacement occurs only through a documented policy at a synchronization boundary, with state mapping, continuity checks and an auditable event.

### 2.10 Topology and electrical calculation are distinct

Connectivity tools determine buses, branches, switch states, islands and graph relationships. Electrical solvers calculate voltage, current, power and dynamic response. Connectivity changes cause the electrical model to be rebuilt or reevaluated; electricity is not described as algorithmic packet rerouting.

### 2.11 Synchronous deterministic core, asynchronous edges

The simulation kernel and CPU-bound model advancement should remain deterministic and explicitly scheduled. Network I/O, user interfaces, protocol adapters and persistence may be asynchronous but must not introduce nondeterministic domain behaviour.

### 2.12 Orthogonal capabilities remain separable

Cybersecurity, reliability, maintenance and compliance attach through defined interfaces. They may influence messages, availability, limits or events without embedding unrelated logic into core physical equations.

### 2.13 Refactoring and replacement are expected

Architecture, models and technology choices may change as maturity demands. Evolution follows the compatibility and migration protocol in `DEVELOPMENT_PROTOCOL.md`: characterize, isolate, implement in parallel where possible, compare, switch reversibly and deprecate deliberately.

## 3. Stable terminology

| Term | Meaning |
|---|---|
| Realm | A continuing capability dimension such as physics or communications |
| Tech-tree node | One bounded learning and implementation increment |
| Capability branch | The evolving sequence of related nodes within a realm |
| Git feature branch | Temporary implementation workspace for one selected node |
| Vertical slice | End-to-end capability crossing the layers required for one scenario |
| Maturity | Evidence-backed level of realism or operational capability within a realm |
| Fallback model | Lightweight implementation used when greater fidelity is unnecessary or unavailable |
| Detailed model | More computationally or behaviourally expressive implementation of the same contract |
| Canonical contract | Technology-independent typed interface used inside the system |
| Final boss | The versioned north-star reference system and representative integrated scenario |

## 4. Repository-wide invariants

1. Inter-component state, commands, telemetry, alarms and events use canonical typed contracts.
2. Units, reference directions and sign conventions are explicit.
3. Logical simulation time never depends on frontend rendering or network arrival time unless delay is itself part of the model.
4. Randomness is seeded, injectable and snapshot-aware.
5. Model limitations and unsupported claims are documented.
6. Validated regression scenarios survive refactoring or receive explicit versioned migrations.
7. Tool-specific objects do not cross their adapter boundaries.
8. No node is marked unlocked until its Definition of Done and validation gate pass.
9. Candidate future nodes do not become commitments until selected and specified.
10. Current architecture documentation describes reality rather than aspiration.

## 5. Project-level non-goals

The project does not promise to become:

- a universal simulator for every power-system phenomenon;
- a certified grid-planning or grid-code-compliance product;
- a safety controller or production protection system;
- a replacement for vendor engineering tools;
- a full-scale replica of a national utility;
- maximally realistic on every axis simultaneously.

The target is an educational, operationally representative laboratory with explicit evidence and boundaries.

## 6. Governance

Conflicts are resolved in this order:

1. safety, permissions and applicable repository policies;
2. this constitution;
3. accepted Architecture Decision Records;
4. the selected node's approved `FEATURE_CONTEXT.md`;
5. implementation plans and progress notes.

If a selected feature requires breaking a constitutional invariant, work stops until the change is reviewed and recorded.
