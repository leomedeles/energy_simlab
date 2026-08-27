"""Composition-independent domain orchestration."""

from .fallback_slice import FallbackMacroResult, GridConnectedFallbackSlice, reference_configuration
from .api_facade import RuntimeApiFacade
from .islanding import IslandTransitionCoordinator, IslandTransitionResult
from .replay_runtime import FreshRuntimeDestination, ReplayRuntime

__all__ = [
    "FallbackMacroResult",
    "GridConnectedFallbackSlice",
    "IslandTransitionCoordinator",
    "IslandTransitionResult",
    "FreshRuntimeDestination",
    "ReplayRuntime",
    "RuntimeApiFacade",
    "reference_configuration",
]
