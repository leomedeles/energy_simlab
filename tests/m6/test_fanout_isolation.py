from __future__ import annotations

from energy_simlab.adapters.api import BoundedViewerFanout
from energy_simlab.adapters.persistence import InMemoryPublicationSink
from energy_simlab.adapters.serialization import canonical_json_bytes, parse_json_bytes
from energy_simlab.contracts.records import MacroPublicationV1

from .helpers import publication


def test_websocket_frame_carries_logical_sequence_and_contract_version_fields():
    fanout = BoundedViewerFanout(encoder=canonical_json_bytes)
    viewer = fanout.connect("viewer-schema")
    expected = publication(1)
    fanout.publish(expected)
    frame = viewer.pop_nowait()
    assert frame.logical_tick == expected.logical_tick
    assert frame.sequence == expected.sequence
    assert frame.schema_version == "1.0.0"
    assert parse_json_bytes(MacroPublicationV1, frame.canonical_bytes) == expected


def test_queue_capacity_is_64_and_slow_telemetry_coalesces_to_latest_per_signal():
    evidence = InMemoryPublicationSink()
    fanout = BoundedViewerFanout(encoder=canonical_json_bytes, evidence_sink=evidence)
    viewer = fanout.connect("slow-telemetry")
    for sequence in range(1, 65):
        signal = "applied_power" if sequence % 2 == 0 else "stored_energy"
        fanout.publish(publication(sequence, signal_id=signal))
    assert viewer.capacity == 64
    assert viewer.queued_count == 64

    fanout.publish(publication(65, signal_id="stored_energy"))
    assert viewer.connected
    assert viewer.queued_count == 1
    coalesced = viewer.pop_nowait().publication
    latest = {sample.signal_id: sample.value for sample in coalesced.telemetry}
    assert latest == {"applied_power": 64.0, "stored_energy": 65.0}
    assert fanout.viewer_dropped_publications_total == 64
    assert len(evidence.publications) == 65


def test_discrete_overflow_disconnects_for_resynchronization_without_affecting_lossless_sink():
    evidence = InMemoryPublicationSink()
    fanout = BoundedViewerFanout(encoder=canonical_json_bytes, evidence_sink=evidence)
    viewer = fanout.connect("slow-discrete")
    for sequence in range(1, 66):
        fanout.publish(publication(sequence, discrete=True))
    assert not viewer.connected
    assert viewer.disconnect_reason == "SLOW_VIEWER_RESYNC_REQUIRED"
    assert viewer.queued_count == 64
    assert len(evidence.publications) == 65
    assert fanout.viewer_dropped_publications_total == 0
