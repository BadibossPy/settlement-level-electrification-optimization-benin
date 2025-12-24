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

\[
\text{is\_urban} = (\text{population} > 5000)\ \lor\ (\text{num\_buildings} > 500)
\]

**Households**

\[
\text{households}=\left\lceil\frac{\text{population}}{s}\right\rceil
\]

with \(s=4.3\) (urban) and \(s=5.2\) (rural).

**Tiering (RWI)**

\[
\text{tier}=\begin{cases}
1 & \text{if } \text{RWI} < -0.3\\
2 & \text{if } -0.3 \le \text{RWI} < 0.4\\
3 & \text{otherwise}
\end{cases}
\]

If `has_nightlight > 0`, tier is raised to at least 2.

**Residential demand**

\[
E_{res}=\text{households}\cdot E_{tier}(\text{tier})\cdot uptake
\]

where \(uptake=0.95\) for urban and \(0.85\) for rural.

**Commercial demand**

\[
g = \text{clip}\left(1+\frac{20}{d_{hub}+1},\ 1,\ 2.5\right)
\]

\[
n_{SME}=\left\lfloor \frac{N}{k}\cdot g \right\rfloor
\]

with \(k=50\) (urban) or \(k=100\) (rural), and \(N\) = num_buildings if available, else households.

\[
E_{comm}=n_{SME}\cdot 600
\]

**Agricultural demand**

- Mills (rural, population > 500): \(E_{mill}=\max(1,\lfloor pop/1500\rfloor)\cdot 4500\)
- Irrigation (distance to water < 3 km, population > 300): \(E_{irr}=\max(1,\lfloor pop/800\rfloor)\cdot 3500\)
- Dryers (latitude > 8°, rural, population > 400): \(E_{dryer}=\max(1,\lfloor pop/2000\rfloor)\cdot 6000\)

**Public demand**

\[
E_{pub}=n_{health}\cdot 4000 + n_{edu}\cdot 1500
\]

**Growth**

\[
G=\big((1+g_{pop})(1+g_{wealth})\big)^{H}
\]

with \(g_{pop}=0.027\), \(g_{wealth}=0.015\), \(H=15\).

\[
E_{proj}=(E_{res}+E_{comm}+E_{agri}+E_{pub})\cdot G
\]

**Peak load**

\[
P_{peak}=\frac{E_{proj}}{8760\cdot LF(\text{tier})}
\]

### LCOE model

**Capital Recovery Factor**

\[
CRF(r,n)=\frac{r(1+r)^n}{(1+r)^n-1}
\]

Discount rate \(r=0.08\) by default.

**Grid**

\[
d_{grid}=\min(d_{sub},\ d_{trans} + C_{sub}/C_{MV})
\]

Terrain factor is 1.3 when `dist_main_road_km > 10`, else 1.0.

\[
Ann_{grid}=CAPEX_{grid}\cdot(CRF(r,40)+0.02)+\left(\frac{E_{proj}}{1-0.18}\right)\cdot 0.10
\]

\[
LCOE_{grid}=\frac{Ann_{grid}}{E_{proj}}
\]

**Mini-Grid (PV + battery)**

\[
PV_{kW}=\left(\frac{E_{proj}/365}{CF\cdot 24\cdot \eta}\right)\cdot 1.2
\]

with \(CF=0.18\), \(\eta=0.85\).

\[
Batt_{kWh}=\frac{E_{proj}/365}{DoD}
\]

with \(DoD=0.8\).

\[
NPV_{batt}=\sum_{y\in\{7,14\}} \frac{Batt_{kWh}\cdot 300}{(1+r)^y}
\]

\[
LCOE_{mg}=\frac{CAPEX_{mg}\cdot(CRF(r,20)+0.03)}{E_{proj}}
\]

**SHS**

\[
E_{del}=\min\left(\frac{E_{proj}}{households},\ cap(\text{tier})\right)\cdot households
\]

\[
LCOE_{shs}=\frac{CAPEX_{shs}\cdot(CRF(r,5)+0.05)}{E_{del}}
\]

Penalty: if `tier > 3` or any of `dem_comm`, `dem_agri`, `dem_pub` is positive, \(LCOE_{shs}=999.9\).

**Selection**

\[
\text{optimal\_tech}=\arg\min(LCOE_{grid},LCOE_{mg},LCOE_{shs})
\]

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
