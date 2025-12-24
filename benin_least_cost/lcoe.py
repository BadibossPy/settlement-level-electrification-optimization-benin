"""LCOE calculation and technology selection."""

import numpy as np
import pandas as pd
from typing import Optional
from .parameters import ProjectConfig
from .schema import DataSchema as DS

def crf(r: float, n: int) -> float:
    """Capital Recovery Factor."""
    if r == 0: 
        return 1.0 / n
    return (r * (1 + r) ** n) / ((1 + r) ** n - 1)

def run_lcoe_model(gdf: pd.DataFrame, config: Optional[ProjectConfig] = None) -> pd.DataFrame:
    """Calculate LCOE and select optimal technology."""
    if config is None: 
        config = ProjectConfig()

    grid_p, mg_p, shs_p = config.grid, config.minigrid, config.shs
    r = config.planning.discount_rate

    # Grid Interconnection Analysis
    
    # Distance optimization: choose nearest substation or transmission line with penalty
    substation_penalty = grid_p.substation_cost / grid_p.mv_cost_per_km
    dist_grid = np.minimum(
        gdf.get(DS.DIST_SUBSTATION, 999.0), 
        gdf.get(DS.DIST_TRANSMISSION, 999.0) + substation_penalty
    )
    
    # Infrastructure cost multipliers
    # 30% penalty for remote/unpaved road access
    terrain_factor = np.where(gdf.get(DS.DIST_ROAD, 0.0) > 10, 1.3, 1.0)
    
    # MV Line CAPEX (Distance-based)
    capex_mv = dist_grid * grid_p.mv_cost_per_km * terrain_factor
    
    # Distribution-side CAPEX (LV + Transformer)
    capex_lv = gdf["households"] * (grid_p.lv_line_per_hh * grid_p.lv_cost_per_km + grid_p.connection_cost)
    capex_trans = np.ceil(gdf[DS.PROJECTED_PEAK] * grid_p.transformer_diversity / grid_p.transformer_kva) * grid_p.transformer_cost
    
    total_capex_grid = capex_mv + capex_lv + capex_trans
    
    # Annualized lifecycle cost (CRF + O&M)
    ann_grid = (total_capex_grid * (crf(r, grid_p.lifetime_years) + grid_p.om_rate) + 
                (gdf[DS.PROJECTED_DEMAND] / (1.0 - grid_p.loss_factor)) * grid_p.energy_price_usd_kwh)
    
    gdf[DS.LCOE_GRID] = ann_grid / gdf[DS.PROJECTED_DEMAND]

    # Mini-Grid Analysis (Hybrid PV/Battery)
    
    # PV Sizing: E_annual / (365 * CF * SysEff)
    pv_kw = (gdf[DS.PROJECTED_DEMAND] / 365.0) / (mg_p.solar_capacity_factor * 24 * mg_p.sys_efficiency) * mg_p.pv_oversizing
    
    # Battery Sizing: Daily energy / DoD (Depth of Discharge)
    batt_kwh = (gdf[DS.PROJECTED_DEMAND] / 365.0) / mg_p.battery_dod
    
    # Lifecycle battery replacement NPV
    batt_npv = sum((batt_kwh * mg_p.battery_cost_per_kwh) / ((1 + r) ** y) 
                   for y in range(mg_p.battery_lifetime_years, mg_p.project_lifetime_years, mg_p.battery_lifetime_years))

    capex_mg = (pv_kw * mg_p.pv_cost_per_kw + 
                batt_kwh * mg_p.battery_cost_per_kwh + 
                batt_npv +
                gdf[DS.PROJECTED_PEAK] * mg_p.inverter_margin * mg_p.inverter_cost_per_kw +
                gdf["households"] * (mg_p.connection_cost + mg_p.lv_reticulation_factor * grid_p.lv_cost_per_km))
    
    gdf[DS.LCOE_MG] = (capex_mg * (crf(r, mg_p.project_lifetime_years) + mg_p.om_rate)) / gdf[DS.PROJECTED_DEMAND]

    # Solar Home Systems (SHS) Analysis
    
    energy_delivered = np.minimum(
        gdf[DS.PROJECTED_DEMAND] / gdf["households"], 
        gdf[DS.TIER].map(shs_p.capacity_limit)
    ) * gdf["households"]
    
    capex_shs = gdf[DS.TIER].map(shs_p.costs) * gdf["households"]
    
    gdf[DS.LCOE_SHS] = (capex_shs * (crf(r, shs_p.lifetime_years) + shs_p.om_rate)) / energy_delivered

    # Technical support constraints
    unsupported = (gdf[DS.TIER] > shs_p.max_supported_tier) | \
                  (gdf[DS.DEMAND_COMMERCIAL] > 0) | \
                  (gdf[DS.DEMAND_AGRI] > 0) | \
                  (gdf[DS.DEMAND_PUBLIC] > 0)
    gdf.loc[unsupported, DS.LCOE_SHS] = 999.9 # Cost penalty

    # Technology Selection
    tech_cols = [DS.LCOE_GRID, DS.LCOE_MG, DS.LCOE_SHS]
    tech_labels = {DS.LCOE_GRID: "Grid", DS.LCOE_MG: "MiniGrid", DS.LCOE_SHS: "SHS"}
    
    gdf[DS.OPTIMAL_TECH] = gdf[tech_cols].idxmin(axis=1).map(tech_labels)
    
    # Investment Valuation
    gdf[DS.INVESTMENT] = np.select(
        [gdf[DS.OPTIMAL_TECH] == "Grid", gdf[DS.OPTIMAL_TECH] == "MiniGrid", gdf[DS.OPTIMAL_TECH] == "SHS"],
        [total_capex_grid, capex_mg, capex_shs], 
        default=0.0
    )

    return gdf
