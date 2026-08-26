from math import isclose

import pytest

from energy_simlab.contracts.enums import EnergizationState, OperatingMode
from energy_simlab.models.bess import BessParameters, FallbackBess
from energy_simlab.topology import reference_topology


PARAMETERS = BessParameters(
    energy_nominal_mwh=2.0,
    soc_min=0.1,
    soc_max=0.9,
    charge_limit_mw=1.0,
    discharge_limit_mw=1.0,
)


def test_closed_pcc_is_one_sorted_source_connected_component():
    topology = reference_topology()
    assert len(topology.components) == 1
    component = topology.components[0]
    assert component.bus_ids == ("GRID", "LOCAL")
    assert component.contains_infinite_source
    assert component.energization is EnergizationState.GRID_CONNECTED
    assert [item.id for item in topology.buses] == ["GRID", "LOCAL"]


@pytest.mark.parametrize(
    ("power_mw", "expected_energy_mwh"),
    [(0.4, 0.6), (-0.4, 1.4)],
)
def test_fallback_constant_power_matches_analytic_energy(power_mw, expected_energy_mwh):
    model = FallbackBess(parameters=PARAMETERS, initial_energy_mwh=1.0)
    step = model.advance(power_mw, 3600.0)
    assert isclose(step.end_energy_mwh, expected_energy_mwh, rel_tol=1e-12, abs_tol=1e-12)
    assert isclose(step.energy_residual_mwh, 0.0, rel_tol=1e-12, abs_tol=1e-12)
    assert step.loss_energy_mwh == 0.0


@pytest.mark.parametrize(
    ("initial_energy_mwh", "request_mw", "bound_mwh"),
    [(PARAMETERS.energy_min_mwh, 1.0, PARAMETERS.energy_min_mwh),
     (PARAMETERS.energy_max_mwh, -1.0, PARAMETERS.energy_max_mwh)],
)
def test_energy_bounds_are_enforced_before_integration(initial_energy_mwh, request_mw, bound_mwh):
    model = FallbackBess(parameters=PARAMETERS, initial_energy_mwh=initial_energy_mwh)
    step = model.advance(request_mw, 1.0)
    assert step.limited
    assert abs(step.end_energy_mwh - bound_mwh) <= 1e-12
    assert PARAMETERS.energy_min_mwh - 1e-12 <= model.energy_stored_mwh <= PARAMETERS.energy_max_mwh + 1e-12


def test_model_observation_declares_identity_units_state_and_mode():
    model = FallbackBess(parameters=PARAMETERS, initial_energy_mwh=1.0)
    observation = model.observe()
    assert observation.model_id == "bess.fallback"
    assert observation.model_version == "1.0.0"
    assert observation.soc == 0.5
    assert observation.applied_power_mw == 0.0
    assert observation.operating_mode is OperatingMode.GRID_CONNECTED_AVAILABLE

