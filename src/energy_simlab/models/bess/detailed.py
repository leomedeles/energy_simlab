"""Reduced-order detailed BESS with declared aggregate AC-boundary semantics."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite

from energy_simlab.contracts.enums import OperatingMode

from .common import BessObservation, BessParameters, BessStepResult


@dataclass(frozen=True, slots=True, kw_only=True)
class DetailedBessParameters:
    base: BessParameters
    charge_efficiency: float
    discharge_efficiency: float
    response_time_constant_seconds: float
    ramp_up_mw_per_second: float
    ramp_down_mw_per_second: float

    def __post_init__(self) -> None:
        for name, value in (
            ("charge_efficiency", self.charge_efficiency),
            ("discharge_efficiency", self.discharge_efficiency),
        ):
            if not isfinite(value) or not 0 < value <= 1:
                raise ValueError(f"{name} must be finite and in (0, 1]")
        for name, value in (
            ("response_time_constant_seconds", self.response_time_constant_seconds),
            ("ramp_up_mw_per_second", self.ramp_up_mw_per_second),
            ("ramp_down_mw_per_second", self.ramp_down_mw_per_second),
        ):
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")


class DetailedBess:
    model_id = "bess.detailed"
    model_version = "1.0.0"

    def __init__(
        self,
        *,
        parameters: DetailedBessParameters,
        initial_energy_mwh: float,
        initial_applied_power_mw: float = 0.0,
        operating_mode: OperatingMode = OperatingMode.GRID_CONNECTED_AVAILABLE,
    ) -> None:
        if not isfinite(initial_energy_mwh) or not isfinite(initial_applied_power_mw):
            raise ValueError("initial energy and power must be finite")
        if not parameters.base.energy_min_mwh <= initial_energy_mwh <= parameters.base.energy_max_mwh:
            raise ValueError("initial energy is outside configured bounds")
        lower, upper = self._static_range(parameters)
        if not lower <= initial_applied_power_mw <= upper:
            raise ValueError("initial applied power is outside detailed nameplate limits")
        self.parameters = parameters
        self.energy_stored_mwh = initial_energy_mwh
        self.applied_power_mw = initial_applied_power_mw
        self.operating_mode = operating_mode

    @staticmethod
    def _static_range(parameters: DetailedBessParameters) -> tuple[float, float]:
        return (-parameters.base.charge_limit_mw, parameters.base.discharge_limit_mw)

    def static_power_range_mw(self) -> tuple[float, float]:
        return self._static_range(self.parameters)

    def feasible_power_range_mw(self, duration_seconds: float) -> tuple[float, float]:
        """Return the energy-feasible AC mean-power range for one interval."""

        if not isfinite(duration_seconds) or duration_seconds <= 0:
            raise ValueError("duration must be finite and positive")
        base = self.parameters.base
        discharge_energy_limit = (
            (self.energy_stored_mwh - base.energy_min_mwh)
            * 3600.0
            * self.parameters.discharge_efficiency
            / duration_seconds
        )
        charge_energy_limit = (
            (base.energy_max_mwh - self.energy_stored_mwh)
            * 3600.0
            / (self.parameters.charge_efficiency * duration_seconds)
        )
        return (
            -min(base.charge_limit_mw, max(0.0, charge_energy_limit)),
            min(base.discharge_limit_mw, max(0.0, discharge_energy_limit)),
        )

    def advance(self, target_power_mw: float, duration_seconds: float) -> BessStepResult:
        if not isfinite(target_power_mw):
            raise ValueError("target power must be finite")
        if not isfinite(duration_seconds) or duration_seconds <= 0:
            raise ValueError("duration must be finite and positive")
        lower_static, upper_static = self.static_power_range_mw()
        target = min(max(target_power_mw, lower_static), upper_static)
        start_power = self.applied_power_mw
        lag_endpoint = target + (start_power - target) * exp(
            -duration_seconds / self.parameters.response_time_constant_seconds
        )
        ramp_lower = start_power - self.parameters.ramp_down_mw_per_second * duration_seconds
        ramp_upper = start_power + self.parameters.ramp_up_mw_per_second * duration_seconds
        desired_endpoint = min(max(lag_endpoint, ramp_lower), ramp_upper)

        feasible_mean_lower, feasible_mean_upper = self.feasible_power_range_mw(duration_seconds)
        energy_endpoint_lower = 2.0 * feasible_mean_lower - start_power
        energy_endpoint_upper = 2.0 * feasible_mean_upper - start_power
        endpoint_lower = max(lower_static, ramp_lower, energy_endpoint_lower)
        endpoint_upper = min(upper_static, ramp_upper, energy_endpoint_upper)
        if endpoint_lower > endpoint_upper + 1e-12:
            raise ValueError("no endpoint satisfies simultaneous ramp, rating and energy constraints")
        end_power = min(max(desired_endpoint, endpoint_lower), endpoint_upper)
        mean_power = (start_power + end_power) / 2.0

        if mean_power >= 0:
            battery_power = mean_power / self.parameters.discharge_efficiency
            loss_power = mean_power * (1.0 / self.parameters.discharge_efficiency - 1.0)
        else:
            battery_power = self.parameters.charge_efficiency * mean_power
            loss_power = (-mean_power) * (1.0 - self.parameters.charge_efficiency)

        start_energy = self.energy_stored_mwh
        stored_change = -battery_power * duration_seconds / 3600.0
        end_energy = start_energy + stored_change
        base = self.parameters.base
        if end_energy < base.energy_min_mwh - 1e-12 or end_energy > base.energy_max_mwh + 1e-12:
            raise AssertionError("pre-step detailed feasibility allowed an energy-bound violation")
        ac_energy = mean_power * duration_seconds / 3600.0
        loss_energy = loss_power * duration_seconds / 3600.0
        residual = stored_change + ac_energy + loss_energy
        self.energy_stored_mwh = end_energy
        self.applied_power_mw = end_power
        return BessStepResult(
            start_energy_mwh=start_energy,
            end_energy_mwh=end_energy,
            start_power_mw=start_power,
            end_power_mw=end_power,
            mean_power_mw=mean_power,
            ac_energy_mwh=ac_energy,
            loss_energy_mwh=loss_energy,
            stored_energy_change_mwh=stored_change,
            energy_residual_mwh=residual,
            limited=abs(end_power - lag_endpoint) > 1e-15,
        )

    def observe(self) -> BessObservation:
        base = self.parameters.base
        return BessObservation(
            model_id=self.model_id,
            model_version=self.model_version,
            energy_stored_mwh=self.energy_stored_mwh,
            energy_nominal_mwh=base.energy_nominal_mwh,
            soc=self.energy_stored_mwh / base.energy_nominal_mwh,
            applied_power_mw=self.applied_power_mw,
            operating_mode=self.operating_mode,
        )

    def force_safe_zero(self, operating_mode: OperatingMode) -> tuple[float, float]:
        previous_power = self.applied_power_mw
        energy_before = self.energy_stored_mwh
        self.applied_power_mw = 0.0
        self.operating_mode = operating_mode
        return previous_power, energy_before
