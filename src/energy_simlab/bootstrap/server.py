"""Single-owner ASGI composition and Uvicorn launch guard."""

from __future__ import annotations

from dataclasses import dataclass

import uvicorn

from energy_simlab.adapters.api import BoundedViewerFanout, create_app
from energy_simlab.adapters.persistence import InMemoryPublicationSink
from energy_simlab.adapters.serialization import canonical_json_bytes
from energy_simlab.application import ReplayRuntime, RuntimeApiFacade
from energy_simlab.viewer import viewer_html


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerConfiguration:
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    reload: bool = False

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.workers != 1:
            raise ValueError("the in-memory simulation owner requires exactly one ASGI worker")
        if self.reload:
            raise ValueError("auto-reload can duplicate the in-memory simulation owner")


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerComponents:
    runtime: ReplayRuntime
    application: RuntimeApiFacade
    evidence_sink: InMemoryPublicationSink
    fanout: BoundedViewerFanout
    asgi_app: object


def compose_server(
    configuration: ServerConfiguration | None = None,
) -> ServerComponents:
    _ = configuration or ServerConfiguration()
    runtime = ReplayRuntime.new_reference(record_encoder=canonical_json_bytes)
    application = RuntimeApiFacade(runtime)
    evidence_sink = InMemoryPublicationSink()
    fanout = BoundedViewerFanout(
        encoder=canonical_json_bytes,
        evidence_sink=evidence_sink,
    )
    return ServerComponents(
        runtime=runtime,
        application=application,
        evidence_sink=evidence_sink,
        fanout=fanout,
        asgi_app=create_app(
            application=application,
            fanout=fanout,
            viewer_html=viewer_html(),
        ),
    )


def run_server(configuration: ServerConfiguration | None = None) -> None:
    config = configuration or ServerConfiguration()
    components = compose_server(config)
    uvicorn.run(
        components.asgi_app,
        host=config.host,
        port=config.port,
        workers=config.workers,
        reload=config.reload,
    )


__all__ = ["ServerComponents", "ServerConfiguration", "compose_server", "run_server"]
