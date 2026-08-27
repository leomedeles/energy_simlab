"""Single composition root and command-line entry points."""

from .server import ServerComponents, ServerConfiguration, compose_server, run_server

__all__ = [
    "ServerComponents",
    "ServerConfiguration",
    "compose_server",
    "run_server",
]
