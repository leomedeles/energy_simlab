from __future__ import annotations

from energy_simlab.adapters.serialization import canonical_json_bytes, encode_snapshot
from energy_simlab.application import ReplayRuntime
from energy_simlab.contracts.enums import (
    CommandAuthority,
    CommandKind,
    EventPhase,
    Unit,
)
from energy_simlab.contracts.records import CommandV1
from energy_simlab.kernel import KernelEventKind


def command(
    command_id: str,
    *,
    sequence: int,
    tick: int,
    kind: CommandKind,
    target_id: str,
    value_mw: float | None = None,
    source_id: str = "scenario",
) -> CommandV1:
    return CommandV1(
        id=command_id,
        source_id=source_id,
        logical_tick=tick,
        sequence=sequence,
        target_id=target_id,
        kind=kind,
        authority=(
            CommandAuthority.SCENARIO
            if source_id == "scenario"
            else CommandAuthority.OPERATOR
        ),
        apply_tick=tick,
        expiry_tick=tick,
        requested_value=value_mw,
        unit=Unit.MEGAWATT if value_mw is not None else Unit.NONE,
        correlation_id=command_id,
    )


def reference_runtime_at_90() -> tuple[ReplayRuntime, dict[str, CommandV1]]:
    runtime = ReplayRuntime.new_reference(record_encoder=canonical_json_bytes)
    commands = {
        "power_1": command(
            "CMD-P-001",
            sequence=1,
            tick=10,
            kind=CommandKind.SET_ACTIVE_POWER,
            target_id="BESS",
            value_mw=0.4,
        ),
        "model": command(
            "CMD-M-001",
            sequence=2,
            tick=30,
            kind=CommandKind.ACTIVATE_DETAILED_MODEL,
            target_id="BESS",
        ),
        "power_2": command(
            "CMD-P-002",
            sequence=3,
            tick=40,
            kind=CommandKind.SET_ACTIVE_POWER,
            target_id="BESS",
            value_mw=-1.0,
        ),
        "open": command(
            "CMD-PCC-001",
            sequence=4,
            tick=80,
            kind=CommandKind.OPEN_PCC,
            target_id="PCC",
        ),
    }
    runtime.execute_power_command(commands["power_1"])
    runtime.activate_detailed(commands["model"])
    runtime.execute_power_command(commands["power_2"])
    runtime.open_pcc(commands["open"])

    cancelled = runtime.scheduler.schedule(
        logical_tick=200,
        phase=EventPhase.COMMAND,
        source_order=2,
        source_id="snapshot-fixture",
        kind=KernelEventKind.TOY,
        subject_id="CANCELLED-FUTURE-WORK",
    )
    runtime.scheduler.schedule(
        logical_tick=200,
        phase=EventPhase.TOPOLOGY,
        source_order=1,
        source_id="snapshot-fixture",
        kind=KernelEventKind.TOY,
        subject_id="EARLIER-PHASE-FUTURE-WORK",
    )
    runtime.scheduler.schedule(
        logical_tick=210,
        phase=EventPhase.PUBLICATION,
        source_order=1,
        source_id="snapshot-fixture",
        kind=KernelEventKind.PUBLICATION,
        subject_id="FUTURE-PUBLICATION",
    )
    assert runtime.scheduler.cancel(cancelled.id)
    runtime.publication_sequence = 7
    runtime.pending_ingress.append(
        command(
            "CMD-PENDING-001",
            sequence=1,
            tick=120,
            kind=CommandKind.SET_ACTIVE_POWER,
            target_id="BESS",
            value_mw=0.2,
            source_id="operator",
        )
    )
    runtime.rng.gauss(0.0, 1.0)
    runtime.run_until(90)
    return runtime, commands


def reference_snapshot_bytes() -> tuple[bytes, ReplayRuntime, dict[str, CommandV1]]:
    runtime, commands = reference_runtime_at_90()
    payload = runtime.capture_bytes(
        snapshot_id="S-TT000-090",
        correlation_id="CMD-SNAP-001",
        causation_id="CMD-SNAP-001",
        snapshot_encoder=encode_snapshot,
    )
    return payload, runtime, commands
