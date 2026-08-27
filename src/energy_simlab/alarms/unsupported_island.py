"""Minimal two-axis lifecycle for the unsupported-island imbalance alarm."""

from __future__ import annotations

from energy_simlab.contracts.enums import AlarmSeverity, AlarmTransition
from energy_simlab.contracts.records import AlarmEventV1, AlarmRuntimeSnapshotV1, AlarmStateV1


class UnsupportedIslandAlarm:
    condition_key = "UNSUPPORTED_ISLAND_POWER_IMBALANCE"
    source_id = "alarm-service"

    def __init__(self, *, threshold_mw: float = 0.05) -> None:
        if threshold_mw < 0:
            raise ValueError("alarm threshold must be non-negative")
        self.threshold_mw = threshold_mw
        self._event_sequence = 0
        self._occurrence_sequence = 0
        self._state: AlarmStateV1 | None = None

    @property
    def state(self) -> AlarmStateV1 | None:
        return self._state

    def export_snapshot(self) -> AlarmRuntimeSnapshotV1:
        return AlarmRuntimeSnapshotV1(
            states=() if self._state is None else (self._state,),
            event_sequence=self._event_sequence,
            next_occurrence_sequence=self._occurrence_sequence,
        )

    @classmethod
    def from_snapshot(
        cls,
        snapshot: AlarmRuntimeSnapshotV1,
        *,
        threshold_mw: float = 0.05,
    ) -> "UnsupportedIslandAlarm":
        if len(snapshot.states) > 1:
            raise ValueError("TT-000 supports one alarm condition state")
        alarm = cls(threshold_mw=threshold_mw)
        alarm._state = None if not snapshot.states else snapshot.states[0]
        alarm._event_sequence = snapshot.event_sequence
        alarm._occurrence_sequence = snapshot.next_occurrence_sequence
        return alarm

    def evaluate(
        self,
        *,
        islanded_unsupported: bool,
        imbalance_mw: float,
        logical_tick: int,
        correlation_id: str,
        causation_id: str,
    ) -> tuple[AlarmEventV1, ...]:
        condition = islanded_unsupported and abs(imbalance_mw) > self.threshold_mw
        if condition and (self._state is None or not self._state.active):
            if self._state is not None and not self._state.acknowledged:
                raise ValueError("a returned unacknowledged occurrence must be acknowledged before re-occurrence")
            self._occurrence_sequence += 1
            occurrence_id = f"OCC-UNSUPPORTED-ISLAND-{self._occurrence_sequence:08d}"
            event = self._event(
                occurrence_id=occurrence_id,
                transition=AlarmTransition.OCCURRED,
                active=True,
                acknowledged=False,
                logical_tick=logical_tick,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            self._state = self._state_record(
                occurrence_id=occurrence_id,
                active=True,
                acknowledged=False,
                active_since_tick=logical_tick,
                return_tick=None,
                acknowledge_tick=None,
                acknowledge_source_id=None,
                logical_tick=logical_tick,
                correlation_id=correlation_id,
            )
            return (event,)

        if not condition and self._state is not None and self._state.active:
            returned = self._event(
                occurrence_id=self._state.occurrence_id,
                transition=AlarmTransition.RETURNED_TO_NORMAL,
                active=False,
                acknowledged=self._state.acknowledged,
                logical_tick=logical_tick,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            previous = self._state
            self._state = self._state_record(
                occurrence_id=previous.occurrence_id,
                active=False,
                acknowledged=previous.acknowledged,
                active_since_tick=previous.active_since_tick,
                return_tick=logical_tick,
                acknowledge_tick=previous.acknowledge_tick,
                acknowledge_source_id=previous.acknowledge_source_id,
                logical_tick=logical_tick,
                correlation_id=correlation_id,
            )
            if self._state.acknowledged:
                return (returned, self._close(logical_tick, correlation_id, returned.id))
            return (returned,)
        return ()

    def acknowledge(
        self,
        *,
        occurrence_id: str,
        acknowledge_source_id: str,
        logical_tick: int,
        correlation_id: str,
        causation_id: str,
    ) -> tuple[AlarmEventV1, ...]:
        if self._state is None or self._state.occurrence_id != occurrence_id:
            raise ValueError("unknown alarm occurrence")
        if self._state.acknowledged:
            return ()
        acknowledged = self._event(
            occurrence_id=occurrence_id,
            transition=AlarmTransition.ACKNOWLEDGED,
            active=self._state.active,
            acknowledged=True,
            logical_tick=logical_tick,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        previous = self._state
        self._state = self._state_record(
            occurrence_id=occurrence_id,
            active=previous.active,
            acknowledged=True,
            active_since_tick=previous.active_since_tick,
            return_tick=previous.return_tick,
            acknowledge_tick=logical_tick,
            acknowledge_source_id=acknowledge_source_id,
            logical_tick=logical_tick,
            correlation_id=correlation_id,
        )
        if not self._state.active:
            return (acknowledged, self._close(logical_tick, correlation_id, acknowledged.id))
        return (acknowledged,)

    def _close(self, logical_tick: int, correlation_id: str, causation_id: str) -> AlarmEventV1:
        assert self._state is not None
        closed = self._event(
            occurrence_id=self._state.occurrence_id,
            transition=AlarmTransition.CLOSED,
            active=False,
            acknowledged=True,
            logical_tick=logical_tick,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        previous = self._state
        self._state = self._state_record(
            occurrence_id=previous.occurrence_id,
            active=False,
            acknowledged=True,
            active_since_tick=previous.active_since_tick,
            return_tick=previous.return_tick,
            acknowledge_tick=previous.acknowledge_tick,
            acknowledge_source_id=previous.acknowledge_source_id,
            logical_tick=logical_tick,
            correlation_id=correlation_id,
        )
        return closed

    def _event(
        self,
        *,
        occurrence_id: str,
        transition: AlarmTransition,
        active: bool,
        acknowledged: bool,
        logical_tick: int,
        correlation_id: str,
        causation_id: str,
    ) -> AlarmEventV1:
        self._event_sequence += 1
        return AlarmEventV1(
            id=f"ALARM-EVENT-{self._event_sequence:08d}",
            source_id=self.source_id,
            logical_tick=logical_tick,
            sequence=self._event_sequence,
            condition_key=self.condition_key,
            occurrence_id=occurrence_id,
            subject_id="LOCAL",
            transition=transition,
            active=active,
            acknowledged=acknowledged,
            severity=AlarmSeverity.WARNING,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def _state_record(
        self,
        *,
        occurrence_id: str,
        active: bool,
        acknowledged: bool,
        active_since_tick: int | None,
        return_tick: int | None,
        acknowledge_tick: int | None,
        acknowledge_source_id: str | None,
        logical_tick: int,
        correlation_id: str,
    ) -> AlarmStateV1:
        return AlarmStateV1(
            id=f"ALARM-STATE-{occurrence_id}",
            source_id=self.source_id,
            logical_tick=logical_tick,
            sequence=self._event_sequence,
            condition_key=self.condition_key,
            occurrence_id=occurrence_id,
            subject_id="LOCAL",
            active=active,
            acknowledged=acknowledged,
            severity=AlarmSeverity.WARNING,
            active_since_tick=active_since_tick,
            return_tick=return_tick,
            acknowledge_tick=acknowledge_tick,
            acknowledge_source_id=acknowledge_source_id,
            correlation_id=correlation_id,
        )
