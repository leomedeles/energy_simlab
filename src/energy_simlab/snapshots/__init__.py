"""Versioned snapshot and replay boundary."""

from .compatibility import SnapshotCompatibilityError, SnapshotCompatibilityPolicy

__all__ = ["SnapshotCompatibilityError", "SnapshotCompatibilityPolicy"]
