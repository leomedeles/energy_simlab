from __future__ import annotations

import asyncio
import json

from energy_simlab.adapters.serialization import (
    canonical_json_bytes,
    parse_json_bytes,
)
from energy_simlab.application import IntegratedRuntimeOwner, ReplayRuntime, RuntimeApiFacade
from energy_simlab.bootstrap import ServerConfiguration, compose_server
from energy_simlab.contracts.enums import CommandAuthority, CommandKind, Unit
from energy_simlab.contracts.records import AcknowledgementV1, CommandV1, TopologySnapshotV1


async def asgi_request(app, method: str, path: str, body: bytes = b""):
    messages: list[dict] = []
    received = False

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": [(b"content-type", b"application/json")],
            "client": ("test", 1234),
            "server": ("test", 80),
        },
        receive,
        send,
    )
    status = next(item["status"] for item in messages if item["type"] == "http.response.start")
    response_body = b"".join(
        item.get("body", b"") for item in messages if item["type"] == "http.response.body"
    )
    return status, response_body


def operator_command() -> CommandV1:
    return CommandV1(
        id="CMD-API-00000001",
        source_id="operator-api",
        logical_tick=10,
        sequence=1,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.OPERATOR,
        apply_tick=10,
        expiry_tick=10,
        requested_value=0.4,
        unit=Unit.MEGAWATT,
        correlation_id="CMD-API-00000001",
        reason="M6 HTTP mapping fixture",
    )


def test_http_request_acknowledgement_and_reads_map_through_edge_dtos():
    components = compose_server()
    command = operator_command()
    status, body = asyncio.run(
        asgi_request(
            components.asgi_app,
            "POST",
            "/api/v1/commands",
            canonical_json_bytes(command),
        )
    )
    assert status == 202
    admitted = parse_json_bytes(CommandV1, body)
    assert admitted == command
    assert type(admitted) is CommandV1

    eligible = components.application.drain_for_tick(10)
    assert eligible == (command,)
    owner = IntegratedRuntimeOwner(runtime=components.runtime)
    owner.run_until(10)
    owner.advance_one_macro(eligible)
    status, body = asyncio.run(
        asgi_request(
            components.asgi_app,
            "GET",
            f"/api/v1/acknowledgements/{command.id}",
        )
    )
    assert status == 200
    acknowledgement = parse_json_bytes(AcknowledgementV1, body)
    assert acknowledgement.command_id == command.id
    assert type(acknowledgement) is AcknowledgementV1

    status, body = asyncio.run(asgi_request(components.asgi_app, "GET", "/api/v1/topology"))
    assert status == 200
    topology = parse_json_bytes(TopologySnapshotV1, body)
    assert topology == components.runtime.topology
    openapi = components.asgi_app.openapi()
    assert openapi["paths"]["/api/v1/commands"]["post"]["requestBody"]
    assert openapi["paths"]["/api/v1/acknowledgements/{command_id}"]["get"]["responses"]["200"]


def test_live_ingress_is_future_boundary_only_and_arrival_order_is_not_execution_order():
    runtime = ReplayRuntime.new_reference(record_encoder=canonical_json_bytes)
    facade = RuntimeApiFacade(runtime)
    later_id = operator_command()
    earlier_id = CommandV1(
        id="CMD-API-00000000",
        source_id=later_id.source_id,
        logical_tick=10,
        sequence=later_id.sequence,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.OPERATOR,
        apply_tick=10,
        expiry_tick=10,
        requested_value=0.2,
        unit=Unit.MEGAWATT,
        correlation_id="CMD-API-00000000",
        reason="canonical ID tie breaker",
    )
    facade.admit_command(later_id)
    facade.admit_command(earlier_id)
    assert facade.drain_for_tick(10) == (earlier_id, later_id)

    stale = CommandV1(
        id="CMD-API-STALE",
        source_id="operator-api",
        logical_tick=0,
        sequence=2,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.OPERATOR,
        apply_tick=0,
        expiry_tick=0,
        requested_value=0.0,
        unit=Unit.MEGAWATT,
    )
    try:
        facade.admit_command(stale)
    except ValueError as error:
        assert "future macro boundary" in str(error)
    else:
        raise AssertionError("current-tick live ingress was not rejected")


def test_in_memory_owner_rejects_multiple_workers_and_auto_reload():
    for kwargs, message in [
        ({"workers": 2}, "exactly one"),
        ({"reload": True}, "auto-reload"),
    ]:
        try:
            ServerConfiguration(**kwargs)
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError(f"invalid server configuration was accepted: {json.dumps(kwargs)}")
