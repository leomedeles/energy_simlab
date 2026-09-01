from __future__ import annotations

import asyncio

import pytest

from energy_simlab.adapters.serialization import canonical_json_bytes
from energy_simlab.application import IntegratedRuntimeOwner
from energy_simlab.bootstrap import ServerConfiguration, compose_server
from energy_simlab.contracts.enums import CommandAuthority, CommandKind, Unit
from energy_simlab.contracts.records import CommandV1


def _power_command() -> CommandV1:
    return CommandV1(
        id="CMD-R0-GD003-00000001",
        source_id="corrective-r0",
        logical_tick=10,
        sequence=1,
        target_id="BESS",
        kind=CommandKind.SET_ACTIVE_POWER,
        authority=CommandAuthority.OPERATOR,
        apply_tick=10,
        expiry_tick=10,
        requested_value=0.4,
        unit=Unit.MEGAWATT,
        correlation_id="CMD-R0-GD003-00000001",
        reason="R0 characterization of commandless macro advancement",
    )


async def _observe_lifespan_idle_state() -> tuple[int, int]:
    components = compose_server(
        ServerConfiguration(pacing_interval_seconds=0.01)
    )
    inbound: asyncio.Queue[dict[str, str]] = asyncio.Queue()
    outbound: asyncio.Queue[dict[str, str]] = asyncio.Queue()
    await inbound.put({"type": "lifespan.startup"})

    async def receive() -> dict[str, str]:
        return await inbound.get()

    async def send(message: dict[str, str]) -> None:
        await outbound.put(message)

    task = asyncio.create_task(
        components.asgi_app(
            {"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}},
            receive,
            send,
        )
    )
    startup = await asyncio.wait_for(outbound.get(), timeout=1.0)
    assert startup["type"] == "lifespan.startup.complete"
    await asyncio.sleep(0.04)
    observed = (
        components.runtime.scheduler.current_tick,
        len(components.evidence_sink.publications),
    )
    await inbound.put({"type": "lifespan.shutdown"})
    shutdown = await asyncio.wait_for(outbound.get(), timeout=1.0)
    assert shutdown["type"] == "lifespan.shutdown.complete"
    await asyncio.wait_for(task, timeout=1.0)
    return observed


def test_gd002_launched_composition_advances_and_publishes_while_idle() -> None:
    tick, publication_count = asyncio.run(_observe_lifespan_idle_state())
    assert tick >= 10
    assert publication_count >= 1


def test_gd003_commandless_macro_advances_held_fallback_power() -> None:
    owner = IntegratedRuntimeOwner.new_reference(record_encoder=canonical_json_bytes)
    owner.run_until(10)
    owner.advance_one_macro((_power_command(),))
    energy_at_tick_20 = owner.runtime.active_model.energy_stored_mwh

    owner.run_until(30)

    assert owner.runtime.active_model.energy_stored_mwh == pytest.approx(
        energy_at_tick_20 - 0.4 / 3600.0,
        rel=1e-12,
        abs=1e-12,
    )
