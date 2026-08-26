"""Lossless bounded fallback BESS used by the M2 vertical slice."""

from __future__ import annotations

from math import isfinite

from energy_simlab.contracts.enums import OperatingMode

from .common import BessObservation, BessParameters, BessStepResult


class FallbackBess:
    model_id = "bess.fallback"
    model_version = "1.0.0"

    def __init__(
        self,
        *,
        parameters: BessParameters,
        initial_energy_mwh: float,
        operating_mode: OperatingMode = OperatingMode.GRID_CONNECTED_AVAILABLE,
    ) -> None:
        if not isfinite(initial_energy_mwh):
            raise ValueError("initial energy must be finite")
        if not parameters.energy_min_mwh <= initial_energy_mwh <= parameters.energy_max_mwh:
            raise ValueError("initial energy is outside configured bounds")
        self.parameters = parameters
        self.energy_stored_mwh = initial_energy_mwh
        self.applied_power_mw = 0.0
        self.operating_mode = operating_mode

    def static_power_range_mw(self) -> tuple[float, float]:
        return (-self.parameters.charge_limit_mw, self.parameters.discharge_limit_mw)

    def feasible_power_range_mw(self, duration_seconds: float) -> tuple[float, float]:
        if not isfinite(duration_seconds) or duration_seconds <= 0:
            raise ValueError("duration must be finite and positive")
        charge_energy_limit = (
            (self.parameters.energy_max_mwh - self.energy_stored_mwh) * 3600.0 / duration_seconds
        )
        discharge_energy_limit = (
            (self.energy_stored_mwh - self.parameters.energy_min_mwh) * 3600.0 / duration_seconds
        )
        return (
            -min(self.parameters.charge_limit_mw, max(0.0, charge_energy_limit)),
            min(self.parameters.discharge_limit_mw, max(0.0, discharge_energy_limit)),
        )

    def advance(self, target_power_mw: float, duration_seconds: float) -> BessStepResult:
        if not isfinite(target_power_mw):
            raise ValueError("target power must be finite")
        lower, upper = self.feasible_power_range_mw(duration_seconds)
        applied = min(max(target_power_mw, lower), upper)
        start_energy = self.energy_stored_mwh
        end_energy = start_energy - applied * duration_seconds / 3600.0
        if end_energy < self.parameters.energy_min_mwh - 1e-12:
            raise AssertionError("pre-step feasible limit allowed energy below minimum")
        if end_energy > self.parameters.energy_max_mwh + 1e-12:
            raise AssertionError("pre-step feasible limit allowed energy above maximum")
        self.energy_stored_mwh = end_energy
        self.applied_power_mw = applied
        stored_change = end_energy - start_energy
        ac_energy = applied * duration_seconds / 3600.0
        residual = stored_change + ac_energy
        return BessStepResult(
            start_energy_mwh=start_energy,
            end_energy_mwh=end_energy,
            start_power_mw=applied,
            end_power_mw=applied,
            mean_power_mw=applied,
            ac_energy_mwh=ac_energy,
            loss_energy_mwh=0.0,
            stored_energy_change_mwh=stored_change,
            energy_residual_mwh=residual,
            limited=applied != target_power_mw,
        )

    def observe(self) -> BessObservation:
        return BessObservation(
            model_id=self.model_id,
            model_version=self.model_version,
            energy_stored_mwh=self.energy_stored_mwh,
            energy_nominal_mwh=self.parameters.energy_nominal_mwh,
            soc=self.energy_stored_mwh / self.parameters.energy_nominal_mwh,
            applied_power_mw=self.applied_power_mw,
            operating_mode=self.operating_mode,
        )

