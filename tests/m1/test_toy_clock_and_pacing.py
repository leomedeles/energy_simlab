from __future__ import annotations

from energy_simlab.kernel import FixedRatioClock, NoOpPacer, WallClockPacer, run_toy


class ManualClock:
    def __init__(self, initial: float = 0.0) -> None:
        self.now = initial
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_fixed_ratio_clock_rejects_non_integral_ratio():
    try:
        FixedRatioClock(child_ticks=3, macro_ticks=10)
    except ValueError as error:
        assert "integral" in str(error)
    else:
        raise AssertionError("non-integral clock ratio was accepted")


def test_toy_clock_completes_exact_integer_ticks_and_ten_to_one_boundaries():
    result = run_toy(pacer=NoOpPacer(), macro_periods=3)
    assert result.final_tick == 30
    assert result.child_completions == 30
    assert result.macro_boundaries == (10, 20, 30)
    assert all(isinstance(entry.logical_tick, int) for entry in result.trace)


def test_fast_forward_and_paced_runs_have_byte_identical_canonical_trace():
    fast = run_toy(pacer=NoOpPacer(), macro_periods=2)
    manual = ManualClock()
    paced_adapter = WallClockPacer(clock=manual.monotonic, sleeper=manual.sleep)
    paced = run_toy(pacer=paced_adapter, macro_periods=2)
    assert manual.sleeps == [1.0, 1.0]
    assert paced_adapter.diagnostics == ()
    assert paced.canonical_trace_bytes() == fast.canonical_trace_bytes()
    assert paced.final_tick == fast.final_tick
    assert paced.child_completions == fast.child_completions


def test_pacer_overrun_is_diagnostic_only_and_cannot_change_logical_result():
    baseline = run_toy(pacer=NoOpPacer(), macro_periods=2)
    manual = ManualClock()
    overrun_pacer = WallClockPacer(clock=manual.monotonic, sleeper=manual.sleep)
    manual.now = 100.0
    overrun = run_toy(pacer=overrun_pacer, macro_periods=2)
    assert manual.sleeps == []
    assert [item.logical_tick for item in overrun_pacer.diagnostics] == [10, 20]
    assert overrun.canonical_trace_bytes() == baseline.canonical_trace_bytes()

