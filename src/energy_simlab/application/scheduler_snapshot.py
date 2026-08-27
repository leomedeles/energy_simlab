"""Canonical mapping between the scheduler's private heap state and V1 contracts."""

from __future__ import annotations

from energy_simlab.contracts.records import (
    ScheduledEventSnapshotV1,
    SchedulerSnapshotV1,
    SourceCounterV1,
)
from energy_simlab.kernel.events import (
    KernelEvent,
    KernelEventKind,
    QueuedEventState,
    SchedulerState,
    SourceSequenceState,
)


def scheduler_to_snapshot(
    state: SchedulerState,
    *,
    publication_sequence: int,
) -> SchedulerSnapshotV1:
    return SchedulerSnapshotV1(
        current_tick=state.current_tick,
        current_phase=state.active_phase,
        closed_through_tick=state.closed_through_tick,
        insertion_sequence=state.next_insertion_sequence,
        publication_sequence=publication_sequence,
        source_counters=tuple(
            SourceCounterV1(source_id=item.source_id, value=item.value)
            for item in state.source_sequences
        ),
        pending_events=tuple(
            ScheduledEventSnapshotV1(
                event_id=item.event.id,
                source_id=item.event.source_id,
                event_kind=item.event.kind.value,
                subject_id=item.event.subject_id,
                logical_tick=item.event.logical_tick,
                phase=item.event.phase,
                source_order=item.event.source_order,
                insertion_sequence=item.event.insertion_sequence,
                command=item.event.command,
                cancelled=item.cancelled,
            )
            for item in state.queued_events
        ),
        cancelled_event_ids=state.cancelled_event_ids,
    )


def scheduler_from_snapshot(snapshot: SchedulerSnapshotV1) -> SchedulerState:
    cancelled = set(snapshot.cancelled_event_ids)
    queued = tuple(
        QueuedEventState(
            event=KernelEvent(
                logical_tick=item.logical_tick,
                phase=item.phase,
                source_order=item.source_order,
                insertion_sequence=item.insertion_sequence,
                id=item.event_id,
                source_id=item.source_id,
                kind=KernelEventKind(item.event_kind),
                subject_id=item.subject_id,
                command=item.command,
            ),
            cancelled=item.cancelled,
        )
        for item in snapshot.pending_events
    )
    if any(item.cancelled != (item.event.id in cancelled) for item in queued):
        raise ValueError("queued cancellation flags disagree with tombstone state")
    return SchedulerState(
        current_tick=snapshot.current_tick,
        active_phase=snapshot.current_phase,
        closed_through_tick=snapshot.closed_through_tick,
        next_insertion_sequence=snapshot.insertion_sequence,
        queued_events=queued,
        cancelled_event_ids=snapshot.cancelled_event_ids,
        source_sequences=tuple(
            SourceSequenceState(source_id=item.source_id, value=item.value)
            for item in snapshot.source_counters
        ),
    )


__all__ = ["scheduler_from_snapshot", "scheduler_to_snapshot"]
