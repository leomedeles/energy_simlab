"""Inward-facing ports owned by the domain/application boundary."""

from __future__ import annotations

from typing import Protocol

from .records import (
    ActivePowerBalanceV1,
    CommandV1,
    MacroPublicationV1,
    SnapshotEnvelopeV1,
    TopologySnapshotV1,
    TraceEntryV1,
)


class CommandIngress(Protocol):
    def drain_for_tick(self, logical_tick: int) -> tuple[CommandV1, ...]: ...


class PublicationSink(Protocol):
    def publish(self, publication: MacroPublicationV1) -> None: ...


class TraceRecorder(Protocol):
    def append(self, entry: TraceEntryV1) -> None: ...


class SnapshotStore(Protocol):
    def put(self, snapshot_id: str, canonical_bytes: bytes) -> None: ...

    def get(self, snapshot_id: str) -> bytes: ...


class Pacer(Protocol):
    def wait_until(self, logical_tick: int, tick_seconds: float) -> None: ...


class TopologyService(Protocol):
    def recompute(self, topology: TopologySnapshotV1, logical_tick: int) -> TopologySnapshotV1: ...


class ActivePowerBalance(Protocol):
    def calculate(
        self,
        *,
        logical_tick: int,
        load_mw: float,
        bess_ac_power_mw: float,
        topology: TopologySnapshotV1,
    ) -> ActivePowerBalanceV1: ...


class SnapshotAssembler(Protocol):
    def capture(self) -> SnapshotEnvelopeV1: ...

