"""Integrated deterministic owner for complete TT-000 macro execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from energy_simlab.balance import AlgebraicActivePowerBalance
from energy_simlab.contracts.enums import (
    AggregationKind,
    CommandAuthority,
    CommandKind,
    EventPhase,
    TraceRecordKind,
    Unit,
)
from energy_simlab.contracts.ports import Pacer, PublicationSink, SnapshotStore
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
    VersionedV1,
)

from .replay_runtime import ModelMacroExecution, ReplayRuntime, SnapshotEncoder


_AUTHORITY_ORDER = {
    CommandAuthority.INTERLOCK: 1,
    CommandAuthority.SCENARIO: 2,
    CommandAuthority.OPERATOR: 3,
    CommandAuthority.SUPERVISORY: 4,
}

RecordEncoder = Callable[[VersionedV1], bytes]


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroAdvanceResult:
    interval_start_tick: int
    interval_end_tick: int
    phase_order: tuple[EventPhase, ...]
    child_completions: int
    acknowledgements: tuple[AcknowledgementV1, ...]
    publication: MacroPublicationV1
    captured_snapshots: tuple[tuple[str, bytes], ...]


class IntegratedRuntimeOwner:
    """The only operational path that advances mutable domain state."""

    def __init__(
        self,
        *,
        runtime: ReplayRuntime,
        publication_sink: PublicationSink | None = None,
        snapshot_encoder: SnapshotEncoder | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.runtime = runtime
        self.publication_sink = publication_sink
        self.snapshot_encoder = snapshot_encoder
        self.snapshot_store = snapshot_store
        self._advancing = False
        self.last_phase_order: tuple[EventPhase, ...] = ()

    @classmethod
    def new_reference(
        cls,
        *,
        record_encoder: RecordEncoder,
        scenario: ScenarioV1 | None = None,
        publication_sink: PublicationSink | None = None,
        snapshot_encoder: SnapshotEncoder | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> "IntegratedRuntimeOwner":
        return cls(
            runtime=ReplayRuntime.new_reference(
                record_encoder=record_encoder,
                scenario=scenario,
            ),
            publication_sink=publication_sink,
            snapshot_encoder=snapshot_encoder,
            snapshot_store=snapshot_store,
        )

    @property
    def current_tick(self) -> int:
        return self.runtime.scheduler.current_tick

    @property
    def macro_ticks(self) -> int:
        return self.runtime.scenario.configuration.macro_ticks

    def begin_branch(self, branch_id: str) -> None:
        """Assign branch lineage after a shared deterministic continuation prefix."""

        if self._advancing:
            raise RuntimeError("branch lineage cannot change during macro advancement")
        if not branch_id or not branch_id.strip():
            raise ValueError("branch_id must not be empty")
        if self.runtime.parent_snapshot_id is None:
            raise ValueError("branch lineage requires a runtime restored from a snapshot")
        self.runtime.run_id = f"{self.runtime.parent_snapshot_id}:{branch_id}"

    def run_until(self, logical_tick: int, *, pacer: Pacer | None = None) -> None:
        if logical_tick < self.current_tick:
            raise ValueError("run target cannot move logical time backwards")
        if logical_tick % self.macro_ticks:
            raise ValueError("run target must be an exact macro boundary")
        while self.current_tick < logical_tick:
            next_tick = self.current_tick + self.macro_ticks
            if pacer is not None:
                pacer.wait_until(
                    next_tick,
                    self.runtime.scenario.configuration.base_tick_seconds,
                )
            self.advance_one_macro()

    def advance_one_macro(
        self,
        commands: tuple[CommandV1, ...] = (),
    ) -> MacroAdvanceResult:
        if self._advancing:
            raise RuntimeError("runtime-owner macro advancement is not reentrant")
        start_tick = self.current_tick
        if start_tick % self.macro_ticks:
            raise ValueError("macro advancement requires a quiescent macro boundary")
        self._advancing = True
        phases: list[EventPhase] = []
        discrete: list[DiscreteRecordV1] = []
        acknowledgements: list[AcknowledgementV1] = []
        topology_work: list[tuple[CommandV1, TopologyEventV1]] = []
        island_work: list[tuple[CommandV1, InterlockEventV1]] = []
        try:
            boundary_commands = self._commands_for_tick(start_tick, commands=commands)

            phases.append(EventPhase.EXOGENOUS)

            phases.append(EventPhase.TOPOLOGY)
            for command in self._of_kind(boundary_commands, CommandKind.OPEN_PCC):
                acknowledgement, topology = self.runtime._apply_pcc_topology(command)
                acknowledgements.append(acknowledgement)
                discrete.extend((acknowledgement, topology))
                topology_work.append((command, topology))
                self.runtime.last_command_id = command.id

            phases.append(EventPhase.OPERATING_CONTEXT)
            for command, topology in topology_work:
                interlock = self.runtime._apply_unsupported_island_context(
                    command,
                    topology,
                )
                discrete.append(interlock)
                island_work.append((command, interlock))

            phases.append(EventPhase.FIDELITY)
            for command in self._of_kind(
                boundary_commands,
                CommandKind.ACTIVATE_DETAILED_MODEL,
            ):
                fidelity = self.runtime._activate_detailed(command)
                acknowledgement = self._acknowledgement(command.id)
                acknowledgements.append(acknowledgement)
                discrete.extend((acknowledgement, fidelity))

            phases.append(EventPhase.COMMAND)
            for command in boundary_commands:
                if command.kind is CommandKind.SET_ACTIVE_POWER:
                    acknowledgement = self.runtime._process_power_command(command)
                    acknowledgements.append(acknowledgement)
                    discrete.append(acknowledgement)
                elif command.kind is CommandKind.ACKNOWLEDGE_ALARM:
                    acknowledgement, alarm_events = self.runtime._acknowledge_alarm(command)
                    acknowledgements.append(acknowledgement)
                    discrete.extend((acknowledgement, *alarm_events))
                elif command.kind in {
                    CommandKind.OPEN_PCC,
                    CommandKind.ACTIVATE_DETAILED_MODEL,
                }:
                    continue
                elif command.kind is CommandKind.CAPTURE_SNAPSHOT:
                    raise ValueError("snapshot commands are processed at the ending SNAPSHOT phase")
                else:
                    raise ValueError(f"command kind is outside the integrated TT-000 owner: {command.kind}")

            phases.append(EventPhase.CONTROL)

            phases.append(EventPhase.MODEL_ADVANCE)
            model_execution = self.runtime._advance_held_power_macro()
            if model_execution.child_completions != self.macro_ticks:
                raise AssertionError("every uninterrupted macro must complete exactly ten child intervals")

            phases.append(EventPhase.AGGREGATION)

            phases.append(EventPhase.ALARM)
            for command, interlock in island_work:
                alarm = self.runtime._evaluate_unsupported_island_alarm(
                    command,
                    interlock,
                )
                discrete.append(alarm)

            phases.append(EventPhase.PUBLICATION)
            publication = self._publication(
                interval_start_tick=start_tick,
                discrete_records=tuple(discrete),
                model_execution=model_execution,
            )
            self.runtime.record_publication(publication)
            if self.publication_sink is not None:
                self.publication_sink.publish(publication)

            phases.append(EventPhase.SNAPSHOT)
            captured = self._capture_ending_snapshots()

            self.last_phase_order = tuple(phases)
            return MacroAdvanceResult(
                interval_start_tick=start_tick,
                interval_end_tick=self.current_tick,
                phase_order=self.last_phase_order,
                child_completions=model_execution.child_completions,
                acknowledgements=tuple(acknowledgements),
                publication=publication,
                captured_snapshots=captured,
            )
        finally:
            self._advancing = False

    def _commands_for_tick(
        self,
        logical_tick: int,
        *,
        commands: tuple[CommandV1, ...] = (),
    ) -> tuple[CommandV1, ...]:
        receipt_ids = {
            item.command.id for item in self.runtime.validator.export_receipts()
        }
        scheduled = tuple(
            command
            for command in self.runtime.scenario.scheduled_commands
            if command.apply_tick == logical_tick
            and command.kind is not CommandKind.CAPTURE_SNAPSHOT
            and command.id not in receipt_ids
        )
        admitted = tuple(
            command
            for command in self.runtime.pending_ingress
            if command.apply_tick == logical_tick
            and command.kind is not CommandKind.CAPTURE_SNAPSHOT
        )
        self.runtime.pending_ingress = [
            command
            for command in self.runtime.pending_ingress
            if not (
                command.apply_tick == logical_tick
                and command.kind is not CommandKind.CAPTURE_SNAPSHOT
            )
        ]
        combined = sorted((*scheduled, *admitted, *commands), key=self._command_key)
        unique: list[CommandV1] = []
        by_id: dict[str, CommandV1] = {}
        for command in combined:
            if command.apply_tick != logical_tick:
                raise ValueError("explicit commands must target the current macro boundary")
            previous = by_id.get(command.id)
            if previous is not None:
                if previous != command:
                    raise ValueError("a command ID cannot be reused with different content")
                continue
            by_id[command.id] = command
            unique.append(command)
        return tuple(unique)

    def _capture_ending_snapshots(self) -> tuple[tuple[str, bytes], ...]:
        tick = self.current_tick
        receipt_ids = {
            item.command.id for item in self.runtime.validator.export_receipts()
        }
        scheduled = tuple(
            command
            for command in self.runtime.scenario.scheduled_commands
            if command.apply_tick == tick
            and command.kind is CommandKind.CAPTURE_SNAPSHOT
            and command.id not in receipt_ids
        )
        admitted = tuple(
            command
            for command in self.runtime.pending_ingress
            if command.apply_tick == tick
            and command.kind is CommandKind.CAPTURE_SNAPSHOT
        )
        snapshot_commands = tuple(sorted((*scheduled, *admitted), key=self._command_key))
        if not snapshot_commands:
            return ()
        if self.snapshot_encoder is None:
            raise ValueError("snapshot command requires an injected canonical snapshot encoder")
        self.runtime.pending_ingress = [
            command
            for command in self.runtime.pending_ingress
            if not (
                command.apply_tick == tick
                and command.kind is CommandKind.CAPTURE_SNAPSHOT
            )
        ]
        captured: list[tuple[str, bytes]] = []
        for command in snapshot_commands:
            _, payload = self.runtime._capture_command(
                command,
                snapshot_id=command.target_id,
                snapshot_encoder=self.snapshot_encoder,
            )
            if self.snapshot_store is not None:
                self.snapshot_store.put(command.target_id, payload)
            captured.append((command.target_id, payload))
        return tuple(captured)

    def _publication(
        self,
        *,
        interval_start_tick: int,
        discrete_records: tuple[DiscreteRecordV1, ...],
        model_execution: ModelMacroExecution,
    ) -> MacroPublicationV1:
        runtime = self.runtime
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
            ("stored_energy", observation.energy_stored_mwh, Unit.MEGAWATT_HOUR),
            ("soc", observation.soc, Unit.PER_UNIT),
            ("applied_power", observation.applied_power_mw, Unit.MEGAWATT),
            ("operating_mode", observation.operating_mode.value, Unit.NONE),
            ("model_id", observation.model_id, Unit.NONE),
            (
                "grid_import"
                if balance.grid_import_mw is not None
                else "island_imbalance",
                balance.grid_import_mw
                if balance.grid_import_mw is not None
                else balance.island_imbalance_mw,
                Unit.MEGAWATT,
            ),
        )
        telemetry = tuple(
            TelemetrySampleV1(
                id=f"TEL-RUNTIME-{sequence:08d}-{index:02d}",
                source_id="runtime-owner",
                logical_tick=tick,
                sequence=(sequence - 1) * len(values) + index,
                subject_id=(
                    "PCC" if signal in {"grid_import", "island_imbalance"} else "BESS"
                ),
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
            id=f"PUB-RUNTIME-{sequence:08d}",
            source_id="runtime-owner",
            logical_tick=tick,
            sequence=sequence,
            run_id=runtime.run_id,
            interval_start_tick=interval_start_tick,
            interval_end_tick=tick,
            telemetry=telemetry,
            discrete_records=discrete_records,
            energy_residual_mwh=model_execution.energy_residual_mwh,
            coupling_residual_mwh=model_execution.coupling_residual_mwh,
        )

    def _acknowledgement(self, command_id: str) -> AcknowledgementV1:
        return next(
            item.acknowledgement
            for item in self.runtime.validator.export_receipts()
            if item.command.id == command_id
        )

    @staticmethod
    def _of_kind(
        commands: tuple[CommandV1, ...],
        kind: CommandKind,
    ) -> tuple[CommandV1, ...]:
        return tuple(command for command in commands if command.kind is kind)

    @staticmethod
    def _command_key(command: CommandV1) -> tuple[int, int, str, int, str]:
        return (
            command.apply_tick,
            _AUTHORITY_ORDER[command.authority],
            command.source_id,
            command.sequence,
            command.id,
        )


__all__ = ["IntegratedRuntimeOwner", "MacroAdvanceResult"]
