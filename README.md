# Hierarchical Energy Co-Simulation Lab

This repository is the documentation bootstrap for a learning-first, modular Model-in-the-Loop energy simulation laboratory.

The long-term direction is an operationally representative, open-source power-system laboratory. Development begins with deliberately simplified models and replaces or complements them with more mature implementations only when a validated learning step requires it.

No simulation code has been implemented yet. `TT-000` is the proposed first vertical slice and must pass the research and architecture gates before development begins.

## Reading order

1. [`MASTER_PROJECT_CONTEXT.md`](MASTER_PROJECT_CONTEXT.md) — project constitution and invariants.
2. [`NORTH_STAR.md`](NORTH_STAR.md) — final-boss reference system and direction of growth.
3. [`DEVELOPMENT_PROTOCOL.md`](DEVELOPMENT_PROTOCOL.md) — lifecycle for every tech-tree node.
4. [`TECH_TREE.md`](TECH_TREE.md) — live state and current frontier; initially empty.
5. [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture that actually exists; initially unimplemented.
6. [`docs/nodes/TT-000-vertical-slice-0/NODE_CONTEXT.md`](docs/nodes/TT-000-vertical-slice-0/NODE_CONTEXT.md) — proposed V0 learning charter.

Codex and other implementation agents must also read [`AGENTS.md`](AGENTS.md).

## Sources of truth

| Question | Source of truth |
|---|---|
| Why does the project exist? | `MASTER_PROJECT_CONTEXT.md` |
| What direction should maturation take? | `NORTH_STAR.md` |
| How is a new capability developed? | `DEVELOPMENT_PROTOCOL.md` |
| What has actually been unlocked? | `TECH_TREE.md` |
| What is currently implemented? | `ARCHITECTURE.md` |
| What is one selected node required to deliver? | Its `FEATURE_CONTEXT.md` |
| Why was an architectural decision made? | `docs/decisions/ADR-*.md` |

## Immediate workflow

1. Review and approve the `TT-000` learning charter.
2. Run the prepared V0 deep-research prompt.
3. Save the cited synthesis as `RESEARCH_REPORT.md`.
4. Generate and review `FEATURE_CONTEXT.md`.
5. Only then create the implementation branch and write code.

The tech tree is not a frozen roadmap. It is populated after validated integrations and proposes only the nearby frontier revealed by the current system.
