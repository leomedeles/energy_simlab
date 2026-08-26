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
    TopologySnapshotV1,
)


class DeterministicTopologyService:
    source_id = "topology-service"

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

