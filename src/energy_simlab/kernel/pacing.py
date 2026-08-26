"""Wall-clock pacing adapters that cannot alter logical execution."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Protocol


class MonotonicClock(Protocol):
    def __call__(self) -> float: ...


class Sleeper(Protocol):
    def __call__(self, seconds: float) -> None: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class PacerDiagnostic:
    logical_tick: int
    deadline_seconds: float
    observed_seconds: float
    overrun_seconds: float


class NoOpPacer:
    diagnostics: tuple[PacerDiagnostic, ...] = ()

    def wait_until(self, logical_tick: int, tick_seconds: float) -> None:
        if logical_tick < 0 or tick_seconds <= 0:
            raise ValueError("pacing requires non-negative ticks and a positive tick duration")


class WallClockPacer:
    def __init__(
        self,
        *,
        logical_origin_tick: int = 0,
        clock: MonotonicClock = time.monotonic,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        if logical_origin_tick < 0:
            raise ValueError("logical origin must be non-negative")
        self._logical_origin_tick = logical_origin_tick
        self._clock = clock
        self._sleeper = sleeper
        self._wall_origin_seconds = clock()
        self._diagnostics: list[PacerDiagnostic] = []

    @property
    def diagnostics(self) -> tuple[PacerDiagnostic, ...]:
        return tuple(self._diagnostics)

    def wait_until(self, logical_tick: int, tick_seconds: float) -> None:
        if logical_tick < self._logical_origin_tick:
            raise ValueError("pacer cannot target a tick before its logical origin")
        if tick_seconds <= 0:
            raise ValueError("tick duration must be positive")
        deadline = self._wall_origin_seconds + (
            logical_tick - self._logical_origin_tick
        ) * tick_seconds
        observed = self._clock()
        remaining = deadline - observed
        if remaining > 0:
            self._sleeper(remaining)
            observed = self._clock()
        overrun = max(0.0, observed - deadline)
        if overrun > 0:
            self._diagnostics.append(
                PacerDiagnostic(
                    logical_tick=logical_tick,
                    deadline_seconds=deadline,
                    observed_seconds=observed,
                    overrun_seconds=overrun,
                )
            )

