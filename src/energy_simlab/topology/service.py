"""Deterministic graph connectivity, deliberately separate from power balance."""

from __future__ import annotations

from collections import deque

from energy_simlab.contracts.enums import (
    BranchState,
    EnergizationState,
    QualityReason,
    QualityValidity,
)
from energy_simlab.contracts.records import (
    BranchV1,
    BusV1,
    ConnectedComponentV1,
    QualityV1,
    TerminalV1,
    TopologyEventV1,
    TopologySnapshotV1,
)


class DeterministicTopologyService:
    source_id = "topology-service"

    def __init__(self) -> None:
        self._event_sequence = 0

    def recompute(self, topology: TopologySnapshotV1, logical_tick: int) -> TopologySnapshotV1:
        bus_by_id = {bus.id: bus for bus in topology.buses}
        adjacency = {bus_id: set[str]() for bus_id in bus_by_id}
        for branch in topology.branches:
            if branch.from_bus_id not in bus_by_id or branch.to_bus_id not in bus_by_id:
                raise ValueError(f"branch {branch.id} references an unknown bus")
            if branch.actual_state is BranchState.CLOSED:
                adjacency[branch.from_bus_id].add(branch.to_bus_id)
                adjacency[branch.to_bus_id].add(branch.from_bus_id)

        unseen = set(bus_by_id)
        components: list[ConnectedComponentV1] = []
        while unseen:
            first = min(unseen)
            queue = deque([first])
            members: list[str] = []
            unseen.remove(first)
            while queue:
                bus_id = queue.popleft()
                members.append(bus_id)
                for neighbour in sorted(adjacency[bus_id]):
                    if neighbour in unseen:
                        unseen.remove(neighbour)
                        queue.append(neighbour)
            bus_ids = tuple(sorted(members))
            contains_source = any(bus_by_id[item].is_infinite_source for item in bus_ids)
            energization = (
                EnergizationState.GRID_CONNECTED
                if contains_source
                else EnergizationState.ISLANDED_UNSUPPORTED
            )
            components.append(
                ConnectedComponentV1(
                    id=f"{'+'.join(bus_ids)}@{topology.topology_version}",
                    bus_ids=bus_ids,
                    contains_infinite_source=contains_source,
                    energization=energization,
                )
            )

        quality = QualityV1(
            validity=QualityValidity.GOOD,
            reason=QualityReason.NORMAL,
            detail="boolean connectivity calculated deterministically",
            origin_id=self.source_id,
            since_tick=logical_tick,
        )
        return TopologySnapshotV1(
            id=f"TOPOLOGY-{topology.topology_version:08d}",
            source_id=self.source_id,
            logical_tick=logical_tick,
            sequence=topology.sequence + 1,
            topology_version=topology.topology_version,
            buses=tuple(sorted(topology.buses, key=lambda item: item.id)),
            branches=tuple(sorted(topology.branches, key=lambda item: item.id)),
            terminals=tuple(sorted(topology.terminals, key=lambda item: item.id)),
            components=tuple(sorted(components, key=lambda item: item.id)),
            quality=quality,
        )

    def open_pcc(
        self,
        topology: TopologySnapshotV1,
        *,
        logical_tick: int,
        correlation_id: str,
        causation_id: str,
    ) -> tuple[TopologySnapshotV1, TopologyEventV1]:
        branches: list[BranchV1] = []
        pcc_before: BranchV1 | None = None
        for branch in topology.branches:
            if branch.id == "PCC":
                pcc_before = branch
                branches.append(
                    BranchV1(
                        id=branch.id,
                        from_bus_id=branch.from_bus_id,
                        to_bus_id=branch.to_bus_id,
                        requested_state=BranchState.OPEN,
                        actual_state=BranchState.OPEN,
                        state_sequence=branch.state_sequence + 1,
                    )
                )
            else:
                branches.append(branch)
        if pcc_before is None:
            raise ValueError("topology has no PCC branch")
        if pcc_before.actual_state is BranchState.OPEN:
            raise ValueError("PCC is already open")

        next_version = topology.topology_version + 1
        unresolved = TopologySnapshotV1(
            id=f"TOPOLOGY-INPUT-{next_version:08d}",
            source_id=self.source_id,
            logical_tick=logical_tick,
            sequence=topology.sequence,
            topology_version=next_version,
            buses=topology.buses,
            branches=tuple(sorted(branches, key=lambda item: item.id)),
            terminals=topology.terminals,
            components=(),
            quality=topology.quality,
        )
        updated = self.recompute(unresolved, logical_tick)
        local_component = next(item for item in updated.components if "LOCAL" in item.bus_ids)
        affected_ids = tuple(
            sorted(
                {item.id for item in topology.components}
                | {item.id for item in updated.components}
            )
        )
        self._event_sequence += 1
        event = TopologyEventV1(
            id=f"TOPOLOGY-EVENT-{self._event_sequence:08d}",
            source_id=self.source_id,
            logical_tick=logical_tick,
            sequence=self._event_sequence,
            branch_id="PCC",
            old_requested_state=pcc_before.requested_state,
            new_requested_state=BranchState.OPEN,
            old_actual_state=pcc_before.actual_state,
            new_actual_state=BranchState.OPEN,
            trigger_kind="COMMAND",
            correlation_id=correlation_id,
            causation_id=causation_id,
            topology_version_before=topology.topology_version,
            topology_version_after=updated.topology_version,
            affected_component_ids=affected_ids,
            energization=local_component.energization,
        )
        return updated, event


def reference_topology(*, logical_tick: int = 0) -> TopologySnapshotV1:
    quality = QualityV1(
        validity=QualityValidity.GOOD,
        reason=QualityReason.NORMAL,
        detail="reference topology input",
        origin_id="bootstrap",
        since_tick=logical_tick,
    )
    unresolved = TopologySnapshotV1(
        id="TOPOLOGY-INPUT-00000000",
        source_id="bootstrap",
        logical_tick=logical_tick,
        sequence=0,
        topology_version=0,
        buses=(
            BusV1(id="GRID", is_infinite_source=True),
            BusV1(id="LOCAL", is_infinite_source=False),
        ),
        branches=(
            BranchV1(
                id="PCC",
                from_bus_id="GRID",
                to_bus_id="LOCAL",
                requested_state=BranchState.CLOSED,
                actual_state=BranchState.CLOSED,
                state_sequence=0,
            ),
        ),
        terminals=(
            TerminalV1(id="BESS-TERMINAL", asset_id="BESS", bus_id="LOCAL"),
            TerminalV1(id="GRID-SOURCE-TERMINAL", asset_id="GRID-SOURCE", bus_id="GRID"),
            TerminalV1(id="LOAD-TERMINAL", asset_id="LOAD", bus_id="LOCAL"),
        ),
        components=(),
        quality=quality,
    )
    return DeterministicTopologyService().recompute(unresolved, logical_tick)
