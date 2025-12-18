# BatterySim

A physics-based battery charging simulator for analyzing and comparing different charging strategies.

## Project Goal

The goal of this project is to measure the effectiveness of different charging policies and their impact on both **charging speed** and **battery lifetime**. We evaluate policies using two key metrics:

- **Charging Time per Cycle**: How quickly the battery reaches full charge (measures efficiency)
- **SEI Layer Growth**: Rate of solid-electrolyte interphase formation (measures degradation and lifetime)

This allows us to understand the fundamental trade-off: fast charging policies may complete cycles quickly but potentially accelerate battery degradation, while gentler charging approaches may extend battery life at the cost of longer charging times.

## Overview

BatterySim is a comprehensive ordinary differential equation (ODE)-based model that simulates the dynamic behavior of lithium-ion batteries during charging. The simulator accounts for multiple coupled physical mechanisms that interact during battery operation.

### Physical Mechanisms

The model incorporates four key mechanisms:

1. **Thermal Dynamics** 
   - Tracks battery temperature changes from internal heating and environmental cooling
   - Joule heating from current flow through internal resistance
   - Newton's law of cooling for heat dissipation to the environment
   - Temperature affects other mechanisms (resistance, SEI growth rate)

2. **State of Charge (SoC) Dynamics**
   - Models how current flow changes the battery's charge level
   - Integrates current over time normalized by battery capacity
   - Determines open circuit voltage through voltage-SoC lookup tables

3. **Transient Voltage Response**
   - Captures short-term voltage dynamics using RC circuit model
   - Represents polarization effects and charge transfer limitations
   - Models voltage drop that builds during current flow and relaxes during rest

4. **SEI Layer Growth**
   - Simulates irreversible formation of solid-electrolyte interphase on anode
   - Primary mechanism for capacity fade and battery aging
   - Growth rate depends on temperature (Arrhenius), state of charge, and current
   - Accumulates across charging cycles to model long-term degradation

### Charging Policies

The simulator supports multiple charging strategies:

- **Constant Voltage (CV)**: Maintains fixed voltage throughout charging
- **Constant Current (CC)**: Adaptively adjusts voltage to maintain constant current
- **Pulse Charging**: Alternates between high-current pulses and rest periods
- **Sinusoidal Charging**: Applies smoothly varying current with configurable frequency

### Numerical Method

The simulation uses the **Runge-Kutta 4th Order (RK4)** method for numerical integration of the coupled differential equations. RK4 provides:

- **High accuracy**: Fourth-order convergence ensures precise results
- **Stability**: Handles stiff equations common in battery dynamics
- **Efficiency**: Good balance between accuracy and computational cost

At each time step, RK4 evaluates the system derivatives at four carefully chosen points and combines them with weighted averaging to advance the state. This is significantly more accurate than simple Euler integration while remaining computationally tractable for multi-cycle simulations.

## Usage

### Running a Simulation

1. Configure the simulation parameters in `main.py`:
   - Choose charging policy (CV, CC, Pulse, Sinusoidal)
   - Set initial conditions (temperature, SoC, resistance)
   - Define simulation parameters (time step, number of cycles)

2. Run the simulation:
   ```bash
   python main.py
   ```

3. Results are saved to `log/log_{policy_name}.csv` with columns:
   - time, voltage, current, resistance, temperature, soc, sei, transient_voltage

### Example Configuration

```python
# In main.py
_pulse = PulseCharging(current=50, pulse_time=2, rest_time=0.25)
policies = [_pulse]  # Simulate pulse charging
cycles = 100  # Run 100 charging cycles
dt = 0.1  # 0.1 second time step
```

## Project Structure

```
BatterySim/
├── main.py                 # Main simulation loop and configuration
├── charging_policy.py      # Charging policy implementations
├── update_state.py         # Algebraic state updates
├── utils.py               # Helper functions and data processing
├── mechanism/             # Physical mechanism models
│   ├── charging.py        # SoC dynamics
│   ├── thermo.py          # Thermal dynamics
│   ├── transient.py       # RC circuit dynamics
│   ├── sei.py             # SEI layer growth (full model)
│   └── sei_simplified.py  # SEI layer growth (simplified)
└── log/                   # Simulation output files
```

## Key Features

- **Modular Design**: Each physical mechanism is independent and can be easily modified or extended
- **Multiple Charging Policies**: Compare different strategies side-by-side
- **Physics-Based**: Grounded in established electrochemical and thermal models
- **Configurable**: Easy to adjust parameters for different battery chemistries and conditions
- **Comprehensive Output**: Logs all state variables for detailed analysis

## Requirements

- Python 3.x
- NumPy
- Matplotlib (for visualization)

See `requirements.txt` for complete dependencies.

## Background

This battery simulator was developed for MAT292 as a tool to explore the mathematical modeling of complex physical systems using ordinary differential equations. It demonstrates how coupled ODEs can capture the intricate behavior of real-world systems like lithium-ion batteries.
