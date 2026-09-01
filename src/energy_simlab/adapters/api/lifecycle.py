"""ASGI lifespan-managed wall pacing around the synchronous runtime owner."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from energy_simlab.application import IntegratedRuntimeOwner


class RuntimePacingLifecycle:
    """Own exactly one async pacing task and no domain state of its own."""

    def __init__(
        self,
        *,
        owner: IntegratedRuntimeOwner,
        interval_seconds: float,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if interval_seconds <= 0.0:
            raise ValueError("pacing interval must be positive")
        self.owner = owner
        self.interval_seconds = interval_seconds
        self._clock = clock
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None
        self.running = False
        self.macro_in_progress = False
        self.completed_macros = 0
        self.overrun_count = 0

    @property
    def task(self) -> asyncio.Task[None] | None:
        return self._task

    async def start(self) -> None:
        if self.running or self._task is not None:
            raise RuntimeError("runtime pacing lifecycle is already started")
        self._stop_event = asyncio.Event()
        self.running = True
        self._task = asyncio.create_task(
            self._run(),
            name="energy-simlab-runtime-owner",
        )

    async def stop(self) -> None:
        if self._task is None or self._stop_event is None:
            return
        self._stop_event.set()
        await self._task
        self._task = None
        self._stop_event = None
        self.running = False

    @asynccontextmanager
    async def lifespan(self, _app: FastAPI) -> AsyncIterator[None]:
        await self.start()
        try:
            yield
        finally:
            await self.stop()

    async def _run(self) -> None:
        assert self._stop_event is not None
        loop = asyncio.get_running_loop()
        clock = self._clock or loop.time
        next_deadline = clock() + self.interval_seconds
        while not self._stop_event.is_set():
            remaining = next_deadline - clock()
            if remaining > 0.0:
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=remaining,
                    )
                    break
                except TimeoutError:
                    pass
            else:
                self.overrun_count += 1
                await asyncio.sleep(0)

            self.macro_in_progress = True
            try:
                self.owner.advance_one_macro()
                self.completed_macros += 1
            finally:
                self.macro_in_progress = False
            next_deadline += self.interval_seconds
            if next_deadline <= clock():
                self.overrun_count += 1
                next_deadline = clock() + self.interval_seconds


__all__ = ["RuntimePacingLifecycle"]
