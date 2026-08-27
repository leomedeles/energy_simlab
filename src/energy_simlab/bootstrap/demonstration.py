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
from energy_simlab.application import FreshRuntimeDestination, PowerMacroExecution, ReplayRuntime
from energy_simlab.balance import AlgebraicActivePowerBalance
from energy_simlab.contracts.enums import (
    AggregationKind,
    CommandAuthority,
    CommandKind,
    Unit,
)
from energy_simlab.contracts.ports import Pacer, PublicationSink
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    AlarmEventV1,
    CommandV1,
    DiscreteRecordV1,
    FidelityEventV1,
    InterlockEventV1,
    MacroPublicationV1,
    ScenarioV1,
    TelemetrySampleV1,
    TopologyEventV1,
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


def _publication(
    runtime: ReplayRuntime,
    *,
    interval_start_tick: int,
    discrete_records: tuple[DiscreteRecordV1, ...],
    macro: PowerMacroExecution | None = None,
) -> MacroPublicationV1:
    observation = runtime.active_model.observe()
    tick = runtime.scheduler.current_tick
    sequence = runtime.publication_sequence + 1
    balance = AlgebraicActivePowerBalance().calculate(
        logical_tick=tick,
        load_mw=runtime.scenario.configuration.load_mw,
        bess_ac_power_mw=observation.applied_power_mw,
        topology=runtime.topology,
    )
    values = (
        ("requested_power", runtime.controller.requested_power_mw, Unit.MEGAWATT),
        ("accepted_power", runtime.controller.accepted_power_mw, Unit.MEGAWATT),
        ("target_power", runtime.controller.target_power_mw, Unit.MEGAWATT),
        ("applied_power", observation.applied_power_mw, Unit.MEGAWATT),
        ("stored_energy", observation.energy_stored_mwh, Unit.MEGAWATT_HOUR),
        ("soc", observation.soc, Unit.PER_UNIT),
        ("operating_mode", observation.operating_mode.value, Unit.NONE),
        (
            "grid_import" if balance.grid_import_mw is not None else "island_imbalance",
            balance.grid_import_mw
            if balance.grid_import_mw is not None
            else balance.island_imbalance_mw,
            Unit.MEGAWATT,
        ),
    )
    telemetry = tuple(
        TelemetrySampleV1(
            id=f"TEL-REFERENCE-{sequence:04d}-{index:02d}",
            source_id="reference-publisher",
            logical_tick=tick,
            sequence=(sequence - 1) * len(values) + index,
            subject_id="PCC" if signal in {"grid_import", "island_imbalance"} else "BESS",
            signal_id=signal,
            value=value,
            unit=unit,
            aggregation=AggregationKind.END,
            interval_start_tick=interval_start_tick,
            interval_end_tick=tick,
            quality=balance.quality,
            model_id=observation.model_id,
            model_version=observation.model_version,
            topology_version=runtime.topology.topology_version,
        )
        for index, (signal, value, unit) in enumerate(values, start=1)
    )
    return MacroPublicationV1(
        id=f"PUB-REFERENCE-{sequence:08d}",
        source_id="reference-publisher",
        logical_tick=tick,
        sequence=sequence,
        run_id=runtime.run_id,
        interval_start_tick=interval_start_tick,
        interval_end_tick=tick,
        telemetry=telemetry,
        discrete_records=discrete_records,
        energy_residual_mwh=0.0 if macro is None else macro.energy_residual_mwh,
        coupling_residual_mwh=0.0 if macro is None else macro.coupling_residual_mwh,
    )


def _record_publication(
    runtime: ReplayRuntime,
    recorder: _PublicationRecorder,
    *,
    interval_start_tick: int,
    discrete_records: tuple[DiscreteRecordV1, ...],
    macro: PowerMacroExecution | None = None,
) -> None:
    publication = _publication(
        runtime,
        interval_start_tick=interval_start_tick,
        discrete_records=discrete_records,
        macro=macro,
    )
    runtime.record_publication(publication)
    recorder.publish(publication)


def _acknowledgement(runtime: ReplayRuntime, command_id: str) -> AcknowledgementV1:
    return next(
        item.acknowledgement
        for item in runtime.validator.export_receipts()
        if item.command.id == command_id
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
    runtime = ReplayRuntime.new_reference(
        record_encoder=canonical_json_bytes,
        scenario=scenario,
    )
    tick_seconds = scenario.configuration.base_tick_seconds

    pacer.wait_until(10, tick_seconds)
    macro_1 = runtime.execute_power_macro(commands["power_1"])
    _record_publication(
        runtime,
        recorder,
        interval_start_tick=10,
        discrete_records=(macro_1.acknowledgement,),
        macro=macro_1,
    )

    pacer.wait_until(30, tick_seconds)
    fidelity = runtime.activate_detailed(commands["model"])
    model_ack = _acknowledgement(runtime, commands["model"].id)
    _record_publication(
        runtime,
        recorder,
        interval_start_tick=20,
        discrete_records=(model_ack, fidelity),
    )

    pacer.wait_until(40, tick_seconds)
    macro_2 = runtime.execute_power_macro(commands["power_2"])
    _record_publication(
        runtime,
        recorder,
        interval_start_tick=40,
        discrete_records=(macro_2.acknowledgement,),
        macro=macro_2,
    )

    pacer.wait_until(80, tick_seconds)
    topology_event, interlock_event, alarm_event = runtime.open_pcc(commands["open"])
    open_ack = _acknowledgement(runtime, commands["open"].id)
    _record_publication(
        runtime,
        recorder,
        interval_start_tick=70,
        discrete_records=(open_ack, topology_event, interlock_event, alarm_event),
    )

    pacer.wait_until(90, tick_seconds)
    _, snapshot_at_90 = runtime.capture_command(
        commands["snapshot"],
        snapshot_id="S-TT000-090",
        snapshot_encoder=encode_snapshot,
    )
    restored = FreshRuntimeDestination().restore_bytes(
        snapshot_at_90,
        branch_id=suffix,
        record_encoder=canonical_json_bytes,
        snapshot_decoder=decode_snapshot,
    )

    pacer.wait_until(100, tick_seconds)
    if suffix == "A":
        suffix_ack, alarm_events = restored.acknowledge_alarm(commands["ack"])
        discrete: tuple[DiscreteRecordV1, ...] = (suffix_ack, *alarm_events)
    else:
        macro_alt = restored.execute_power_macro(commands["alternative"])
        discrete = (macro_alt.acknowledgement,)
    _record_publication(
        restored,
        recorder,
        interval_start_tick=90,
        discrete_records=discrete,
    )

    pacer.wait_until(120, tick_seconds)
    restored.run_until(120)
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
