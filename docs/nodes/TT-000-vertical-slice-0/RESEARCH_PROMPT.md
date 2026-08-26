# TT-000 Deep Research Prompt

## Status

Prepared draft — run only after Gate A approval of `NODE_CONTEXT.md`

---

Conduct a rigorous, implementation-oriented deep research study for Vertical Slice 0 of an educational, modular, hierarchical Model-in-the-Loop energy simulation laboratory.

The long-term project aims to become an operationally representative open-source laboratory, while V0 must use the smallest technically honest models capable of proving the architecture. The research must not design a universal power-system simulator or assume production-grade fidelity.

## V0 reference system

Research a minimal system consisting of:

- an infinite-grid equivalent;
- one PCC breaker;
- one local AC bus;
- one aggregate load;
- one BESS with a fallback and a more detailed reduced-order model;
- supervisory and local control boundaries;
- typed commands, acknowledgements, telemetry and alarms;
- deterministic logical time with one macro rate and one fixed-ratio child rate;
- controlled model-fidelity transition;
- snapshot, restore and alternative continuation;
- an asynchronous API/viewer that must not alter logical outcomes.

## Questions to answer

### A. Deterministic simulation semantics

1. What scheduling model is appropriate for a small deterministic hybrid fixed-step/discrete-event simulator?
2. How should logical time, wall-clock pacing and fast-forward execution be separated?
3. What deterministic priority policy should apply to simultaneous topology events, faults, commands, controller evaluation, model advancement, telemetry and alarms?
4. What state is required to reproduce an execution exactly?

### B. Multi-rate coupling

1. What is the smallest correct fixed-ratio macro/micro coupling algorithm?
2. Which inputs should use zero-order hold, interpolation or event interruption?
3. Which outputs should be sampled, averaged, integrated or reduced to extrema/events?
4. How should energy conservation and coupling residuals be measured?
5. What initial macro and micro time steps are suitable for the proposed reduced-order models, and why?
6. Which phenomena cannot be represented at those steps?

### C. BESS model hierarchy

1. Define a minimal fallback BESS model based on bounded power and SoC integration.
2. Define the smallest meaningful detailed model that adds efficiency, lag/ramp response, operating modes and selected island behaviour without pretending to be an EMT inverter model.
3. Identify required state variables, parameters, units, sign conventions and validity ranges.
4. Explain how battery power, grid power, losses and stored energy should be signed and balanced.
5. Determine whether simplified frequency/power or voltage/reactive-power droop belongs in V0; recommend deferral if it adds unsupported complexity.

### D. Fidelity transition

1. What lifecycle interface should interchangeable models implement?
2. How should fallback state initialize the detailed model?
3. How should the detailed model collapse back to fallback state?
4. Which discontinuities must be measured?
5. What tolerances or invariants can establish an honest transition?
6. Should V0 support both transition directions or only fallback-to-detailed activation?

### E. Topology and islanding

1. What is the minimum canonical topology model for buses, branches and a breaker?
2. How should connectivity/island detection remain separated from electrical calculation?
3. Is NetworkX justified for V0, or would a smaller implementation teach the same concept while preserving an upgrade boundary?
4. What state and events must change when the PCC opens?

### F. Contracts and control flow

1. Define minimum canonical schemas for command, acknowledgement, telemetry, alarm, topology event and quality.
2. Include correlation, source identity, logical timestamp, sequence and schema/model versioning.
3. Define ownership of actual state, requested setpoint, accepted setpoint and applied actuator value.
4. Identify a minimum command-validation and alarm lifecycle suitable for V0.

### G. Snapshot and replay

1. Identify all state that a valid snapshot must capture: models, controllers, topology, scheduler, event queue, random generators, active commands, alarms and metadata.
2. Recommend a versioned snapshot strategy appropriate to V0.
3. Define tests for identical continuation and alternative continuation.
4. Explain limitations of snapshot portability across model or schema versions.

### H. API, viewer and persistence boundary

1. Define the smallest asynchronous API/viewer that tests observation and control without influencing simulation scheduling.
2. Recommend how commands arriving from wall-clock I/O enter deterministic logical time.
3. Determine whether DuckDB or Parquet adds learning value in V0 or should be deferred.
4. Recommend ports/adapters that make FastAPI, storage and visualization replaceable.

### I. Open-source tools and validation

1. Evaluate the smallest justified open-source stack for V0 rather than accepting every tool named in the long-term vision.
2. Use official documentation and current versions for tool-specific recommendations.
3. Identify reference equations, published test cases or independent calculations suitable for validation.
4. Propose numerical tolerances and explain their basis.
5. Identify licence, maintenance, determinism or interoperability risks.

## Required output

Produce a cited `RESEARCH_REPORT.md` with:

1. Executive recommendation.
2. Direct answer to every research question.
3. Glossary and prerequisite explanation.
4. Real-world context versus V0 simplification.
5. Recommended equations/state machines with symbols and units.
6. Validity boundaries and explicit nonclaims.
7. Recommended time and event semantics.
8. Recommended model lifecycle and fidelity mapping.
9. Recommended canonical contracts.
10. Recommended minimal open-source stack and deferred tools.
11. Validation matrix with reference, method and tolerance.
12. Architecture-relevant risks and alternatives.
13. Decisions the feature architect must make.
14. Exact reference list suitable for the project registry.
15. Gate B verdict: ready, blocked or charter revision required.

Prioritize primary and authoritative sources. Clearly label inference. Do not write implementation code, a milestone plan or a completed feature context.
