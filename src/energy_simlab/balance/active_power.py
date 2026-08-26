"""Algebraic active-power accounting with no electrical solver claims."""

from __future__ import annotations

from energy_simlab.contracts.enums import (
    EnergizationState,
    QualityReason,
    QualityValidity,
)
from energy_simlab.contracts.records import ActivePowerBalanceV1, QualityV1, TopologySnapshotV1


class AlgebraicActivePowerBalance:
    source_id = "active-power-balance"

    def calculate(
        self,
        *,
        logical_tick: int,
        load_mw: float,
        bess_ac_power_mw: float,
        topology: TopologySnapshotV1,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> ActivePowerBalanceV1:
        local_components = [component for component in topology.components if "LOCAL" in component.bus_ids]
        if len(local_components) != 1:
            raise ValueError("topology must place LOCAL in exactly one component")
        energization = local_components[0].energization
        if energization is EnergizationState.GRID_CONNECTED:
            quality = QualityV1(
                validity=QualityValidity.GOOD,
                reason=QualityReason.NORMAL,
                detail="grid-connected algebraic active-power balance",
                origin_id=self.source_id,
                since_tick=logical_tick,
            )
            return ActivePowerBalanceV1(
                logical_tick=logical_tick,
                load_mw=load_mw,
                bess_ac_power_mw=bess_ac_power_mw,
                grid_import_mw=load_mw - bess_ac_power_mw,
                island_imbalance_mw=None,
                energization=energization,
                quality=quality,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

        quality = QualityV1(
            validity=QualityValidity.UNCERTAIN,
            reason=QualityReason.SIMPLIFIED_ISLAND_PROXY,
            detail="unsupported-island algebraic imbalance; not an electrical state",
            origin_id=self.source_id,
            since_tick=logical_tick,
        )
        return ActivePowerBalanceV1(
            logical_tick=logical_tick,
            load_mw=load_mw,
            bess_ac_power_mw=bess_ac_power_mw,
            grid_import_mw=None,
            island_imbalance_mw=bess_ac_power_mw - load_mw,
            energization=energization,
            quality=quality,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
