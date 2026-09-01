from __future__ import annotations

from energy_simlab.adapters.serialization import (
    canonical_json_bytes,
    decode_snapshot,
    encode_snapshot,
)
from energy_simlab.application import FreshRuntimeDestination, IntegratedRuntimeOwner
from energy_simlab.contracts.enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    CommandKind,
)

from .helpers import command, reference_snapshot_bytes


def restore(payload: bytes, branch_id: str):
    return FreshRuntimeDestination().restore_bytes(
        payload,
        branch_id=branch_id,
        record_encoder=canonical_json_bytes,
        snapshot_decoder=decode_snapshot,
    )


def run_suffix_a(payload: bytes) -> tuple[bytes, object]:
    runtime = restore(payload, "PRE-BRANCH")
    owner = IntegratedRuntimeOwner(runtime=runtime)
    assert runtime.alarm.state is not None
    owner.run_until(100)
    owner.begin_branch("A")
    result = owner.advance_one_macro(
        (
            command(
            "CMD-ACK-001",
            sequence=5,
            tick=100,
            kind=CommandKind.ACKNOWLEDGE_ALARM,
            target_id=runtime.alarm.state.occurrence_id,
            ),
        )
    )
    acknowledgement = result.acknowledgements[0]
    assert acknowledgement.status is AcknowledgementStatus.ACCEPTED
    runtime.rng.random()
    owner.run_until(120)
    final = runtime.capture_bytes(
        snapshot_id="S-TT000-A-120",
        correlation_id="END-A",
        causation_id="CMD-ACK-001",
        snapshot_encoder=encode_snapshot,
    )
    return final, runtime


def run_suffix_b(payload: bytes) -> tuple[bytes, object]:
    runtime = restore(payload, "PRE-BRANCH")
    owner = IntegratedRuntimeOwner(runtime=runtime)
    owner.run_until(100)
    owner.begin_branch("B")
    result = owner.advance_one_macro(
        (
            command(
                "CMD-P-ALT-001",
                sequence=1,
                tick=100,
                kind=CommandKind.SET_ACTIVE_POWER,
                target_id="BESS",
                value_mw=0.3,
                source_id="operator",
            ),
        )
    )
    acknowledgement = result.acknowledgements[0]
    assert acknowledgement.status is AcknowledgementStatus.REJECTED
    assert acknowledgement.reason is AcknowledgementReason.TARGET_MODE_UNAVAILABLE
    runtime.rng.random()
    owner.run_until(120)
    final = runtime.capture_bytes(
        snapshot_id="S-TT000-B-120",
        correlation_id="END-B",
        causation_id="CMD-P-ALT-001",
        snapshot_encoder=encode_snapshot,
    )
    return final, runtime


def test_canonical_snapshot_is_independent_of_map_insertion_and_heap_backing_order():
    payload, _, _ = reference_snapshot_bytes()
    left = restore(payload, "CANONICAL")
    right = restore(payload, "CANONICAL")

    left.scheduler._queue.reverse()
    left.validator._receipts = dict(reversed(tuple(left.validator._receipts.items())))
    left.validator._source_sequences = dict(
        reversed(tuple(left.validator._source_sequences.items()))
    )
    left.pending_ingress.reverse()

    left_bytes = left.capture_bytes(
        snapshot_id="S-CANONICAL",
        correlation_id="CANONICAL",
        causation_id="CANONICAL",
        snapshot_encoder=encode_snapshot,
    )
    right_bytes = right.capture_bytes(
        snapshot_id="S-CANONICAL",
        correlation_id="CANONICAL",
        causation_id="CANONICAL",
        snapshot_encoder=encode_snapshot,
    )
    assert left_bytes == right_bytes


def test_identical_and_alternative_continuations_are_exact_and_causally_diverge():
    payload, _, _ = reference_snapshot_bytes()
    source = decode_snapshot(payload)
    prefix = source.trace.entries

    final_a_1, branch_a_1 = run_suffix_a(payload)
    final_a_2, branch_a_2 = run_suffix_a(payload)
    assert final_a_1 == final_a_2
    assert branch_a_1.trace_entries == branch_a_2.trace_entries
    assert branch_a_1.trace_entries[: len(prefix)] == list(prefix)
    assert branch_a_1.alarm.state is not None and branch_a_1.alarm.state.acknowledged

    final_b_1, branch_b_1 = run_suffix_b(payload)
    final_b_2, branch_b_2 = run_suffix_b(payload)
    assert final_b_1 == final_b_2
    assert branch_b_1.trace_entries == branch_b_2.trace_entries
    assert branch_b_1.trace_entries[: len(prefix)] == list(prefix)
    assert branch_b_1.alarm.state is not None and not branch_b_1.alarm.state.acknowledged

    suffix_a = branch_a_1.trace_entries[len(prefix) :]
    suffix_b = branch_b_1.trace_entries[len(prefix) :]
    first_difference = next(
        index for index, pair in enumerate(zip(suffix_a, suffix_b, strict=True)) if pair[0] != pair[1]
    )
    assert suffix_a[:first_difference] == suffix_b[:first_difference]
    assert suffix_a[first_difference].record_id == "CMD-ACK-001"
    assert suffix_b[first_difference].record_id == "CMD-P-ALT-001"
    assert '"reason":"TARGET_MODE_UNAVAILABLE"' in suffix_b[first_difference + 1].canonical_json
    assert decode_snapshot(final_a_1).rng != source.rng
    assert decode_snapshot(final_b_1).rng == decode_snapshot(final_a_1).rng
