from energy_simlab.alarms import UnsupportedIslandAlarm
from energy_simlab.contracts.enums import AlarmTransition


def occurrence(alarm: UnsupportedIslandAlarm):
    events = alarm.evaluate(
        islanded_unsupported=True,
        imbalance_mw=-0.6,
        logical_tick=80,
        correlation_id="CMD-PCC-001",
        causation_id="INTERLOCK-EVENT-00000001",
    )
    assert [item.transition for item in events] == [AlarmTransition.OCCURRED]
    assert alarm.state is not None
    return alarm.state.occurrence_id


def test_alarm_acknowledge_while_active_then_return_and_close_sequence_is_exact():
    alarm = UnsupportedIslandAlarm()
    occurrence_id = occurrence(alarm)
    acknowledged = alarm.acknowledge(
        occurrence_id=occurrence_id,
        acknowledge_source_id="operator",
        logical_tick=90,
        correlation_id="CMD-ACK-001",
        causation_id="CMD-ACK-001",
    )
    assert [item.transition for item in acknowledged] == [AlarmTransition.ACKNOWLEDGED]
    assert alarm.state is not None and alarm.state.active and alarm.state.acknowledged
    cleared = alarm.evaluate(
        islanded_unsupported=False,
        imbalance_mw=0.0,
        logical_tick=100,
        correlation_id="TEST-CLEAR",
        causation_id="TEST-CLEAR",
    )
    assert [item.transition for item in cleared] == [
        AlarmTransition.RETURNED_TO_NORMAL,
        AlarmTransition.CLOSED,
    ]
    assert alarm.state is not None and not alarm.state.active and alarm.state.acknowledged


def test_alarm_clear_before_acknowledge_then_acknowledge_and_close_sequence_is_exact():
    alarm = UnsupportedIslandAlarm()
    occurrence_id = occurrence(alarm)
    cleared = alarm.evaluate(
        islanded_unsupported=False,
        imbalance_mw=0.0,
        logical_tick=90,
        correlation_id="TEST-CLEAR",
        causation_id="TEST-CLEAR",
    )
    assert [item.transition for item in cleared] == [AlarmTransition.RETURNED_TO_NORMAL]
    assert alarm.state is not None and not alarm.state.active and not alarm.state.acknowledged
    acknowledged = alarm.acknowledge(
        occurrence_id=occurrence_id,
        acknowledge_source_id="operator",
        logical_tick=100,
        correlation_id="CMD-ACK-001",
        causation_id="CMD-ACK-001",
    )
    assert [item.transition for item in acknowledged] == [
        AlarmTransition.ACKNOWLEDGED,
        AlarmTransition.CLOSED,
    ]
    assert alarm.state is not None and not alarm.state.active and alarm.state.acknowledged

