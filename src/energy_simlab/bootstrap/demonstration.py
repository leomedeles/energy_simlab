"""Deterministic TT-000 reference scenario and branching continuations."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json

from energy_simlab.adapters.serialization import (
    canonical_json_bytes,
    decode_snapshot,
    encode_snapshot,
)
from energy_simlab.adapters.persistence import InMemorySnapshotStore
from energy_simlab.application import FreshRuntimeDestination, IntegratedRuntimeOwner
from energy_simlab.contracts.enums import (
    CommandAuthority,
    CommandKind,
    Unit,
)
from energy_simlab.contracts.ports import Pacer, PublicationSink
from energy_simlab.contracts.records import (
    CommandV1,
    MacroPublicationV1,
    ScenarioV1,
    TraceV1,
)
from energy_simlab.kernel import NoOpPacer, WallClockPacer


@dataclass(frozen=True, slots=True, kw_only=True)
class ReferenceDemonstrationResult:
    suffix: str
    snapshot_at_90: bytes
    final_snapshot: bytes
    trace: TraceV1
    canonical_trace: bytes
    publications: tuple[MacroPublicationV1, ...]
    final_energy_mwh: float
    final_applied_power_mw: float
    final_operating_mode: str
    alarm_active: bool
    alarm_acknowledged: bool


class _PublicationRecorder:
    def __init__(self, downstream: PublicationSink | None) -> None:
        self.downstream = downstream
        self.publications: list[MacroPublicationV1] = []

    def publish(self, publication: MacroPublicationV1) -> None:
        self.publications.append(publication)
        if self.downstream is not None:
            self.downstream.publish(publication)


def _command(
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
        reason="approved TT-000 reference input",
    )


def reference_commands() -> dict[str, CommandV1]:
    occurrence_id = "OCC-UNSUPPORTED-ISLAND-00000001"
    return {
        "power_1": _command(
            "CMD-P-001",
            sequence=1,
            tick=10,
            kind=CommandKind.SET_ACTIVE_POWER,
            target_id="BESS",
            value_mw=0.4,
        ),
        "model": _command(
            "CMD-M-001",
            sequence=2,
            tick=30,
            kind=CommandKind.ACTIVATE_DETAILED_MODEL,
            target_id="BESS",
        ),
        "power_2": _command(
            "CMD-P-002",
            sequence=3,
            tick=40,
            kind=CommandKind.SET_ACTIVE_POWER,
            target_id="BESS",
            value_mw=-1.0,
        ),
        "open": _command(
            "CMD-PCC-001",
            sequence=4,
            tick=80,
            kind=CommandKind.OPEN_PCC,
            target_id="PCC",
        ),
        "snapshot": _command(
            "CMD-SNAP-001",
            sequence=5,
            tick=90,
            kind=CommandKind.CAPTURE_SNAPSHOT,
            target_id="S-TT000-090",
        ),
        "ack": _command(
            "CMD-ACK-001",
            sequence=6,
            tick=100,
            kind=CommandKind.ACKNOWLEDGE_ALARM,
            target_id=occurrence_id,
        ),
        "alternative": _command(
            "CMD-P-ALT-001",
            sequence=1,
            tick=100,
            kind=CommandKind.SET_ACTIVE_POWER,
            target_id="BESS",
            value_mw=0.3,
            source_id="operator",
        ),
    }


def _scenario(commands: dict[str, CommandV1]) -> ScenarioV1:
    from energy_simlab.application import reference_configuration

    configuration = reference_configuration()
    scheduled = tuple(
        commands[key] for key in ("power_1", "model", "power_2", "open", "snapshot")
    )
    content = b"\0".join(
        (canonical_json_bytes(configuration), *(canonical_json_bytes(item) for item in scheduled))
    )
    return ScenarioV1(
        id="TT000-REF",
        version="1.0.0",
        content_sha256=sha256(content).hexdigest(),
        run_id="TT000-REF-V1",
        configuration=configuration,
        scheduled_commands=scheduled,
    )


def run_reference_demonstration(
    *,
    suffix: str = "A",
    pacer: Pacer | None = None,
    publication_sink: PublicationSink | None = None,
) -> ReferenceDemonstrationResult:
    if suffix not in {"A", "B"}:
        raise ValueError("reference suffix must be A or B")
    commands = reference_commands()
    scenario = _scenario(commands)
    pacer = pacer or NoOpPacer()
    recorder = _PublicationRecorder(publication_sink)
    snapshot_store = InMemorySnapshotStore()
    owner = IntegratedRuntimeOwner.new_reference(
        record_encoder=canonical_json_bytes,
        scenario=scenario,
        publication_sink=recorder,
        snapshot_encoder=encode_snapshot,
        snapshot_store=snapshot_store,
    )
    tick_seconds = scenario.configuration.base_tick_seconds

    owner.run_until(90, pacer=pacer)
    snapshot_at_90 = snapshot_store.get("S-TT000-090")
    restored = FreshRuntimeDestination().restore_bytes(
        snapshot_at_90,
        branch_id="PRE-BRANCH",
        record_encoder=canonical_json_bytes,
        snapshot_decoder=decode_snapshot,
    )
    owner = IntegratedRuntimeOwner(
        runtime=restored,
        publication_sink=recorder,
        snapshot_encoder=encode_snapshot,
        snapshot_store=snapshot_store,
    )

    owner.run_until(100, pacer=pacer)
    owner.begin_branch(suffix)
    pacer.wait_until(110, tick_seconds)
    if suffix == "A":
        owner.advance_one_macro((commands["ack"],))
    else:
        owner.advance_one_macro((commands["alternative"],))
    owner.run_until(120, pacer=pacer)
    final_snapshot = restored.capture_bytes(
        snapshot_id=f"S-TT000-{suffix}-120",
        correlation_id=f"END-{suffix}",
        causation_id=commands["ack" if suffix == "A" else "alternative"].id,
        snapshot_encoder=encode_snapshot,
    )
    trace = TraceV1(
        run_id=restored.run_id,
        parent_snapshot_id=restored.parent_snapshot_id,
        entries=tuple(restored.trace_entries),
    )
    observation = restored.active_model.observe()
    alarm_state = restored.alarm.state
    assert alarm_state is not None
    return ReferenceDemonstrationResult(
        suffix=suffix,
        snapshot_at_90=snapshot_at_90,
        final_snapshot=final_snapshot,
        trace=trace,
        canonical_trace=canonical_json_bytes(trace),
        publications=tuple(recorder.publications),
        final_energy_mwh=observation.energy_stored_mwh,
        final_applied_power_mw=observation.applied_power_mw,
        final_operating_mode=observation.operating_mode.value,
        alarm_active=alarm_state.active,
        alarm_acknowledged=alarm_state.acknowledged,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the approved TT-000 reference scenario")
    parser.add_argument("--mode", choices=("fast", "paced"), default="fast")
    parser.add_argument("--suffix", choices=("A", "B"), default="A")
    parser.add_argument("--trace", action="store_true", help="print the full canonical trace")
    args = parser.parse_args(argv)
    pacer: Pacer = NoOpPacer() if args.mode == "fast" else WallClockPacer()
    result = run_reference_demonstration(suffix=args.suffix, pacer=pacer)
    if args.trace:
        print(result.canonical_trace.decode("utf-8"))
    else:
        print(
            json.dumps(
                {
                    "alarm_acknowledged": result.alarm_acknowledged,
                    "alarm_active": result.alarm_active,
                    "final_applied_power_mw": result.final_applied_power_mw,
                    "final_energy_mwh": result.final_energy_mwh,
                    "final_operating_mode": result.final_operating_mode,
                    "final_snapshot_sha256": sha256(result.final_snapshot).hexdigest(),
                    "suffix": result.suffix,
                    "trace_sha256": sha256(result.canonical_trace).hexdigest(),
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ReferenceDemonstrationResult",
    "reference_commands",
    "run_reference_demonstration",
]
