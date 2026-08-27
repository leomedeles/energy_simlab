"""Load the packaged static single-line viewer without runtime templating."""

from __future__ import annotations

from importlib.resources import files


def viewer_html() -> str:
    return files("energy_simlab.viewer").joinpath("index.html").read_text(encoding="utf-8")


__all__ = ["viewer_html"]
