"""M5 state owner for complete snapshots and deterministic branch continuations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from math import fsum
import random

from energy_simlab.alarms import UnsupportedIslandAlarm
from energy_simlab.balance import AlgebraicActivePowerBalance
from energy_simlab.contracts.enums import (
    AcknowledgementStatus,
    CommandKind,
    EnergizationState,
    EventPhase,
    FidelityResult,
    InterlockReason,
    OperatingMode,
    SnapshotAction,
    TraceRecordKind,
)
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    AlarmEventV1,
    CommandV1,
    FidelityEventV1,
    InterlockEventV1,
    RngSnapshotV1,
    ScenarioV1,
    SimulationConfigV1,
    SnapshotEnvelopeV1,
    SnapshotLifecycleEventV1,
    TopologyEventV1,
    TopologyRuntimeSnapshotV1,
    TraceEntryV1,
    TraceV1,
    VersionedV1,
    MacroPublicationV1,
)
from energy_simlab.control import CommandValidator, PowerController
from energy_simlab.kernel import DeterministicScheduler, KernelEvent, KernelEventKind
from energy_simlab.models.bess import (
    BessModelRegistry,
    BessParameters,
    DetailedBess,
    DetailedBessParameters,
    FallbackBess,
    FixedRatioBessRunner,
)
from energy_simlab.snapshots import SnapshotCompatibilityPolicy
from energy_simlab.topology import DeterministicTopologyService, reference_topology

from .fallback_slice import reference_configuration
from .scheduler_snapshot import scheduler_from_snapshot, scheduler_to_snapshot


RecordEncoder = Callable[[VersionedV1], bytes]
SnapshotDecoder = Callable[[bytes], SnapshotEnvelopeV1]
SnapshotEncoder = Callable[[SnapshotEnvelopeV1], bytes]


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelMacroExecution:
    child_completions: int
    mean_power_mw: float
    energy_residual_mwh: float
    coupling_residual_mwh: float


def _detailed_parameters(configuration: SimulationConfigV1) -> DetailedBessParameters:
    config = configuration
    return DetailedBessParameters(
        base=BessParameters(
            energy_nominal_mwh=config.energy_nominal_mwh,
            soc_min=config.soc_min,
            soc_max=config.soc_max,
            charge_limit_mw=config.charge_limit_mw,
            discharge_limit_mw=config.discharge_limit_mw,
        ),
        charge_efficiency=config.charge_efficiency,
        discharge_efficiency=config.discharge_efficiency,
        response_time_constant_seconds=config.response_time_constant_seconds,
        ramp_up_mw_per_second=config.ramp_up_mw_per_second,
        ramp_down_mw_per_second=config.ramp_down_mw_per_second,
    )


class ReplayRuntime:
    """One synchronous owner whose complete mutable state is captured by M5."""

    engine_name = "energy-simlab"
    engine_version = "1.0.0"
    engine_build = "tt000-m5"
    runtime_profile = "cpython-3.14.7-windows-x86_64"
    canonicalization_profile = "python-json-v1"
    excluded_infrastructure_state = (
        "asgi_pacing_task",
        "asgi_stop_event",
        "http_connections",
        "pacer_wall_clock",
        "server_sleep_history",
        "viewer_fanout_queues",
        "viewer_render_state",
        "websocket_protocol_state",
    )

    def __init__(self, *, record_encoder: RecordEncoder) -> None:
        self.record_encoder = record_encoder
        self.started = False

    @classmethod
    def new_reference(
        cls,
        *,
        record_encoder: RecordEncoder,
        scenario: ScenarioV1 | None = None,
    ) -> "ReplayRuntime":
        runtime = cls(record_encoder=record_encoder)
        configuration = reference_configuration() if scenario is None else scenario.configuration
        configuration_sha256 = sha256(record_encoder(configuration)).hexdigest()
        if scenario is None:
            scenario = ScenarioV1(
                id="TT000-REF",
                version="1.0.0",
                content_sha256=sha256(
                    b"TT000-REF-V1\0" + record_encoder(configuration)
                ).hexdigest(),
                run_id="TT000-REF-V1",
                configuration=configuration,
                scheduled_commands=(),
            )
        parameters = _detailed_parameters(configuration)
        fallback = FallbackBess(
            parameters=parameters.base,
            initial_energy_mwh=configuration.initial_soc * configuration.energy_nominal_mwh,
        )
        runtime.scenario = scenario
        runtime.configuration_sha256 = configuration_sha256
        runtime.run_id = scenario.run_id
        runtime.parent_run_id: str | None = None
        runtime.parent_snapshot_id: str | None = None
        runtime.scheduler = DeterministicScheduler()
        runtime.publication_sequence = 0
        runtime.registry = BessModelRegistry(
            fallback=fallback,
            detailed_parameters=parameters,
            macro_ticks=configuration.macro_ticks,
        )
        runtime.validator = CommandValidator()
        runtime.controller = PowerController()
        runtime.topology = reference_topology()
        runtime.alarm = UnsupportedIslandAlarm(
            threshold_mw=configuration.island_alarm_threshold_mw
        )
        runtime.rng = random.Random(configuration.seed)
        runtime.pending_ingress: list[CommandV1] = []
        runtime.trace_entries: list[TraceEntryV1] = []
        runtime.last_command_id = "NONE"
        runtime.started = True
        return runtime

    @property
    def active_model(self) -> FallbackBess | DetailedBess:
        return self.registry.active_model

    @property
    def macro_duration_seconds(self) -> float:
        config = self.scenario.configuration
        return config.base_tick_seconds * config.macro_ticks

    def _advance_scheduler_only(self, logical_tick: int) -> None:
        """Move the queue clock after semantic work; never expose as simulation advance."""

        self.scheduler.run_until(logical_tick, self._handle_kernel_event)

    def _handle_kernel_event(
        self,
        event: KernelEvent,
        _scheduler: DeterministicScheduler,
    ) -> None:
        if event.kind is KernelEventKind.PUBLICATION:
            self.publication_sequence += 1

    def _process_power_command(self, command: CommandV1) -> AcknowledgementV1:
        if command.apply_tick != self.scheduler.current_tick:
            raise ValueError("power commands execute only at the current macro boundary")
        decision = self.validator.validate_power_request(
            command,
            current_tick=command.apply_tick,
            topology_version=self.topology.topology_version,
            model=self.active_model,
            feasibility_duration_seconds=self.macro_duration_seconds,
        )
        self._append(command, TraceRecordKind.COMMAND)
        self._append(decision.acknowledgement, TraceRecordKind.ACKNOWLEDGEMENT)
        if (
            not decision.duplicate
            and decision.acknowledgement.status
            in {AcknowledgementStatus.ACCEPTED, AcknowledgementStatus.ACCEPTED_WITH_LIMIT}
        ):
            self.controller.apply_decision(command, decision)
            self.last_command_id = command.id
        return decision.acknowledgement

    def _advance_held_power_macro(self) -> ModelMacroExecution:
        """Advance all child intervals under the controller's zero-order-held target."""

        start_tick = self.scheduler.current_tick
        configuration = self.scenario.configuration
        if start_tick % configuration.macro_ticks:
            raise ValueError("model advancement requires a macro boundary")
        if isinstance(self.active_model, DetailedBess):
            reduction = FixedRatioBessRunner(
                macro_seconds=self.macro_duration_seconds,
                child_seconds=configuration.base_tick_seconds,
            ).advance_macro(self.active_model, self.controller.target_power_mw)
            execution = ModelMacroExecution(
                child_completions=reduction.child_completions,
                mean_power_mw=reduction.mean_power_mw,
                energy_residual_mwh=reduction.energy_residual_mwh,
                coupling_residual_mwh=reduction.coupling_residual_mwh,
            )
        else:
            steps = tuple(
                self.active_model.advance(
                    self.controller.target_power_mw,
                    configuration.base_tick_seconds,
                )
                for _ in range(configuration.macro_ticks)
            )
            ac_energy_mwh = fsum(item.ac_energy_mwh for item in steps)
            execution = ModelMacroExecution(
                child_completions=len(steps),
                mean_power_mw=ac_energy_mwh * 3600.0 / self.macro_duration_seconds,
                energy_residual_mwh=fsum(item.energy_residual_mwh for item in steps),
                coupling_residual_mwh=(
                    ac_energy_mwh * 3600.0 / self.macro_duration_seconds
                )
                * self.macro_duration_seconds
                / 3600.0
                - ac_energy_mwh,
            )
        self._advance_scheduler_only(start_tick + configuration.macro_ticks)
        return execution

    def _activate_detailed(self, command: CommandV1) -> FidelityEventV1:
        if command.apply_tick != self.scheduler.current_tick:
            raise ValueError("fidelity commands execute only at the current macro boundary")
        local_component = self._local_component()
        decision = self.validator.validate_action_request(
            command,
            current_tick=command.apply_tick,
            topology_version=self.topology.topology_version,
            model=self.active_model,
            expected_kind=CommandKind.ACTIVATE_DETAILED_MODEL,
            expected_target_id="BESS",
            target_available=self.registry.detailed is None
            and local_component.energization is EnergizationState.GRID_CONNECTED,
        )
        self._append(command, TraceRecordKind.COMMAND)
        self._append(decision.acknowledgement, TraceRecordKind.ACKNOWLEDGEMENT)
        if decision.acknowledgement.status is not AcknowledgementStatus.ACCEPTED:
            raise ValueError("detailed-model activation command was rejected")
        event = self.registry.activate_detailed(
            logical_tick=command.apply_tick,
            requested_power_mw=self.controller.requested_power_mw,
            accepted_power_mw=self.controller.accepted_power_mw,
            energization=local_component.energization,
            topology_version=self.topology.topology_version,
            component_id=local_component.id,
            quality=self.topology.quality,
            last_command_id=self.last_command_id,
            source_sequences=self.validator.export_source_sequences(),
            correlation_id=command.correlation_id or command.id,
            causation_id=decision.acknowledgement.id,
        )
        self._append(event, TraceRecordKind.FIDELITY)
        if event.result is not FidelityResult.SUCCEEDED:
            raise ValueError(event.detail)
        self.last_command_id = command.id
        return event

    def _open_pcc(self, command: CommandV1) -> tuple[TopologyEventV1, InterlockEventV1, AlarmEventV1]:
        acknowledgement, topology_event = self._apply_pcc_topology(command)
        interlock_event = self._apply_unsupported_island_context(
            command,
            topology_event,
        )
        alarm_event = self._evaluate_unsupported_island_alarm(
            command,
            interlock_event,
        )
        self.last_command_id = command.id
        return topology_event, interlock_event, alarm_event

    def _apply_pcc_topology(
        self,
        command: CommandV1,
    ) -> tuple[AcknowledgementV1, TopologyEventV1]:
        if command.apply_tick != self.scheduler.current_tick:
            raise ValueError("topology commands execute only at the current macro boundary")
        decision = self.validator.validate_action_request(
            command,
            current_tick=command.apply_tick,
            topology_version=self.topology.topology_version,
            model=self.active_model,
            expected_kind=CommandKind.OPEN_PCC,
            expected_target_id="PCC",
            target_available=self.topology.topology_version == 0,
        )
        self._append(command, TraceRecordKind.COMMAND)
        self._append(decision.acknowledgement, TraceRecordKind.ACKNOWLEDGEMENT)
        if decision.acknowledgement.status is not AcknowledgementStatus.ACCEPTED:
            raise ValueError("PCC-open command was rejected")

        self.topology, topology_event = DeterministicTopologyService().open_pcc(
            self.topology,
            logical_tick=command.apply_tick,
            correlation_id=command.correlation_id or command.id,
            causation_id=decision.acknowledgement.id,
        )
        self._append(topology_event, TraceRecordKind.TOPOLOGY)
        return decision.acknowledgement, topology_event

    def _apply_unsupported_island_context(
        self,
        command: CommandV1,
        topology_event: TopologyEventV1,
    ) -> InterlockEventV1:
        previous_target = self.controller.engage_safe_zero_interlock()
        previous_applied, energy_before = self.active_model.force_safe_zero(
            OperatingMode.ISLANDED_UNSUPPORTED
        )
        interlock_event = InterlockEventV1(
            id=f"INTERLOCK-EVENT-{self.topology.topology_version:08d}",
            source_id="operating-context",
            logical_tick=command.apply_tick,
            sequence=self.topology.topology_version,
            target_id="BESS",
            reason=InterlockReason.UNSUPPORTED_ISLAND_SAFE_ZERO,
            previous_target_power_mw=previous_target,
            new_target_power_mw=0.0,
            previous_applied_power_mw=previous_applied,
            new_applied_power_mw=0.0,
            energy_before_mwh=energy_before,
            energy_after_mwh=self.active_model.energy_stored_mwh,
            correlation_id=command.correlation_id or command.id,
            causation_id=topology_event.id,
            topology_version=self.topology.topology_version,
        )
        return interlock_event

    def _evaluate_unsupported_island_alarm(
        self,
        command: CommandV1,
        interlock_event: InterlockEventV1,
    ) -> AlarmEventV1:
        balance = AlgebraicActivePowerBalance().calculate(
            logical_tick=command.apply_tick,
            load_mw=self.scenario.configuration.load_mw,
            bess_ac_power_mw=0.0,
            topology=self.topology,
            correlation_id=command.correlation_id or command.id,
            causation_id=interlock_event.id,
        )
        assert balance.island_imbalance_mw is not None
        alarm_events = self.alarm.evaluate(
            islanded_unsupported=True,
            imbalance_mw=balance.island_imbalance_mw,
            logical_tick=command.apply_tick,
            correlation_id=command.correlation_id or command.id,
            causation_id=interlock_event.id,
        )
        if len(alarm_events) != 1:
            raise AssertionError("reference PCC opening must create one alarm occurrence")
        self._append(alarm_events[0], TraceRecordKind.ALARM)
        return alarm_events[0]

    def _acknowledge_alarm(self, command: CommandV1) -> tuple[AcknowledgementV1, tuple[AlarmEventV1, ...]]:
        if command.apply_tick != self.scheduler.current_tick:
            raise ValueError("alarm commands execute only at the current macro boundary")
        occurrence_id = "" if self.alarm.state is None else self.alarm.state.occurrence_id
        decision = self.validator.validate_action_request(
            command,
            current_tick=command.apply_tick,
            topology_version=self.topology.topology_version,
            model=self.active_model,
            expected_kind=CommandKind.ACKNOWLEDGE_ALARM,
            expected_target_id=occurrence_id,
            target_available=bool(occurrence_id),
        )
        self._append(command, TraceRecordKind.COMMAND)
        self._append(decision.acknowledgement, TraceRecordKind.ACKNOWLEDGEMENT)
        if decision.acknowledgement.status is not AcknowledgementStatus.ACCEPTED:
            return decision.acknowledgement, ()
        events = self.alarm.acknowledge(
            occurrence_id=occurrence_id,
            acknowledge_source_id=command.source_id,
            logical_tick=command.apply_tick,
            correlation_id=command.correlation_id or command.id,
            causation_id=decision.acknowledgement.id,
        )
        for event in events:
            self._append(event, TraceRecordKind.ALARM)
        self.last_command_id = command.id
        return decision.acknowledgement, events

    def _capture_command(
        self,
        command: CommandV1,
        *,
        snapshot_id: str,
        snapshot_encoder: SnapshotEncoder,
    ) -> tuple[AcknowledgementV1, bytes]:
        if command.apply_tick != self.scheduler.current_tick:
            raise ValueError("snapshot commands execute only at the current macro boundary")
        decision = self.validator.validate_action_request(
            command,
            current_tick=command.apply_tick,
            topology_version=self.topology.topology_version,
            model=self.active_model,
            expected_kind=CommandKind.CAPTURE_SNAPSHOT,
            expected_target_id=snapshot_id,
        )
        self._append(command, TraceRecordKind.COMMAND)
        self._append(decision.acknowledgement, TraceRecordKind.ACKNOWLEDGEMENT)
        if decision.acknowledgement.status is not AcknowledgementStatus.ACCEPTED:
            raise ValueError("snapshot command was rejected")
        self.last_command_id = command.id
        return decision.acknowledgement, self.capture_bytes(
            snapshot_id=snapshot_id,
            correlation_id=command.correlation_id or command.id,
            causation_id=decision.acknowledgement.id,
            snapshot_encoder=snapshot_encoder,
        )

    def record_publication(self, publication: MacroPublicationV1) -> None:
        if publication.run_id != self.run_id:
            raise ValueError("publication run lineage does not match the runtime")
        if publication.sequence != self.publication_sequence + 1:
            raise ValueError("publication sequence must be the next canonical value")
        self.publication_sequence = publication.sequence
        self._append(publication, TraceRecordKind.PUBLICATION)

    def capture_envelope(
        self,
        *,
        snapshot_id: str,
        correlation_id: str,
        causation_id: str,
    ) -> SnapshotEnvelopeV1:
        if self.scheduler.active_phase is not None:
            raise ValueError("snapshot capture requires a quiescent scheduler")
        if self.scheduler.current_tick % self.scenario.configuration.macro_ticks:
            raise ValueError("snapshot capture requires a macro boundary")
        self._append_snapshot_lifecycle(
            snapshot_id=snapshot_id,
            action=SnapshotAction.CAPTURED,
            correlation_id=correlation_id,
            causation_id=causation_id,
            detail="quiescent canonical snapshot captured",
        )
        observation = self.active_model.observe()
        local_component = self._local_component()
        controller_snapshot = self.controller.export_snapshot(
            receipts=self.validator.export_receipts(),
            source_sequences=self.validator.export_source_sequences(),
            acknowledgement_sequence=self.validator.acknowledgement_sequence,
        )
        return SnapshotEnvelopeV1(
            snapshot_id=snapshot_id,
            logical_tick=self.scheduler.current_tick,
            phase=EventPhase.SNAPSHOT,
            run_id=self.run_id,
            parent_run_id=self.parent_run_id,
            parent_snapshot_id=self.parent_snapshot_id,
            engine_name=self.engine_name,
            engine_version=self.engine_version,
            engine_build=self.engine_build,
            runtime_profile=self.runtime_profile,
            compatibility_range="==1.0.0",
            scenario=self.scenario,
            configuration_sha256=self.configuration_sha256,
            contract_versions=("1.0.0",),
            scheduler=scheduler_to_snapshot(
                self.scheduler.export_state(),
                publication_sequence=self.publication_sequence,
            ),
            models=self.registry.export_snapshot(
                requested_power_mw=self.controller.requested_power_mw,
                accepted_power_mw=self.controller.accepted_power_mw,
                target_power_mw=self.controller.target_power_mw,
                last_command_id=self.last_command_id,
            ),
            controller=controller_snapshot,
            topology=TopologyRuntimeSnapshotV1(
                topology=self.topology,
                local_component_id=local_component.id,
                operating_mode=observation.operating_mode,
                energization=local_component.energization,
            ),
            alarms=self.alarm.export_snapshot(),
            rng=self._rng_snapshot(),
            pending_ingress=tuple(
                sorted(
                    self.pending_ingress,
                    key=lambda item: (item.apply_tick, item.source_id, item.sequence, item.id),
                )
            ),
            trace=TraceV1(
                run_id=self.run_id,
                parent_snapshot_id=self.parent_snapshot_id,
                entries=tuple(self.trace_entries),
            ),
            canonicalization_profile=self.canonicalization_profile,
            excluded_infrastructure_state=tuple(sorted(self.excluded_infrastructure_state)),
        )

    def capture_bytes(
        self,
        *,
        snapshot_id: str,
        correlation_id: str,
        causation_id: str,
        snapshot_encoder: SnapshotEncoder,
    ) -> bytes:
        return snapshot_encoder(
            self.capture_envelope(
                snapshot_id=snapshot_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
        )

    @classmethod
    def from_envelope(
        cls,
        envelope: SnapshotEnvelopeV1,
        *,
        branch_id: str,
        record_encoder: RecordEncoder,
        compatibility_policy: SnapshotCompatibilityPolicy | None = None,
    ) -> "ReplayRuntime":
        policy = compatibility_policy or SnapshotCompatibilityPolicy()
        policy.validate(envelope)
        runtime = cls(record_encoder=record_encoder)
        parameters = _detailed_parameters(envelope.scenario.configuration)
        runtime.scenario = envelope.scenario
        runtime.configuration_sha256 = envelope.configuration_sha256
        runtime.run_id = f"{envelope.snapshot_id}:{branch_id}"
        runtime.parent_run_id = envelope.run_id
        runtime.parent_snapshot_id = envelope.snapshot_id
        runtime.scheduler = DeterministicScheduler.from_state(
            scheduler_from_snapshot(envelope.scheduler)
        )
        runtime.publication_sequence = envelope.scheduler.publication_sequence
        runtime.registry = BessModelRegistry.from_snapshot(
            envelope.models,
            detailed_parameters=parameters,
            macro_ticks=envelope.scenario.configuration.macro_ticks,
        )
        runtime.validator = CommandValidator.from_snapshot(
            receipts=envelope.controller.receipts,
            source_sequences=envelope.controller.source_sequences,
            acknowledgement_sequence=envelope.controller.acknowledgement_sequence,
        )
        runtime.controller = PowerController.from_snapshot(envelope.controller)
        runtime.topology = envelope.topology.topology
        runtime.alarm = UnsupportedIslandAlarm.from_snapshot(
            envelope.alarms,
            threshold_mw=envelope.scenario.configuration.island_alarm_threshold_mw,
        )
        runtime.rng = random.Random()
        runtime.rng.setstate(
            (
                envelope.rng.state_version,
                envelope.rng.state_values,
                envelope.rng.gaussian_next,
            )
        )
        runtime.pending_ingress = list(envelope.pending_ingress)
        runtime.trace_entries = list(envelope.trace.entries)
        active_state = next(
            item
            for item in envelope.models.model_states
            if item.model_id == envelope.models.active_model_id
        )
        runtime.last_command_id = active_state.last_command_id
        runtime.started = True
        return runtime

    def _rng_snapshot(self) -> RngSnapshotV1:
        state_version, state_values, gaussian_next = self.rng.getstate()
        return RngSnapshotV1(
            algorithm="MT19937",
            state_version=state_version,
            state_values=tuple(state_values),
            gaussian_next=gaussian_next,
        )

    def _local_component(self):
        return next(item for item in self.topology.components if "LOCAL" in item.bus_ids)

    def _append(self, record: VersionedV1, kind: TraceRecordKind) -> None:
        record_id = getattr(record, "id")
        logical_tick = getattr(record, "logical_tick")
        self.trace_entries.append(
            TraceEntryV1(
                record_kind=kind,
                record_id=record_id,
                logical_tick=logical_tick,
                sequence=len(self.trace_entries) + 1,
                payload_schema_version=record.schema_version,
                canonical_json=self.record_encoder(record).decode("utf-8"),
            )
        )

    def _append_snapshot_lifecycle(
        self,
        *,
        snapshot_id: str,
        action: SnapshotAction,
        correlation_id: str,
        causation_id: str,
        detail: str,
    ) -> None:
        sequence = (
            sum(
                entry.record_kind is TraceRecordKind.SNAPSHOT
                for entry in self.trace_entries
            )
            + 1
        )
        self._append(
            SnapshotLifecycleEventV1(
                id=f"SNAPSHOT-EVENT-{sequence:08d}",
                source_id="snapshot-service",
                logical_tick=self.scheduler.current_tick,
                sequence=sequence,
                snapshot_id=snapshot_id,
                action=action,
                correlation_id=correlation_id,
                causation_id=causation_id,
                detail=detail,
            ),
            TraceRecordKind.SNAPSHOT,
        )


class FreshRuntimeDestination:
    """Transactional restore target: failure leaves ``runtime`` unset."""

    def __init__(self) -> None:
        self.runtime: ReplayRuntime | None = None

    @property
    def started(self) -> bool:
        return self.runtime is not None

    def restore_bytes(
        self,
        payload: bytes,
        *,
        branch_id: str,
        record_encoder: RecordEncoder,
        snapshot_decoder: SnapshotDecoder,
        compatibility_policy: SnapshotCompatibilityPolicy | None = None,
    ) -> ReplayRuntime:
        envelope = snapshot_decoder(payload)
        staged = ReplayRuntime.from_envelope(
            envelope,
            branch_id=branch_id,
            record_encoder=record_encoder,
            compatibility_policy=compatibility_policy,
        )
        staged._append_snapshot_lifecycle(
            snapshot_id=envelope.snapshot_id,
            action=SnapshotAction.RESTORED,
            correlation_id=f"RESTORE-{envelope.snapshot_id}",
            causation_id=envelope.snapshot_id,
            detail="fresh runtime restored after complete compatibility validation",
        )
        self.runtime = staged
        return staged


__all__ = [
    "FreshRuntimeDestination",
    "ModelMacroExecution",
    "ReplayRuntime",
]
