"""Single-owner ASGI composition and Uvicorn launch guard."""

from __future__ import annotations

from dataclasses import dataclass

import uvicorn

from energy_simlab.adapters.api import (
    BoundedViewerFanout,
    RuntimePacingLifecycle,
    create_app,
)
from energy_simlab.adapters.persistence import InMemoryPublicationSink, InMemorySnapshotStore
from energy_simlab.adapters.serialization import canonical_json_bytes, encode_snapshot
from energy_simlab.application import IntegratedRuntimeOwner, ReplayRuntime, RuntimeApiFacade
from energy_simlab.viewer import viewer_html


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerConfiguration:
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    pacing_interval_seconds: float = 1.0

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.workers != 1:
            raise ValueError("the in-memory simulation owner requires exactly one ASGI worker")
        if self.reload:
            raise ValueError("auto-reload can duplicate the in-memory simulation owner")
        if self.pacing_interval_seconds <= 0.0:
            raise ValueError("pacing interval must be positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerComponents:
    runtime: ReplayRuntime
    owner: IntegratedRuntimeOwner
    application: RuntimeApiFacade
    evidence_sink: InMemoryPublicationSink
    snapshot_store: InMemorySnapshotStore
    fanout: BoundedViewerFanout
    lifecycle: RuntimePacingLifecycle
    asgi_app: object


def compose_server(
    configuration: ServerConfiguration | None = None,
) -> ServerComponents:
    config = configuration or ServerConfiguration()
    runtime = ReplayRuntime.new_reference(record_encoder=canonical_json_bytes)
    application = RuntimeApiFacade(runtime)
    evidence_sink = InMemoryPublicationSink()
    snapshot_store = InMemorySnapshotStore()
    fanout = BoundedViewerFanout(
        encoder=canonical_json_bytes,
        evidence_sink=evidence_sink,
    )
    owner = IntegratedRuntimeOwner(
        runtime=runtime,
        publication_sink=fanout,
        snapshot_encoder=encode_snapshot,
        snapshot_store=snapshot_store,
    )
    lifecycle = RuntimePacingLifecycle(
        owner=owner,
        interval_seconds=config.pacing_interval_seconds,
    )
    return ServerComponents(
        runtime=runtime,
        owner=owner,
        application=application,
        evidence_sink=evidence_sink,
        snapshot_store=snapshot_store,
        fanout=fanout,
        lifecycle=lifecycle,
        asgi_app=create_app(
            application=application,
            fanout=fanout,
            viewer_html=viewer_html(),
            lifespan=lifecycle.lifespan,
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
