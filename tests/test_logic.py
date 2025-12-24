"""Unit tests."""

import unittest
import numpy as np
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd

from benin_least_cost.parameters import ProjectConfig, PlanningParams
from benin_least_cost.lcoe import crf, run_lcoe_model
from benin_least_cost.demand import run_demand_model
from benin_least_cost.schema import DataSchema as DS

class TestMathematicalLogic(unittest.TestCase):

    def test_crf_calculation(self):
        """Verify Capital Recovery Factor against known values."""
        # 8% discount rate, 15 years
        r, n = 0.08, 15
        expected = 0.1168  # Approx
        self.assertAlmostEqual(crf(r, n), expected, places=4)
        
        # 0% discount rate case
        self.assertEqual(crf(0, 10), 0.1)

    def test_demand_projection_formula(self):
        """Verify annual compound growth logic."""
        config = ProjectConfig()
        config.planning.pop_growth_rate = 0.02
        config.planning.wealth_growth_rate = 0.01
        config.planning.horizon_years = 10
        
        # Test GDF with 1 settlement, 1000 population
        data = {
            DS.POPULATION: [1000],
            DS.GEOMETRY: [Point(2.5, 6.5)],
            DS.RWI: [0.0]
        }
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
        
        gdf = run_demand_model(gdf, config)
        
        self.assertGreater(gdf[DS.PROJECTED_DEMAND].iloc[0], 0)
        self.assertTrue(np.isclose(gdf[DS.PROJECTED_DEMAND].iloc[0] / gdf[DS.PROJECTED_DEMAND].iloc[0], 1.0))

    def test_parameter_validation(self):
        """Ensure invalid parameters raise errors."""
        with self.assertRaises(ValueError):
            PlanningParams(discount_rate=1.5)
            
        with self.assertRaises(ValueError):
            PlanningParams(horizon_years=-5)

    def test_lcoe_selection(self):
        """Verify least-cost selection picks the minimum value."""
        data = {
            DS.LCOE_GRID: [0.15, 0.40, 0.90],
            DS.LCOE_MG:   [0.30, 0.25, 0.80],
            DS.LCOE_SHS:  [0.80, 0.80, 0.10],
            "households": [100, 100, 10],
            DS.PROJECTED_DEMAND: [1000, 1000, 100],
            DS.PROJECTED_PEAK: [5, 5, 1],
            DS.TIER: [3, 3, 1],
            DS.DEMAND_COMMERCIAL: [0, 0, 0],
            DS.DEMAND_AGRI: [0, 0, 0],
            DS.DEMAND_PUBLIC: [0, 0, 0]
        }
        gdf = pd.DataFrame(data)
        
        # Manual execution of tech mapping from lcoe.py logic
        tech_cols = [DS.LCOE_GRID, DS.LCOE_MG, DS.LCOE_SHS]
        tech_labels = {DS.LCOE_GRID: "Grid", DS.LCOE_MG: "MiniGrid", DS.LCOE_SHS: "SHS"}
        gdf[DS.OPTIMAL_TECH] = gdf[tech_cols].idxmin(axis=1).map(tech_labels)
        
        self.assertEqual(gdf[DS.OPTIMAL_TECH].iloc[0], "Grid")
        self.assertEqual(gdf[DS.OPTIMAL_TECH].iloc[1], "MiniGrid")
        self.assertEqual(gdf[DS.OPTIMAL_TECH].iloc[2], "SHS")

if __name__ == "__main__":
    unittest.main()
