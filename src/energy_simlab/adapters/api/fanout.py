"""Bounded observation fan-out that cannot back-pressure the simulation owner."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, replace

from energy_simlab.contracts.ports import PublicationSink
from energy_simlab.contracts.records import MacroPublicationV1, TelemetrySampleV1, VersionedV1


PublicationEncoder = Callable[[VersionedV1], bytes]


class ViewerDisconnected(RuntimeError):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ViewerPublicationFrame:
    logical_tick: int
    sequence: int
    schema_version: str
    canonical_bytes: bytes
    publication: MacroPublicationV1


class ViewerSession:
    def __init__(self, *, viewer_id: str, capacity: int, encoder: PublicationEncoder) -> None:
        self.viewer_id = viewer_id
        self.capacity = capacity
        self._encoder = encoder
        self._queue: deque[ViewerPublicationFrame] = deque()
        self._available = asyncio.Event()
        self.connected = True
        self.disconnect_reason: str | None = None
        self.dropped_publications = 0

    @property
    def queued_count(self) -> int:
        return len(self._queue)

    def enqueue(self, publication: MacroPublicationV1) -> None:
        if not self.connected:
            return
        if len(self._queue) < self.capacity:
            self._queue.append(self._frame(publication))
            self._available.set()
            return

        telemetry_frames = [
            frame for frame in self._queue if not frame.publication.discrete_records
        ]
        discrete_frames = [
            frame for frame in self._queue if frame.publication.discrete_records
        ]
        if telemetry_frames:
            self.dropped_publications += len(telemetry_frames)
            self._queue = deque(discrete_frames)
            coalesced = self._coalesce(
                [frame.publication for frame in telemetry_frames]
                + ([] if publication.discrete_records else [publication])
            )
            if coalesced is not None:
                self._queue.append(self._frame(coalesced))
                if not publication.discrete_records:
                    self._available.set()
                    return

        if publication.discrete_records:
            if len(self._queue) >= self.capacity:
                self.disconnect("SLOW_VIEWER_RESYNC_REQUIRED")
                return
            self._queue.append(self._frame(publication))
            self._available.set()
            return

        if len(self._queue) < self.capacity:
            self._queue.append(self._frame(publication))
            self._available.set()
        else:
            self.dropped_publications += 1

    def pop_nowait(self) -> ViewerPublicationFrame:
        if not self._queue:
            if not self.connected:
                raise ViewerDisconnected(self.disconnect_reason or "viewer disconnected")
            raise IndexError("viewer queue is empty")
        frame = self._queue.popleft()
        if not self._queue:
            self._available.clear()
        return frame

    async def next_frame(self) -> ViewerPublicationFrame:
        while True:
            if not self.connected:
                raise ViewerDisconnected(self.disconnect_reason or "viewer disconnected")
            if self._queue:
                return self.pop_nowait()
            self._available.clear()
            await self._available.wait()

    def disconnect(self, reason: str) -> None:
        self.connected = False
        self.disconnect_reason = reason
        self._available.set()

    def _frame(self, publication: MacroPublicationV1) -> ViewerPublicationFrame:
        return ViewerPublicationFrame(
            logical_tick=publication.logical_tick,
            sequence=publication.sequence,
            schema_version=publication.schema_version,
            canonical_bytes=self._encoder(publication),
            publication=publication,
        )

    @staticmethod
    def _coalesce(publications: list[MacroPublicationV1]) -> MacroPublicationV1 | None:
        if not publications:
            return None
        latest: dict[tuple[str, str], TelemetrySampleV1] = {}
        for publication in publications:
            for sample in publication.telemetry:
                latest[(sample.subject_id, sample.signal_id)] = sample
        newest = publications[-1]
        return replace(
            newest,
            telemetry=tuple(latest[key] for key in sorted(latest)),
            discrete_records=(),
        )


class BoundedViewerFanout(PublicationSink):
    capacity = 64

    def __init__(
        self,
        *,
        encoder: PublicationEncoder,
        evidence_sink: PublicationSink | None = None,
    ) -> None:
        self._encoder = encoder
        self._evidence_sink = evidence_sink
        self._sessions: dict[str, ViewerSession] = {}
        self.viewer_dropped_publications_total = 0
        self._viewer_sequence = 0

    @property
    def connected_viewers(self) -> int:
        return sum(session.connected for session in self._sessions.values())

    def connect(self, viewer_id: str | None = None) -> ViewerSession:
        if viewer_id is None:
            self._viewer_sequence += 1
            viewer_id = f"viewer-{self._viewer_sequence:08d}"
        if viewer_id in self._sessions and self._sessions[viewer_id].connected:
            raise ValueError(f"viewer is already connected: {viewer_id}")
        session = ViewerSession(
            viewer_id=viewer_id,
            capacity=self.capacity,
            encoder=self._encoder,
        )
        self._sessions[viewer_id] = session
        return session

    def disconnect(self, viewer_id: str, reason: str = "CLIENT_DISCONNECTED") -> None:
        session = self._sessions.get(viewer_id)
        if session is not None and session.connected:
            session.disconnect(reason)

    def publish(self, publication: MacroPublicationV1) -> None:
        if self._evidence_sink is not None:
            self._evidence_sink.publish(publication)
        before = sum(session.dropped_publications for session in self._sessions.values())
        for session in tuple(self._sessions.values()):
            session.enqueue(publication)
        after = sum(session.dropped_publications for session in self._sessions.values())
        self.viewer_dropped_publications_total += after - before


__all__ = [
    "BoundedViewerFanout",
    "ViewerDisconnected",
    "ViewerPublicationFrame",
    "ViewerSession",
]
