"""Lossless in-memory evidence sink for canonical domain publications."""

from __future__ import annotations

from energy_simlab.contracts.records import MacroPublicationV1


class InMemoryPublicationSink:
    def __init__(self) -> None:
        self.publications: list[MacroPublicationV1] = []

    def publish(self, publication: MacroPublicationV1) -> None:
        self.publications.append(publication)


__all__ = ["InMemoryPublicationSink"]
