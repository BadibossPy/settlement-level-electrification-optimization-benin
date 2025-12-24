# Settlement-Level Least-Cost Electrification (Benin, 2025-2040)

Least-cost electrification model for 17,205 settlements in Benin comparing Grid, Mini-Grid, and Solar Home Systems (SHS).

## Results

| Technology | Settlements | Population | Investment |
|------------|-------------|------------|------------|
| Grid | 1,523 (9%) | 11.5M (81%) | $1.58B |
| Mini-Grid | 7,552 (44%) | 2.1M (15%) | $0.67B |
| SHS | 8,130 (47%) | 0.5M (4%) | $0.01B |
| **Total** | **17,205** | **14.1M** | **$2.26B** |

## Workflow

```mermaid
flowchart TB
    subgraph INPUT["1. INPUT"]
        A[settlements.geojson<br/>17,205 settlements<br/>population, wealth, distances]
    end

    subgraph CLASSIFY["2. CLASSIFICATION"]
        B1[Urban/Rural<br/>pop > 5000 or buildings > 500]
        B2[MTF Tier 1-3<br/>from wealth index RWI]
        B3[Households<br/>pop / hh_size]
    end

    subgraph DEMAND["3. DEMAND ESTIMATION"]
        C1[Residential<br/>households × tier_kWh × uptake]
        C2[Commercial<br/>SME count × 600 kWh]
        C3[Agricultural<br/>mills + irrigation + dryers]
        C4[Public<br/>health + education facilities]
        C5[Growth 2025→2040<br/>pop 2.7% + wealth 1.5%]
    end

    subgraph COST["4. LCOE CALCULATION"]
        D1[Grid<br/>MV distance + LV + transformers<br/>+ connections + energy cost]
        D2[Mini-Grid<br/>PV sizing + battery + inverter<br/>+ replacements Y7,Y14]
        D3[SHS<br/>unit cost by tier<br/>excluded if productive loads]
    end

    subgraph SELECT["5. OPTIMIZATION"]
        E1[LCOE comparison<br/>Grid vs Mini-Grid vs SHS]
        E2[Select minimum<br/>per settlement]
    end

    subgraph OUTPUT["6. OUTPUT"]
        F[results.geojson<br/>optimal_tech + investment<br/>per settlement]
    end

    A --> B1 --> B2 --> B3
    B3 --> C1 & C2 & C3 & C4
    C1 & C2 & C3 & C4 --> C5
    C5 --> D1 & D2 & D3
    D1 & D2 & D3 --> E1 --> E2 --> F

    style INPUT fill:#e3f2fd
    style CLASSIFY fill:#fff3e0
    style DEMAND fill:#f3e5f5
    style COST fill:#e8f5e9
    style SELECT fill:#fce4ec
    style OUTPUT fill:#e0f2f1
```

## Data

**Required:** `geometry`, `population`

**Optional:** `num_buildings`, `mean_rwi`, `has_nightlight`, `dist_to_substations`, `distance_to_existing_transmission_lines`, `dist_main_road_km`, `dist_lake_river_km`, `num_health_facilities`, `num_education_facilities`

## Usage

```bash
pip install -r requirements.txt
python run_model.py --input data/settlements.geojson --output results.geojson
```

## Output Fields

- `projected_demand` - Annual demand 2040 (kWh/year)
- `projected_peak` - Peak load (kW)
- `lcoe_grid`, `lcoe_mg`, `lcoe_shs` - LCOE per technology (USD/kWh)
- `optimal_tech` - Selected technology (Grid / MiniGrid / SHS)
- `investment` - CAPEX for selected technology (USD)

## Parameters

All parameters in `benin_least_cost/parameters.py`:
- Planning: discount rate 8%, horizon 15 years, population growth 2.7%
- Grid: MV $14,000/km, LV $5,500/km, transformer $8,000, losses 18%
- Mini-Grid: PV $700/kW, battery $300/kWh, CF 18%
- SHS: $80-$600 per household by tier

## Structure

```
├── benin_least_cost/
│   ├── demand.py      # Demand estimation
│   ├── lcoe.py        # LCOE and selection
│   ├── parameters.py  # All parameters
│   └── schema.py      # Data validation
├── data/
│   └── settlements.geojson
├── notebooks/
│   └── electrification_analysis.ipynb
├── run_model.py
└── requirements.txt
```

## Verification

```bash
pytest tests/
jupyter nbconvert --execute notebooks/electrification_analysis.ipynb
```

