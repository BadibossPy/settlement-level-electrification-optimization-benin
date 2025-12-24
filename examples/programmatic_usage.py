"""Example usage."""

import geopandas as gpd
from benin_least_cost.parameters import ProjectConfig
from benin_least_cost.demand import run_demand_model
from benin_least_cost.lcoe import run_lcoe_model

def main():
    gdf = gpd.read_file("../data/settlements.geojson")
    
    config = ProjectConfig()
    config.planning.discount_rate = 0.10
    
    print(f"Processing {len(gdf)} settlements...")
    
    gdf = run_demand_model(gdf, config)
    gdf = run_lcoe_model(gdf, config)
    
    mg_sites = gdf[gdf["optimal_tech"] == "MiniGrid"]
    print(f"Mini-Grid sites: {len(mg_sites)}")

if __name__ == "__main__":
    main()
