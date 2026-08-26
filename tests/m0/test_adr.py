from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs/decisions/ADR-0001-deterministic-time-contracts-and-snapshots.md"


def test_adr_0001_is_accepted_by_gate_c_and_contains_frozen_phase_order():
    text = ADR.read_text(encoding="utf-8")
    assert "- Status: accepted" in text
    assert "Human project owner through TT-000 Gate C approval" in text
    expected = (
        (10, "EXOGENOUS"),
        (20, "TOPOLOGY"),
        (30, "OPERATING_CONTEXT"),
        (40, "FIDELITY"),
        (50, "COMMAND"),
        (60, "CONTROL"),
        (70, "MODEL_ADVANCE"),
        (80, "AGGREGATION"),
        (90, "ALARM"),
        (100, "PUBLICATION"),
        (110, "SNAPSHOT"),
    )
    positions = [text.index(f"| {value} | {phase} |") for value, phase in expected]
    assert positions == sorted(positions)


def test_adr_0001_transcribes_authority_and_snapshot_decisions():
    text = ADR.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for required in (
        "Safety/interlock actions",
        "Scripted scenario/fault commands",
        "Operator/API commands",
        "Supervisory-controller scheduled requests",
        "python-json-v1",
        "SHA-256 lowercase hexadecimal",
        "CPython 3.14.7",
        "Pickle and executable deserialization are forbidden",
        "byte-identical suffix trace",
    ):
        assert required in normalized
