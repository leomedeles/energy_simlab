from __future__ import annotations

from math import isclose

from energy_simlab.application import GridConnectedFallbackSlice
from energy_simlab.contracts.enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    AggregationKind,
    CommandAuthority,
    CommandKind,
    Unit,
)
from energy_simlab.contracts.records import CommandV1


def command(
    *,
    command_id: str = "CMD-P-001",
    source_id: str = "scenario",
    sequence: int = 1,
    apply_tick: int = 10,
    expiry_tick: int = 20,
    value_mw: float = 0.4,
    model_version: str | None = "1.0.0",
    topology_version: int | None = 0,
) -> CommandV1:
    return CommandV1(
        id=command_id,
        source_id=source_id,
        logical_tick=0,
        sequence=sequence,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.SCENARIO,
        apply_tick=apply_tick,
        expiry_tick=expiry_tick,
        requested_value=value_mw,
        unit=Unit.MEGAWATT,
        expected_model_version=model_version,
        expected_topology_version=topology_version,
        reason="M2 test request",
    )


def validate(slice_: GridConnectedFallbackSlice, request: CommandV1, *, current_tick: int | None = None):
    return slice_.validator.validate_power_request(
        request,
        current_tick=request.apply_tick if current_tick is None else current_tick,
        topology_version=slice_.topology.topology_version,
        model=slice_.model,
        feasibility_duration_seconds=slice_.macro_duration_seconds,
    )


def test_valid_duplicate_and_stale_source_sequence_are_deterministic():
    slice_ = GridConnectedFallbackSlice()
    original = command()
    accepted = validate(slice_, original)
    duplicate = validate(slice_, original)
    stale = validate(slice_, command(command_id="CMD-P-STALE", sequence=1))

    assert accepted.acknowledgement.status is AcknowledgementStatus.ACCEPTED
    assert duplicate.duplicate
    assert duplicate.acknowledgement is accepted.acknowledgement
    assert stale.acknowledgement.status is AcknowledgementStatus.REJECTED
    assert stale.acknowledgement.reason is AcknowledgementReason.STALE_SEQUENCE


def test_expired_and_wrong_versions_are_rejected():
    expired_slice = GridConnectedFallbackSlice()
    expired = command(apply_tick=10, expiry_tick=10)
    expired_decision = validate(expired_slice, expired, current_tick=20)
    assert expired_decision.acknowledgement.reason is AcknowledgementReason.EXPIRED

    model_slice = GridConnectedFallbackSlice()
    wrong_model = validate(model_slice, command(model_version="9.0.0"))
    assert wrong_model.acknowledgement.reason is AcknowledgementReason.VERSION_MISMATCH

    topology_slice = GridConnectedFallbackSlice()
    wrong_topology = validate(topology_slice, command(topology_version=9))
    assert wrong_topology.acknowledgement.reason is AcknowledgementReason.VERSION_MISMATCH


def test_static_nameplate_request_is_rejected_without_clipping():
    slice_ = GridConnectedFallbackSlice()
    decision = validate(slice_, command(value_mw=1.01))
    acknowledgement = decision.acknowledgement
    assert acknowledgement.status is AcknowledgementStatus.REJECTED
    assert acknowledgement.reason is AcknowledgementReason.NAMEPLATE_LIMIT
    assert acknowledgement.accepted_value is None


def test_energy_feasible_limit_is_explicit_and_ownership_fields_remain_distinct():
    slice_ = GridConnectedFallbackSlice(initial_energy_mwh=0.2001)
    result = slice_.execute_macro(command(apply_tick=0, expiry_tick=10, value_mw=1.0))
    assert result.acknowledgement.status is AcknowledgementStatus.ACCEPTED_WITH_LIMIT
    assert result.acknowledgement.reason is AcknowledgementReason.ENERGY_FEASIBLE_LIMIT
    assert result.ownership.requested_power_mw == 1.0
    assert result.ownership.accepted_power_mw < result.ownership.requested_power_mw
    assert result.ownership.target_power_mw == result.ownership.accepted_power_mw
    assert result.ownership.applied_power_mw == result.ownership.target_power_mw
    assert abs(result.step.end_energy_mwh - 0.2) <= 1e-12


def test_grid_connected_command_produces_complete_energy_consistent_publication():
    slice_ = GridConnectedFallbackSlice()
    result = slice_.execute_macro(command())
    expected_energy = 1.0 - 0.4 * 1.0 / 3600.0
    assert result.acknowledgement.status is AcknowledgementStatus.ACCEPTED
    assert isclose(result.step.end_energy_mwh, expected_energy, rel_tol=1e-12, abs_tol=1e-12)
    assert abs(result.step.energy_residual_mwh) <= 1e-12
    assert result.balance.grid_import_mw == 0.6 - 0.4
    assert result.balance.island_imbalance_mw is None

    publication = result.publication
    assert publication.interval_start_tick == 10
    assert publication.interval_end_tick == 20
    assert publication.discrete_records == (result.acknowledgement,)
    assert publication.energy_residual_mwh == result.step.energy_residual_mwh
    by_signal = {sample.signal_id: sample for sample in publication.telemetry}
    assert set(by_signal) == {
        "requested_power",
        "accepted_power",
        "target_power",
        "applied_power",
        "applied_power_mean",
        "ac_energy",
        "stored_energy",
        "soc",
        "grid_import",
    }
    assert by_signal["applied_power_mean"].aggregation is AggregationKind.MEAN
    assert by_signal["ac_energy"].aggregation is AggregationKind.INTEGRAL
    assert by_signal["ac_energy"].unit is Unit.MEGAWATT_HOUR
    assert len({sample.sequence for sample in publication.telemetry}) == len(publication.telemetry)
