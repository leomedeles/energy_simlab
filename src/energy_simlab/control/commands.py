"""Deterministic command validation and acknowledgement ownership."""

from __future__ import annotations

from dataclasses import dataclass

from energy_simlab.contracts.enums import (
    AcknowledgementReason,
    AcknowledgementStatus,
    CommandKind,
    OperatingMode,
    Unit,
)
from energy_simlab.contracts.ports import BessPowerModel
from energy_simlab.contracts.records import (
    AcknowledgementV1,
    CommandReceiptV1,
    CommandV1,
    SourceCounterV1,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandDecision:
    acknowledgement: AcknowledgementV1
    accepted_power_mw: float | None
    duplicate: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class _Receipt:
    command: CommandV1
    decision: CommandDecision


class CommandValidator:
    source_id = "command-validator"

    def __init__(self) -> None:
        self._receipts: dict[str, _Receipt] = {}
        self._source_sequences: dict[str, int] = {}
        self._acknowledgement_sequence = 0

    @property
    def acknowledgement_sequence(self) -> int:
        return self._acknowledgement_sequence

    def export_receipts(self) -> tuple[CommandReceiptV1, ...]:
        return tuple(
            CommandReceiptV1(
                command=receipt.command,
                acknowledgement=receipt.decision.acknowledgement,
                executed=receipt.decision.acknowledgement.status
                in {AcknowledgementStatus.ACCEPTED, AcknowledgementStatus.ACCEPTED_WITH_LIMIT},
            )
            for _, receipt in sorted(self._receipts.items())
        )

    def export_source_sequences(self) -> tuple[SourceCounterV1, ...]:
        return tuple(
            SourceCounterV1(source_id=source_id, value=value)
            for source_id, value in sorted(self._source_sequences.items())
        )

    @classmethod
    def from_snapshot(
        cls,
        *,
        receipts: tuple[CommandReceiptV1, ...],
        source_sequences: tuple[SourceCounterV1, ...],
        acknowledgement_sequence: int,
    ) -> "CommandValidator":
        validator = cls()
        validator._acknowledgement_sequence = acknowledgement_sequence
        validator._source_sequences = {item.source_id: item.value for item in source_sequences}
        if len(validator._source_sequences) != len(source_sequences):
            raise ValueError("duplicate validator source sequence")
        for receipt in receipts:
            decision = CommandDecision(
                acknowledgement=receipt.acknowledgement,
                accepted_power_mw=receipt.acknowledgement.accepted_value,
            )
            validator._receipts[receipt.command.id] = _Receipt(
                command=receipt.command,
                decision=decision,
            )
        return validator

    def validate_power_request(
        self,
        command: CommandV1,
        *,
        current_tick: int,
        topology_version: int,
        model: BessPowerModel,
        feasibility_duration_seconds: float,
    ) -> CommandDecision:
        previous = self._receipts.get(command.id)
        if previous is not None:
            if previous.command != command:
                raise ValueError("a command ID cannot be reused with different content")
            return CommandDecision(
                acknowledgement=previous.decision.acknowledgement,
                accepted_power_mw=previous.decision.accepted_power_mw,
                duplicate=True,
            )

        status = AcknowledgementStatus.REJECTED
        reason = AcknowledgementReason.INVALID_SCHEMA
        detail = "unsupported command"
        accepted: float | None = None

        last_sequence = self._source_sequences.get(command.source_id, 0)
        if command.sequence <= last_sequence:
            reason = AcknowledgementReason.STALE_SEQUENCE
            detail = "source sequence is not newer than the last observed command"
        else:
            self._source_sequences[command.source_id] = command.sequence
            if command.apply_tick != current_tick or current_tick > command.expiry_tick:
                reason = AcknowledgementReason.EXPIRED
                detail = "command is not eligible at this logical boundary"
            elif command.target_id != "BESS":
                reason = AcknowledgementReason.UNKNOWN_TARGET
                detail = "target is not the TT-000 BESS"
            elif command.kind is not CommandKind.SET_ACTIVE_POWER or command.unit is not Unit.MEGAWATT:
                reason = AcknowledgementReason.INVALID_UNIT
                detail = "M2 accepts only active-power commands in MW"
            elif command.expected_model_version not in (None, model.model_version):
                reason = AcknowledgementReason.VERSION_MISMATCH
                detail = "expected BESS model version does not match"
            elif command.expected_topology_version not in (None, topology_version):
                reason = AcknowledgementReason.VERSION_MISMATCH
                detail = "expected topology version does not match"
            elif model.operating_mode is not OperatingMode.GRID_CONNECTED_AVAILABLE:
                reason = AcknowledgementReason.TARGET_MODE_UNAVAILABLE
                detail = "BESS is not available in the current operating mode"
            else:
                assert command.requested_value is not None
                static_lower, static_upper = model.static_power_range_mw()
                if not static_lower <= command.requested_value <= static_upper:
                    reason = AcknowledgementReason.NAMEPLATE_LIMIT
                    detail = "requested power is outside the static nameplate range"
                else:
                    feasible_lower, feasible_upper = model.feasible_power_range_mw(
                        feasibility_duration_seconds
                    )
                    accepted = min(max(command.requested_value, feasible_lower), feasible_upper)
                    if accepted != command.requested_value:
                        status = AcknowledgementStatus.ACCEPTED_WITH_LIMIT
                        reason = AcknowledgementReason.ENERGY_FEASIBLE_LIMIT
                        detail = "stored-energy feasibility limits the accepted power"
                    else:
                        status = AcknowledgementStatus.ACCEPTED
                        reason = AcknowledgementReason.ACCEPTED
                        detail = "power request accepted"

        self._acknowledgement_sequence += 1
        acknowledgement_sequence = self._acknowledgement_sequence
        acknowledgement_id = f"ACK-COMMAND-VALIDATOR-{acknowledgement_sequence:08d}"
        acknowledgement = AcknowledgementV1(
            id=acknowledgement_id,
            source_id=self.source_id,
            logical_tick=current_tick,
            sequence=acknowledgement_sequence,
            command_id=command.id,
            correlation_id=command.correlation_id or command.id,
            target_id=command.target_id,
            status=status,
            reason=reason,
            detail=detail,
            effective_tick=current_tick,
            requested_value=command.requested_value,
            accepted_value=accepted,
            unit=command.unit,
            model_version=model.model_version,
            topology_version=topology_version,
        )
        decision = CommandDecision(
            acknowledgement=acknowledgement,
            accepted_power_mw=accepted,
        )
        self._receipts[command.id] = _Receipt(command=command, decision=decision)
        return decision

    def validate_action_request(
        self,
        command: CommandV1,
        *,
        current_tick: int,
        topology_version: int,
        model: BessPowerModel,
        expected_kind: CommandKind,
        expected_target_id: str,
        target_available: bool = True,
    ) -> CommandDecision:
        """Validate a non-numeric TT-000 action through the same dedupe lineage."""

        previous = self._receipts.get(command.id)
        if previous is not None:
            if previous.command != command:
                raise ValueError("a command ID cannot be reused with different content")
            return CommandDecision(
                acknowledgement=previous.decision.acknowledgement,
                accepted_power_mw=None,
                duplicate=True,
            )

        status = AcknowledgementStatus.REJECTED
        reason = AcknowledgementReason.INVALID_SCHEMA
        detail = "unsupported command"
        last_sequence = self._source_sequences.get(command.source_id, 0)
        if command.sequence <= last_sequence:
            reason = AcknowledgementReason.STALE_SEQUENCE
            detail = "source sequence is not newer than the last observed command"
        else:
            self._source_sequences[command.source_id] = command.sequence
            if command.apply_tick != current_tick or current_tick > command.expiry_tick:
                reason = AcknowledgementReason.EXPIRED
                detail = "command is not eligible at this logical boundary"
            elif command.target_id != expected_target_id:
                reason = AcknowledgementReason.UNKNOWN_TARGET
                detail = "command target does not match the requested TT-000 action"
            elif command.kind is not expected_kind:
                reason = AcknowledgementReason.INVALID_SCHEMA
                detail = "command kind does not match the requested TT-000 action"
            elif command.expected_model_version not in (None, model.model_version):
                reason = AcknowledgementReason.VERSION_MISMATCH
                detail = "expected BESS model version does not match"
            elif command.expected_topology_version not in (None, topology_version):
                reason = AcknowledgementReason.VERSION_MISMATCH
                detail = "expected topology version does not match"
            elif not target_available:
                reason = AcknowledgementReason.TARGET_MODE_UNAVAILABLE
                detail = "command target is unavailable in the current operating state"
            else:
                status = AcknowledgementStatus.ACCEPTED
                reason = AcknowledgementReason.ACCEPTED
                detail = "action request accepted"

        self._acknowledgement_sequence += 1
        sequence = self._acknowledgement_sequence
        acknowledgement = AcknowledgementV1(
            id=f"ACK-COMMAND-VALIDATOR-{sequence:08d}",
            source_id=self.source_id,
            logical_tick=current_tick,
            sequence=sequence,
            command_id=command.id,
            correlation_id=command.correlation_id or command.id,
            target_id=command.target_id,
            status=status,
            reason=reason,
            detail=detail,
            effective_tick=current_tick,
            requested_value=None,
            accepted_value=None,
            unit=command.unit,
            model_version=model.model_version,
            topology_version=topology_version,
        )
        decision = CommandDecision(acknowledgement=acknowledgement, accepted_power_mw=None)
        self._receipts[command.id] = _Receipt(command=command, decision=decision)
        return decision
