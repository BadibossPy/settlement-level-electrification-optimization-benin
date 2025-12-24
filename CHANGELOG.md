# Changelog

## [1.0.0] - 2025-12-24

### Added
- Core demand estimation module with MTF tier logic
- LCOE calculation for Grid, Mini-Grid, and SHS
- CLI entry point (`run_model.py`)
- Python API for programmatic usage
- Unit tests for mathematical logic
- Analysis notebook with visualizations

### Model Features
- Settlement classification (urban/rural)
- Multi-tier demand estimation (residential, commercial, agricultural, public)
- 15-year growth projection (2025-2040)
- Grid extension costing (MV/LV lines, transformers, connections)
- Mini-grid sizing (PV + battery with replacements)
- SHS tier-based allocation with exclusion logic
- Least-cost technology selection per settlement

### Data
- Input: 17,205 settlements from Benin
- Output: Technology assignment and investment per settlement

