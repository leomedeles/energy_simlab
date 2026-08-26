"""Approved total order for all work at one logical tick."""

from energy_simlab.contracts.enums import EventPhase


PHASE_PRIORITY: dict[EventPhase, int] = {
    EventPhase.EXOGENOUS: 10,
    EventPhase.TOPOLOGY: 20,
    EventPhase.OPERATING_CONTEXT: 30,
    EventPhase.FIDELITY: 40,
    EventPhase.COMMAND: 50,
    EventPhase.CONTROL: 60,
    EventPhase.MODEL_ADVANCE: 70,
    EventPhase.AGGREGATION: 80,
    EventPhase.ALARM: 90,
    EventPhase.PUBLICATION: 100,
    EventPhase.SNAPSHOT: 110,
}


def phase_priority(phase: EventPhase) -> int:
    return PHASE_PRIORITY[phase]

