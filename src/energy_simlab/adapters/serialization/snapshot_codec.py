"""python-json-v1 snapshot canonicalization and SHA-256 integrity."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from hmac import compare_digest
from typing import cast

from pydantic import ValidationError

from energy_simlab.contracts.records import SnapshotEnvelopeV1

from .json_codec import canonical_json_bytes, parse_json_bytes


class SnapshotIntegrityError(ValueError):
    pass


def encode_snapshot(envelope: SnapshotEnvelopeV1) -> bytes:
    unsigned = replace(envelope, checksum_sha256="")
    checksum = sha256(canonical_json_bytes(unsigned)).hexdigest()
    return canonical_json_bytes(replace(unsigned, checksum_sha256=checksum))


def decode_snapshot(payload: bytes) -> SnapshotEnvelopeV1:
    try:
        parsed = cast(SnapshotEnvelopeV1, parse_json_bytes(SnapshotEnvelopeV1, payload))
    except (ValidationError, ValueError) as error:
        raise SnapshotIntegrityError("snapshot is not a valid SnapshotEnvelopeV1") from error
    unsigned = replace(parsed, checksum_sha256="")
    expected = sha256(canonical_json_bytes(unsigned)).hexdigest()
    if not compare_digest(parsed.checksum_sha256, expected):
        raise SnapshotIntegrityError("snapshot checksum does not match canonical content")
    return parsed


__all__ = ["SnapshotIntegrityError", "decode_snapshot", "encode_snapshot"]

