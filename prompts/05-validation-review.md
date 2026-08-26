# Prompt: Validate and Review a Completed Node

Use this prompt after the developer reports all implementation milestones complete.

---

You are acting as the validation reviewer for a completed tech-tree node in the Hierarchical Energy Co-Simulation Lab.

Read completely:

1. `MASTER_PROJECT_CONTEXT.md`
2. `NORTH_STAR.md`
3. `DEVELOPMENT_PROTOCOL.md`
4. `AGENTS.md`
5. `ARCHITECTURE.md`
6. the node's `NODE_CONTEXT.md`
7. its `RESEARCH_REPORT.md`
8. its approved `FEATURE_CONTEXT.md`
9. its `PROGRESS.md`
10. relevant source, tests, scenarios and ADRs

Independently evaluate whether the implementation supports the claimed capability and learning outcomes. Do not infer success from the presence of code or passing unit tests alone.

Create or complete `VALIDATION_REPORT.md` with:

- verdict: pass, conditional pass or fail;
- answers to every learning question;
- milestone and Definition-of-Done evidence;
- unit, contract, integration, invariant and regression results;
- deterministic replay evidence;
- reference comparisons and tolerances;
- claim-to-source-to-code-to-test traceability;
- demonstration results;
- compatibility and migration results where applicable;
- known limitations and explicitly rejected claims;
- deviations from `FEATURE_CONTEXT.md`;
- required corrective actions;
- justified maturity changes by realm.

Only a passing report may recommend unlocking the node. After a pass, update the architecture ledger, reference registry, changelog and live tech tree. Propose nearby non-binding frontier candidates, but do not select or implement them.
