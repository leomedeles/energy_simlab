from __future__ import annotations

from energy_simlab.adapters.api import BoundedViewerFanout
from energy_simlab.adapters.persistence import InMemoryPublicationSink
from energy_simlab.adapters.serialization import canonical_json_bytes
from energy_simlab.bootstrap.demonstration import run_reference_demonstration


class ViewerPatternSink:
    def __init__(self, viewer_count: int, pattern: str) -> None:
        self.evidence = InMemoryPublicationSink()
        self.fanout = BoundedViewerFanout(
            encoder=canonical_json_bytes,
            evidence_sink=self.evidence,
        )
        self.viewers = [self.fanout.connect(f"reference-{index}") for index in range(viewer_count)]
        self.pattern = pattern
        self.publication_count = 0

    def publish(self, publication) -> None:
        self.publication_count += 1
        self.fanout.publish(publication)
        if self.pattern == "fast":
            for viewer in self.viewers:
                viewer.pop_nowait()
        elif self.pattern == "mixed" and self.publication_count % 2 == 0:
            for viewer in self.viewers[::2]:
                while viewer.queued_count:
                    viewer.pop_nowait()


def run_pattern(viewer_count: int, pattern: str):
    sink = ViewerPatternSink(viewer_count, pattern)
    result = run_reference_demonstration(suffix="A", publication_sink=sink)
    assert len(sink.evidence.publications) == 12
    return result.canonical_trace, result.final_snapshot


def test_reference_scenario_is_exact_with_zero_one_and_multiple_viewer_patterns():
    zero = run_pattern(0, "none")
    one_fast = run_pattern(1, "fast")
    one_slow = run_pattern(1, "none")
    multiple = run_pattern(3, "mixed")
    assert zero == one_fast == one_slow == multiple
