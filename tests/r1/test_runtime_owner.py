from __future__ import annotations

from hashlib import sha256

import pytest

from energy_simlab.adapters.serialization import canonical_json_bytes
from energy_simlab.application import IntegratedRuntimeOwner, ReplayRuntime
from energy_simlab.contracts.enums import (
    CommandAuthority,
    CommandKind,
    EventPhase,
    Unit,
)
from energy_simlab.contracts.records import CommandV1, TraceV1
from energy_simlab.kernel import NoOpPacer, WallClockPacer


def command(
    command_id: str,
    *,
    sequence: int,
    tick: int,
    kind: CommandKind = CommandKind.SET_ACTIVE_POWER,
    value_mw: float | None = None,
) -> CommandV1:
    return CommandV1(
        id=command_id,
        source_id="r1-scenario",
        logical_tick=tick,
        sequence=sequence,
        target_id="BESS",
        kind=kind,
        authority=CommandAuthority.SCENARIO,
        apply_tick=tick,
        expiry_tick=tick,
        requested_value=value_mw,
        unit=Unit.MEGAWATT if value_mw is not None else Unit.NONE,
        correlation_id=command_id,
        reason="R1 integrated owner fixture",
    )


def trace_bytes(owner: IntegratedRuntimeOwner) -> bytes:
    runtime = owner.runtime
    return canonical_json_bytes(
        TraceV1(
            run_id=runtime.run_id,
            parent_snapshot_id=runtime.parent_snapshot_id,
            entries=tuple(runtime.trace_entries),
        )
    )


def test_two_consecutive_fallback_macros_hold_power_and_complete_all_children() -> None:
    owner = IntegratedRuntimeOwner.new_reference(record_encoder=canonical_json_bytes)
    owner.run_until(10)

    commanded = owner.advance_one_macro(
        (command("CMD-R1-P-001", sequence=1, tick=10, value_mw=0.4),)
    )
    energy_at_20 = owner.runtime.active_model.energy_stored_mwh
    commandless = owner.advance_one_macro()

    assert commanded.child_completions == commandless.child_completions == 10
    assert energy_at_20 == pytest.approx(1.0 - 0.4 / 3600.0, rel=1e-12, abs=1e-12)
    assert owner.runtime.active_model.energy_stored_mwh == pytest.approx(
        1.0 - 2.0 * 0.4 / 3600.0,
        rel=1e-12,
        abs=1e-12,
    )
    assert owner.runtime.controller.accepted_power_mw == 0.4
    assert owner.runtime.controller.target_power_mw == 0.4
    assert commanded.publication.sequence == 2
    assert commandless.publication.sequence == 3


def test_detailed_commandless_macro_has_ten_children_energy_and_residuals() -> None:
    owner = IntegratedRuntimeOwner.new_reference(record_encoder=canonical_json_bytes)
    owner.run_until(10)
    owner.advance_one_macro(
        (command("CMD-R1-P-001", sequence=1, tick=10, value_mw=0.4),)
    )
    owner.run_until(30)
    activated = owner.advance_one_macro(
        (
            command(
                "CMD-R1-M-001",
                sequence=2,
                tick=30,
                kind=CommandKind.ACTIVATE_DETAILED_MODEL,
            ),
        )
    )
    energy_at_40 = owner.runtime.active_model.energy_stored_mwh

    commandless = owner.advance_one_macro()

    assert activated.child_completions == commandless.child_completions == 10
    assert owner.runtime.active_model.energy_stored_mwh < energy_at_40
    assert abs(activated.publication.energy_residual_mwh) <= 1e-10
    assert abs(commandless.publication.energy_residual_mwh) <= 1e-10
    assert abs(activated.publication.coupling_residual_mwh) <= 1e-12
    assert abs(commandless.publication.coupling_residual_mwh) <= 1e-12


def test_real_owner_executes_the_approved_phase_order_and_publishes_every_macro() -> None:
    owner = IntegratedRuntimeOwner.new_reference(record_encoder=canonical_json_bytes)

    result = owner.advance_one_macro()

    assert result.phase_order == tuple(EventPhase)
    assert owner.last_phase_order == tuple(EventPhase)
    assert result.interval_start_tick == 0
    assert result.interval_end_tick == 10
    assert result.publication.logical_tick == 10
    assert result.publication.interval_start_tick == 0
    assert result.publication.interval_end_tick == 10
    assert result.publication.discrete_records == ()


def test_public_simulation_advancement_exists_only_on_the_integrated_owner() -> None:
    assert not hasattr(ReplayRuntime, "run_until")
    assert hasattr(ReplayRuntime, "_advance_scheduler_only")
    assert callable(IntegratedRuntimeOwner.run_until)
    assert callable(IntegratedRuntimeOwner.advance_one_macro)


class FakeWallTime:
    def __init__(self) -> None:
        self.value = 1000.0

    def clock(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


def run_with_pacer(paced: bool) -> tuple[bytes, float, str]:
    owner = IntegratedRuntimeOwner.new_reference(record_encoder=canonical_json_bytes)
    if paced:
        wall = FakeWallTime()
        pacer = WallClockPacer(clock=wall.clock, sleeper=wall.sleep)
    else:
        pacer = NoOpPacer()
    owner.run_until(10, pacer=pacer)
    owner.advance_one_macro(
        (command("CMD-R1-P-001", sequence=1, tick=10, value_mw=0.4),)
    )
    owner.run_until(40, pacer=pacer)
    return (
        trace_bytes(owner),
        owner.runtime.active_model.energy_stored_mwh,
        sha256(trace_bytes(owner)).hexdigest(),
    )


def test_fast_and_paced_modes_share_the_owner_and_are_canonically_equal() -> None:
    assert run_with_pacer(False) == run_with_pacer(True)
