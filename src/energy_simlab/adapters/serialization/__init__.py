"""Pydantic and strict-JSON mappings at infrastructure boundaries."""

from .dto import ContractDTO, dto_type_for, to_domain, to_dto
from .json_codec import canonical_json_bytes, parse_json_bytes, validate_json_bytes
from .snapshot_codec import SnapshotIntegrityError, decode_snapshot, encode_snapshot

__all__ = [
    "ContractDTO",
    "SnapshotIntegrityError",
    "canonical_json_bytes",
    "dto_type_for",
    "decode_snapshot",
    "encode_snapshot",
    "parse_json_bytes",
    "to_domain",
    "to_dto",
    "validate_json_bytes",
]
