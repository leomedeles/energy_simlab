"""Thin FastAPI mapping around canonical application/domain records."""

from __future__ import annotations

from typing import Protocol, cast

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from energy_simlab.adapters.serialization import ContractDTO, dto_type_for, to_domain, to_dto
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    CommandV1,
    TopologySnapshotV1,
    TraceV1,
)

from .fanout import BoundedViewerFanout, ViewerDisconnected


CommandV1DTO = dto_type_for(CommandV1)
AcknowledgementV1DTO = dto_type_for(AcknowledgementV1)
TopologySnapshotV1DTO = dto_type_for(TopologySnapshotV1)
TraceV1DTO = dto_type_for(TraceV1)


class ApiApplication(Protocol):
    def admit_command(self, command: CommandV1) -> CommandV1: ...

    def get_acknowledgement(self, command_id: str) -> AcknowledgementV1 | None: ...

    def read_topology(self) -> TopologySnapshotV1: ...

    def read_trace(self) -> TraceV1: ...


def create_app(
    *,
    application: ApiApplication,
    fanout: BoundedViewerFanout,
    viewer_html: str,
) -> FastAPI:
    app = FastAPI(title="Energy SimLab TT-000", version="1.0.0")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def viewer() -> str:
        return viewer_html

    @app.post(
        "/api/v1/commands",
        response_model=CommandV1DTO,
        status_code=202,
    )
    async def submit_command(command: CommandV1DTO) -> ContractDTO:
        domain_command = cast(CommandV1, to_domain(command))
        try:
            admitted = application.admit_command(domain_command)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return to_dto(admitted)

    @app.get(
        "/api/v1/acknowledgements/{command_id}",
        response_model=AcknowledgementV1DTO,
    )
    async def acknowledgement(command_id: str) -> ContractDTO:
        record = application.get_acknowledgement(command_id)
        if record is None:
            raise HTTPException(status_code=404, detail="acknowledgement is not available")
        return to_dto(record)

    @app.get("/api/v1/topology", response_model=TopologySnapshotV1DTO)
    async def topology() -> ContractDTO:
        return to_dto(application.read_topology())

    @app.get("/api/v1/trace", response_model=TraceV1DTO)
    async def trace() -> ContractDTO:
        return to_dto(application.read_trace())

    @app.get("/api/v1/diagnostics")
    async def diagnostics() -> dict[str, int]:
        return {
            "connected_viewers": fanout.connected_viewers,
            "viewer_dropped_publications_total": fanout.viewer_dropped_publications_total,
        }

    @app.websocket("/api/v1/publications")
    async def publications(websocket: WebSocket) -> None:
        await websocket.accept()
        session = fanout.connect()
        try:
            while True:
                frame = await session.next_frame()
                await websocket.send_text(frame.canonical_bytes.decode("utf-8"))
        except ViewerDisconnected as error:
            await websocket.close(code=4409, reason=str(error))
        except WebSocketDisconnect:
            pass
        finally:
            fanout.disconnect(session.viewer_id)

    return app


__all__ = ["ApiApplication", "create_app"]
