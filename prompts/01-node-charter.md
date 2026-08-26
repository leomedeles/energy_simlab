# Prompt: Create a Tech-Tree Node Learning Charter

Use this prompt after selecting a non-binding candidate from `TECH_TREE.md`.

---

You are acting as the learning-charter agent for the Hierarchical Energy Co-Simulation Lab.

Read completely:

1. `MASTER_PROJECT_CONTEXT.md`
2. `NORTH_STAR.md`
3. `DEVELOPMENT_PROTOCOL.md`
4. `TECH_TREE.md`
5. `ARCHITECTURE.md`
6. all accepted ADRs relevant to the candidate

Selected candidate: `<candidate title and realm>`

Do not perform deep research, select implementation libraries, create milestones or write code.

Create `docs/nodes/<proposed-node>/NODE_CONTEXT.md` containing:

- proposed node ID and title;
- status `proposed — awaiting Gate A approval`;
- affected realms;
- satisfied prerequisites with evidence links;
- current-system limitation;
- three to seven precise learning questions;
- intended capability after completion;
- explanation of the north-star vector;
- scope;
- explicit non-goals;
- expected demonstration expressed as observable behaviour;
- expected validation types;
- unknowns that research must resolve;
- risks of implementing the node too early;
- potential cross-realm effects.

Keep engineering decisions as hypotheses until research supports them. End with a Gate A checklist requiring human approval of the learning questions and boundaries.
