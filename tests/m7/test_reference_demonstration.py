from __future__ import annotations

from hashlib import sha256
import json

from energy_simlab.adapters.serialization import decode_snapshot
from energy_simlab.bootstrap.demonstration import run_reference_demonstration
from energy_simlab.contracts.enums import TraceRecordKind
from energy_simlab.kernel import NoOpPacer, WallClockPacer


class FakeWallTime:
    def __init__(self) -> None:
        self.value = 1000.0

    def clock(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


def test_fast_and_paced_reference_scenario_match_exact_golden_trace_and_outcomes():
    fast = run_reference_demonstration(suffix="A", pacer=NoOpPacer())
    wall = FakeWallTime()
    paced_pacer = WallClockPacer(clock=wall.clock, sleeper=wall.sleep)
    paced = run_reference_demonstration(suffix="A", pacer=paced_pacer)

    assert fast.canonical_trace == paced.canonical_trace
    assert fast.snapshot_at_90 == paced.snapshot_at_90
    assert fast.final_snapshot == paced.final_snapshot
    assert paced_pacer.diagnostics == ()
    assert sha256(fast.canonical_trace).hexdigest() == (
        "ee7552f36e05b795ac76562443dbd5e205f0ddec307f2a5d38e467f9f0f5b2c4"
    )
    assert sha256(fast.snapshot_at_90).hexdigest() == (
        "9c7b603800faac29678256cc1d285f5caf8d3dc29030fe349be2e2a0ad640fd0"
    )
    assert sha256(fast.final_snapshot).hexdigest() == (
        "b084af87407376735a1ab5b0b772943cf8296e6c1e5e6812c38cbdc121f30dc9"
    )
    assert fast.final_operating_mode == "ISLANDED_UNSUPPORTED"
    assert fast.final_applied_power_mw == 0.0
    assert fast.final_energy_mwh == 0.9998446478818566
    assert fast.alarm_active and fast.alarm_acknowledged
    assert len(fast.publications) == 5


def test_golden_trace_has_every_required_record_family_version_and_correlation():
    result = run_reference_demonstration(suffix="A")
    kinds = {entry.record_kind for entry in result.trace.entries}
    assert {
        TraceRecordKind.COMMAND,
        TraceRecordKind.ACKNOWLEDGEMENT,
        TraceRecordKind.FIDELITY,
        TraceRecordKind.TOPOLOGY,
        TraceRecordKind.ALARM,
        TraceRecordKind.PUBLICATION,
        TraceRecordKind.SNAPSHOT,
    } <= kinds
    assert all(entry.schema_version == "1.0.0" for entry in result.trace.entries)
    assert all(entry.payload_schema_version == "1.0.0" for entry in result.trace.entries)
    payloads = [json.loads(entry.canonical_json) for entry in result.trace.entries]
    correlated = [
        payload
        for payload in payloads
        if payload.get("correlation_id") == "CMD-PCC-001"
    ]
    assert {payload["id"] for payload in correlated} >= {
        "TOPOLOGY-EVENT-00000001",
        "ALARM-EVENT-00000001",
    }
    snapshot = decode_snapshot(result.snapshot_at_90)
    assert snapshot.logical_tick == 90
    assert snapshot.alarms.states[0].active
    assert not snapshot.alarms.states[0].acknowledged


def test_alternative_suffix_is_repeatable_and_rejection_is_the_causal_divergence():
    first = run_reference_demonstration(suffix="B")
    second = run_reference_demonstration(suffix="B")
    assert first.canonical_trace == second.canonical_trace
    assert first.final_snapshot == second.final_snapshot
    assert sha256(first.canonical_trace).hexdigest() == (
        "0bfe2d25db59135006993e6a3b438ace74e3b2eef4d40ae7e0b605e9d853a302"
    )
    assert sha256(first.final_snapshot).hexdigest() == (
        "e8d0dfca3a8d96a08e56ee79e744816fbfc7835f1df42630bebb669f8029ca69"
    )
    assert first.alarm_active and not first.alarm_acknowledged
    alternative_ack = next(
        json.loads(entry.canonical_json)
        for entry in first.trace.entries
        if entry.record_kind is TraceRecordKind.ACKNOWLEDGEMENT
        and json.loads(entry.canonical_json)["command_id"] == "CMD-P-ALT-001"
    )
    assert alternative_ack["status"] == "REJECTED"
    assert alternative_ack["reason"] == "TARGET_MODE_UNAVAILABLE"
