"""Fixed-ratio child advancement and explicit macro reductions."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isclose

from .common import BessStepResult
from .detailed import DetailedBess


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroReduction:
    child_completions: int
    duration_seconds: float
    start_energy_mwh: float
    end_energy_mwh: float
    end_power_mw: float
    mean_power_mw: float
    ac_energy_mwh: float
    loss_energy_mwh: float
    stored_energy_change_mwh: float
    minimum_power_mw: float
    maximum_power_mw: float
    minimum_soc: float
    maximum_soc: float
    energy_residual_mwh: float
    coupling_residual_mwh: float
    child_steps: tuple[BessStepResult, ...]


class FixedRatioBessRunner:
    def __init__(self, *, macro_seconds: float = 1.0, child_seconds: float = 0.1) -> None:
        if macro_seconds <= 0 or child_seconds <= 0:
            raise ValueError("macro and child periods must be positive")
        ratio = round(macro_seconds / child_seconds)
        if ratio <= 0 or not isclose(
            ratio * child_seconds,
            macro_seconds,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("macro/child ratio must be integral")
        self.macro_seconds = macro_seconds
        self.child_seconds = child_seconds
        self.ratio = ratio

    def advance_macro(self, model: DetailedBess, target_power_mw: float) -> MacroReduction:
        start = model.observe()
        steps = tuple(model.advance(target_power_mw, self.child_seconds) for _ in range(self.ratio))
        end = model.observe()
        ac_energy = fsum(item.ac_energy_mwh for item in steps)
        loss_energy = fsum(item.loss_energy_mwh for item in steps)
        stored_change = end.energy_stored_mwh - start.energy_stored_mwh
        mean_power = ac_energy * 3600.0 / self.macro_seconds
        macro_integral = mean_power * self.macro_seconds / 3600.0
        endpoints = (steps[0].start_power_mw, *(item.end_power_mw for item in steps))
        energy_points = (start.energy_stored_mwh, *(item.end_energy_mwh for item in steps))
        soc_points = tuple(value / end.energy_nominal_mwh for value in energy_points)
        return MacroReduction(
            child_completions=len(steps),
            duration_seconds=fsum(self.child_seconds for _ in steps),
            start_energy_mwh=start.energy_stored_mwh,
            end_energy_mwh=end.energy_stored_mwh,
            end_power_mw=end.applied_power_mw,
            mean_power_mw=mean_power,
            ac_energy_mwh=ac_energy,
            loss_energy_mwh=loss_energy,
            stored_energy_change_mwh=stored_change,
            minimum_power_mw=min(endpoints),
            maximum_power_mw=max(endpoints),
            minimum_soc=min(soc_points),
            maximum_soc=max(soc_points),
            energy_residual_mwh=stored_change + ac_energy + loss_energy,
            coupling_residual_mwh=macro_integral - ac_energy,
            child_steps=steps,
        )

