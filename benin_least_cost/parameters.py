"""Model parameters."""

from dataclasses import dataclass, field
from typing import Dict

@dataclass
class PlanningParams:
    """Planning assumptions."""
    horizon_years: int = 15
    pop_growth_rate: float = 0.027
    wealth_growth_rate: float = 0.015
    discount_rate: float = 0.08
    target_uptake_rate: float = 0.85
    urban_hh_size: float = 4.3
    rural_hh_size: float = 5.2
    urban_threshold_pop: int = 5000

    def __post_init__(self):
        if not (0 < self.discount_rate < 1):
            raise ValueError("Discount rate must be between 0 and 1.")
        if self.horizon_years <= 0:
            raise ValueError("Planning horizon must be positive.")

@dataclass
class DemandParams:
    """MTF consumption profiles."""
    tier_kwh: Dict[int, int] = field(default_factory=lambda: {
        1: 35, 2: 220, 3: 850, 4: 2200, 5: 3500
    })
    tier_lf: Dict[int, float] = field(default_factory=lambda: {
        1: 0.18, 2: 0.20, 3: 0.25, 4: 0.30, 5: 0.35
    })
    anchor_loads: Dict[str, int] = field(default_factory=lambda: {
        "health": 4000, "education": 1500, "sme": 600,
        "freezer": 2500, "irrigation": 3500, "mill": 4500, "dryer": 6000,
    })
    urban_sme_ratio: int = 50
    rural_sme_ratio: int = 100

@dataclass
class GridParams:
    """Grid extension costs."""
    mv_cost_per_km: float = 14000.0
    lv_cost_per_km: float = 5500.0
    substation_cost: float = 500000.0
    transformer_cost: float = 8000.0
    transformer_kva: float = 45.0
    connection_cost: float = 150.0
    loss_factor: float = 0.18
    energy_price_usd_kwh: float = 0.10
    lifetime_years: int = 40
    om_rate: float = 0.02
    transformer_diversity: float = 0.6
    lv_line_per_hh: float = 0.05

    def __post_init__(self):
        if any(v < 0 for v in [self.mv_cost_per_km, self.substation_cost, self.energy_price_usd_kwh]):
            raise ValueError("Grid costs and prices cannot be negative.")

@dataclass
class MiniGridParams:
    """Mini-grid costs (solar + battery)."""
    pv_cost_per_kw: float = 700.0
    battery_cost_per_kwh: float = 300.0
    inverter_cost_per_kw: float = 180.0
    connection_cost: float = 100.0
    solar_capacity_factor: float = 0.18
    battery_lifetime_years: int = 7
    project_lifetime_years: int = 20
    om_rate: float = 0.03
    pv_oversizing: float = 1.20
    sys_efficiency: float = 0.85
    battery_dod: float = 0.80
    inverter_margin: float = 1.25
    lv_reticulation_factor: float = 0.1
    
    def __post_init__(self):
        if self.battery_lifetime_years >= self.project_lifetime_years:
            raise ValueError("Battery life should be shorter than project life for NPV logic.")

@dataclass
class SHSParams:
    """SHS costs by tier."""
    costs: Dict[int, float] = field(default_factory=lambda: {1: 80, 2: 250, 3: 600})
    capacity_limit: Dict[int, int] = field(default_factory=lambda: {1: 35, 2: 150, 3: 350})
    max_supported_tier: int = 3
    lifetime_years: int = 5
    om_rate: float = 0.05

@dataclass
class ProjectConfig:
    """All model parameters."""
    planning: PlanningParams = field(default_factory=PlanningParams)
    demand: DemandParams = field(default_factory=DemandParams)
    grid: GridParams = field(default_factory=GridParams)
    minigrid: MiniGridParams = field(default_factory=MiniGridParams)
    shs: SHSParams = field(default_factory=SHSParams)
