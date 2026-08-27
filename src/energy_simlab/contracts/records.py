"""Frozen, technology-independent TT-000 domain contracts.

All quantities carry an explicit unit or a field name containing the unit.  The
records deliberately use only Python standard-library types so infrastructure
libraries cannot become domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    AggregationKind,
    AlarmSeverity,
    AlarmTransition,
    BranchState,
    CommandAuthority,
    CommandKind,
    EnergizationState,
    EventPhase,
    FidelityResult,
    InterlockReason,
    OperatingMode,
    QualityReason,
    QualityValidity,
    SnapshotAction,
    TraceRecordKind,
    Unit,
    event_phase_priority,
)
from .validation import (
    SCHEMA_VERSION,
    require_finite,
    require_non_negative,
    require_positive,
    require_probability,
    require_sha256,
    require_text,
    require_v1,
    require_version,
)


ScalarValue: TypeAlias = bool | int | float | str


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionedV1:
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_v1(self.schema_version)


@dataclass(frozen=True, slots=True, kw_only=True)
class IdentifiedRecordV1(VersionedV1):
    id: str
    source_id: str
    logical_tick: int
    sequence: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.id, "id")
        require_text(self.source_id, "source_id")
        require_non_negative(self.logical_tick, "logical_tick")
        require_non_negative(self.sequence, "sequence")


@dataclass(frozen=True, slots=True, kw_only=True)
class QualityV1(VersionedV1):
    validity: QualityValidity
    reason: QualityReason
    detail: str
    origin_id: str
    since_tick: int
    retained_value: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.detail, "detail")
        require_text(self.origin_id, "origin_id")
        require_non_negative(self.since_tick, "since_tick")


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandV1(IdentifiedRecordV1):
    target_id: str
    kind: CommandKind
    authority: CommandAuthority
    apply_tick: int
    expiry_tick: int
    requested_value: float | None
    unit: Unit
    correlation_id: str | None = None
    expected_model_version: str | None = None
    expected_topology_version: int | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.target_id, "target_id")
        require_non_negative(self.apply_tick, "apply_tick")
        require_non_negative(self.expiry_tick, "expiry_tick")
        if self.expiry_tick < self.apply_tick:
            raise ValueError("expiry_tick must be at or after apply_tick")
        if self.requested_value is not None:
            require_finite(self.requested_value, "requested_value")
        if self.kind is CommandKind.SET_ACTIVE_POWER:
            if self.requested_value is None:
                raise ValueError("active-power commands require requested_value")
            if self.unit is not Unit.MEGAWATT:
                raise ValueError("active-power commands require unit MW")
        elif self.unit is not Unit.NONE or self.requested_value is not None:
            raise ValueError("non-numeric commands require no value and unit 1")
        if self.correlation_id is not None:
            require_text(self.correlation_id, "correlation_id")
        if self.expected_model_version is not None:
            require_version(self.expected_model_version, "expected_model_version")
        if self.expected_topology_version is not None:
            require_non_negative(self.expected_topology_version, "expected_topology_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class AcknowledgementV1(IdentifiedRecordV1):
    command_id: str
    correlation_id: str
    target_id: str
    status: AcknowledgementStatus
    reason: AcknowledgementReason
    detail: str
    effective_tick: int
    requested_value: float | None
    accepted_value: float | None
    unit: Unit
    model_version: str
    topology_version: int

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("command_id", self.command_id),
            ("correlation_id", self.correlation_id),
            ("target_id", self.target_id),
            ("detail", self.detail),
        ):
            require_text(value, field)
        require_non_negative(self.effective_tick, "effective_tick")
        for field, value in (
            ("requested_value", self.requested_value),
            ("accepted_value", self.accepted_value),
        ):
            if value is not None:
                require_finite(value, field)
        if (self.requested_value is not None or self.accepted_value is not None) and self.unit is not Unit.MEGAWATT:
            raise ValueError("numeric command acknowledgements require unit MW")
        require_version(self.model_version, "model_version")
        require_non_negative(self.topology_version, "topology_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class TelemetrySampleV1(IdentifiedRecordV1):
    subject_id: str
    signal_id: str
    value: ScalarValue
    unit: Unit
    aggregation: AggregationKind
    interval_start_tick: int
    interval_end_tick: int
    quality: QualityV1
    model_id: str
    model_version: str
    topology_version: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.subject_id, "subject_id")
        require_text(self.signal_id, "signal_id")
        if isinstance(self.value, float):
            require_finite(self.value, "value")
        require_non_negative(self.interval_start_tick, "interval_start_tick")
        require_non_negative(self.interval_end_tick, "interval_end_tick")
        if self.interval_end_tick < self.interval_start_tick:
            raise ValueError("telemetry interval ends before it starts")
        require_text(self.model_id, "model_id")
        require_version(self.model_version, "model_version")
        require_non_negative(self.topology_version, "topology_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class AlarmStateV1(IdentifiedRecordV1):
    condition_key: str
    occurrence_id: str
    subject_id: str
    active: bool
    acknowledged: bool
    severity: AlarmSeverity
    active_since_tick: int | None
    return_tick: int | None
    acknowledge_tick: int | None
    acknowledge_source_id: str | None
    correlation_id: str

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("condition_key", self.condition_key),
            ("occurrence_id", self.occurrence_id),
            ("subject_id", self.subject_id),
            ("correlation_id", self.correlation_id),
        ):
            require_text(value, field)
        for field, value in (
            ("active_since_tick", self.active_since_tick),
            ("return_tick", self.return_tick),
            ("acknowledge_tick", self.acknowledge_tick),
        ):
            if value is not None:
                require_non_negative(value, field)
        if self.acknowledge_source_id is not None:
            require_text(self.acknowledge_source_id, "acknowledge_source_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class AlarmEventV1(IdentifiedRecordV1):
    condition_key: str
    occurrence_id: str
    subject_id: str
    transition: AlarmTransition
    active: bool
    acknowledged: bool
    severity: AlarmSeverity
    correlation_id: str
    causation_id: str

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("condition_key", self.condition_key),
            ("occurrence_id", self.occurrence_id),
            ("subject_id", self.subject_id),
            ("correlation_id", self.correlation_id),
            ("causation_id", self.causation_id),
        ):
            require_text(value, field)


@dataclass(frozen=True, slots=True, kw_only=True)
class BusV1(VersionedV1):
    id: str
    is_infinite_source: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.id, "id")


@dataclass(frozen=True, slots=True, kw_only=True)
class BranchV1(VersionedV1):
    id: str
    from_bus_id: str
    to_bus_id: str
    requested_state: BranchState
    actual_state: BranchState
    state_sequence: int

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("id", self.id),
            ("from_bus_id", self.from_bus_id),
            ("to_bus_id", self.to_bus_id),
        ):
            require_text(value, field)
        if self.from_bus_id == self.to_bus_id:
            raise ValueError("branch endpoints must differ")
        require_non_negative(self.state_sequence, "state_sequence")


@dataclass(frozen=True, slots=True, kw_only=True)
class TerminalV1(VersionedV1):
    id: str
    asset_id: str
    bus_id: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.id, "id")
        require_text(self.asset_id, "asset_id")
        require_text(self.bus_id, "bus_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectedComponentV1(VersionedV1):
    id: str
    bus_ids: tuple[str, ...]
    contains_infinite_source: bool
    energization: EnergizationState

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.id, "id")
        if not self.bus_ids or self.bus_ids != tuple(sorted(set(self.bus_ids))):
            raise ValueError("bus_ids must be a non-empty sorted unique tuple")


@dataclass(frozen=True, slots=True, kw_only=True)
class TopologySnapshotV1(IdentifiedRecordV1):
    topology_version: int
    buses: tuple[BusV1, ...]
    branches: tuple[BranchV1, ...]
    terminals: tuple[TerminalV1, ...]
    components: tuple[ConnectedComponentV1, ...]
    quality: QualityV1

    def __post_init__(self) -> None:
        super().__post_init__()
        require_non_negative(self.topology_version, "topology_version")
        for field, values in (
            ("buses", self.buses),
            ("branches", self.branches),
            ("terminals", self.terminals),
            ("components", self.components),
        ):
            ids = tuple(item.id for item in values)
            if ids != tuple(sorted(set(ids))):
                raise ValueError(f"{field} must be sorted by unique id")


@dataclass(frozen=True, slots=True, kw_only=True)
class TopologyEventV1(IdentifiedRecordV1):
    branch_id: str
    old_requested_state: BranchState
    new_requested_state: BranchState
    old_actual_state: BranchState
    new_actual_state: BranchState
    trigger_kind: str
    correlation_id: str
    causation_id: str
    topology_version_before: int
    topology_version_after: int
    affected_component_ids: tuple[str, ...]
    energization: EnergizationState

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("branch_id", self.branch_id),
            ("trigger_kind", self.trigger_kind),
            ("correlation_id", self.correlation_id),
            ("causation_id", self.causation_id),
        ):
            require_text(value, field)
        require_non_negative(self.topology_version_before, "topology_version_before")
        if self.topology_version_after <= self.topology_version_before:
            raise ValueError("topology version must increase")
        if self.affected_component_ids != tuple(sorted(set(self.affected_component_ids))):
            raise ValueError("affected_component_ids must be sorted and unique")


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivePowerBalanceV1(VersionedV1):
    logical_tick: int
    load_mw: float
    bess_ac_power_mw: float
    grid_import_mw: float | None
    island_imbalance_mw: float | None
    energization: EnergizationState
    quality: QualityV1
    correlation_id: str | None = None
    causation_id: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        require_non_negative(self.logical_tick, "logical_tick")
        for field, value in (
            ("load_mw", self.load_mw),
            ("bess_ac_power_mw", self.bess_ac_power_mw),
        ):
            require_finite(value, field)
        require_non_negative(self.load_mw, "load_mw")
        for field, value in (
            ("grid_import_mw", self.grid_import_mw),
            ("island_imbalance_mw", self.island_imbalance_mw),
        ):
            if value is not None:
                require_finite(value, field)
        if (self.grid_import_mw is None) == (self.island_imbalance_mw is None):
            raise ValueError("exactly one balance result must be present")
        if (self.correlation_id is None) != (self.causation_id is None):
            raise ValueError("balance correlation and causation must be present together")
        if self.correlation_id is not None:
            require_text(self.correlation_id, "correlation_id")
            require_text(self.causation_id or "", "causation_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelHandoffV1(VersionedV1):
    asset_id: str
    from_model_id: str
    from_model_version: str
    to_model_id: str
    to_model_version: str
    logical_tick: int
    energy_stored_mwh: float
    energy_nominal_mwh: float
    soc: float
    requested_power_mw: float
    accepted_power_mw: float
    applied_power_mw: float
    operating_mode: OperatingMode
    energization: EnergizationState
    topology_version: int
    component_id: str
    quality: QualityV1
    last_command_id: str
    source_sequences: tuple[SourceCounterV1, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("asset_id", self.asset_id),
            ("from_model_id", self.from_model_id),
            ("to_model_id", self.to_model_id),
            ("component_id", self.component_id),
            ("last_command_id", self.last_command_id),
        ):
            require_text(value, field)
        require_version(self.from_model_version, "from_model_version")
        require_version(self.to_model_version, "to_model_version")
        require_non_negative(self.logical_tick, "logical_tick")
        for field, value in (
            ("energy_stored_mwh", self.energy_stored_mwh),
            ("energy_nominal_mwh", self.energy_nominal_mwh),
            ("soc", self.soc),
            ("requested_power_mw", self.requested_power_mw),
            ("accepted_power_mw", self.accepted_power_mw),
            ("applied_power_mw", self.applied_power_mw),
        ):
            require_finite(value, field)
        require_positive(self.energy_nominal_mwh, "energy_nominal_mwh")
        require_probability(self.soc, "soc")
        require_non_negative(self.topology_version, "topology_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class FidelityEventV1(IdentifiedRecordV1):
    correlation_id: str
    causation_id: str
    result: FidelityResult
    handoff: ModelHandoffV1
    energy_discontinuity_mwh: float
    soc_discontinuity: float
    power_discontinuity_mw: float
    detail: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.correlation_id, "correlation_id")
        require_text(self.causation_id, "causation_id")
        require_text(self.detail, "detail")
        for field, value in (
            ("energy_discontinuity_mwh", self.energy_discontinuity_mwh),
            ("soc_discontinuity", self.soc_discontinuity),
            ("power_discontinuity_mw", self.power_discontinuity_mw),
        ):
            require_finite(value, field)


@dataclass(frozen=True, slots=True, kw_only=True)
class InterlockEventV1(IdentifiedRecordV1):
    target_id: str
    reason: InterlockReason
    previous_target_power_mw: float
    new_target_power_mw: float
    previous_applied_power_mw: float
    new_applied_power_mw: float
    energy_before_mwh: float
    energy_after_mwh: float
    correlation_id: str
    causation_id: str
    topology_version: int

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("target_id", self.target_id),
            ("correlation_id", self.correlation_id),
            ("causation_id", self.causation_id),
        ):
            require_text(value, field)
        for field, value in (
            ("previous_target_power_mw", self.previous_target_power_mw),
            ("new_target_power_mw", self.new_target_power_mw),
            ("previous_applied_power_mw", self.previous_applied_power_mw),
            ("new_applied_power_mw", self.new_applied_power_mw),
            ("energy_before_mwh", self.energy_before_mwh),
            ("energy_after_mwh", self.energy_after_mwh),
        ):
            require_finite(value, field)
        require_non_negative(self.topology_version, "topology_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class SnapshotLifecycleEventV1(IdentifiedRecordV1):
    snapshot_id: str
    action: SnapshotAction
    correlation_id: str
    causation_id: str
    detail: str

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("snapshot_id", self.snapshot_id),
            ("correlation_id", self.correlation_id),
            ("causation_id", self.causation_id),
            ("detail", self.detail),
        ):
            require_text(value, field)


DiscreteRecordV1: TypeAlias = (
    AcknowledgementV1
    | AlarmEventV1
    | TopologyEventV1
    | FidelityEventV1
    | InterlockEventV1
    | SnapshotLifecycleEventV1
)


@dataclass(frozen=True, slots=True, kw_only=True)
class MacroPublicationV1(IdentifiedRecordV1):
    run_id: str
    interval_start_tick: int
    interval_end_tick: int
    telemetry: tuple[TelemetrySampleV1, ...]
    discrete_records: tuple[DiscreteRecordV1, ...]
    energy_residual_mwh: float
    coupling_residual_mwh: float

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.run_id, "run_id")
        require_non_negative(self.interval_start_tick, "interval_start_tick")
        require_non_negative(self.interval_end_tick, "interval_end_tick")
        if self.interval_end_tick <= self.interval_start_tick:
            raise ValueError("macro publication interval must be positive")
        require_finite(self.energy_residual_mwh, "energy_residual_mwh")
        require_finite(self.coupling_residual_mwh, "coupling_residual_mwh")


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationConfigV1(VersionedV1):
    base_tick_seconds: float
    macro_ticks: int
    energy_nominal_mwh: float
    initial_soc: float
    soc_min: float
    soc_max: float
    charge_limit_mw: float
    discharge_limit_mw: float
    charge_efficiency: float
    discharge_efficiency: float
    response_time_constant_seconds: float
    ramp_up_mw_per_second: float
    ramp_down_mw_per_second: float
    load_mw: float
    island_alarm_threshold_mw: float
    seed: int

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("base_tick_seconds", self.base_tick_seconds),
            ("energy_nominal_mwh", self.energy_nominal_mwh),
            ("charge_limit_mw", self.charge_limit_mw),
            ("discharge_limit_mw", self.discharge_limit_mw),
            ("response_time_constant_seconds", self.response_time_constant_seconds),
            ("ramp_up_mw_per_second", self.ramp_up_mw_per_second),
            ("ramp_down_mw_per_second", self.ramp_down_mw_per_second),
        ):
            require_finite(value, field)
            require_positive(value, field)
        require_positive(self.macro_ticks, "macro_ticks")
        require_probability(self.initial_soc, "initial_soc")
        require_probability(self.soc_min, "soc_min")
        require_probability(self.soc_max, "soc_max")
        if not self.soc_min < self.initial_soc < self.soc_max:
            raise ValueError("initial SoC must lie strictly inside configured bounds")
        for field, value in (
            ("charge_efficiency", self.charge_efficiency),
            ("discharge_efficiency", self.discharge_efficiency),
        ):
            require_probability(value, field)
            require_positive(value, field)
        require_finite(self.load_mw, "load_mw")
        require_non_negative(self.load_mw, "load_mw")
        require_finite(self.island_alarm_threshold_mw, "island_alarm_threshold_mw")
        require_non_negative(self.island_alarm_threshold_mw, "island_alarm_threshold_mw")
        require_non_negative(self.seed, "seed")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScenarioV1(VersionedV1):
    id: str
    version: str
    content_sha256: str
    run_id: str
    configuration: SimulationConfigV1
    scheduled_commands: tuple[CommandV1, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.id, "id")
        require_version(self.version, "version")
        require_sha256(self.content_sha256, "content_sha256")
        require_text(self.run_id, "run_id")
        keys = tuple((item.apply_tick, item.source_id, item.sequence, item.id) for item in self.scheduled_commands)
        if keys != tuple(sorted(keys)):
            raise ValueError("scheduled_commands must be in canonical command order")


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceEntryV1(VersionedV1):
    record_kind: TraceRecordKind
    record_id: str
    logical_tick: int
    sequence: int
    payload_schema_version: str
    canonical_json: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.record_id, "record_id")
        require_non_negative(self.logical_tick, "logical_tick")
        require_non_negative(self.sequence, "sequence")
        require_v1(self.payload_schema_version)
        require_text(self.canonical_json, "canonical_json")


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceV1(VersionedV1):
    run_id: str
    parent_snapshot_id: str | None
    entries: tuple[TraceEntryV1, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.run_id, "run_id")
        if self.parent_snapshot_id is not None:
            require_text(self.parent_snapshot_id, "parent_snapshot_id")
        keys = tuple((item.logical_tick, item.sequence, item.record_id) for item in self.entries)
        if keys != tuple(sorted(keys)):
            raise ValueError("trace entries must be in canonical order")


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceCounterV1(VersionedV1):
    source_id: str
    value: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.source_id, "source_id")
        require_non_negative(self.value, "value")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScheduledEventSnapshotV1(VersionedV1):
    event_id: str
    source_id: str
    event_kind: str
    subject_id: str
    logical_tick: int
    phase: EventPhase
    source_order: int
    insertion_sequence: int
    command: CommandV1 | None
    cancelled: bool

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.event_id, "event_id")
        require_text(self.source_id, "source_id")
        require_text(self.event_kind, "event_kind")
        require_text(self.subject_id, "subject_id")
        require_non_negative(self.logical_tick, "logical_tick")
        require_non_negative(self.source_order, "source_order")
        require_non_negative(self.insertion_sequence, "insertion_sequence")


@dataclass(frozen=True, slots=True, kw_only=True)
class SchedulerSnapshotV1(VersionedV1):
    current_tick: int
    current_phase: EventPhase | None
    closed_through_tick: int
    insertion_sequence: int
    publication_sequence: int
    source_counters: tuple[SourceCounterV1, ...]
    pending_events: tuple[ScheduledEventSnapshotV1, ...]
    cancelled_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        require_non_negative(self.current_tick, "current_tick")
        if self.closed_through_tick < -1:
            raise ValueError("closed_through_tick must be -1 or non-negative")
        require_non_negative(self.insertion_sequence, "insertion_sequence")
        require_non_negative(self.publication_sequence, "publication_sequence")
        source_ids = tuple(item.source_id for item in self.source_counters)
        if source_ids != tuple(sorted(set(source_ids))):
            raise ValueError("source counters must be sorted and unique")
        keys = tuple(
            (
                item.logical_tick,
                event_phase_priority(item.phase),
                item.source_order,
                item.insertion_sequence,
            )
            for item in self.pending_events
        )
        if keys != tuple(sorted(keys)):
            raise ValueError("pending events must be in canonical semantic order")
        if self.cancelled_event_ids != tuple(sorted(set(self.cancelled_event_ids))):
            raise ValueError("cancelled event IDs must be sorted and unique")


@dataclass(frozen=True, slots=True, kw_only=True)
class BessModelStateV1(VersionedV1):
    model_id: str
    model_version: str
    energy_stored_mwh: float
    energy_nominal_mwh: float
    requested_power_mw: float
    accepted_power_mw: float
    target_power_mw: float
    applied_power_mw: float
    operating_mode: OperatingMode
    response_state_mw: float | None
    last_command_id: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.model_id, "model_id")
        require_version(self.model_version, "model_version")
        for field, value in (
            ("energy_stored_mwh", self.energy_stored_mwh),
            ("energy_nominal_mwh", self.energy_nominal_mwh),
            ("requested_power_mw", self.requested_power_mw),
            ("accepted_power_mw", self.accepted_power_mw),
            ("target_power_mw", self.target_power_mw),
            ("applied_power_mw", self.applied_power_mw),
        ):
            require_finite(value, field)
        require_positive(self.energy_nominal_mwh, "energy_nominal_mwh")
        if self.response_state_mw is not None:
            require_finite(self.response_state_mw, "response_state_mw")
        require_text(self.last_command_id, "last_command_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelRegistrySnapshotV1(VersionedV1):
    active_model_id: str
    model_states: tuple[BessModelStateV1, ...]
    transition_sequence: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.active_model_id, "active_model_id")
        require_non_negative(self.transition_sequence, "transition_sequence")
        ids = tuple(item.model_id for item in self.model_states)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("model states must be sorted by unique model_id")
        if self.active_model_id not in ids:
            raise ValueError("active_model_id must identify a captured model")


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandReceiptV1(VersionedV1):
    command: CommandV1
    acknowledgement: AcknowledgementV1
    executed: bool

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.acknowledgement.command_id != self.command.id:
            raise ValueError("receipt acknowledgement must reference its command")


@dataclass(frozen=True, slots=True, kw_only=True)
class ControllerSnapshotV1(VersionedV1):
    requested_power_mw: float
    accepted_power_mw: float
    target_power_mw: float
    interlock_active: bool
    acknowledgement_sequence: int
    receipts: tuple[CommandReceiptV1, ...]
    source_sequences: tuple[SourceCounterV1, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        require_non_negative(self.acknowledgement_sequence, "acknowledgement_sequence")
        for field, value in (
            ("requested_power_mw", self.requested_power_mw),
            ("accepted_power_mw", self.accepted_power_mw),
            ("target_power_mw", self.target_power_mw),
        ):
            require_finite(value, field)


@dataclass(frozen=True, slots=True, kw_only=True)
class TopologyRuntimeSnapshotV1(VersionedV1):
    topology: TopologySnapshotV1
    local_component_id: str
    operating_mode: OperatingMode
    energization: EnergizationState

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.local_component_id, "local_component_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class AlarmRuntimeSnapshotV1(VersionedV1):
    states: tuple[AlarmStateV1, ...]
    event_sequence: int
    next_occurrence_sequence: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require_non_negative(self.event_sequence, "event_sequence")
        require_non_negative(self.next_occurrence_sequence, "next_occurrence_sequence")


@dataclass(frozen=True, slots=True, kw_only=True)
class RngSnapshotV1(VersionedV1):
    algorithm: str
    state_version: int
    state_values: tuple[int, ...]
    gaussian_next: float | None

    def __post_init__(self) -> None:
        super().__post_init__()
        require_text(self.algorithm, "algorithm")
        require_non_negative(self.state_version, "state_version")
        if not self.state_values:
            raise ValueError("RNG state must not be empty")
        if self.gaussian_next is not None:
            require_finite(self.gaussian_next, "gaussian_next")


@dataclass(frozen=True, slots=True, kw_only=True)
class SnapshotEnvelopeV1(VersionedV1):
    snapshot_id: str
    logical_tick: int
    phase: EventPhase
    run_id: str
    parent_run_id: str | None
    parent_snapshot_id: str | None
    engine_name: str
    engine_version: str
    engine_build: str
    runtime_profile: str
    compatibility_range: str
    scenario: ScenarioV1
    configuration_sha256: str
    contract_versions: tuple[str, ...]
    scheduler: SchedulerSnapshotV1
    models: ModelRegistrySnapshotV1
    controller: ControllerSnapshotV1
    topology: TopologyRuntimeSnapshotV1
    alarms: AlarmRuntimeSnapshotV1
    rng: RngSnapshotV1
    pending_ingress: tuple[CommandV1, ...]
    trace: TraceV1
    canonicalization_profile: str
    excluded_infrastructure_state: tuple[str, ...]
    checksum_sha256: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        for field, value in (
            ("snapshot_id", self.snapshot_id),
            ("run_id", self.run_id),
            ("engine_name", self.engine_name),
            ("engine_build", self.engine_build),
            ("runtime_profile", self.runtime_profile),
            ("compatibility_range", self.compatibility_range),
            ("canonicalization_profile", self.canonicalization_profile),
        ):
            require_text(value, field)
        require_non_negative(self.logical_tick, "logical_tick")
        require_version(self.engine_version, "engine_version")
        require_sha256(self.configuration_sha256, "configuration_sha256")
        require_sha256(self.checksum_sha256, "checksum_sha256", allow_empty=True)
        if self.parent_run_id is not None:
            require_text(self.parent_run_id, "parent_run_id")
        if self.parent_snapshot_id is not None:
            require_text(self.parent_snapshot_id, "parent_snapshot_id")
        if not self.contract_versions:
            raise ValueError("contract_versions must not be empty")
        for version in self.contract_versions:
            require_v1(version)
        if self.excluded_infrastructure_state != tuple(sorted(set(self.excluded_infrastructure_state))):
            raise ValueError("excluded infrastructure state must be sorted and unique")


V1_DOMAIN_TYPES: tuple[type[VersionedV1], ...] = (
    QualityV1,
    CommandV1,
    AcknowledgementV1,
    TelemetrySampleV1,
    AlarmStateV1,
    AlarmEventV1,
    BusV1,
    BranchV1,
    TerminalV1,
    ConnectedComponentV1,
    TopologySnapshotV1,
    TopologyEventV1,
    ActivePowerBalanceV1,
    SourceCounterV1,
    ModelHandoffV1,
    FidelityEventV1,
    InterlockEventV1,
    SnapshotLifecycleEventV1,
    MacroPublicationV1,
    SimulationConfigV1,
    ScenarioV1,
    TraceEntryV1,
    TraceV1,
    ScheduledEventSnapshotV1,
    SchedulerSnapshotV1,
    BessModelStateV1,
    ModelRegistrySnapshotV1,
    CommandReceiptV1,
    ControllerSnapshotV1,
    TopologyRuntimeSnapshotV1,
    AlarmRuntimeSnapshotV1,
    RngSnapshotV1,
    SnapshotEnvelopeV1,
)
