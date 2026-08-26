"""Composition-independent domain orchestration."""

from .fallback_slice import FallbackMacroResult, GridConnectedFallbackSlice, reference_configuration
from .islanding import IslandTransitionCoordinator, IslandTransitionResult

__all__ = [
    "FallbackMacroResult",
    "GridConnectedFallbackSlice",
    "IslandTransitionCoordinator",
    "IslandTransitionResult",
    "reference_configuration",
]
