"""Standard-library-only semantic validation shared by domain contracts."""

from math import isfinite
import re


SCHEMA_VERSION = "1.0.0"
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def require_v1(version: str) -> None:
    match = _SEMVER.fullmatch(version)
    if match is None or int(match.group(1)) != 1:
        raise ValueError(f"unsupported schema version: {version!r}; expected major version 1")


def require_version(value: str, field: str) -> None:
    if _SEMVER.fullmatch(value) is None:
        raise ValueError(f"{field} must be a semantic version")


def require_text(value: str, field: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field} must not be empty")


def require_non_negative(value: int | float, field: str) -> None:
    if value < 0:
        raise ValueError(f"{field} must be non-negative")


def require_positive(value: int | float, field: str) -> None:
    if value <= 0:
        raise ValueError(f"{field} must be positive")


def require_finite(value: float, field: str) -> None:
    if not isfinite(value):
        raise ValueError(f"{field} must be finite")


def require_probability(value: float, field: str) -> None:
    require_finite(value, field)
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field} must be in [0, 1]")


def require_sha256(value: str, field: str, *, allow_empty: bool = False) -> None:
    if allow_empty and value == "":
        return
    if _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 hexadecimal digest")

