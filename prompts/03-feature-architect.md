# Prompt: Create a Node Feature Context

Use this prompt only after Gate B approves the research report.

---

You are acting as the architect agent for one researched tech-tree node in the Hierarchical Energy Co-Simulation Lab.

Read completely:

1. `MASTER_PROJECT_CONTEXT.md`
2. `NORTH_STAR.md`
3. `DEVELOPMENT_PROTOCOL.md`
4. `AGENTS.md`
5. `TECH_TREE.md`
6. `ARCHITECTURE.md`
7. `REFERENCES.md`
8. the node's approved `NODE_CONTEXT.md`
9. the node's approved `RESEARCH_REPORT.md`
10. relevant accepted ADRs

Do not implement code, create a Git branch or mark the node active or unlocked.

Create the node's `FEATURE_CONTEXT.md` with this structure:

1. Status and Gate C approval state.
2. Node identity and proposed Git branch name.
3. Learning outcomes.
4. Current architecture and prerequisite evidence.
5. Scope and explicit non-goals.
6. Selected model boundary, equations/behaviour and cited basis.
7. Units, sign conventions, time semantics and validity domain.
8. Components, package boundaries and dependency direction.
9. Canonical contracts, schema versions and ownership.
10. Clock, scheduling and event-ordering rules.
11. Persistence, snapshot and replay implications.
12. Compatibility and migration plan, if applicable.
13. Sequential milestones.
14. Required tests and gate for every milestone.
15. Deterministic reference scenario.
16. Node-specific Definition of Done.
17. Required documentation updates.
18. Risks, stop conditions and rollback strategy.
19. Candidate learning questions exposed but explicitly outside scope.

Every milestone must deliver a coherent, testable increment. Do not begin a later milestone when an earlier gate fails. Prefer replaceable interfaces around volatile tools without creating speculative abstractions around every class.

End with a Gate C checklist for human approval. The file becomes prescriptive only after that approval is recorded.
