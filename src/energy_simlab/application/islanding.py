"""Topology-first unsupported-island transition for M4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from energy_simlab.alarms import UnsupportedIslandAlarm
from energy_simlab.balance import AlgebraicActivePowerBalance
from energy_simlab.contracts.enums import (
    AcknowledgementStatus,
    CommandKind,
    EnergizationState,
    InterlockReason,
    OperatingMode,
)
from energy_simlab.contracts.ports import BessPowerModel
from energy_simlab.contracts.records import (
    ActivePowerBalanceV1,
    AlarmEventV1,
    AlarmStateV1,
    AcknowledgementV1,
    CommandV1,
    InterlockEventV1,
    TopologyEventV1,
    TopologySnapshotV1,
)
from energy_simlab.control import CommandValidator, PowerController
from energy_simlab.topology import DeterministicTopologyService


class IslandableBess(BessPowerModel, Protocol):
    energy_stored_mwh: float
    applied_power_mw: float

    def force_safe_zero(self, operating_mode: OperatingMode) -> tuple[float, float]: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class IslandTransitionResult:
    topology: TopologySnapshotV1
    topology_event: TopologyEventV1
    interlock_event: InterlockEventV1
    simultaneous_power_acknowledgement: AcknowledgementV1
    balance: ActivePowerBalanceV1
    alarm_events: tuple[AlarmEventV1, ...]
    alarm_state: AlarmStateV1


class IslandTransitionCoordinator:
    def __init__(
        self,
        *,
        model: IslandableBess,
        controller: PowerController,
        topology: TopologySnapshotV1,
        load_mw: float = 0.6,
        feasibility_duration_seconds: float = 1.0,
        validator: CommandValidator | None = None,
    ) -> None:
        self.model = model
        self.controller = controller
        self.topology = topology
        self.load_mw = load_mw
        self.feasibility_duration_seconds = feasibility_duration_seconds
        self.validator = validator or CommandValidator()
        self.topology_service = DeterministicTopologyService()
        self.balance_service = AlgebraicActivePowerBalance()
        self.alarm = UnsupportedIslandAlarm()
        self._interlock_sequence = 0

    def open_pcc(
        self,
        *,
        open_command: CommandV1,
        simultaneous_power_command: CommandV1,
    ) -> IslandTransitionResult:
        logical_tick = open_command.apply_tick
        if open_command.kind is not CommandKind.OPEN_PCC or open_command.target_id != "PCC":
            raise ValueError("open_pcc requires an OPEN_PCC command targeting PCC")
        if simultaneous_power_command.apply_tick != logical_tick:
            raise ValueError("the M4 simultaneous command must share the PCC-open tick")

        updated_topology, topology_event = self.topology_service.open_pcc(
            self.topology,
            logical_tick=logical_tick,
            correlation_id=open_command.id,
            causation_id=open_command.id,
        )
        self.topology = updated_topology
        local_component = next(
            component for component in updated_topology.components if "LOCAL" in component.bus_ids
        )
        if local_component.energization is not EnergizationState.ISLANDED_UNSUPPORTED:
            raise AssertionError("PCC opening did not derive the approved unsupported-island context")

        previous_target = self.controller.engage_safe_zero_interlock()
        previous_applied, energy_before = self.model.force_safe_zero(
            OperatingMode.ISLANDED_UNSUPPORTED
        )
        energy_after = self.model.energy_stored_mwh
        self._interlock_sequence += 1
        interlock_event = InterlockEventV1(
            id=f"INTERLOCK-EVENT-{self._interlock_sequence:08d}",
            source_id="operating-context",
            logical_tick=logical_tick,
            sequence=self._interlock_sequence,
            target_id="BESS",
            reason=InterlockReason.UNSUPPORTED_ISLAND_SAFE_ZERO,
            previous_target_power_mw=previous_target,
            new_target_power_mw=self.controller.target_power_mw,
            previous_applied_power_mw=previous_applied,
            new_applied_power_mw=self.model.applied_power_mw,
            energy_before_mwh=energy_before,
            energy_after_mwh=energy_after,
            correlation_id=open_command.id,
            causation_id=topology_event.id,
            topology_version=updated_topology.topology_version,
        )

        power_decision = self.validator.validate_power_request(
            simultaneous_power_command,
            current_tick=logical_tick,
            topology_version=updated_topology.topology_version,
            model=self.model,
            feasibility_duration_seconds=self.feasibility_duration_seconds,
        )
        if power_decision.acknowledgement.status is not AcknowledgementStatus.REJECTED:
            raise AssertionError("unsupported-island dispatch was not rejected")

        balance = self.balance_service.calculate(
            logical_tick=logical_tick,
            load_mw=self.load_mw,
            bess_ac_power_mw=self.model.applied_power_mw,
            topology=updated_topology,
            correlation_id=open_command.id,
            causation_id=interlock_event.id,
        )
        assert balance.island_imbalance_mw is not None
        alarm_events = self.alarm.evaluate(
            islanded_unsupported=True,
            imbalance_mw=balance.island_imbalance_mw,
            logical_tick=logical_tick,
            correlation_id=open_command.id,
            causation_id=interlock_event.id,
        )
        if self.alarm.state is None:
            raise AssertionError("unsupported-island imbalance did not create an alarm state")
        return IslandTransitionResult(
            topology=updated_topology,
            topology_event=topology_event,
            interlock_event=interlock_event,
            simultaneous_power_acknowledgement=power_decision.acknowledgement,
            balance=balance,
            alarm_events=alarm_events,
            alarm_state=self.alarm.state,
        )
