from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import asynccontextmanager

from energy_simlab.adapters.serialization import (
    canonical_json_bytes,
    parse_json_bytes,
)
from energy_simlab.bootstrap import ServerConfiguration, compose_server
from energy_simlab.contracts.enums import (
    AcknowledgementStatus,
    CommandAuthority,
    CommandKind,
    Unit,
)
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    CommandV1,
    TraceV1,
)


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
            "client": ("r2-test", 1234),
            "server": ("r2-test", 80),
        },
        receive,
        send,
    )
    status = next(item["status"] for item in messages if item["type"] == "http.response.start")
    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return status, response_body


@asynccontextmanager
async def active_lifespan(app):
    inbound: asyncio.Queue[dict[str, str]] = asyncio.Queue()
    outbound: asyncio.Queue[dict[str, str]] = asyncio.Queue()

    async def receive() -> dict[str, str]:
        return await inbound.get()

    async def send(message: dict[str, str]) -> None:
        await outbound.put(message)

    task = asyncio.create_task(
        app(
            {"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}},
            receive,
            send,
        )
    )
    await inbound.put({"type": "lifespan.startup"})
    startup = await asyncio.wait_for(outbound.get(), timeout=1.0)
    assert startup["type"] == "lifespan.startup.complete"
    try:
        yield
    finally:
        await inbound.put({"type": "lifespan.shutdown"})
        shutdown = await asyncio.wait_for(outbound.get(), timeout=1.0)
        assert shutdown["type"] == "lifespan.shutdown.complete"
        await asyncio.wait_for(task, timeout=1.0)


async def wait_until(predicate: Callable[[], bool], timeout: float = 1.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() >= deadline:
            raise AssertionError("timed out waiting for the live composition")
        await asyncio.sleep(0.002)


def live_power_command(*, apply_tick: int) -> CommandV1:
    return CommandV1(
        id="CMD-R2-LIVE-00000001",
        source_id="r2-live-operator",
        logical_tick=apply_tick,
        sequence=1,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.OPERATOR,
        apply_tick=apply_tick,
        expiry_tick=apply_tick,
        requested_value=0.4,
        unit=Unit.MEGAWATT,
        correlation_id="CMD-R2-LIVE-00000001",
        reason="R2 live ASGI owner fixture",
    )


def test_lifespan_advances_while_idle_and_shutdown_is_quiescent() -> None:
    async def exercise() -> None:
        components = compose_server(
            ServerConfiguration(pacing_interval_seconds=0.01)
        )
        async with active_lifespan(components.asgi_app):
            await wait_until(lambda: components.owner.current_tick >= 30)
            assert components.lifecycle.running
            assert components.lifecycle.task is not None
            assert components.lifecycle.completed_macros >= 3
            assert len(components.evidence_sink.publications) == (
                components.lifecycle.completed_macros
            )
            assert tuple(
                publication.sequence
                for publication in components.evidence_sink.publications
            ) == tuple(range(1, len(components.evidence_sink.publications) + 1))

        assert not components.lifecycle.running
        assert components.lifecycle.task is None
        assert not components.lifecycle.macro_in_progress
        assert components.runtime.scheduler.active_phase is None
        assert components.owner.current_tick % components.owner.macro_ticks == 0

    asyncio.run(exercise())


def test_http_post_becomes_final_acknowledgement_without_manual_execution() -> None:
    async def exercise() -> None:
        components = compose_server(
            ServerConfiguration(pacing_interval_seconds=0.02)
        )
        command = live_power_command(apply_tick=20)
        async with active_lifespan(components.asgi_app):
            status, body = await asgi_request(
                components.asgi_app,
                "POST",
                "/api/v1/commands",
                canonical_json_bytes(command),
            )
            assert status == 202
            assert parse_json_bytes(CommandV1, body) == command

            await wait_until(lambda: components.owner.current_tick >= 30)
            status, body = await asgi_request(
                components.asgi_app,
                "GET",
                f"/api/v1/acknowledgements/{command.id}",
            )
            assert status == 200
            acknowledgement = parse_json_bytes(AcknowledgementV1, body)
            assert acknowledgement.command_id == command.id
            assert acknowledgement.status is AcknowledgementStatus.ACCEPTED

            status, body = await asgi_request(
                components.asgi_app,
                "GET",
                "/api/v1/trace",
            )
            assert status == 200
            trace = parse_json_bytes(TraceV1, body)
            assert command.id in {entry.record_id for entry in trace.entries}
            assert acknowledgement.id in {entry.record_id for entry in trace.entries}
            assert components.runtime.active_model.energy_stored_mwh < 1.0
            assert any(
                publication.logical_tick >= 30
                and command.id
                in {
                    record.command_id
                    for record in publication.discrete_records
                    if isinstance(record, AcknowledgementV1)
                }
                for publication in components.evidence_sink.publications
            )

    asyncio.run(exercise())


async def run_viewer_pattern(viewer_count: int, slow: bool) -> bytes:
    components = compose_server(ServerConfiguration(pacing_interval_seconds=0.015))
    viewers = [
        components.fanout.connect(f"r2-viewer-{index}")
        for index in range(viewer_count)
    ]
    components.application.admit_command(live_power_command(apply_tick=20))
    async with active_lifespan(components.asgi_app):
        await wait_until(lambda: components.owner.current_tick >= 60)
        if not slow:
            for viewer in viewers:
                while viewer.queued_count:
                    viewer.pop_nowait()
    prefix = tuple(
        entry
        for entry in components.runtime.trace_entries
        if entry.logical_tick <= 60
    )
    return canonical_json_bytes(
        TraceV1(
            run_id=components.runtime.run_id,
            parent_snapshot_id=components.runtime.parent_snapshot_id,
            entries=prefix,
        )
    )


def test_live_zero_one_multiple_and_slow_viewers_preserve_canonical_results() -> None:
    async def exercise() -> None:
        zero = await run_viewer_pattern(0, slow=False)
        one_fast = await run_viewer_pattern(1, slow=False)
        one_slow = await run_viewer_pattern(1, slow=True)
        multiple_slow = await run_viewer_pattern(3, slow=True)
        assert zero == one_fast == one_slow == multiple_slow

    asyncio.run(exercise())
