from __future__ import annotations

from importlib import metadata
from pathlib import Path
import base64
import os
import socket
import subprocess
import sys
import time
import tomllib

from energy_simlab.adapters.api import create_app
from energy_simlab.adapters.api.fanout import BoundedViewerFanout
from energy_simlab.adapters.persistence import InMemoryPublicationSink
from energy_simlab.adapters.serialization import canonical_json_bytes
from energy_simlab.application import ReplayRuntime, RuntimeApiFacade
from energy_simlab.viewer import viewer_html
from uvicorn.config import Config


ROOT = Path(__file__).resolve().parents[2]


def test_locked_api_profile_loads_the_selected_wsproto_backend() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "wsproto==1.3.2" in project["project"]["optional-dependencies"]["api"]
    assert "wsproto==1.3.2" in (ROOT / "requirements.lock").read_text(encoding="utf-8").splitlines()
    assert metadata.version("wsproto") == "1.3.2"

    runtime = ReplayRuntime.new_reference(record_encoder=canonical_json_bytes)
    evidence = InMemoryPublicationSink()
    fanout = BoundedViewerFanout(encoder=canonical_json_bytes, evidence_sink=evidence)
    app = create_app(
        application=RuntimeApiFacade(runtime),
        fanout=fanout,
        viewer_html=viewer_html(),
    )
    config = Config(app=app, ws="auto", lifespan="off")
    config.load()

    assert config.ws_protocol_class is not None
    assert config.ws_protocol_class.__module__ == "uvicorn.protocols.websockets.wsproto_impl"


def test_locked_profile_accepts_the_real_publication_websocket_upgrade() -> None:
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
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    connection: socket.socket | None = None
    try:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError("the Uvicorn WebSocket probe exited before accepting connections")
            try:
                connection = socket.create_connection(("127.0.0.1", port), timeout=0.25)
                break
            except OSError:
                time.sleep(0.05)
        if connection is None:
            raise AssertionError("the Uvicorn WebSocket probe did not become ready")

        websocket_key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            "GET /api/v1/publications HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {websocket_key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        connection.sendall(request)
        response = connection.recv(4096)
        assert response.startswith(b"HTTP/1.1 101 Switching Protocols\r\n")
    finally:
        if connection is not None:
            connection.close()
        process.terminate()
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5.0)
