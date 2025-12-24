# Settlement-Level Least-Cost Electrification (Benin, 2025-2040)

Least-cost model for 17,205 settlements in Benin. Technologies: Grid Extension, Mini-Grid (PV + battery), Solar Home Systems (SHS). Demand follows ESMAP Multi-Tier Framework; selection is by minimum LCOE.

## Headline results

| Metric | Value |
| --- | --- |
| Settlements | 17,205 |
| Population | 14,111,192 |
| Grid | 1,523 (9%) |
| Mini-Grid | 7,552 (44%) |
| SHS | 8,130 (47%) |
| Total Investment | USD 2.26B |
| Projected Demand 2040 | 2,694 GWh/year |

## Pipeline (minimal, with workflow graph)

```mermaid
flowchart LR
    A[Input\nsettlements.geojson] --> B[Validate\nrequired fields, defaults]
    B --> C[Categorize\nurban/rural, households, MTF tier (+nightlight)]
    C --> D[Demand\nres/commercial/agri/public + growth + peak]
    D --> E[Cost\nGrid MV/LV/tx + losses; Mini-grid PV/battery/inverter; SHS caps/exclusions]
    E --> F[Optimize\nargmin LCOE]
    F --> G[Output\nresults.geojson\ntech, LCOE, investment, demand, peak]
```

1) Validate inputs.  
2) Categorize settlements.  
3) Demand: sectors, growth, peak.  
4) Cost: grid / mini-grid / SHS.  
5) Optimize: lowest LCOE, carry CAPEX.  
6) Output: GeoJSON + notebook/CLI reproducibility.

## Method snapshot
- Demand: households by urban/rural size; tier from RWI (+nightlights); sector loads (residential, SME gravity, agri mills/irrigation/dryers, public); growth to 2040; peak via tier load factors.
- Cost: grid MV/LV/transformers/connections + losses and energy price; mini-grid PV/battery/inverter with replacements; SHS tier caps and exclusion when productive loads exist.
- Selection: `argmin(LCOE_grid, LCOE_mg, LCOE_shs)`; investment = CAPEX of chosen tech.

## Data
- Required: geometry, population.
- Optional (improves accuracy): num_buildings, mean_rwi, has_nightlight, dist_to_substations, distance_to_existing_transmission_lines, dist_main_road_km, dist_lake_river_km, dist_nearest_hub_km, num_health_facilities, num_education_facilities.

## Outputs
- GeoJSON fields: projected_demand, projected_peak, lcoe_grid, lcoe_mg, lcoe_shs, optimal_tech, investment.

## Usage
```bash
pip install -r requirements.txt
python run_model.py --input data/settlements.geojson --output results.geojson
```
Notebook: `notebooks/electrification_analysis.ipynb` (executed, plots embedded).

## Assumptions
- Horizon 15y; g_pop 2.7%/y; g_wealth 1.5%/y; discount 8%; solar CF 18%; grid losses 18%; SHS excluded when productive loads exist.

## Limits
- Static (no phasing), uniform solar CF, Euclidean distances, no diesel backup, no reliability modeling.

## Verification
- `pytest tests/test_logic.py`
- `jupyter nbconvert --execute notebooks/electrification_analysis.ipynb`
- `results.geojson` generated from current code/config.

