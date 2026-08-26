"""M1-only deterministic toy run used to characterize kernel semantics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from energy_simlab.contracts.enums import EventPhase
from energy_simlab.contracts.ports import Pacer

from .events import KernelEvent, KernelEventKind
from .scheduler import DeterministicScheduler


@dataclass(frozen=True, slots=True, kw_only=True)
class FixedRatioClock:
    base_tick_seconds: float = 0.1
    child_ticks: int = 1
    macro_ticks: int = 10

    def __post_init__(self) -> None:
        if self.base_tick_seconds <= 0 or self.child_ticks <= 0 or self.macro_ticks <= 0:
            raise ValueError("clock periods must be positive")
        if self.macro_ticks % self.child_ticks:
            raise ValueError("macro/child ratio must be integral")

    @property
    def ratio(self) -> int:
        return self.macro_ticks // self.child_ticks


@dataclass(frozen=True, slots=True, kw_only=True)
class ToyTraceEntry:
    event_id: str
    logical_tick: int
    phase: EventPhase
    source_order: int
    insertion_sequence: int
    kind: KernelEventKind


@dataclass(frozen=True, slots=True, kw_only=True)
class ToyRunResult:
    trace: tuple[ToyTraceEntry, ...]
    final_tick: int
    child_completions: int
    macro_boundaries: tuple[int, ...]

    def canonical_trace_bytes(self) -> bytes:
        values = []
        for entry in self.trace:
            value = asdict(entry)
            value["phase"] = entry.phase.value
            value["kind"] = entry.kind.value
            values.append(value)
        return json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_toy(
    *,
    pacer: Pacer,
    macro_periods: int = 2,
    clock: FixedRatioClock = FixedRatioClock(),
) -> ToyRunResult:
    if macro_periods <= 0:
        raise ValueError("macro_periods must be positive")
    scheduler = DeterministicScheduler()
    final_tick = macro_periods * clock.macro_ticks
    for child_tick in range(clock.child_ticks, final_tick + 1, clock.child_ticks):
        scheduler.schedule(
            logical_tick=child_tick,
            phase=EventPhase.MODEL_ADVANCE,
            source_order=0,
            source_id="toy-model",
            kind=KernelEventKind.CHILD_STEP,
            subject_id="toy-child",
        )
    macro_boundaries = tuple(range(clock.macro_ticks, final_tick + 1, clock.macro_ticks))
    for boundary in macro_boundaries:
        scheduler.schedule(
            logical_tick=boundary,
            phase=EventPhase.AGGREGATION,
            source_order=0,
            source_id="toy-application",
            kind=KernelEventKind.MACRO_AGGREGATION,
            subject_id="toy-macro",
        )
        scheduler.schedule(
            logical_tick=boundary,
            phase=EventPhase.PUBLICATION,
            source_order=0,
            source_id="toy-application",
            kind=KernelEventKind.PUBLICATION,
            subject_id="toy-publication",
        )

    trace: list[ToyTraceEntry] = []

    def record(event: KernelEvent, _scheduler: DeterministicScheduler) -> None:
        trace.append(
            ToyTraceEntry(
                event_id=event.id,
                logical_tick=event.logical_tick,
                phase=event.phase,
                source_order=event.source_order,
                insertion_sequence=event.insertion_sequence,
                kind=event.kind,
            )
        )

    for boundary in macro_boundaries:
        scheduler.run_until(boundary, record)
        pacer.wait_until(boundary, clock.base_tick_seconds)

    return ToyRunResult(
        trace=tuple(trace),
        final_tick=scheduler.current_tick,
        child_completions=sum(entry.kind is KernelEventKind.CHILD_STEP for entry in trace),
        macro_boundaries=macro_boundaries,
    )

