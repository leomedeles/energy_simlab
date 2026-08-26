"""Atomic fallback-to-detailed activation at an approved synchronization boundary."""

from __future__ import annotations

from dataclasses import dataclass

from energy_simlab.contracts.enums import EnergizationState, FidelityResult
from energy_simlab.contracts.records import (
    FidelityEventV1,
    ModelHandoffV1,
    QualityV1,
    SourceCounterV1,
)
from .common import BessObservation
from .detailed import DetailedBess, DetailedBessParameters
from .fallback import FallbackBess


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelRegistryState:
    active_model_id: str
    fallback: BessObservation
    detailed: BessObservation | None


class BessModelRegistry:
    source_id = "model-registry"

    def __init__(
        self,
        *,
        fallback: FallbackBess,
        detailed_parameters: DetailedBessParameters,
        macro_ticks: int = 10,
    ) -> None:
        if macro_ticks <= 0:
            raise ValueError("macro_ticks must be positive")
        self.fallback = fallback
        self.detailed_parameters = detailed_parameters
        self.macro_ticks = macro_ticks
        self.detailed: DetailedBess | None = None
        self._active: FallbackBess | DetailedBess = fallback
        self._event_sequence = 0

    @property
    def active_model(self) -> FallbackBess | DetailedBess:
        return self._active

    def export_state(self) -> ModelRegistryState:
        return ModelRegistryState(
            active_model_id=self._active.model_id,
            fallback=self.fallback.observe(),
            detailed=None if self.detailed is None else self.detailed.observe(),
        )

    def activate_detailed(
        self,
        *,
        logical_tick: int,
        requested_power_mw: float,
        accepted_power_mw: float,
        energization: EnergizationState,
        topology_version: int,
        component_id: str,
        quality: QualityV1,
        last_command_id: str,
        source_sequences: tuple[SourceCounterV1, ...],
        correlation_id: str,
        causation_id: str,
    ) -> FidelityEventV1:
        if logical_tick % self.macro_ticks:
            raise ValueError("model activation requires a quiescent macro boundary")
        source_observation = self.fallback.observe()
        handoff = ModelHandoffV1(
            asset_id="BESS",
            from_model_id=self.fallback.model_id,
            from_model_version=self.fallback.model_version,
            to_model_id=DetailedBess.model_id,
            to_model_version=DetailedBess.model_version,
            logical_tick=logical_tick,
            energy_stored_mwh=source_observation.energy_stored_mwh,
            energy_nominal_mwh=source_observation.energy_nominal_mwh,
            soc=source_observation.soc,
            requested_power_mw=requested_power_mw,
            accepted_power_mw=accepted_power_mw,
            applied_power_mw=source_observation.applied_power_mw,
            operating_mode=source_observation.operating_mode,
            energization=energization,
            topology_version=topology_version,
            component_id=component_id,
            quality=quality,
            last_command_id=last_command_id,
            source_sequences=source_sequences,
        )
        self._event_sequence += 1
        sequence = self._event_sequence
        event_id = f"FID-MODEL-REGISTRY-{sequence:08d}"
        try:
            self._validate_handoff(handoff)
            candidate = DetailedBess(
                parameters=self.detailed_parameters,
                initial_energy_mwh=handoff.energy_stored_mwh,
                initial_applied_power_mw=handoff.applied_power_mw,
                operating_mode=handoff.operating_mode,
            )
            preview = candidate.observe()
            energy_jump = preview.energy_stored_mwh - source_observation.energy_stored_mwh
            soc_jump = preview.soc - source_observation.soc
            power_jump = preview.applied_power_mw - source_observation.applied_power_mw
            if any(abs(value) > 1e-12 for value in (energy_jump, soc_jump, power_jump)):
                raise ValueError("candidate violates approved transition continuity tolerances")
        except ValueError as error:
            return FidelityEventV1(
                id=event_id,
                source_id=self.source_id,
                logical_tick=logical_tick,
                sequence=sequence,
                correlation_id=correlation_id,
                causation_id=causation_id,
                result=FidelityResult.FAILED,
                handoff=handoff,
                energy_discontinuity_mwh=0.0,
                soc_discontinuity=0.0,
                power_discontinuity_mw=0.0,
                detail=str(error),
            )

        self.detailed = candidate
        self._active = candidate
        return FidelityEventV1(
            id=event_id,
            source_id=self.source_id,
            logical_tick=logical_tick,
            sequence=sequence,
            correlation_id=correlation_id,
            causation_id=causation_id,
            result=FidelityResult.SUCCEEDED,
            handoff=handoff,
            energy_discontinuity_mwh=energy_jump,
            soc_discontinuity=soc_jump,
            power_discontinuity_mw=power_jump,
            detail="fallback-to-detailed activation succeeded atomically",
        )

    def _validate_handoff(self, handoff: ModelHandoffV1) -> None:
        base = self.detailed_parameters.base
        if abs(handoff.energy_nominal_mwh - base.energy_nominal_mwh) > 1e-12:
            raise ValueError("nominal-energy mismatch has no approved mapper")
        if not base.energy_min_mwh <= handoff.energy_stored_mwh <= base.energy_max_mwh:
            raise ValueError("stored energy is outside detailed-model bounds")
        lower, upper = (-base.charge_limit_mw, base.discharge_limit_mw)
        if not lower <= handoff.applied_power_mw <= upper:
            raise ValueError("applied power is outside detailed-model nameplate limits")
        if abs(handoff.energy_stored_mwh - base.energy_min_mwh) <= 1e-12 and handoff.applied_power_mw > 0:
            raise ValueError("cannot activate at minimum energy while discharging")
        if abs(handoff.energy_stored_mwh - base.energy_max_mwh) <= 1e-12 and handoff.applied_power_mw < 0:
            raise ValueError("cannot activate at maximum energy while charging")
