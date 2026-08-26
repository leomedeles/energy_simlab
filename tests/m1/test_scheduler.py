from __future__ import annotations

import pytest

from energy_simlab.contracts.enums import EventPhase
from energy_simlab.kernel import (
    PHASE_PRIORITY,
    DeterministicIdSource,
    DeterministicScheduler,
    KernelEvent,
    KernelEventKind,
    SchedulingCausalityError,
)


APPROVED_PHASES = (
    EventPhase.EXOGENOUS,
    EventPhase.TOPOLOGY,
    EventPhase.OPERATING_CONTEXT,
    EventPhase.FIDELITY,
    EventPhase.COMMAND,
    EventPhase.CONTROL,
    EventPhase.MODEL_ADVANCE,
    EventPhase.AGGREGATION,
    EventPhase.ALARM,
    EventPhase.PUBLICATION,
    EventPhase.SNAPSHOT,
)


def _schedule_toy(
    scheduler: DeterministicScheduler,
    *,
    tick: int,
    phase: EventPhase,
    source_order: int,
    subject: str,
) -> KernelEvent:
    return scheduler.schedule(
        logical_tick=tick,
        phase=phase,
        source_order=source_order,
        source_id="test-source",
        kind=KernelEventKind.TOY,
        subject_id=subject,
    )


def test_phase_priorities_are_the_gate_c_approved_values():
    assert tuple(PHASE_PRIORITY[phase] for phase in APPROVED_PHASES) == (
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        80,
        90,
        100,
        110,
    )


def test_hand_authored_order_across_every_phase():
    scheduler = DeterministicScheduler()
    for phase in reversed(APPROVED_PHASES):
        _schedule_toy(scheduler, tick=5, phase=phase, source_order=0, subject=phase.value)
    observed: list[EventPhase] = []
    scheduler.run_until(5, lambda event, _: observed.append(event.phase))
    assert tuple(observed) == APPROVED_PHASES


def test_equal_phase_orders_by_source_before_insertion():
    scheduler = DeterministicScheduler()
    _schedule_toy(scheduler, tick=3, phase=EventPhase.COMMAND, source_order=20, subject="later-source")
    _schedule_toy(scheduler, tick=3, phase=EventPhase.COMMAND, source_order=10, subject="earlier-source")
    observed: list[str] = []
    scheduler.run_until(3, lambda event, _: observed.append(event.subject_id))
    assert observed == ["earlier-source", "later-source"]


def test_equal_phase_and_source_preserve_insertion_order():
    scheduler = DeterministicScheduler()
    for subject in ("first", "second", "third"):
        _schedule_toy(scheduler, tick=3, phase=EventPhase.COMMAND, source_order=10, subject=subject)
    observed: list[str] = []
    scheduler.run_until(3, lambda event, _: observed.append(event.subject_id))
    assert observed == ["first", "second", "third"]


def test_same_tick_later_phase_can_be_scheduled_during_handler():
    scheduler = DeterministicScheduler()
    _schedule_toy(scheduler, tick=4, phase=EventPhase.COMMAND, source_order=0, subject="command")
    observed: list[EventPhase] = []

    def handle(event: KernelEvent, active: DeterministicScheduler) -> None:
        observed.append(event.phase)
        if event.phase is EventPhase.COMMAND:
            _schedule_toy(active, tick=4, phase=EventPhase.CONTROL, source_order=0, subject="control")

    scheduler.run_until(4, handle)
    assert observed == [EventPhase.COMMAND, EventPhase.CONTROL]


@pytest.mark.parametrize("phase", [EventPhase.EXOGENOUS, EventPhase.COMMAND])
def test_equal_or_completed_phase_is_rejected_during_handler(phase: EventPhase):
    scheduler = DeterministicScheduler()
    _schedule_toy(scheduler, tick=4, phase=EventPhase.COMMAND, source_order=0, subject="command")

    def handle(_event: KernelEvent, active: DeterministicScheduler) -> None:
        with pytest.raises(SchedulingCausalityError):
            _schedule_toy(active, tick=4, phase=phase, source_order=0, subject="invalid")

    scheduler.run_until(4, handle)


def test_quiesced_tick_is_closed_to_new_work():
    scheduler = DeterministicScheduler()
    scheduler.run_until(6, lambda _event, _active: None)
    with pytest.raises(SchedulingCausalityError, match="closed"):
        _schedule_toy(scheduler, tick=6, phase=EventPhase.SNAPSHOT, source_order=0, subject="late")


def test_cancelled_event_remains_a_tombstone_and_never_executes_after_restore():
    scheduler = DeterministicScheduler()
    first = _schedule_toy(scheduler, tick=1, phase=EventPhase.COMMAND, source_order=0, subject="first")
    cancelled = _schedule_toy(scheduler, tick=2, phase=EventPhase.COMMAND, source_order=0, subject="cancelled")
    assert scheduler.cancel(cancelled.id)
    assert not scheduler.cancel(cancelled.id)

    state = scheduler.export_state()
    assert state.cancelled_event_ids == (cancelled.id,)
    assert [item.cancelled for item in state.queued_events] == [False, True]

    restored = DeterministicScheduler.from_state(state)
    next_event = _schedule_toy(
        restored,
        tick=3,
        phase=EventPhase.COMMAND,
        source_order=0,
        subject="after-restore",
    )
    assert next_event.insertion_sequence == 3
    assert next_event.id.endswith("00000003")
    observed: list[str] = []
    restored.run_until(3, lambda event, _: observed.append(event.subject_id))
    assert observed == [first.subject_id, "after-restore"]
    assert restored.export_state().cancelled_event_ids == (cancelled.id,)


def test_deterministic_id_source_state_is_sorted_and_restorable():
    source = DeterministicIdSource()
    assert source.next_id("z-source", "REC") == ("REC-Z-SOURCE-00000001", 1)
    assert source.next_id("a-source", "REC") == ("REC-A-SOURCE-00000001", 1)
    state = source.export_state()
    assert [item.source_id for item in state] == ["a-source", "z-source"]
    restored = DeterministicIdSource(state)
    assert restored.next_id("z-source", "REC") == ("REC-Z-SOURCE-00000002", 2)

