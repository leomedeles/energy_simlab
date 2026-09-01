"""Deterministic live-ingress seam and read model for asynchronous adapters."""

from __future__ import annotations

from energy_simlab.contracts.enums import CommandAuthority
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    CommandV1,
    TopologySnapshotV1,
    TraceV1,
)

from .replay_runtime import ReplayRuntime


_AUTHORITY_ORDER = {
    CommandAuthority.INTERLOCK: 1,
    CommandAuthority.SCENARIO: 2,
    CommandAuthority.OPERATOR: 3,
    CommandAuthority.SUPERVISORY: 4,
}


class RuntimeApiFacade:
    def __init__(self, runtime: ReplayRuntime) -> None:
        self.runtime = runtime

    def admit_command(self, command: CommandV1) -> CommandV1:
        current_tick = self.runtime.scheduler.current_tick
        macro_ticks = self.runtime.scenario.configuration.macro_ticks
        if command.apply_tick <= current_tick:
            raise ValueError("live commands must target a future macro boundary")
        if command.apply_tick % macro_ticks:
            raise ValueError("live commands must target an exact macro boundary")
        existing = next(
            (item for item in self.runtime.pending_ingress if item.id == command.id),
            None,
        )
        if existing is not None:
            if existing != command:
                raise ValueError("a command ID cannot be reused with different content")
            return existing
        self.runtime.pending_ingress.append(command)
        self.runtime.pending_ingress.sort(key=self._ingress_key)
        return command

    def get_acknowledgement(self, command_id: str) -> AcknowledgementV1 | None:
        return next(
            (
                item.acknowledgement
                for item in self.runtime.validator.export_receipts()
                if item.command.id == command_id
            ),
            None,
        )

    def read_topology(self) -> TopologySnapshotV1:
        return self.runtime.topology

    def read_trace(self) -> TraceV1:
        return TraceV1(
            run_id=self.runtime.run_id,
            parent_snapshot_id=self.runtime.parent_snapshot_id,
            entries=tuple(self.runtime.trace_entries),
        )

    @staticmethod
    def _ingress_key(command: CommandV1) -> tuple[int, int, str, int, str]:
        return (
            command.apply_tick,
            _AUTHORITY_ORDER[command.authority],
            command.source_id,
            command.sequence,
            command.id,
        )


__all__ = ["RuntimeApiFacade"]
