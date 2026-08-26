from __future__ import annotations

from energy_simlab.application import GridConnectedFallbackSlice, IslandTransitionCoordinator
from energy_simlab.contracts.enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    BranchState,
    CommandAuthority,
    CommandKind,
    EnergizationState,
    InterlockReason,
    OperatingMode,
    QualityReason,
    QualityValidity,
    Unit,
)
from energy_simlab.contracts.records import CommandV1
from energy_simlab.topology import DeterministicTopologyService, reference_topology


def power_command(
    *,
    command_id: str,
    apply_tick: int,
    value_mw: float,
    expected_topology_version: int | None = None,
) -> CommandV1:
    return CommandV1(
        id=command_id,
        source_id="operator",
        logical_tick=70,
        sequence=1,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.OPERATOR,
        apply_tick=apply_tick,
        expiry_tick=apply_tick + 10,
        requested_value=value_mw,
        unit=Unit.MEGAWATT,
        expected_model_version="1.0.0",
        expected_topology_version=expected_topology_version,
        reason="simultaneous M4 dispatch",
    )


def open_command(*, apply_tick: int = 80) -> CommandV1:
    return CommandV1(
        id="CMD-PCC-001",
        source_id="scenario",
        logical_tick=70,
        sequence=2,
        target_id="PCC",
        kind=CommandKind.OPEN_PCC,
        authority=CommandAuthority.SCENARIO,
        apply_tick=apply_tick,
        expiry_tick=apply_tick,
        requested_value=None,
        unit=Unit.NONE,
        expected_topology_version=0,
        reason="open PCC",
    )


def initialized_coordinator() -> tuple[GridConnectedFallbackSlice, IslandTransitionCoordinator]:
    slice_ = GridConnectedFallbackSlice()
    initial = CommandV1(
        id="CMD-P-001",
        source_id="scenario",
        logical_tick=0,
        sequence=1,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.SCENARIO,
        apply_tick=10,
        expiry_tick=20,
        requested_value=0.4,
        unit=Unit.MEGAWATT,
        expected_model_version="1.0.0",
        expected_topology_version=0,
        reason="initial dispatch",
    )
    slice_.execute_macro(initial)
    return slice_, IslandTransitionCoordinator(
        model=slice_.model,
        controller=slice_.controller,
        topology=slice_.topology,
        load_mw=0.6,
        validator=slice_.validator,
    )


def test_open_pcc_components_and_versions_are_exact_and_deterministic():
    topology = reference_topology()
    updated, event = DeterministicTopologyService().open_pcc(
        topology,
        logical_tick=80,
        correlation_id="CMD-PCC-001",
        causation_id="CMD-PCC-001",
    )
    assert [(item.id, item.bus_ids) for item in updated.components] == [
        ("GRID@1", ("GRID",)),
        ("LOCAL@1", ("LOCAL",)),
    ]
    assert [item.actual_state for item in updated.branches] == [BranchState.OPEN]
    assert event.topology_version_before == 0
    assert event.topology_version_after == 1
    assert updated.topology_version == 1
    assert event.energization is EnergizationState.ISLANDED_UNSUPPORTED


def test_topology_first_transition_applies_safe_zero_without_energy_jump_and_raises_alarm():
    slice_, coordinator = initialized_coordinator()
    energy_before = slice_.model.energy_stored_mwh
    result = coordinator.open_pcc(
        open_command=open_command(),
        simultaneous_power_command=power_command(
            command_id="CMD-P-SIMULTANEOUS",
            apply_tick=80,
            value_mw=0.3,
        ),
    )
    assert result.topology.components[1].energization is EnergizationState.ISLANDED_UNSUPPORTED
    assert slice_.model.operating_mode is OperatingMode.ISLANDED_UNSUPPORTED
    assert slice_.controller.target_power_mw == 0.0
    assert slice_.model.applied_power_mw == 0.0
    assert result.interlock_event.reason is InterlockReason.UNSUPPORTED_ISLAND_SAFE_ZERO
    assert result.interlock_event.previous_target_power_mw == 0.4
    assert result.interlock_event.previous_applied_power_mw == 0.4
    assert result.interlock_event.energy_before_mwh == energy_before
    assert result.interlock_event.energy_after_mwh == energy_before
    assert slice_.model.energy_stored_mwh == energy_before

    acknowledgement = result.simultaneous_power_acknowledgement
    assert acknowledgement.status is AcknowledgementStatus.REJECTED
    assert acknowledgement.reason is AcknowledgementReason.TARGET_MODE_UNAVAILABLE
    assert result.balance.grid_import_mw is None
    assert result.balance.island_imbalance_mw == -0.6
    assert result.balance.quality.validity is QualityValidity.UNCERTAIN
    assert result.balance.quality.reason is QualityReason.SIMPLIFIED_ISLAND_PROXY
    assert result.alarm_state.active
    assert not result.alarm_state.acknowledged


def test_correlation_links_topology_interlock_imbalance_alarm_and_simultaneous_command():
    _, coordinator = initialized_coordinator()
    result = coordinator.open_pcc(
        open_command=open_command(),
        simultaneous_power_command=power_command(
            command_id="CMD-P-SIMULTANEOUS",
            apply_tick=80,
            value_mw=0.3,
        ),
    )
    assert result.topology_event.correlation_id == "CMD-PCC-001"
    assert result.interlock_event.correlation_id == "CMD-PCC-001"
    assert result.interlock_event.causation_id == result.topology_event.id
    occurrence = result.alarm_events[0]
    assert occurrence.correlation_id == "CMD-PCC-001"
    assert occurrence.causation_id == result.interlock_event.id
    assert result.balance.correlation_id == "CMD-PCC-001"
    assert result.balance.causation_id == result.interlock_event.id
    assert result.balance.logical_tick == result.topology_event.logical_tick == occurrence.logical_tick
    assert result.simultaneous_power_acknowledgement.correlation_id == "CMD-P-SIMULTANEOUS"


def test_simultaneous_command_with_old_expected_version_proves_post_open_validation():
    _, coordinator = initialized_coordinator()
    result = coordinator.open_pcc(
        open_command=open_command(),
        simultaneous_power_command=power_command(
            command_id="CMD-P-OLD-TOPOLOGY",
            apply_tick=80,
            value_mw=0.3,
            expected_topology_version=0,
        ),
    )
    assert result.topology.topology_version == 1
    assert result.simultaneous_power_acknowledgement.reason is AcknowledgementReason.VERSION_MISMATCH
