"""Approved total order for all work at one logical tick."""

from energy_simlab.contracts.enums import EventPhase, event_phase_priority


PHASE_PRIORITY = {phase: event_phase_priority(phase) for phase in EventPhase}


def phase_priority(phase: EventPhase) -> int:
    return PHASE_PRIORITY[phase]
