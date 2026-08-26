"""Single-threaded deterministic logical-time scheduler."""

from __future__ import annotations

import heapq
from collections.abc import Callable

from energy_simlab.contracts.enums import EventPhase
from energy_simlab.contracts.records import CommandV1

from .events import KernelEvent, KernelEventKind, QueuedEventState, SchedulerState
from .ids import DeterministicIdSource
from .phases import phase_priority


class SchedulingCausalityError(ValueError):
    """Raised when new work attempts to enter completed logical time."""


EventHandler = Callable[[KernelEvent, "DeterministicScheduler"], None]


class DeterministicScheduler:
    def __init__(self) -> None:
        self._queue: list[KernelEvent] = []
        self._event_ids: set[str] = set()
        self._cancelled: set[str] = set()
        self._next_insertion_sequence = 0
        self._ids = DeterministicIdSource()
        self.current_tick = 0
        self.active_phase: EventPhase | None = None
        self.closed_through_tick = -1

    def schedule(
        self,
        *,
        logical_tick: int,
        phase: EventPhase,
        source_order: int,
        source_id: str,
        kind: KernelEventKind,
        subject_id: str,
        event_id: str | None = None,
        command: CommandV1 | None = None,
    ) -> KernelEvent:
        if logical_tick <= self.closed_through_tick:
            raise SchedulingCausalityError(
                f"tick {logical_tick} is closed through {self.closed_through_tick}"
            )
        if logical_tick < self.current_tick:
            raise SchedulingCausalityError(
                f"cannot schedule tick {logical_tick} before current tick {self.current_tick}"
            )
        if logical_tick == self.current_tick and self.active_phase is not None:
            if phase_priority(phase) <= phase_priority(self.active_phase):
                raise SchedulingCausalityError(
                    f"same-tick phase {phase.value} must follow active phase {self.active_phase.value}"
                )
        if event_id is None:
            event_id, _ = self._ids.next_id(source_id, "EVT")
        elif event_id in self._event_ids:
            raise ValueError(f"duplicate event ID: {event_id}")

        self._next_insertion_sequence += 1
        event = KernelEvent(
            logical_tick=logical_tick,
            phase=phase,
            source_order=source_order,
            insertion_sequence=self._next_insertion_sequence,
            id=event_id,
            source_id=source_id,
            kind=kind,
            subject_id=subject_id,
            command=command,
        )
        self._event_ids.add(event.id)
        heapq.heappush(self._queue, event)
        return event

    def cancel(self, event_id: str) -> bool:
        if event_id not in self._event_ids or event_id in self._cancelled:
            return False
        self._cancelled.add(event_id)
        return True

    def run_until(self, logical_tick: int, handler: EventHandler) -> None:
        if logical_tick < self.current_tick:
            raise ValueError("run target cannot move logical time backwards")
        while self._queue and self._queue[0].logical_tick <= logical_tick:
            event = heapq.heappop(self._queue)
            self.current_tick = event.logical_tick
            self.active_phase = event.phase
            if event.id in self._cancelled:
                continue
            handler(event, self)
        self.current_tick = logical_tick
        self.active_phase = None
        self.closed_through_tick = max(self.closed_through_tick, logical_tick)

    def export_state(self) -> SchedulerState:
        queued = tuple(
            QueuedEventState(event=event, cancelled=event.id in self._cancelled)
            for event in sorted(self._queue)
        )
        return SchedulerState(
            current_tick=self.current_tick,
            active_phase=self.active_phase,
            closed_through_tick=self.closed_through_tick,
            next_insertion_sequence=self._next_insertion_sequence,
            queued_events=queued,
            cancelled_event_ids=tuple(sorted(self._cancelled)),
            source_sequences=self._ids.export_state(),
        )

    @classmethod
    def from_state(cls, state: SchedulerState) -> "DeterministicScheduler":
        scheduler = cls()
        scheduler.current_tick = state.current_tick
        scheduler.active_phase = state.active_phase
        scheduler.closed_through_tick = state.closed_through_tick
        scheduler._next_insertion_sequence = state.next_insertion_sequence
        scheduler._queue = [item.event for item in state.queued_events]
        heapq.heapify(scheduler._queue)
        scheduler._event_ids = {item.event.id for item in state.queued_events}
        scheduler._cancelled = set(state.cancelled_event_ids)
        scheduler._ids.restore_state(state.source_sequences)
        if any(item.cancelled != (item.event.id in scheduler._cancelled) for item in state.queued_events):
            raise ValueError("queued cancellation flags disagree with tombstone state")
        return scheduler

