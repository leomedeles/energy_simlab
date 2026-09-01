"""Launch the single-owner TT-000 HTTP/WebSocket viewer adapter."""

from __future__ import annotations

import argparse

from .server import ServerConfiguration, run_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the TT-000 single-owner viewer server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--pace-seconds", default=1.0, type=float)
    args = parser.parse_args(argv)
    run_server(
        ServerConfiguration(
            host=args.host,
            port=args.port,
            pacing_interval_seconds=args.pace_seconds,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
