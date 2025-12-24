"""Field definitions and validation."""

import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataSchema:
    """Column names."""
    GEOMETRY = "geometry"
    ID = "identifier"
    POPULATION = "population"
    NUM_BUILDINGS = "num_buildings"
    IS_URBAN = "is_urban"
    TIER = "tier"
    RWI = "mean_rwi"
    NIGHTLIGHT = "has_nightlight"
    DIST_SUBSTATION = "dist_to_substations"
    DIST_TRANSMISSION = "distance_to_existing_transmission_lines"
    DIST_ROAD = "dist_main_road_km"
    DIST_WATER = "dist_lake_river_km"
    DIST_HUB = "dist_nearest_hub_km"
    FACILITY_HEALTH = "num_health_facilities"
    FACILITY_EDUCATION = "num_education_facilities"
    DEMAND_RESIDENTIAL = "dem_res"
    DEMAND_COMMERCIAL = "dem_comm"
    DEMAND_AGRI = "dem_agri"
    DEMAND_PUBLIC = "dem_pub"
    PROJECTED_DEMAND = "projected_demand"
    PROJECTED_PEAK = "projected_peak"
    LCOE_GRID = "lcoe_grid"
    LCOE_MG = "lcoe_mg"
    LCOE_SHS = "lcoe_shs"
    OPTIMAL_TECH = "optimal_tech"
    INVESTMENT = "investment"

class DataValidator:
    """Input validation."""
    
    REQUIRED_INPUTS = [DataSchema.GEOMETRY, DataSchema.POPULATION]
    
    @staticmethod
    def validate_input(gdf: pd.DataFrame):
        """Check required fields and fix nulls."""
        logger.info("Validating input...")
        
        missing = [col for col in DataValidator.REQUIRED_INPUTS if col not in gdf.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
            
        if (gdf[DataSchema.POPULATION] < 0).any():
            raise ValueError("Negative population values.")
            
        if gdf.geometry.isnull().any():
            logger.warning("Null geometries found, filtering...")
            gdf = gdf[gdf.geometry.notnull()]
            
        for col in [DataSchema.DIST_SUBSTATION, DataSchema.DIST_TRANSMISSION, DataSchema.DIST_ROAD]:
            if col in gdf.columns:
                gdf[col] = gdf[col].fillna(999.0).clip(lower=0.0)
                
        logger.info("Validation done.")
        return gdf
