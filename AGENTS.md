# Agent Operating Rules

## 1. Required reading order

Before planning or changing code, read completely:

1. `MASTER_PROJECT_CONTEXT.md`
2. `NORTH_STAR.md`
3. `DEVELOPMENT_PROTOCOL.md`
4. `TECH_TREE.md`
5. `ARCHITECTURE.md`
6. the selected node's `NODE_CONTEXT.md`
7. its `RESEARCH_REPORT.md`
8. its approved `FEATURE_CONTEXT.md`
9. its current `PROGRESS.md`

If a required artifact for the current stage is absent or explicitly blocked, stop at that gate instead of inventing it implicitly while implementing.

## 2. Stage separation

### Research stage

Do not write implementation code. Produce cited evidence, distinguish fact from inference and identify unresolved decisions.

### Architect stage

Do not write implementation code. Generate `FEATURE_CONTEXT.md`, including model boundaries, interfaces, milestones, tests, migration needs and Definition of Done.

### Developer stage

Implement only the approved feature context, sequentially by milestone. Do not silently redesign the north star, expand the node or implement speculative frontier candidates.

### Validation stage

Evaluate the delivered behaviour and evidence against the approved context. Do not mark a node unlocked merely because code exists.

## 3. Git isolation

- Never commit directly to `main`.
- Work on the branch named in the approved `FEATURE_CONTEXT.md`.
- Keep unrelated user changes intact.
- Do not use destructive Git operations to solve conflicts.
- Separate behaviour-preserving preparation from behaviour-changing commits where practical.

## 4. Schema and boundary rules

- Import canonical inter-component schemas from the designated contracts package.
- Do not pass arbitrary dictionaries across component boundaries.
- Do not leak objects from external libraries across adapter boundaries.
- Keep physics and controllers independent of UI, database and protocol frameworks.
- Make units, sign conventions, time bases, quality and source identity explicit.
- Version persistent and external contracts.

## 5. Time and concurrency rules

- Preserve deterministic logical-time ordering.
- Keep the simulation kernel synchronous unless an approved design explicitly changes its scheduling semantics.
- Use asynchronous execution for external I/O without allowing arrival order to become accidental simulation truth.
- Inject clocks and random-number generators.
- A viewer connection, frame rate or zoom action must not silently alter physical behaviour.

## 6. Milestone discipline

For each milestone:

1. Confirm its prerequisites.
2. Implement only its defined scope.
3. Run its tests and applicable regressions.
4. Record evidence in `PROGRESS.md`.
5. Stop on failure or contradicted assumptions.
6. Begin the next milestone only after the current gate passes.

## 7. Claims and validation

- Never present plausible output as validated output.
- Preserve citations from model assumptions to validation evidence.
- State unsupported phenomena and operating ranges.
- Do not claim standards compliance, interoperability, protection-grade timing or production suitability without evidence defined in the feature context.
- Numerical changes from model upgrades require tolerance-based or reference-based validation.

## 8. Tech-tree updates

`TECH_TREE.md` is a live state document, not a predetermined roadmap.

After validated integration:

- record only capabilities supported by evidence;
- reassess affected realms;
- propose nearby non-binding candidates based on revealed gaps;
- keep proposals to one to three per relevant realm;
- do not assign permanent IDs or milestones to unselected candidates;
- remove obsolete proposals.

## 9. Architecture and stack evolution

When maturity requires refactoring or replacement:

- classify the change correctly;
- characterize current behaviour first;
- introduce a seam before replacing technology;
- preserve stable contracts where possible;
- use parallel or differential execution where useful;
- provide migration and rollback paths;
- update or create an ADR;
- retain old fidelity models when they remain educationally useful.

## 10. Completion

A node may be marked complete only after its approved Definition of Done, validation report, documentation updates and retrospective are complete. The developer may propose the next frontier but may not select or start it automatically.
