# Battery Charging Simulation

A comprehensive ODE-based simulation framework for analyzing and optimizing lithium-ion battery charging policies.

## Overview

Simulates the dynamic behavior of lithium-ion batteries during charging, accounting for:
- **Thermal dynamics** (Joule heating, environmental cooling)
- **State of charge dynamics** (charge accumulation, open circuit voltage)
- **Transient voltage response** (RC circuit polarization model)
- **SEI layer growth** (temperature and current-dependent degradation)

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run Simulation
Single-trajectory interaction simulations can be found at [Battery Simulation Website](https://boyazhangnb.github.io/BatterySim/).


To produce figures and comparison results, run the follow scripts in this order to store generated figures in `log/` directory.

```bash
# Run parameter sweep (tests multiple current/voltage combinations)
python sweep_policies.py

# Generate comparison plot with grouped bars
python compare_policies.py
```

## File Structure

**Core Simulation:**
- `main.py` - Main simulation runner
- `config.py` - Centralized configuration
- `charging_policy.py` - Charging policy implementations
- `update_state.py` - ODE system and state evolution
- `utils.py` - Utility functions

**Analysis & Visualization:**
- `sweep_policies.py` - Parameter sweep framework
- `compare_policies.py` - Policy comparison with grouped bar charts

**Output:**
- `log/` - Simulation results (CSV logs, metrics, plots)
- `requirements.txt` - Python dependencies

## Charging Policies

- **CC** (Constant Current): Maintains constant current
- **CV** (Constant Voltage): Maintains constant voltage
- **CCCV** (CC-CV Two-stage): Constant current followed by constant voltage
- **CCCVPulse** (Three-stage): CC → CV → Pulse charging

## Output Metrics

Each simulation generates:
- **Charging Time (hours)**: Total time to reach 100% SoC
- **Peak Temperature (K)**: Maximum temperature during charge
- **SEI Growth**: Final SEI layer thickness (degradation indicator)

## Comparison Visualization

The comparison plot shows:
- **Grouped bars** by policy type (CC, CV, CCCV, CCCVPulse)
- **Different bar heights** representing different parameter values
- **Color shading** to distinguish parameter intensity
- **Parameter labels** below each bar (current in Amps or voltage in Volts)
- **Four panels**:
  1. Charging time comparison
  2. Peak temperature (thermal stress)
  3. Voltage and current vs State of Charge
  4. SEI growth (degradation)

## Numerical Method

Uses **Runge-Kutta 4th Order (RK4)** integration for solving coupled ODEs with high accuracy and stability.
