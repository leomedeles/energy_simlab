"""Compatibility checks performed before a destination runtime is mutated."""

from __future__ import annotations

from dataclasses import dataclass

from energy_simlab.contracts.records import SnapshotEnvelopeV1


class SnapshotCompatibilityError(ValueError):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class SnapshotCompatibilityPolicy:
    engine_name: str = "energy-simlab"
    engine_version: str = "1.0.0"
    runtime_profile: str = "cpython-3.14.7-windows-x86_64"
    supported_models: tuple[tuple[str, str], ...] = (
        ("bess.detailed", "1.0.0"),
        ("bess.fallback", "1.0.0"),
    )

    def validate(self, envelope: SnapshotEnvelopeV1) -> None:
        if envelope.engine_name != self.engine_name:
            raise SnapshotCompatibilityError("unknown snapshot engine")
        if envelope.engine_version != self.engine_version:
            raise SnapshotCompatibilityError("unknown engine version")
        if envelope.runtime_profile != self.runtime_profile:
            raise SnapshotCompatibilityError("unsupported numerical runtime profile")
        supported = set(self.supported_models)
        for state in envelope.models.model_states:
            if (state.model_id, state.model_version) not in supported:
                raise SnapshotCompatibilityError(
                    f"unsupported model identity/version: {state.model_id} {state.model_version}"
                )
        if envelope.canonicalization_profile != "python-json-v1":
            raise SnapshotCompatibilityError("unsupported canonicalization profile")

