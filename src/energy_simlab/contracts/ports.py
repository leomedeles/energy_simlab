"""Inward-facing ports owned by the domain/application boundary."""

from __future__ import annotations

from typing import Protocol

from .enums import OperatingMode
from .records import (
    ActivePowerBalanceV1,
    CommandV1,
    MacroPublicationV1,
    SnapshotEnvelopeV1,
    TopologySnapshotV1,
    TraceEntryV1,
)


class BessPowerModel(Protocol):
    model_id: str
    model_version: str
    operating_mode: OperatingMode

    def static_power_range_mw(self) -> tuple[float, float]: ...

    def feasible_power_range_mw(self, duration_seconds: float) -> tuple[float, float]: ...


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
