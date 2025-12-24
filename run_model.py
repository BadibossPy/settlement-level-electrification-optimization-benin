"""Main entry point."""

import argparse
import logging
import sys
import time
from pathlib import Path
import geopandas as gpd

from benin_least_cost.parameters import ProjectConfig
from benin_least_cost.demand import run_demand_model
from benin_least_cost.lcoe import run_lcoe_model
from benin_least_cost.schema import DataSchema as DS, DataValidator

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_pipeline(input_path: Path, output_path: Path):
    """Run the model."""
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        sys.exit(1)

    try:
        gdf = gpd.read_file(input_path)
    except Exception as e:
        logger.error(f"Read error: {e}")
        sys.exit(1)

    try:
        gdf = DataValidator.validate_input(gdf)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)

    config = ProjectConfig()
    
    start_time = time.time()
    logger.info(f"Processing {len(gdf)} settlements...")
    gdf = run_demand_model(gdf, config)
    gdf = run_lcoe_model(gdf, config)
    duration = time.time() - start_time
    
    for tech, count in gdf[DS.OPTIMAL_TECH].value_counts().items():
        logger.info(f"  {tech}: {count}")
    
    logger.info(f"Total: USD {gdf[DS.INVESTMENT].sum():,.0f}")
    logger.info(f"Speed: {len(gdf)/duration:,.0f} settlements/sec")

    try:
        gdf.to_file(output_path, driver="GeoJSON")
        logger.info(f"Saved: {output_path}")
    except Exception as e:
        logger.error(f"Write error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Benin Least-Cost Electrification Strategy Tool (2025-2040)"
    )
    parser.add_argument(
        "--input", "-i", 
        type=Path, 
        default=Path("data/settlements.geojson"),
        help="Path to the input settlements GeoJSON dataset."
    )
    parser.add_argument(
        "--output", "-o", 
        type=Path, 
        default=Path("benin_results.geojson"),
        help="Path to save the optimization results."
    )
    
    args = parser.parse_args()
    run_pipeline(args.input, args.output)

if __name__ == "__main__":
    main()
