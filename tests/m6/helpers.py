from __future__ import annotations

from energy_simlab.contracts.enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    AggregationKind,
    CommandAuthority,
    QualityReason,
    QualityValidity,
    Unit,
)
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    MacroPublicationV1,
    QualityV1,
    TelemetrySampleV1,
)


def publication(
    sequence: int,
    *,
    signal_id: str = "applied_power",
    value: float | None = None,
    discrete: bool = False,
) -> MacroPublicationV1:
    tick = sequence * 10
    sample = TelemetrySampleV1(
        id=f"TEL-VIEWER-{sequence:08d}",
        source_id="viewer-test-publisher",
        logical_tick=tick,
        sequence=sequence,
        subject_id="BESS",
        signal_id=signal_id,
        value=float(sequence) if value is None else value,
        unit=Unit.MEGAWATT,
        aggregation=AggregationKind.END,
        interval_start_tick=tick - 10,
        interval_end_tick=tick,
        quality=QualityV1(
            validity=QualityValidity.GOOD,
            reason=QualityReason.NORMAL,
            detail="viewer isolation fixture",
            origin_id="viewer-test-publisher",
            since_tick=tick,
        ),
        model_id="bess.fallback",
        model_version="1.0.0",
        topology_version=0,
    )
    records = ()
    if discrete:
        records = (
            AcknowledgementV1(
                id=f"ACK-VIEWER-{sequence:08d}",
                source_id="viewer-test-validator",
                logical_tick=tick,
                sequence=sequence,
                command_id=f"CMD-VIEWER-{sequence:08d}",
                correlation_id=f"CMD-VIEWER-{sequence:08d}",
                target_id="BESS",
                status=AcknowledgementStatus.ACCEPTED,
                reason=AcknowledgementReason.ACCEPTED,
                detail="discrete viewer delivery fixture",
                effective_tick=tick,
                requested_value=0.0,
                accepted_value=0.0,
                unit=Unit.MEGAWATT,
                model_version="1.0.0",
                topology_version=0,
            ),
        )
    return MacroPublicationV1(
        id=f"PUB-VIEWER-{sequence:08d}",
        source_id="viewer-test-publisher",
        logical_tick=tick,
        sequence=sequence,
        run_id="TT000-VIEWER-TEST",
        interval_start_tick=tick - 10,
        interval_end_tick=tick,
        telemetry=(sample,),
        discrete_records=records,
        energy_residual_mwh=0.0,
        coupling_residual_mwh=0.0,
    )
