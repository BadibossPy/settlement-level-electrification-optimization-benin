# Settlement-Level Least-Cost Electrification (Benin, 2025-2040)

Least-cost electrification model for 17,205 settlements in Benin. Compares Grid Extension, Mini-Grid (solar PV + battery), and Solar Home Systems (SHS) using levelized cost of electricity (LCOE). The model implements the ESMAP Multi-Tier Framework for demand estimation and performs techno-economic optimization at the settlement level.

## Results

| Metric | Value |
|--------|-------|
| Settlements | 17,205 |
| Population | 14,111,192 |
| Grid | 1,523 (9%) |
| Mini-Grid | 7,552 (44%) |
| SHS | 8,130 (47%) |
| Total Investment | USD 2.26B |
| Projected Demand (2040) | 2,694 GWh/year |

## Key Findings

| Technology | Settlements | Population | Demand (GWh) | Investment | Per Capita | Avg LCOE |
|------------|-------------|------------|--------------|------------|------------|----------|
| Grid | 1,523 (9%) | 11.5M (81%) | 2,532 (94%) | $1.58B (70%) | $137 | $0.38/kWh |
| Mini-Grid | 7,552 (44%) | 2.1M (15%) | 147 (5%) | $0.67B (30%) | $317 | $0.80/kWh |
| SHS | 8,130 (47%) | 0.5M (4%) | 14 (1%) | $0.01B (0%) | $26 | $0.63/kWh |

**Implications:**
- Grid extension serves the minority of settlements (9%) but captures 81% of population and 94% of demand
- Decentralized solutions (Mini-Grid + SHS) dominate settlement count (91%) but serve only 19% of population
- Grid LCOE is lowest ($0.38/kWh) due to economies of scale, despite higher per-capita investment ($137)
- Mini-Grids serve medium-sized settlements with higher per-capita costs ($317) but moderate LCOE ($0.80/kWh)
- SHS serves smallest settlements with lowest per-capita cost ($26) but limited capacity (35-350 kWh/year/household)

## Method

The model estimates electricity demand per settlement and calculates LCOE for three technologies. The technology with minimum LCOE is selected.

### Demand Estimation

**Household count**

```
households = ceil(population / hh_size)
```

where hh_size = 4.3 (urban) or 5.2 (rural).

**Tier assignment** (Multi-Tier Framework)

```
tier = 1 if RWI < -0.3 else 2 if RWI < 0.4 else 3
```

**Residential demand**

```
E_res = households * tier_kwh[tier] * uptake
```

where tier_kwh = {1: 35, 2: 220, 3: 850} kWh/year per household, uptake = 0.85 (rural) or 0.95 (urban).

**Productive demand**

- Commercial: SMEs estimated from building density and distance to hubs (600 kWh/year per SME)
- Agricultural: Mills, irrigation pumps, dryers allocated based on population and location
- Public: Health facilities (4,000 kWh/year) and schools (1,500 kWh/year)

**Growth projection**

```
G = (1 + g_pop) * (1 + g_wealth) ** H
E_proj = (E_res + E_comm + E_agri + E_pub) * G
```

with g_pop = 0.027, g_wealth = 0.015, H = 15 years.

**Peak load**

```
P_peak = E_proj / (8760 * LF[tier])
```

where LF = load factor (0.18 for tier 1, 0.20 for tier 2, 0.25 for tier 3).

### Cost Model

**Capital Recovery Factor**

```
CRF(r, n) = r * (1+r)**n / ((1+r)**n - 1)
```

with discount rate r = 0.08.

**Grid Extension**

Grid LCOE accounts for:
- MV line: $14,000/km (with 30% penalty if >10km from paved roads)
- LV distribution: $5,500/km
- Transformers: $8,000 per 45kVA unit
- Connections: $150/household
- Losses: 18%
- Energy cost: $0.10/kWh

**Mini-Grid** (solar + battery)

PV sizing:

```
PV_kW = (E_proj / 365) / (CF * 24 * eta) * 1.2
```

with CF = 0.18 (capacity factor), eta = 0.85 (system efficiency).

Battery sizing:

```
Batt_kWh = (E_proj / 365) / DoD
```

with DoD = 0.8 (depth of discharge). Battery replacements at years 7 and 14 are included in NPV.

Costs: PV $700/kWp, Battery $300/kWh, Inverter $180/kW.

**Solar Home Systems**

SHS costs per tier: {1: $80, 2: $250, 3: $600} per household.

Energy capacity limits: {1: 35, 2: 150, 3: 350} kWh/year per household.

SHS is excluded if the settlement has productive loads (commercial, agricultural, or public facilities).

### Selection

```
optimal_tech = argmin([LCOE_grid, LCOE_mg, LCOE_shs])
```

## Implementation Workflow

### Stage 1: Data Validation

```
Input: settlements.geojson (17,205 settlements)
├─ Required: geometry, population
└─ Optional: num_buildings, mean_rwi, has_nightlight, infrastructure distances, facilities

Validation:
├─ Check geometry type (Point/Polygon)
├─ Enforce population > 0
├─ Handle missing optional fields (fill defaults or compute from population)
└─ Ensure CRS compatibility

Output: validated GeoDataFrame
```

### Stage 2: Settlement Categorization

```
For each settlement:

Urban/Rural Classification:
├─ IF population > 5000 OR num_buildings > 500 → urban
└─ ELSE → rural

Household Estimation:
├─ households = ceil(population / hh_size)
├─ hh_size = 4.3 (urban) or 5.2 (rural)

Tier Assignment (Multi-Tier Framework):
├─ Base tier from Relative Wealth Index (RWI):
│   ├─ RWI < -0.3 → tier 1
│   ├─ RWI < 0.4 → tier 2
│   └─ RWI ≥ 0.4 → tier 3
└─ Nightlight adjustment: IF has_nightlight > 0 → tier = max(tier, 2)
```

### Stage 3: Demand Estimation

```
Residential Demand:
├─ E_res = households × tier_kwh[tier] × uptake
├─ tier_kwh = {1: 35, 2: 220, 3: 850} kWh/year per household
└─ uptake = 0.85 (rural) or 0.95 (urban)

Commercial Demand:
├─ Gravity factor: g = clip(1 + 20/(dist_hub + 1), 1, 2.5)
├─ SME count: n_SME = floor((N / k) × g)
│   ├─ k = 50 (urban) or 100 (rural) buildings per SME
│   └─ N = num_buildings if available, else households
└─ E_comm = n_SME × 600 kWh/year per SME

Agricultural Demand (rural only):
├─ Mills: IF pop > 500 → E_mill = max(1, floor(pop/1500)) × 4500
├─ Irrigation: IF dist_water < 3km AND pop > 300 → E_irr = max(1, floor(pop/800)) × 3500
└─ Dryers: IF lat > 8° AND pop > 400 → E_dryer = max(1, floor(pop/2000)) × 6000

Public Demand:
└─ E_pub = n_health × 4000 + n_edu × 1500

Growth Projection (2025 → 2040):
├─ G = (1 + g_pop) × (1 + g_wealth) ^ H
├─ g_pop = 0.027, g_wealth = 0.015, H = 15 years
└─ E_proj = (E_res + E_comm + E_agri + E_pub) × G

Peak Load:
├─ P_peak = E_proj / (8760 × LF[tier])
└─ LF = {1: 0.18, 2: 0.20, 3: 0.25} (load factor)
```

### Stage 4: Grid Extension LCOE

```
Distance Calculation:
├─ d_eff_sub = dist_to_substations
├─ d_eff_trans = dist_to_transmission + (C_sub / C_MV)
└─ d_grid = min(d_eff_sub, d_eff_trans)

Terrain Factor:
└─ terrain = 1.3 IF dist_main_road > 10km ELSE 1.0

MV Line Cost:
├─ C_MV_line = d_grid × C_MV × terrain
└─ C_MV = $14,000/km

LV Distribution Cost:
├─ radius = sqrt(area / π) for polygons, or estimated from population
├─ C_LV = 2 × radius × C_LV_per_km
└─ C_LV_per_km = $5,500/km

Transformer Cost:
├─ n_transformers = ceil(P_peak / 45)
└─ C_transformer = n_transformers × $8,000

Connection Cost:
└─ C_connections = households × $150

Total CAPEX:
└─ CAPEX_grid = C_MV_line + C_LV + C_transformer + C_connections

Annualized Cost:
├─ CRF(r, n) = r × (1+r)^n / ((1+r)^n - 1)
├─ Ann_CAPEX = CAPEX_grid × (CRF(0.08, 40) + 0.02)
├─ Ann_OPEX = (E_proj / 0.82) × 0.10  [accounting for 18% losses]
└─ Ann_grid = Ann_CAPEX + Ann_OPEX

LCOE:
└─ LCOE_grid = Ann_grid / E_proj
```

### Stage 5: Mini-Grid LCOE

```
PV Sizing:
├─ Daily demand = E_proj / 365
├─ PV_kW = (Daily demand / (CF × 24 × eta)) × safety_factor
├─ CF = 0.18 (capacity factor), eta = 0.85 (efficiency), safety = 1.2
└─ C_PV = PV_kW × $700

Battery Sizing:
├─ Batt_kWh = Daily demand / DoD
├─ DoD = 0.8 (depth of discharge)
├─ NPV_replacements = sum(Batt_kWh × 300 / (1.08)^y for y in [7, 14])
└─ C_batt = Batt_kWh × 300 + NPV_replacements

Inverter Cost:
└─ C_inv = PV_kW × $180

Total CAPEX:
└─ CAPEX_mg = C_PV + C_batt + C_inv

LCOE:
├─ Ann_mg = CAPEX_mg × (CRF(0.08, 20) + 0.03)
└─ LCOE_mg = Ann_mg / E_proj
```

### Stage 6: SHS LCOE

```
Capacity Constraints:
├─ cap[tier] = {1: 35, 2: 150, 3: 350} kWh/year per household
└─ E_del = min(E_proj / households, cap[tier]) × households

CAPEX:
├─ unit_cost[tier] = {1: $80, 2: $250, 3: $600} per household
└─ CAPEX_shs = households × unit_cost[tier]

Exclusion Logic:
└─ IF tier > 3 OR E_comm > 0 OR E_agri > 0 OR E_pub > 0 → LCOE_shs = 999.9

LCOE (if not excluded):
├─ Ann_shs = CAPEX_shs × (CRF(0.08, 5) + 0.05)
└─ LCOE_shs = Ann_shs / E_del
```

### Stage 7: Technology Selection

```
For each settlement:
├─ Compute: LCOE_grid, LCOE_mg, LCOE_shs
├─ Select: optimal_tech = argmin(LCOE_grid, LCOE_mg, LCOE_shs)
└─ Investment = CAPEX[optimal_tech]

Output:
└─ results.geojson with fields:
    ├─ projected_demand, projected_peak
    ├─ lcoe_grid, lcoe_mg, lcoe_shs
    ├─ optimal_tech
    └─ investment
```

### Computation Flow

```
settlements.geojson → Validation → Categorization → Demand Model
                                                          ↓
                                                    E_proj, P_peak
                                                          ↓
                        ┌─────────────────────────────────┼─────────────────────────────────┐
                        ↓                                 ↓                                 ↓
                   Grid LCOE                         MG LCOE                           SHS LCOE
                 (d_grid, terrain)              (PV, battery, inv)                (tier, exclusion)
                        ↓                                 ↓                                 ↓
                        └─────────────────────────────────┼─────────────────────────────────┘
                                                          ↓
                                                   argmin(LCOE_*)
                                                          ↓
                                                  results.geojson
```

## Usage

### Install

```bash
pip install -r requirements.txt
```

### Run model

```bash
python run_model.py --input data/settlements.geojson --output results.geojson
```

### Notebook

`notebooks/electrification_analysis.ipynb` provides comprehensive analysis with:

1. **Spatial Distribution Map**: Geographic visualization of technology selection across Benin
2. **Economic Analysis**: Investment allocation, LCOE distributions, technology-specific cost breakdowns
3. **Demand Characteristics**: Population vs demand patterns, per-capita consumption, sectoral breakdown
4. **Technology Competitiveness**: Analysis of grid distance thresholds, demand-distance relationships
5. **Statistical Insights**: Summary tables quantifying settlement characteristics, investment efficiency, and technology trade-offs

The notebook generates publication-ready figures and quantitative insights suitable for technical reports.

### Programmatic usage

```python
import geopandas as gpd
from benin_least_cost.parameters import ProjectConfig
from benin_least_cost.demand import run_demand_model
from benin_least_cost.lcoe import run_lcoe_model

gdf = gpd.read_file("data/settlements.geojson")
config = ProjectConfig()

gdf = run_demand_model(gdf, config)
gdf = run_lcoe_model(gdf, config)

print(gdf["optimal_tech"].value_counts())
```

## Data Requirements

**Required fields:**
- geometry (point or polygon)
- population

**Optional fields** (improve accuracy):
- num_buildings, mean_rwi, has_nightlight
- dist_to_substations, distance_to_existing_transmission_lines
- dist_main_road_km, dist_lake_river_km
- num_health_facilities, num_education_facilities

## Output Fields

- projected_demand (kWh/year, 2040)
- projected_peak (kW)
- lcoe_grid, lcoe_mg, lcoe_shs (USD/kWh)
- optimal_tech (Grid / MiniGrid / SHS)
- investment (USD, CAPEX for selected technology)

## Parameters

All model parameters are in `benin_least_cost/parameters.py` and can be modified:

```python
config = ProjectConfig()
config.planning.discount_rate = 0.10  # default: 0.08
config.grid.mv_cost_per_km = 16000    # default: 14000
```

## Assumptions

- Planning horizon: 15 years (2025-2040)
- Population growth: 2.7% annually
- Wealth growth: 1.5% annually
- Discount rate: 8%
- Solar capacity factor: 18%
- Grid technical losses: 18%
- All settlements can technically receive electricity from any technology

## Limitations

- Static model (does not sequence investments over time)
- Uniform solar resource (18% CF nationwide)
- Euclidean distances (road network not modeled)
- No diesel backup for mini-grids
- No consideration of grid reliability or power quality

## Project Structure

```
├── benin_least_cost/
│   ├── demand.py          # Demand estimation
│   ├── lcoe.py            # LCOE calculation
│   ├── parameters.py      # Model parameters
│   └── schema.py          # Data validation
├── data/
│   ├── settlements.geojson
│   └── infrastructure.geojson
├── notebooks/
│   └── electrification_analysis.ipynb
├── run_model.py           # CLI entry point
└── requirements.txt
```

