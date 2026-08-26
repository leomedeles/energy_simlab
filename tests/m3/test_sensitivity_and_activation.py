from __future__ import annotations

from math import isclose

import pytest

from energy_simlab.contracts.enums import (
    EnergizationState,
    FidelityResult,
    QualityReason,
    QualityValidity,
)
from energy_simlab.contracts.records import QualityV1, SourceCounterV1
from energy_simlab.models.bess import (
    BessModelRegistry,
    BessParameters,
    DetailedBess,
    DetailedBessParameters,
    FallbackBess,
)


def detailed_parameters(
    *,
    power_limit_mw: float = 1.0,
    tau_seconds: float = 2.0,
    ramp_mw_per_second: float = 10.0,
) -> DetailedBessParameters:
    return DetailedBessParameters(
        base=BessParameters(
            energy_nominal_mwh=2.0,
            soc_min=0.1,
            soc_max=0.9,
            charge_limit_mw=power_limit_mw,
            discharge_limit_mw=power_limit_mw,
        ),
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        response_time_constant_seconds=tau_seconds,
        ramp_up_mw_per_second=ramp_mw_per_second,
        ramp_down_mw_per_second=ramp_mw_per_second,
    )


def run_steps(model: DetailedBess, *, target_mw: float, step_seconds: float, total_seconds: float):
    endpoints: list[float] = []
    for _ in range(round(total_seconds / step_seconds)):
        endpoints.append(model.advance(target_mw, step_seconds).end_power_mw)
    return endpoints, model.observe()


def test_half_step_uncapped_endpoint_is_analytic_and_capped_case_meets_tolerances():
    coarse_uncapped = DetailedBess(parameters=detailed_parameters(), initial_energy_mwh=1.0)
    fine_uncapped = DetailedBess(parameters=detailed_parameters(), initial_energy_mwh=1.0)
    _, coarse_end = run_steps(coarse_uncapped, target_mw=1.0, step_seconds=0.1, total_seconds=4.0)
    _, fine_end = run_steps(fine_uncapped, target_mw=1.0, step_seconds=0.05, total_seconds=4.0)
    expected = 0.8646647167633873
    assert isclose(coarse_end.applied_power_mw, expected, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(fine_end.applied_power_mw, expected, rel_tol=1e-12, abs_tol=1e-12)

    capped = detailed_parameters(tau_seconds=0.1, ramp_mw_per_second=0.5)
    coarse_model = DetailedBess(parameters=capped, initial_energy_mwh=1.0)
    fine_model = DetailedBess(parameters=capped, initial_energy_mwh=1.0)
    coarse_points, coarse_observation = run_steps(
        coarse_model, target_mw=1.0, step_seconds=0.1, total_seconds=2.0
    )
    fine_points, fine_observation = run_steps(
        fine_model, target_mw=1.0, step_seconds=0.05, total_seconds=2.0
    )
    fine_common_grid = fine_points[1::2]
    assert max(abs(left - right) for left, right in zip(coarse_points, fine_common_grid, strict=True)) <= 1e-3
    assert abs(coarse_observation.energy_stored_mwh - fine_observation.energy_stored_mwh) <= 1e-6


def transition_quality() -> QualityV1:
    return QualityV1(
        validity=QualityValidity.GOOD,
        reason=QualityReason.NORMAL,
        detail="grid-connected transition context",
        origin_id="application",
        since_tick=30,
    )


def test_successful_fallback_to_detailed_activation_preserves_common_state_and_lineage():
    base = detailed_parameters().base
    fallback = FallbackBess(parameters=base, initial_energy_mwh=1.0)
    fallback.advance(0.4, 1.0)
    before = fallback.observe()
    registry = BessModelRegistry(fallback=fallback, detailed_parameters=detailed_parameters())
    source_sequences = (SourceCounterV1(source_id="scenario", value=2),)
    event = registry.activate_detailed(
        logical_tick=30,
        requested_power_mw=0.4,
        accepted_power_mw=0.4,
        energization=EnergizationState.GRID_CONNECTED,
        topology_version=0,
        component_id="GRID+LOCAL@0",
        quality=transition_quality(),
        last_command_id="CMD-P-001",
        source_sequences=source_sequences,
        correlation_id="CMD-M-001",
        causation_id="CMD-M-001",
    )
    after = registry.active_model.observe()
    assert event.result is FidelityResult.SUCCEEDED
    assert registry.active_model.model_id == "bess.detailed"
    assert event.handoff.source_sequences == source_sequences
    assert event.handoff.last_command_id == "CMD-P-001"
    assert event.handoff.from_model_id == "bess.fallback"
    assert event.handoff.to_model_id == "bess.detailed"
    assert abs(after.energy_stored_mwh - before.energy_stored_mwh) <= 1e-12
    assert abs(after.soc - before.soc) <= 1e-12
    assert abs(after.applied_power_mw - before.applied_power_mw) <= 1e-12
    assert abs(event.energy_discontinuity_mwh) <= 1e-12
    assert abs(event.soc_discontinuity) <= 1e-12
    assert abs(event.power_discontinuity_mw) <= 1e-12


def test_failed_activation_is_atomic_and_leaves_active_model_and_state_unchanged():
    fallback_parameters = BessParameters(
        energy_nominal_mwh=2.0,
        soc_min=0.1,
        soc_max=0.9,
        charge_limit_mw=1.0,
        discharge_limit_mw=1.0,
    )
    fallback = FallbackBess(parameters=fallback_parameters, initial_energy_mwh=1.0)
    fallback.advance(0.4, 1.0)
    incompatible = detailed_parameters(power_limit_mw=0.1)
    registry = BessModelRegistry(fallback=fallback, detailed_parameters=incompatible)
    before = registry.export_state()
    event = registry.activate_detailed(
        logical_tick=30,
        requested_power_mw=0.4,
        accepted_power_mw=0.4,
        energization=EnergizationState.GRID_CONNECTED,
        topology_version=0,
        component_id="GRID+LOCAL@0",
        quality=transition_quality(),
        last_command_id="CMD-P-001",
        source_sequences=(SourceCounterV1(source_id="scenario", value=2),),
        correlation_id="CMD-M-FAIL",
        causation_id="CMD-M-FAIL",
    )
    assert event.result is FidelityResult.FAILED
    assert "nameplate" in event.detail
    assert registry.export_state() == before
    assert registry.active_model is fallback
    assert registry.detailed is None


def test_activation_rejects_non_macro_boundary_before_any_state_change():
    params = detailed_parameters()
    fallback = FallbackBess(parameters=params.base, initial_energy_mwh=1.0)
    registry = BessModelRegistry(fallback=fallback, detailed_parameters=params)
    before = registry.export_state()
    with pytest.raises(ValueError, match="macro boundary"):
        registry.activate_detailed(
            logical_tick=31,
            requested_power_mw=0.0,
            accepted_power_mw=0.0,
            energization=EnergizationState.GRID_CONNECTED,
            topology_version=0,
            component_id="GRID+LOCAL@0",
            quality=transition_quality(),
            last_command_id="CMD-P-001",
            source_sequences=(),
            correlation_id="CMD-M-OFFGRID",
            causation_id="CMD-M-OFFGRID",
        )
    assert registry.export_state() == before
