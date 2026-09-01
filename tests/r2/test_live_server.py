from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request as HttpRequest, urlopen

from wsproto import WSConnection
from wsproto.connection import ConnectionType
from wsproto.events import AcceptConnection, Request, TextMessage


ROOT = Path(__file__).resolve().parents[2]


def _open_server() -> tuple[subprocess.Popen[bytes], socket.socket, WSConnection, int]:
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "energy_simlab.bootstrap",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--pace-seconds",
            "0.05",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    connection: socket.socket | None = None
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("the live R2 server exited before accepting connections")
        try:
            connection = socket.create_connection(("127.0.0.1", port), timeout=0.5)
            break
        except OSError:
            time.sleep(0.05)
    if connection is None:
        process.terminate()
        process.wait(timeout=5.0)
        raise AssertionError("the live R2 server did not become ready")
    connection.settimeout(5.0)
    websocket = WSConnection(ConnectionType.CLIENT)
    connection.sendall(
        websocket.send(
            Request(
                host=f"127.0.0.1:{port}",
                target="/api/v1/publications",
            )
        )
    )
    return process, connection, websocket, port


def _receive_publications(
    connection: socket.socket,
    websocket: WSConnection,
    *,
    through_tick: int,
) -> tuple[bool, list[dict]]:
    accepted = False
    publications: list[dict] = []
    text = ""
    while not publications or publications[-1]["logical_tick"] < through_tick:
        payload = connection.recv(65536)
        if not payload:
            raise AssertionError("the publication WebSocket closed before the target tick")
        websocket.receive_data(payload)
        for event in websocket.events():
            if isinstance(event, AcceptConnection):
                accepted = True
            elif isinstance(event, TextMessage):
                text += event.data
                if event.message_finished:
                    publications.append(json.loads(text))
                    text = ""
    return accepted, publications


def test_real_uvicorn_websocket_post_ack_trace_and_idle_progression() -> None:
    process, connection, websocket, port = _open_server()
    try:
        accepted, initial = _receive_publications(
            connection,
            websocket,
            through_tick=20,
        )
        assert accepted
        first = initial[-1]
        apply_tick = first["logical_tick"] + 50
        command_id = "CMD-R2-REAL-00000001"
        command = {
            "schema_version": "1.0.0",
            "id": command_id,
            "source_id": "r2-real-operator",
            "logical_tick": apply_tick,
            "sequence": 1,
            "target_id": "BESS",
            "kind": "SET_ACTIVE_POWER",
            "authority": "OPERATOR",
            "apply_tick": apply_tick,
            "expiry_tick": apply_tick,
            "requested_value": 0.4,
            "unit": "MW",
            "correlation_id": command_id,
            "expected_model_version": None,
            "expected_topology_version": None,
            "reason": "R2 real Uvicorn integration fixture",
        }
        request = HttpRequest(
            f"http://127.0.0.1:{port}/api/v1/commands",
            data=json.dumps(command, separators=(",", ":")).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5.0) as response:
            assert response.status == 202
            assert json.loads(response.read())["id"] == command_id

        _, later = _receive_publications(
            connection,
            websocket,
            through_tick=apply_tick + 10,
        )
        observed = [*initial, *later]
        ticks = [item["logical_tick"] for item in observed]
        sequences = [item["sequence"] for item in observed]
        assert ticks == sorted(set(ticks))
        assert sequences == sorted(set(sequences))
        assert len(observed) >= 2

        with urlopen(
            f"http://127.0.0.1:{port}/api/v1/acknowledgements/{command_id}",
            timeout=5.0,
        ) as response:
            acknowledgement = json.loads(response.read())
        assert acknowledgement["command_id"] == command_id
        assert acknowledgement["status"] == "ACCEPTED"

        with urlopen(f"http://127.0.0.1:{port}/api/v1/trace", timeout=5.0) as response:
            trace = json.loads(response.read())
        assert command_id in {entry["record_id"] for entry in trace["entries"]}
        assert any(
            record.get("command_id") == command_id
            for publication in observed
            for record in publication["discrete_records"]
        )
    finally:
        connection.close()
        process.terminate()
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5.0)
