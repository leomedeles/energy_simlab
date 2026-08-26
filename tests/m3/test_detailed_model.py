from __future__ import annotations

from math import isclose

from energy_simlab.models.bess import (
    BessParameters,
    DetailedBess,
    DetailedBessParameters,
    FixedRatioBessRunner,
)


def parameters(
    *,
    energy_nominal_mwh: float = 4.0,
    soc_min: float = 0.0,
    soc_max: float = 1.0,
    power_limit_mw: float = 1.0,
    tau_seconds: float = 2.0,
    ramp_mw_per_second: float = 10.0,
) -> DetailedBessParameters:
    return DetailedBessParameters(
        base=BessParameters(
            energy_nominal_mwh=energy_nominal_mwh,
            soc_min=soc_min,
            soc_max=soc_max,
            charge_limit_mw=power_limit_mw,
            discharge_limit_mw=power_limit_mw,
        ),
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        response_time_constant_seconds=tau_seconds,
        ramp_up_mw_per_second=ramp_mw_per_second,
        ramp_down_mw_per_second=ramp_mw_per_second,
    )


def test_one_mw_discharge_for_one_hour_matches_energy_and_loss_reference():
    model = DetailedBess(
        parameters=parameters(),
        initial_energy_mwh=2.0,
        initial_applied_power_mw=1.0,
    )
    step = model.advance(1.0, 3600.0)
    expected_delta = -1.0526315789473684
    expected_loss = 0.0526315789473684
    assert isclose(step.stored_energy_change_mwh, expected_delta, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(step.loss_energy_mwh, expected_loss, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(step.energy_residual_mwh, 0.0, rel_tol=1e-12, abs_tol=1e-12)


def test_minus_one_mw_charge_for_one_hour_matches_energy_and_loss_reference():
    model = DetailedBess(
        parameters=parameters(),
        initial_energy_mwh=2.0,
        initial_applied_power_mw=-1.0,
    )
    step = model.advance(-1.0, 3600.0)
    assert isclose(step.stored_energy_change_mwh, 0.95, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(step.loss_energy_mwh, 0.05, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(step.energy_residual_mwh, 0.0, rel_tol=1e-12, abs_tol=1e-12)


def test_uncapped_exact_zoh_lag_matches_two_and_four_second_references():
    model = DetailedBess(
        parameters=parameters(energy_nominal_mwh=100.0),
        initial_energy_mwh=50.0,
    )
    first = model.advance(1.0, 2.0)
    second = model.advance(1.0, 2.0)
    assert isclose(first.end_power_mw, 0.6321205588285577, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(second.end_power_mw, 0.8646647167633873, rel_tol=1e-12, abs_tol=1e-12)


def test_ramp_cap_bounds_every_endpoint_change():
    model = DetailedBess(
        parameters=parameters(
            energy_nominal_mwh=100.0,
            tau_seconds=0.1,
            ramp_mw_per_second=0.5,
        ),
        initial_energy_mwh=50.0,
    )
    previous = model.applied_power_mw
    for _ in range(20):
        step = model.advance(1.0, 0.1)
        assert abs(step.end_power_mw - previous) <= 0.5 * 0.1 + 1e-12
        previous = step.end_power_mw


def test_fixed_ratio_runner_completes_ten_children_and_reports_residuals():
    model = DetailedBess(
        parameters=parameters(energy_nominal_mwh=2.0, soc_min=0.1, soc_max=0.9, ramp_mw_per_second=0.5),
        initial_energy_mwh=1.0,
    )
    reduction = FixedRatioBessRunner().advance_macro(model, 1.0)
    assert reduction.child_completions == 10
    assert reduction.duration_seconds == 1.0
    assert len(reduction.child_steps) == 10
    assert abs(reduction.energy_residual_mwh) <= 1e-10
    assert abs(reduction.coupling_residual_mwh) <= 1e-12
    assert reduction.minimum_power_mw <= reduction.end_power_mw <= reduction.maximum_power_mw
    assert reduction.minimum_soc <= reduction.maximum_soc


def test_short_reference_run_meets_cumulative_energy_residual():
    model = DetailedBess(
        parameters=parameters(energy_nominal_mwh=2.0, soc_min=0.1, soc_max=0.9, ramp_mw_per_second=0.5),
        initial_energy_mwh=1.0,
    )
    runner = FixedRatioBessRunner()
    reductions = [runner.advance_macro(model, -1.0 if index >= 5 else 1.0) for index in range(10)]
    assert all(abs(item.energy_residual_mwh) <= 1e-10 for item in reductions)
    assert abs(sum(item.energy_residual_mwh for item in reductions)) <= 1e-9
    assert all(abs(item.coupling_residual_mwh) <= 1e-12 for item in reductions)

