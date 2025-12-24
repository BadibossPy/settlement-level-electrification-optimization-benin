"""Demand estimation using Multi-Tier Framework."""

import numpy as np
import pandas as pd
from typing import Optional
from .parameters import ProjectConfig
from .schema import DataSchema as DS

def run_demand_model(gdf: pd.DataFrame, config: Optional[ProjectConfig] = None) -> pd.DataFrame:
    """Calculate demand per settlement."""
    if config is None:
        config = ProjectConfig()
        
    pop = gdf[DS.POPULATION]
    gdf[DS.IS_URBAN] = (pop > config.planning.urban_threshold_pop) | (gdf.get(DS.NUM_BUILDINGS, 0) > 500)
    is_urban = gdf[DS.IS_URBAN]
    
    loads = config.demand.anchor_loads
    agri_demand = np.zeros(len(gdf))
    
    mill_mask = (~is_urban) & (pop > 500)
    agri_demand[mill_mask] += np.maximum(1, (pop[mill_mask] / 1500).astype(int)) * loads["mill"]
    
    dist_water = gdf.get(DS.DIST_WATER, 99.0)
    irrig_mask = (dist_water < 3.0) & (pop > 300)
    agri_demand[irrig_mask] += np.maximum(1, (pop[irrig_mask] / 800).astype(int)) * loads["irrigation"]
    
    if "lat" in gdf.columns:
        lats = gdf["lat"]
    else:
        geom = gdf.geometry
        geom_type = getattr(geom, "geom_type", None)
        is_point = geom_type is not None and (geom_type == "Point").all()
        crs = getattr(geom, "crs", None)
        if crs is not None:
            if is_point:
                lats = geom.to_crs(epsg=4326).y
            else:
                lats = geom.to_crs(epsg=3857).centroid.to_crs(epsg=4326).y
        else:
            lats = geom.y if is_point else geom.centroid.y
    dryer_mask = (lats > 8.0) & (~is_urban) & (pop > 400)
    agri_demand[dryer_mask] += np.maximum(1, (pop[dryer_mask] / 2000).astype(int)) * loads["dryer"]
    
    gdf[DS.DEMAND_AGRI] = agri_demand
    
    hh_size = np.where(gdf[DS.IS_URBAN], config.planning.urban_hh_size, config.planning.rural_hh_size)
    gdf["households"] = np.ceil(gdf[DS.POPULATION] / hh_size).clip(lower=1).astype(int)

    rwi = gdf.get(DS.RWI, 0.0)
    gdf[DS.TIER] = np.select([rwi < -0.3, rwi < 0.4], [1, 2], default=3)

    if DS.NIGHTLIGHT in gdf.columns:
        # Settlements with detected nightlights are elevated to Tier 2 (Minimum)
        gdf[DS.TIER] = np.where((gdf[DS.NIGHTLIGHT] > 0) & (gdf[DS.TIER] < 2), 2, gdf[DS.TIER])

    dist_hub = gdf.get(DS.DIST_HUB, pd.Series(30.0, index=gdf.index)).fillna(30.0)
    gravity = np.clip(1.0 + (20.0 / (dist_hub + 1.0)), 1.0, 2.5)
    base_density = np.where(gdf[DS.IS_URBAN], config.demand.urban_sme_ratio, config.demand.rural_sme_ratio)
    
    sme_count = np.floor((gdf.get(DS.NUM_BUILDINGS, gdf["households"]) / base_density) * gravity)
    sme_count = np.clip(sme_count, 0, None)
    gdf[DS.DEMAND_COMMERCIAL] = sme_count * config.demand.anchor_loads["sme"]

    uptake = np.where(gdf[DS.IS_URBAN], 0.95, config.planning.target_uptake_rate)
    
    gdf[DS.DEMAND_RESIDENTIAL] = gdf["households"] * gdf[DS.TIER].map(config.demand.tier_kwh) * uptake
    gdf[DS.DEMAND_PUBLIC] = (
        gdf.get(DS.FACILITY_HEALTH, pd.Series(0.0, index=gdf.index)).fillna(0.0) * config.demand.anchor_loads["health"] +
        gdf.get(DS.FACILITY_EDUCATION, pd.Series(0.0, index=gdf.index)).fillna(0.0) * config.demand.anchor_loads["education"]
    )

    combined_growth = (1.0 + config.planning.pop_growth_rate) * (1.0 + config.planning.wealth_growth_rate)
    growth_multiplier = combined_growth ** config.planning.horizon_years
    
    total_initial = gdf[[DS.DEMAND_RESIDENTIAL, DS.DEMAND_COMMERCIAL, DS.DEMAND_AGRI, DS.DEMAND_PUBLIC]].sum(axis=1)
    gdf[DS.PROJECTED_DEMAND] = total_initial * growth_multiplier

    gdf[DS.PROJECTED_PEAK] = (gdf[DS.PROJECTED_DEMAND] / 8760.0) / gdf[DS.TIER].map(config.demand.tier_lf)

    return gdf
