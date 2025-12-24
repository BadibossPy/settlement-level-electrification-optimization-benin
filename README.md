## Settlement-level least-cost electrification (Benin, 2025–2040)

Least-cost electrification analysis for Benin settlements. The implementation follows the assignment requirements: estimate demand over a planning horizon, compute LCOE for multiple technologies, and select the least-cost option per settlement.

## Architecture

```mermaid
flowchart TD
    subgraph INPUT[Input Data]
        A[settlements.geojson]
        B[infrastructure.geojson]
    end

    subgraph DEMAND[Demand]
        C[Urban flag + households]
        D[MTF tier from RWI (+ nightlights)]
        E[Residential + commercial + agri + public]
        F[Growth + peak]
    end

    subgraph LCOE[LCOE]
        G[Grid]
        H[Mini-Grid]
        I[SHS (+ penalty)]
    end

    subgraph OUTPUT[Output]
        J[Min LCOE]
        K[results.geojson]
    end

    A --> C --> D --> E --> F
    B --> G
    F --> G --> J
    F --> H --> J
    F --> I --> J
    J --> K
```

## Data

### Required fields

- `geometry`
- `population`

### Optional fields used (if present)

- `num_buildings`, `mean_rwi`, `has_nightlight`
- `dist_to_substations`, `distance_to_existing_transmission_lines`, `dist_main_road_km`
- `dist_lake_river_km`, `dist_nearest_hub_km`
- `num_health_facilities`, `num_education_facilities`
- `lat` (used for the `> 8°N` dryer rule)

## Methods (as implemented)

All constants are in `benin_least_cost/parameters.py`.

### Demand model

**Urban flag**

```python
is_urban = (population > 5000) | (num_buildings > 500)
```

**Households**

```python
households = ceil(population / hh_size)
```

where hh_size = 4.3 (urban) or 5.2 (rural).

**Tiering (RWI)**

```python
tier = 1 if RWI < -0.3 else 2 if RWI < 0.4 else 3
```

If `has_nightlight > 0`, tier is raised to at least 2.

**Residential demand**

```python
E_res = households * tier_kwh[tier] * uptake
```

where uptake = 0.95 (urban) or 0.85 (rural).

**Commercial demand**

```python
gravity = min(max(1 + 20/(dist_hub + 1), 1), 2.5)
n_SME = floor((N / k) * gravity)
```

with k = 50 (urban) or 100 (rural), N = num_buildings if available else households.

```python
E_comm = n_SME * 600
```

**Agricultural demand**

- Mills (rural, population > 500): `E_mill = max(1, floor(pop/1500)) * 4500`
- Irrigation (dist_water < 3km, population > 300): `E_irr = max(1, floor(pop/800)) * 3500`
- Dryers (latitude > 8°, rural, population > 400): `E_dryer = max(1, floor(pop/2000)) * 6000`

**Public demand**

```python
E_pub = n_health * 4000 + n_edu * 1500
```

**Growth**

```python
G = (1 + g_pop) * (1 + g_wealth) ** H
```

with g_pop = 0.027, g_wealth = 0.015, H = 15.

```python
E_proj = (E_res + E_comm + E_agri + E_pub) * G
```

**Peak load**

```python
P_peak = E_proj / (8760 * LF[tier])
```

### LCOE model

**Capital Recovery Factor**

```python
CRF = lambda r, n: r * (1+r)**n / ((1+r)**n - 1)
```

Discount rate r = 0.08 by default.

**Grid**

```python
d_grid = min(d_sub, d_trans + C_sub/C_MV)
```

Terrain factor = 1.3 when dist_main_road_km > 10, else 1.0.

```python
Ann_grid = CAPEX_grid * (CRF(r, 40) + 0.02) + (E_proj / 0.82) * 0.10
```

```python
LCOE_grid = Ann_grid / E_proj
```

**Mini-Grid (PV + battery)**

```python
PV_kW = (E_proj / 365) / (CF * 24 * eta) * 1.2
```

with CF = 0.18, eta = 0.85.

```python
Batt_kWh = (E_proj / 365) / DoD
```

with DoD = 0.8.

```python
NPV_batt = sum(Batt_kWh * 300 / (1+r)**y for y in [7, 14])
```

```python
LCOE_mg = CAPEX_mg * (CRF(r, 20) + 0.03) / E_proj
```

**SHS**

```python
E_del = min(E_proj / households, cap[tier]) * households
```

```python
LCOE_shs = CAPEX_shs * (CRF(r, 5) + 0.05) / E_del
```

Penalty: if tier > 3 or any productive demand > 0, LCOE_shs = 999.9.

**Selection**

```python
optimal_tech = argmin([LCOE_grid, LCOE_mg, LCOE_shs])
```

## Results (example run on included `data/settlements.geojson`)

- Technology counts: Grid 1,523; Mini-Grid 7,552; SHS 8,130
- Total investment (sum of per-settlement CAPEX for the selected technology): USD 2,263,483,493

## Run

```bash
pip install -r requirements.txt
python run_model.py --input data/settlements.geojson --output results.geojson
```

## Notebook

`notebooks/benin_electrification_walkthrough.ipynb` runs the full pipeline and writes `results.geojson`.
