"""Shared BESS lifecycle values independent of a model implementation."""

from __future__ import annotations

from dataclasses import dataclass

from energy_simlab.contracts.enums import OperatingMode


@dataclass(frozen=True, slots=True, kw_only=True)
class BessParameters:
    energy_nominal_mwh: float
    soc_min: float
    soc_max: float
    charge_limit_mw: float
    discharge_limit_mw: float

    def __post_init__(self) -> None:
        if self.energy_nominal_mwh <= 0:
            raise ValueError("nominal energy must be positive")
        if not 0 <= self.soc_min < self.soc_max <= 1:
            raise ValueError("invalid SoC bounds")
        if self.charge_limit_mw <= 0 or self.discharge_limit_mw <= 0:
            raise ValueError("power ratings must be positive")

    @property
    def energy_min_mwh(self) -> float:
        return self.energy_nominal_mwh * self.soc_min

    @property
    def energy_max_mwh(self) -> float:
        return self.energy_nominal_mwh * self.soc_max


@dataclass(frozen=True, slots=True, kw_only=True)
class BessObservation:
    model_id: str
    model_version: str
    energy_stored_mwh: float
    energy_nominal_mwh: float
    soc: float
    applied_power_mw: float
    operating_mode: OperatingMode


@dataclass(frozen=True, slots=True, kw_only=True)
class BessStepResult:
    start_energy_mwh: float
    end_energy_mwh: float
    start_power_mw: float
    end_power_mw: float
    mean_power_mw: float
    ac_energy_mwh: float
    loss_energy_mwh: float
    stored_energy_change_mwh: float
    energy_residual_mwh: float
    limited: bool
