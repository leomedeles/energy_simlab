# TT-000 Validation Report

## Status

Developer evidence prepared — ready for a separate validation review. No validation verdict or Gate D decision has been made.

## Verdict

Pending independent validation.

## Learning-question evidence for the reviewer

1. Logical time uses non-negative integer 0.1 s ticks and a closed eleven-phase order. The synchronous scheduler owns domain order; the optional pacer maps ticks to wall deadlines without changing `dt`, skipping, or reordering work. M1 toy evidence and M7 golden evidence produce identical canonical bytes in fast and paced modes.
2. The reference macro interval is exactly ten 0.1 s child intervals under a held target. Typed reductions expose end/mean/integral/extrema and both energy and coupling residuals. M3 tests cover exact child count, duration, analytic lag, ramp, residual, event-boundary, and 0.05 s sensitivity behaviour.
3. Fallback and detailed models share typed identity, observation, feasible-range, advancement, safe-zero, snapshot, and handoff data. Activation constructs and validates the detailed candidate before switching; M3 proves exact lineage and E/SoC/P continuity within 1e-12 and proves failed activation is atomic.
4. Frozen V1 commands, acknowledgements, telemetry, quality, topology, fidelity, interlock, alarm, publication, trace, scenario, and snapshot records preserve source sequence, logical tick, units, versions, correlation, and causation. Requested, accepted, target, and applied power remain separately owned.
5. Sorted BFS connectivity owns component/source/island labels only. `AlgebraicActivePowerBalance` separately computes grid import or the unsupported-island imbalance proxy. No voltage, frequency, stability, or power-flow result is inferred.
6. The M5 inventory captures scheduler keys/queue/tombstones/counters, active and inactive model state, controller and validator state, dedupe receipts, topology/mode, alarm occurrence/acknowledgement, RNG, pending ingress, trace/publication state, compatibility metadata, exclusions, and checksum. Fresh-runtime replay proves identical and alternative continuation.
7. HTTP/Pydantic and WebSocket/fan-out code remains in adapters. Live ingress targets only future macro boundaries and is canonically sorted before draining. Viewer queues are bounded observation state; zero/one/multiple connections and fast/slow/mixed reads leave the canonical reference trace and final snapshot byte-identical.

These are developer evidence summaries, not independent conclusions.

## Milestone and Definition-of-Done evidence

| Requirement | Developer evidence | Implementation result |
|---|---|---|
| M0 foundations | `f89c793`; V1 round trips, dependency lock/licenses, ADR-0001, boundary tests | Developer gate passed |
| M1 deterministic kernel | `a4ed9c5`; exact phase/tie/cancellation/counter/pacing tests | Developer gate passed |
| M2 fallback slice | `197fe25`; analytic energy, bounds, commands, ownership, balance/publication | Developer gate passed |
| M3 detailed model/activation | `13f118e`; analytic energy/loss/lag/ramp/residual/sensitivity/atomicity | Developer gate passed |
| M4 island/alarm | `ecd98a8`; topology-first safe-zero, imbalance/quality/correlation/lifecycle | Developer gate passed |
| M5 snapshot/replay | `323660d`; complete restore, compatibility/checksum, canonical and branch replay | Developer gate passed |
| M6 API/viewer | `bc2ef0d`; DTO/ASGI mapping, bounded loss policy, trace isolation, worker guard | Developer gate passed |
| M7 reference package | `tests/m7`, golden hashes, CLI/setup instructions, isolated locked run | Developer gate passed; validation pending |
| Node unlock/integration | Requires Gate D and integration updates | Not performed |

## Automated tests

| Test layer | Command/suite | Developer result | Evidence artifact |
|---|---|---|---|
| M7 reference | `.\.venv\Scripts\python.exe -m pytest tests/m7 -q` | 4 passed in 3.23 s | `tests/m7/` |
| Full local regression | `.\.venv\Scripts\python.exe -m pytest -q` | 180 passed in 8.22 s | `tests/m0` through `tests/m7` |
| Clean locked CPython 3.14.7 environment | install `requirements.lock`, install project `--no-deps`, then `python -m pytest -q` | 180 passed in 10.19 s; `pip check` clean | Command/result in `PROGRESS.md` |
| Static/import integrity | `.\.venv\Scripts\python.exe -m compileall -q src tests` | Passed | Command/result in `PROGRESS.md` |
| Patch integrity | `git diff --check` | Passed | Command/result in `PROGRESS.md` |

## Reference comparisons

| Behaviour | Reference | Expected/tolerance | Developer actual | Result for review |
|---|---|---|---|---|
| Detailed 1 MW discharge/charge | Approved equations, `RESEARCH_REPORT.md` §§6, 15 | E/loss within 1e-12 | Exact approved values asserted in M3 | Evidence available |
| Detailed lag | Approved exact-ZOH fixture | 0.6321205588285577 MW at 2 s; 0.8646647167633873 MW at 4 s within 1e-12 | Asserted in M3 | Evidence available |
| Multi-rate residual/sensitivity | `FEATURE_CONTEXT.md` §14 M3 | `r_E`, `r_H`, power and E bounds | All approved bounds asserted in M3 | Evidence available |
| Transition continuity | `FEATURE_CONTEXT.md` §§6.7, 14 | E/SoC/P discontinuities no greater than 1e-12 | Exact/within tolerance in M3 | Evidence available |
| Unsupported island | `FEATURE_CONTEXT.md` §§6.8, 14 | -0.6 MW proxy; uncertain/simplified quality; safe zero | Exact in M4/M7 | Evidence available |
| Suffix A golden trace | M7 scripted reference | Stable same-profile bytes | SHA-256 `ee7552f36e05b795ac76562443dbd5e205f0ddec307f2a5d38e467f9f0f5b2c4` | Evidence available |
| Snapshot at tick 90 | M7 scripted reference | Stable same-profile bytes | SHA-256 `9c7b603800faac29678256cc1d285f5caf8d3dc29030fe349be2e2a0ad640fd0` | Evidence available |
| Suffix A final snapshot | M7 scripted reference | Stable same-profile bytes | SHA-256 `b084af87407376735a1ab5b0b772943cf8296e6c1e5e6812c38cbdc121f30dc9` | Evidence available |
| Suffix B trace/final snapshot | Approved alternative continuation | Repeatable and causally divergent | Trace `0bfe2d25...a302`; snapshot `e8d0dfca...ca69` | Evidence available |

## Claim traceability

| Claim or behaviour | Research basis | Implementation | Test/evidence | Developer status |
|---|---|---|---|---|
| Stable logical event order | `RESEARCH_REPORT.md` §§2.A, 7; Lee; Python 3.14 `heapq` | `kernel/scheduler.py`, ADR-0001 | `tests/m1` | Implemented/evidenced |
| Fixed-ratio coupling and residuals | `RESEARCH_REPORT.md` §§2.B, 8, 15; FMI 3.0.2 concepts | `models/bess/multirate.py` | `tests/m3` | Implemented/evidenced |
| BESS equations/signs/limits | `RESEARCH_REPORT.md` §§2.C, 6, 15; Sandia/DOE sources listed in report §20 | `models/bess/fallback.py`, `detailed.py` | `tests/m2`, `tests/m3` | Implemented/evidenced |
| Atomic fidelity handoff | `RESEARCH_REPORT.md` §§2.D, 9 | `models/bess/registry.py` | `tests/m3/test_sensitivity_and_activation.py` | Implemented/evidenced |
| Connectivity is not power flow | `RESEARCH_REPORT.md` §§2.E, 10 | `topology/service.py`, `balance/active_power.py` | `tests/m2`, `tests/m4` | Implemented/evidenced |
| Typed control/alarm semantics | `RESEARCH_REPORT.md` §§2.F, 11; OPC UA/ISA precedents listed in report §20 | `contracts`, `control`, `alarms` | `tests/m0`, `tests/m2`, `tests/m4` | Implemented/evidenced |
| Complete canonical snapshot/replay | `RESEARCH_REPORT.md` §§2.G, 12; FMI state, Python RNG, RFC 8259 | `snapshots`, serialization/persistence adapters, replay runtime | `tests/m5`, `tests/m7` | Implemented/evidenced |
| Async viewer isolation | `RESEARCH_REPORT.md` §§2.H, 13, 14; official FastAPI/Uvicorn docs listed in report §20 | API adapter, fan-out, bootstrap, static viewer | `tests/m6`, `tests/m7` | Implemented/evidenced |

Registration of accepted references in `REFERENCES.md` is reserved for validation/integration.

## Determinism and replay

- Fast-forward and fake-wall paced executions of suffix A have identical canonical trace, tick-90 snapshot, and final snapshot bytes.
- Repeated suffix A and suffix B executions are individually byte-identical under the recorded CPython/runtime profile.
- Snapshot restore creates new run lineage and preserves the exact prefix through tick 90.
- The first branch difference is `CMD-ACK-001` versus `CMD-P-ALT-001`; suffix B's acknowledgement is `REJECTED/TARGET_MODE_UNAVAILABLE`.
- The branches retain equal final physical energy (`0.9998446478818566 MWh`) and zero applied power while alarm acknowledgement state diverges for the explicit command cause.
- Zero, one, and three viewer patterns with fast, slow, and mixed reads preserve exact trace and final snapshot bytes.

## Demonstration result

Reproduction commands are in `README.md`. The fast suffix-A command reports:

- mode `ISLANDED_UNSUPPORTED`;
- applied power `0.0 MW`;
- stored energy `0.9998446478818566 MWh`;
- alarm active/acknowledged;
- the golden trace and final-snapshot hashes listed above.

The golden trace includes commands, acknowledgements, fidelity, topology, alarm, publication, capture, and restore records with V1 versions and causal fields.

## Limitations and rejected claims

TT-000 supports aggregate active-power and usable-energy bookkeeping only within the synthetic configured bounds. It does not support or claim AC/DC power flow, voltage, frequency, current, reactive power, EMT/switching, harmonics, electrical stability, grid-forming/following controls, black start, resynchronization, fault current, protection coordination/timing, breaker travel, device-calibrated battery chemistry, thermal behaviour, degradation/SoH, auxiliaries/safety, multiple feeders, arbitrary clock ratios, adaptive stepping, FMI integration, industrial protocols, production EMS/SCADA, historian guarantees, authentication/authorization, cybersecurity, standards compliance, certification, or production suitability. PCC reclosing and detailed-to-fallback activation remain excluded.

## Deviations and corrective actions

- No approved architecture or scope deviation is recorded.
- During M0, one whitespace-sensitive documentation assertion was corrected without changing the ADR.
- During M5, a dictionary-annotation boundary test rejected the first shared phase-priority representation; it was replaced by a closed-enum function without changing order.
- During M7, the first clean-install instruction incorrectly added `--require-hashes` to a version-pinned lock that does not contain artifact hashes. The README was corrected to the actual approved install command, and the isolated install/full suite then passed.

## Recommended maturity update

No maturity update is proposed by the developer. `TECH_TREE.md` and the validated architecture ledger remain unchanged pending Gate D.

## Gate D decision

Pending separate validation review by the authorized reviewer. The developer has not approved Gate D and has not marked TT-000 validated, integrated, active, or unlocked.
