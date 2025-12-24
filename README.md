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

```mermaid
flowchart TD
    Start[settlements.geojson<br/>17,205 settlements] --> V1{Validation}
    V1 -->|geometry, population| V2[Validated GeoDataFrame]
    
    V2 --> C1[Settlement Categorization]
    C1 --> C2{pop > 5000 OR<br/>buildings > 500?}
    C2 -->|Yes| Urban[Urban]
    C2 -->|No| Rural[Rural]
    
    Urban --> H1[households = ceil pop/4.3]
    Rural --> H2[households = ceil pop/5.2]
    
    H1 --> T1[Tier Assignment]
    H2 --> T1
    
    T1 --> T2{RWI?}
    T2 -->|< -0.3| Tier1[Tier 1]
    T2 -->|< 0.4| Tier2[Tier 2]
    T2 -->|≥ 0.4| Tier3[Tier 3]
    
    Tier1 --> T3{Nightlight?}
    Tier2 --> T3
    Tier3 --> T3
    T3 -->|has_nightlight > 0| TierAdj[tier = max tier, 2]
    T3 -->|else| TierFinal[Final Tier]
    TierAdj --> TierFinal
    
    TierFinal --> D1[Demand Estimation]
    
    D1 --> D2[Residential<br/>households × tier_kWh × uptake]
    D1 --> D3[Commercial<br/>SME_count × 600]
    D1 --> D4[Agricultural<br/>mills + irrigation + dryers]
    D1 --> D5[Public<br/>health + education]
    
    D2 --> D6[E_base = E_res + E_comm + E_agri + E_pub]
    D3 --> D6
    D4 --> D6
    D5 --> D6
    
    D6 --> D7[Growth Projection<br/>G = 1.027 × 1.015^15 = 1.74]
    D7 --> D8[E_proj = E_base × G]
    D8 --> D9[P_peak = E_proj / 8760 × LF]
    
    D9 --> Split{Compute LCOE<br/>for all technologies}
    
    Split --> G1[Grid LCOE]
    Split --> M1[Mini-Grid LCOE]
    Split --> S1[SHS LCOE]
    
    G1 --> G2[Distance Calculation<br/>d_grid = min d_sub, d_trans]
    G2 --> G3[Terrain Factor<br/>1.3 if road > 10km]
    G3 --> G4[CAPEX Components:<br/>MV line + LV dist + transformers + connections]
    G4 --> G5[Annualized Cost<br/>CAPEX × CRF 0.08,40 + OPEX]
    G5 --> G6[LCOE_grid = Ann / E_proj]
    
    M1 --> M2[PV Sizing<br/>daily_demand / CF × 24 × eta × 1.2]
    M2 --> M3[Battery Sizing<br/>daily_demand / DoD<br/>+ replacements Y7, Y14]
    M3 --> M4[CAPEX = PV + Battery + Inverter<br/>$700/kW + $300/kWh + $180/kW]
    M4 --> M5[Annualized Cost<br/>CAPEX × CRF 0.08,20]
    M5 --> M6[LCOE_mg = Ann / E_proj]
    
    S1 --> S2{Exclusion Check<br/>tier > 3 OR<br/>productive loads?}
    S2 -->|Yes| S3[LCOE_shs = 999.9]
    S2 -->|No| S4[Capacity Constraint<br/>E_del = min E_proj/hh, cap]
    S4 --> S5[CAPEX = households × unit_cost<br/>$80/$250/$600 by tier]
    S5 --> S6[Annualized Cost<br/>CAPEX × CRF 0.08,5]
    S6 --> S7[LCOE_shs = Ann / E_del]
    
    G6 --> Select[Technology Selection]
    M6 --> Select
    S3 --> Select
    S7 --> Select
    
    Select --> Opt{argmin LCOE}
    
    Opt -->|Grid| OptGrid[Selected: Grid<br/>Investment = CAPEX_grid<br/>LCOE = 0.38 $/kWh]
    Opt -->|MiniGrid| OptMG[Selected: Mini-Grid<br/>Investment = CAPEX_mg<br/>LCOE = 0.80 $/kWh]
    Opt -->|SHS| OptSHS[Selected: SHS<br/>Investment = CAPEX_shs<br/>LCOE = 0.63 $/kWh]
    
    OptGrid --> Output[results.geojson<br/>17,205 settlements<br/>optimal_tech, investment, LCOE]
    OptMG --> Output
    OptSHS --> Output
    
    Output --> Results[Results:<br/>Grid: 1,523 9%<br/>MiniGrid: 7,552 44%<br/>SHS: 8,130 47%<br/>Total: $2.26B]
    
    style Start fill:#e1f5ff
    style Results fill:#d4edda
    style Urban fill:#fff3cd
    style Rural fill:#fff3cd
    style Tier1 fill:#f8d7da
    style Tier2 fill:#fff3cd
    style Tier3 fill:#d4edda
    style OptGrid fill:#28a745,color:#fff
    style OptMG fill:#fd7e14,color:#fff
    style OptSHS fill:#ffc107
    style Output fill:#e1f5ff
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

