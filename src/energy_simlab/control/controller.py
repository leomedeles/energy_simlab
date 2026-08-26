"""Explicit requested, accepted and target power ownership."""

from __future__ import annotations

from dataclasses import dataclass

from energy_simlab.contracts.enums import AcknowledgementStatus
from energy_simlab.contracts.records import CommandV1

from .commands import CommandDecision


@dataclass(frozen=True, slots=True, kw_only=True)
class PowerOwnership:
    requested_power_mw: float
    accepted_power_mw: float
    target_power_mw: float
    applied_power_mw: float


class PowerController:
    def __init__(self) -> None:
        self.requested_power_mw = 0.0
        self.accepted_power_mw = 0.0
        self.target_power_mw = 0.0

    def apply_decision(self, command: CommandV1, decision: CommandDecision) -> None:
        if decision.acknowledgement.status not in {
            AcknowledgementStatus.ACCEPTED,
            AcknowledgementStatus.ACCEPTED_WITH_LIMIT,
        }:
            return
        assert command.requested_value is not None
        assert decision.accepted_power_mw is not None
        self.requested_power_mw = command.requested_value
        self.accepted_power_mw = decision.accepted_power_mw
        self.target_power_mw = decision.accepted_power_mw

    def observe(self, applied_power_mw: float) -> PowerOwnership:
        return PowerOwnership(
            requested_power_mw=self.requested_power_mw,
            accepted_power_mw=self.accepted_power_mw,
            target_power_mw=self.target_power_mw,
            applied_power_mw=applied_power_mw,
        )

