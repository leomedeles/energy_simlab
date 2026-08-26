# Prompt: Implement an Approved Tech-Tree Node

Use this prompt only after Gate C approval.

---

You are acting as the developer agent for an approved tech-tree node in the Hierarchical Energy Co-Simulation Lab.

Read and obey `AGENTS.md`. Read every document required there completely, including the node's approved `FEATURE_CONTEXT.md` and current `PROGRESS.md`.

Before changing code:

1. Inspect the repository and existing uncommitted changes.
2. Confirm the approved Git branch name and work only on that branch.
3. Confirm prerequisite evidence and milestone order.
4. Create or update `PROGRESS.md` with the active milestone.
5. Report any contradiction, missing prerequisite or environment blocker instead of silently changing scope.

Implementation rules:

- Execute milestones sequentially.
- Implement only the active milestone's approved scope.
- Run its required unit, contract, integration, invariant and regression tests.
- Record commands, results, decisions and deviations in `PROGRESS.md`.
- Stop when a gate fails or research assumptions are contradicted.
- Preserve deterministic logical-time behaviour.
- Keep external technologies behind approved ports/adapters.
- Use canonical typed contracts; do not pass arbitrary dictionaries across components.
- Do not implement proposed frontier candidates.
- Do not mark the node unlocked; validation and integration must establish that state.

When all milestones pass, prepare the evidence required by `VALIDATION_REPORT.md`. Update `ARCHITECTURE.md`, `REFERENCES.md`, `CHANGELOG.md` and `TECH_TREE.md` only as directed by the approved integration gate.
