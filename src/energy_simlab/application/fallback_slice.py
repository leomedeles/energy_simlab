"""M2 composition of the grid-connected fallback vertical slice."""

from __future__ import annotations

from dataclasses import dataclass

from energy_simlab.balance import AlgebraicActivePowerBalance
from energy_simlab.contracts.enums import AggregationKind, QualityReason, QualityValidity, Unit
from energy_simlab.contracts.records import (
    ActivePowerBalanceV1,
    AcknowledgementV1,
    CommandV1,
    MacroPublicationV1,
    QualityV1,
    SimulationConfigV1,
    TelemetrySampleV1,
    TopologySnapshotV1,
)
from energy_simlab.control import CommandValidator, PowerController, PowerOwnership
from energy_simlab.kernel.ids import DeterministicIdSource
from energy_simlab.models.bess import BessParameters, BessStepResult, FallbackBess
from energy_simlab.topology import reference_topology


@dataclass(frozen=True, slots=True, kw_only=True)
class FallbackMacroResult:
    acknowledgement: AcknowledgementV1
    ownership: PowerOwnership
    step: BessStepResult
    balance: ActivePowerBalanceV1
    publication: MacroPublicationV1


def reference_configuration() -> SimulationConfigV1:
    return SimulationConfigV1(
        base_tick_seconds=0.1,
        macro_ticks=10,
        energy_nominal_mwh=2.0,
        initial_soc=0.5,
        soc_min=0.1,
        soc_max=0.9,
        charge_limit_mw=1.0,
        discharge_limit_mw=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        response_time_constant_seconds=2.0,
        ramp_up_mw_per_second=0.5,
        ramp_down_mw_per_second=0.5,
        load_mw=0.6,
        island_alarm_threshold_mw=0.05,
        seed=0,
    )


class GridConnectedFallbackSlice:
    def __init__(
        self,
        *,
        configuration: SimulationConfigV1 | None = None,
        initial_energy_mwh: float | None = None,
    ) -> None:
        self.configuration = configuration or reference_configuration()
        parameters = BessParameters(
            energy_nominal_mwh=self.configuration.energy_nominal_mwh,
            soc_min=self.configuration.soc_min,
            soc_max=self.configuration.soc_max,
            charge_limit_mw=self.configuration.charge_limit_mw,
            discharge_limit_mw=self.configuration.discharge_limit_mw,
        )
        if initial_energy_mwh is None:
            initial_energy_mwh = self.configuration.initial_soc * self.configuration.energy_nominal_mwh
        self.model = FallbackBess(parameters=parameters, initial_energy_mwh=initial_energy_mwh)
        self.topology: TopologySnapshotV1 = reference_topology()
        self.validator = CommandValidator()
        self.controller = PowerController()
        self.balance_service = AlgebraicActivePowerBalance()
        self._telemetry_ids = DeterministicIdSource()
        self._publication_ids = DeterministicIdSource()

    @property
    def macro_duration_seconds(self) -> float:
        return self.configuration.base_tick_seconds * self.configuration.macro_ticks

    def execute_macro(self, command: CommandV1) -> FallbackMacroResult:
        start_tick = command.apply_tick
        end_tick = start_tick + self.configuration.macro_ticks
        decision = self.validator.validate_power_request(
            command,
            current_tick=start_tick,
            topology_version=self.topology.topology_version,
            model=self.model,
            feasibility_duration_seconds=self.macro_duration_seconds,
        )
        if not decision.duplicate:
            self.controller.apply_decision(command, decision)
        step = self.model.advance(self.controller.target_power_mw, self.macro_duration_seconds)
        observation = self.model.observe()
        ownership = self.controller.observe(observation.applied_power_mw)
        balance = self.balance_service.calculate(
            logical_tick=end_tick,
            load_mw=self.configuration.load_mw,
            bess_ac_power_mw=observation.applied_power_mw,
            topology=self.topology,
        )
        quality = QualityV1(
            validity=QualityValidity.GOOD,
            reason=QualityReason.NORMAL,
            detail="fallback BESS value under declared lossless assumptions",
            origin_id=self.model.model_id,
            since_tick=start_tick,
        )
        telemetry = (
            self._sample("requested_power", ownership.requested_power_mw, Unit.MEGAWATT, AggregationKind.END, start_tick, end_tick, quality),
            self._sample("accepted_power", ownership.accepted_power_mw, Unit.MEGAWATT, AggregationKind.END, start_tick, end_tick, quality),
            self._sample("target_power", ownership.target_power_mw, Unit.MEGAWATT, AggregationKind.END, start_tick, end_tick, quality),
            self._sample("applied_power", ownership.applied_power_mw, Unit.MEGAWATT, AggregationKind.END, start_tick, end_tick, quality),
            self._sample("applied_power_mean", step.mean_power_mw, Unit.MEGAWATT, AggregationKind.MEAN, start_tick, end_tick, quality),
            self._sample("ac_energy", step.ac_energy_mwh, Unit.MEGAWATT_HOUR, AggregationKind.INTEGRAL, start_tick, end_tick, quality),
            self._sample("stored_energy", observation.energy_stored_mwh, Unit.MEGAWATT_HOUR, AggregationKind.END, start_tick, end_tick, quality),
            self._sample("soc", observation.soc, Unit.PER_UNIT, AggregationKind.END, start_tick, end_tick, quality),
            self._sample("grid_import", balance.grid_import_mw or 0.0, Unit.MEGAWATT, AggregationKind.MEAN, start_tick, end_tick, balance.quality),
        )
        publication_id, publication_sequence = self._publication_ids.next_id(
            "application-publisher", "PUB"
        )
        publication = MacroPublicationV1(
            id=publication_id,
            source_id="application-publisher",
            logical_tick=end_tick,
            sequence=publication_sequence,
            run_id="TT000-M2",
            interval_start_tick=start_tick,
            interval_end_tick=end_tick,
            telemetry=telemetry,
            discrete_records=(decision.acknowledgement,),
            energy_residual_mwh=step.energy_residual_mwh,
            coupling_residual_mwh=0.0,
        )
        return FallbackMacroResult(
            acknowledgement=decision.acknowledgement,
            ownership=ownership,
            step=step,
            balance=balance,
            publication=publication,
        )

    def _sample(
        self,
        signal_id: str,
        value: float,
        unit: Unit,
        aggregation: AggregationKind,
        start_tick: int,
        end_tick: int,
        quality: QualityV1,
    ) -> TelemetrySampleV1:
        record_id, sequence = self._telemetry_ids.next_id("telemetry-publisher", "TEL")
        return TelemetrySampleV1(
            id=record_id,
            source_id="telemetry-publisher",
            logical_tick=end_tick,
            sequence=sequence,
            subject_id="BESS" if signal_id != "grid_import" else "PCC",
            signal_id=signal_id,
            value=value,
            unit=unit,
            aggregation=aggregation,
            interval_start_tick=start_tick,
            interval_end_tick=end_tick,
            quality=quality,
            model_id=self.model.model_id,
            model_version=self.model.model_version,
            topology_version=self.topology.topology_version,
        )

