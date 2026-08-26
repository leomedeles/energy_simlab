"""Injectable deterministic record identity and source-local sequences."""

from __future__ import annotations

from .events import SourceSequenceState


class DeterministicIdSource:
    def __init__(self, state: tuple[SourceSequenceState, ...] = ()) -> None:
        self._sequences = {item.source_id: item.value for item in state}
        if len(self._sequences) != len(state):
            raise ValueError("source sequence state contains duplicate source IDs")

    def next_sequence(self, source_id: str) -> int:
        if not source_id or not source_id.strip():
            raise ValueError("source_id must not be empty")
        next_value = self._sequences.get(source_id, 0) + 1
        self._sequences[source_id] = next_value
        return next_value

    def next_id(self, source_id: str, prefix: str) -> tuple[str, int]:
        if not prefix or not prefix.strip():
            raise ValueError("prefix must not be empty")
        sequence = self.next_sequence(source_id)
        normalized_source = source_id.upper().replace(" ", "-")
        return f"{prefix}-{normalized_source}-{sequence:08d}", sequence

    def export_state(self) -> tuple[SourceSequenceState, ...]:
        return tuple(
            SourceSequenceState(source_id=source_id, value=value)
            for source_id, value in sorted(self._sequences.items())
        )

    def restore_state(self, state: tuple[SourceSequenceState, ...]) -> None:
        restored = {item.source_id: item.value for item in state}
        if len(restored) != len(state):
            raise ValueError("source sequence state contains duplicate source IDs")
        self._sequences = restored

