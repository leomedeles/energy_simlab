"""Typed scheduler entries; callbacks and arbitrary payload dictionaries are excluded."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from energy_simlab.contracts.enums import EventPhase
from energy_simlab.contracts.records import CommandV1

from .phases import phase_priority


class KernelEventKind(StrEnum):
    TOY = "TOY"
    COMMAND = "COMMAND"
    CHILD_STEP = "CHILD_STEP"
    MACRO_AGGREGATION = "MACRO_AGGREGATION"
    PUBLICATION = "PUBLICATION"


@dataclass(frozen=True, slots=True, order=True, kw_only=True)
class KernelEvent:
    sort_key: tuple[int, int, int, int] = field(init=False, repr=False)
    logical_tick: int = field(compare=False)
    phase: EventPhase = field(compare=False)
    source_order: int = field(compare=False)
    insertion_sequence: int = field(compare=False)
    id: str = field(compare=False)
    source_id: str = field(compare=False)
    kind: KernelEventKind = field(compare=False)
    subject_id: str = field(compare=False)
    command: CommandV1 | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.logical_tick < 0:
            raise ValueError("logical_tick must be non-negative")
        if self.source_order < 0:
            raise ValueError("source_order must be non-negative")
        if self.insertion_sequence < 0:
            raise ValueError("insertion_sequence must be non-negative")
        for name, value in (("id", self.id), ("source_id", self.source_id), ("subject_id", self.subject_id)):
            if not value or not value.strip():
                raise ValueError(f"{name} must not be empty")
        object.__setattr__(
            self,
            "sort_key",
            (
                self.logical_tick,
                phase_priority(self.phase),
                self.source_order,
                self.insertion_sequence,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class QueuedEventState:
    event: KernelEvent
    cancelled: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceSequenceState:
    source_id: str
    value: int


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerState:
    current_tick: int
    active_phase: EventPhase | None
    closed_through_tick: int
    next_insertion_sequence: int
    queued_events: tuple[QueuedEventState, ...]
    cancelled_event_ids: tuple[str, ...]
    source_sequences: tuple[SourceSequenceState, ...]

