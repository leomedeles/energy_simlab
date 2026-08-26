"""Deterministic finite-JSON mapping at the serialization boundary."""

from __future__ import annotations

import json

from pydantic import ValidationError

from energy_simlab.contracts.records import VersionedV1

from .dto import ContractDTO, dto_type_for, to_domain, to_dto


def canonical_json_bytes(record: VersionedV1) -> bytes:
    payload = to_dto(record).model_dump(mode="json")
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def parse_json_bytes(domain_type: type[VersionedV1], payload: bytes) -> VersionedV1:
    dto_type = dto_type_for(domain_type)
    dto = dto_type.model_validate_json(payload)
    return to_domain(dto)


def validate_json_bytes(domain_type: type[VersionedV1], payload: bytes) -> ContractDTO:
    """Validate external bytes while retaining an edge-only DTO."""

    return dto_type_for(domain_type).model_validate_json(payload)


__all__ = [
    "ValidationError",
    "canonical_json_bytes",
    "parse_json_bytes",
    "validate_json_bytes",
]

