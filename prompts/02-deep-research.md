# Prompt: Generate and Execute Node Deep Research

Use this prompt only after Gate A approval of `NODE_CONTEXT.md`.

---

You are acting as the research agent for one approved tech-tree node in the Hierarchical Energy Co-Simulation Lab.

Read completely:

1. `MASTER_PROJECT_CONTEXT.md`
2. `NORTH_STAR.md`
3. `DEVELOPMENT_PROTOCOL.md`
4. `TECH_TREE.md`
5. `ARCHITECTURE.md`
6. the selected node's approved `NODE_CONTEXT.md`
7. relevant accepted ADRs and existing node research

First update the node's `RESEARCH_PROMPT.md` so it is self-contained and directly answers the approved learning questions. Then conduct the research and write `RESEARCH_REPORT.md`.

Research requirements:

- Prefer standards, official specifications, peer-reviewed research, established textbooks, official open-source documentation/source code and relevant vendor technical documentation.
- Use current exact versions when the behaviour may vary by software or standard revision.
- Cite every material factual or normative claim near the claim.
- Distinguish cited fact, engineering inference, project choice and unresolved uncertainty.
- Do not treat software availability as evidence of model validity.
- Do not claim compliance, certification, interoperability or production suitability without a defined basis.
- Summarize copyrighted sources instead of reproducing substantial text.

The report must include:

1. Executive explanation.
2. Answers to every learning question.
3. Prerequisite concepts and terminology.
4. Real-world system behaviour and architecture.
5. Candidate simplified educational models.
6. Equations, state variables, units, signs and validity boundaries.
7. Time, event and coupling implications.
8. Canonical interface and data requirements.
9. Open-source tool candidates with boundary and replacement analysis.
10. Validation cases, reference values and defensible tolerances.
11. Failure modes and common modelling errors.
12. Recommended model boundary for this node.
13. Alternatives rejected or deferred.
14. Unresolved decisions for the architect.
15. Reference list suitable for registration in `REFERENCES.md`.

Do not write implementation code or `FEATURE_CONTEXT.md`. End with the Gate B decision: ready for architecture, blocked pending evidence or learning charter requires revision.
