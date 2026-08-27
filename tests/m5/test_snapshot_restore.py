from __future__ import annotations

from dataclasses import replace
import json

import pytest

from energy_simlab.adapters.serialization import (
    SnapshotIntegrityError,
    canonical_json_bytes,
    decode_snapshot,
    encode_snapshot,
)
from energy_simlab.application import FreshRuntimeDestination
from energy_simlab.contracts.enums import CommandKind
from energy_simlab.snapshots import SnapshotCompatibilityError

from .helpers import command, reference_runtime_at_90, reference_snapshot_bytes


def test_inventory_mutates_and_restores_every_declared_mutable_state_class():
    runtime, commands = reference_runtime_at_90()
    assert runtime.alarm.state is not None
    acknowledgement_command = command(
        "CMD-ACK-INVENTORY",
        sequence=5,
        tick=90,
        kind=CommandKind.ACKNOWLEDGE_ALARM,
        target_id=runtime.alarm.state.occurrence_id,
    )
    runtime.acknowledge_alarm(acknowledgement_command)
    runtime.run_until(100)
    envelope = runtime.capture_envelope(
        snapshot_id="S-TT000-INVENTORY-100",
        correlation_id="CMD-SNAP-INVENTORY",
        causation_id="CMD-SNAP-INVENTORY",
    )
    payload = encode_snapshot(envelope)

    destination = FreshRuntimeDestination()
    restored = destination.restore_bytes(
        payload,
        branch_id="INVENTORY",
        record_encoder=canonical_json_bytes,
        snapshot_decoder=decode_snapshot,
    )
    assert destination.started
    assert restored.scheduler.export_state() == runtime.scheduler.export_state()
    assert restored.publication_sequence == runtime.publication_sequence == 7
    assert restored.registry.export_snapshot(
        requested_power_mw=restored.controller.requested_power_mw,
        accepted_power_mw=restored.controller.accepted_power_mw,
        target_power_mw=restored.controller.target_power_mw,
        last_command_id=restored.last_command_id,
    ) == envelope.models
    assert {item.model_id for item in envelope.models.model_states} == {
        "bess.detailed",
        "bess.fallback",
    }
    inactive = next(item for item in envelope.models.model_states if item.model_id == "bess.fallback")
    assert inactive.applied_power_mw == 0.4
    assert restored.controller.export_snapshot(
        receipts=restored.validator.export_receipts(),
        source_sequences=restored.validator.export_source_sequences(),
        acknowledgement_sequence=restored.validator.acknowledgement_sequence,
    ) == envelope.controller
    assert restored.topology == envelope.topology.topology
    assert restored.alarm.export_snapshot() == envelope.alarms
    assert restored.alarm.state is not None and restored.alarm.state.acknowledged
    assert restored.pending_ingress == list(envelope.pending_ingress)
    assert restored.rng.getstate() == runtime.rng.getstate()
    assert restored.trace_entries[:-1] == list(envelope.trace.entries)

    scheduler_snapshot = envelope.scheduler
    assert scheduler_snapshot.insertion_sequence == 3
    assert scheduler_snapshot.source_counters[0].value == 3
    assert len(scheduler_snapshot.pending_events) == 3
    assert len(scheduler_snapshot.cancelled_event_ids) == 1
    duplicate = restored.validator.validate_power_request(
        commands["power_1"],
        current_tick=10,
        topology_version=0,
        model=restored.active_model,
        feasibility_duration_seconds=restored.macro_duration_seconds,
    )
    assert duplicate.duplicate
    assert duplicate.acknowledgement.command_id == "CMD-P-001"
    assert restored.rng.random() == runtime.rng.random()


@pytest.mark.parametrize("incompatibility", ["schema", "model", "runtime"])
def test_unknown_schema_model_or_runtime_is_rejected_before_destination_mutation(incompatibility: str):
    payload, _, _ = reference_snapshot_bytes()
    envelope = decode_snapshot(payload)
    if incompatibility == "schema":
        raw = json.loads(payload)
        raw["schema_version"] = "2.0.0"
        incompatible_payload = json.dumps(
            raw,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        expected_error = SnapshotIntegrityError
    elif incompatibility == "model":
        changed = replace(envelope.models.model_states[0], model_version="9.0.0")
        incompatible_payload = encode_snapshot(
            replace(
                envelope,
                models=replace(
                    envelope.models,
                    model_states=(changed, *envelope.models.model_states[1:]),
                ),
            )
        )
        expected_error = SnapshotCompatibilityError
    else:
        incompatible_payload = encode_snapshot(
            replace(envelope, runtime_profile="cpython-9.9-unsupported")
        )
        expected_error = SnapshotCompatibilityError

    destination = FreshRuntimeDestination()
    with pytest.raises(expected_error):
        destination.restore_bytes(
            incompatible_payload,
            branch_id="REJECTED",
            record_encoder=canonical_json_bytes,
            snapshot_decoder=decode_snapshot,
        )
    assert not destination.started
    assert destination.runtime is None


def test_checksum_corruption_is_detected():
    payload, _, _ = reference_snapshot_bytes()
    corrupted = payload.replace(b'"engine_build":"tt000-m5"', b'"engine_build":"tt000-m6"')
    assert corrupted != payload
    with pytest.raises(SnapshotIntegrityError, match="checksum"):
        decode_snapshot(corrupted)
