from __future__ import annotations

from energy_simlab.adapters.api import BoundedViewerFanout
from energy_simlab.adapters.persistence import InMemoryPublicationSink
from energy_simlab.adapters.serialization import canonical_json_bytes
from energy_simlab.application import ReplayRuntime
from energy_simlab.contracts.enums import CommandKind
from energy_simlab.contracts.records import TraceV1

from tests.m5.helpers import command

from .helpers import publication


def run_with_viewers(viewer_count: int, drain_pattern: str) -> tuple[bytes, int]:
    runtime = ReplayRuntime.new_reference(record_encoder=canonical_json_bytes)
    evidence = InMemoryPublicationSink()
    fanout = BoundedViewerFanout(encoder=canonical_json_bytes, evidence_sink=evidence)
    viewers = [fanout.connect(f"viewer-{index}") for index in range(viewer_count)]
    commands = (
        command("CMD-P-001", sequence=1, tick=10, kind=CommandKind.SET_ACTIVE_POWER, target_id="BESS", value_mw=0.4),
        command("CMD-M-001", sequence=2, tick=30, kind=CommandKind.ACTIVATE_DETAILED_MODEL, target_id="BESS"),
        command("CMD-P-002", sequence=3, tick=40, kind=CommandKind.SET_ACTIVE_POWER, target_id="BESS", value_mw=-1.0),
        command("CMD-PCC-001", sequence=4, tick=80, kind=CommandKind.OPEN_PCC, target_id="PCC"),
    )
    actions = (
        runtime.execute_power_command,
        runtime.activate_detailed,
        runtime.execute_power_command,
        runtime.open_pcc,
    )
    for index, (action, item) in enumerate(zip(actions, commands, strict=True), start=1):
        action(item)
        fanout.publish(publication(index, discrete=index in {2, 4}))
        if drain_pattern == "fast":
            for viewer in viewers:
                viewer.pop_nowait()
        elif drain_pattern == "mixed" and index % 2 == 0:
            for viewer in viewers[::2]:
                while viewer.queued_count:
                    viewer.pop_nowait()
    trace = TraceV1(run_id=runtime.run_id, parent_snapshot_id=None, entries=tuple(runtime.trace_entries))
    return canonical_json_bytes(trace), len(evidence.publications)


def test_zero_one_multiple_viewers_and_read_rates_do_not_change_canonical_domain_trace():
    zero = run_with_viewers(0, "none")
    one_fast = run_with_viewers(1, "fast")
    one_slow = run_with_viewers(1, "none")
    multiple_mixed = run_with_viewers(3, "mixed")
    assert zero[0] == one_fast[0] == one_slow[0] == multiple_mixed[0]
    assert zero[1] == one_fast[1] == one_slow[1] == multiple_mixed[1] == 4
