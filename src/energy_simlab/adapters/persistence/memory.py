"""In-memory byte stores used by TT-000 snapshot and trace evidence."""

from __future__ import annotations


class InMemorySnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, bytes] = {}

    def put(self, snapshot_id: str, canonical_bytes: bytes) -> None:
        if not snapshot_id or not snapshot_id.strip():
            raise ValueError("snapshot_id must not be empty")
        self._snapshots[snapshot_id] = bytes(canonical_bytes)

    def get(self, snapshot_id: str) -> bytes:
        try:
            return bytes(self._snapshots[snapshot_id])
        except KeyError as error:
            raise KeyError(f"unknown snapshot: {snapshot_id}") from error


__all__ = ["InMemorySnapshotStore"]

