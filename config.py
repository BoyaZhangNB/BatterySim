"""
Centralized Configuration for Battery Charging Simulation

This module consolidates all simulation parameters in one place.
Users only need to edit this file to run different experiments—no need to modify
main.py, charging_policy.py, or other modules.

RECOMMENDED WORKFLOW:
=====================
1. Edit BATTERY_CONFIG and MECHANISM_CONFIG for battery/cell parameters
2. Edit POLICY_DEFINITIONS to add new charging policies or modify existing ones
3. Edit EXPERIMENT_CONFIG to select which policies to run
4. Edit SIMULATION_CONFIG to adjust dt (time step) and cycles
5. Run: python main.py              (generates log files and metrics)
6. Run: python compare_policies.py  (generates comparison plots)

Structure:
- BATTERY_CONFIG: Physical battery properties (capacity, voltage range, resistance)
- MECHANISM_CONFIG: Thermal, SEI, and transient dynamics parameters
- POLICY_DEFINITIONS: All charging policies with their parameters
- SIMULATION_CONFIG: Runtime parameters (dt, cycles, initial conditions)
- EXPERIMENT_CONFIG: Which policies to run

Usage:
    from config import (
        get_battery_config,
        get_mechanism_config,
        get_policies,
        get_simulation_config
    )
"""

import pandas as pd
from charging_policy import CC, CV, CCCV, CCCVPulse, CVPulse, PulseCharging, SinusoidalCharging


# ============================================================================
# BATTERY CONFIGURATION
# ============================================================================
# Define battery physical properties. Change these to model different batteries.

BATTERY_CONFIG = {
    'C_nominal': 3.0,        # Nominal capacity (Ah) - 3000 mAh
    'V_min': 3.0,            # Minimum voltage (V)
    'V_max': 4.2,            # Maximum voltage (V)
    'V_nominal': 3.7,        # Nominal voltage (V) - used for OCV curve
    'internal_resistance': 0.03,  # Initial internal resistance (Ω)
    'description': '3 Ah Li-ion cell (3000 mAh single cell)'
}


# ============================================================================
# MECHANISM CONFIGURATION
# ============================================================================
# Physical mechanism parameters: thermal dynamics, SEI growth, transients

MECHANISM_CONFIG = {
    'thermal': {
        'mass': 1.0,             # Battery mass (kg)
        'specific_heat': 0.5,    # Specific heat capacity (J/(kg·K))
        'heat_transfer': 3,      # Heat transfer coefficient to ambient
        'ambient_temp': 298,     # Ambient temperature (K) = 25°C
    },
    'sei': {
        # SEI layer growth parameters (all using default values)
        # Modify these to simulate different degradation rates
    },
    'transient': {
        'R': 0.008,              # RC circuit resistance (Ω)
        'C': 5000,               # RC circuit capacitance (F)
    },
}


# ============================================================================
# CHARGING POLICY DEFINITIONS
# ============================================================================
# Define all available charging policies with their parameters.
# Change voltage/current values here ONLY—no need to edit elsewhere.
# Format: 'policy_name': {'class': PolicyClass, 'params': {...}}

POLICY_DEFINITIONS = {
    # ========== BASELINE POLICIES (Original configuration) ==========
    'CC_20A': {
        'class': CC,
        'params': {'current': 20},
        'description': 'Constant Current at 20A'
    },
    
    'CV_4.2V': {
        'class': CV,
        'params': {'voltage': 4.2},
        'description': 'Constant Voltage at 4.2V'
    },
    
    'CCCV_20A_4.2V': {
        'class': CCCV,
        'params': {'cc_current': 20, 'cv_voltage': 4.2},
        'description': 'Two-stage: 20A CC → 4.2V CV (80% SOC threshold)'
    },
    
    'CCCVPulse_20A_4.2V': {
        'class': CCCVPulse,
        'params': {'cc_current': 20, 'cv_voltage': 4.2, 'pulse_current': 5, 'pulse_freq': 1},
        'description': 'Three-stage: 20A CC → 4.2V CV → 5A pulse @ 1Hz'
    },

    'CVPulse_4.2V': {
        'class': CVPulse,
        'params': {'cv_voltage': 4.2, 'pulse_current': 5, 'pulse_freq': 1},
        'description': 'Constant Voltage with 5A pulse @ 1Hz'
    },
    
    
    # ========== OPTIMIZED POLICIES (From Pareto analysis) ==========
    'CCCV_20A_4.2V': {
        'class': CCCV,
        'params': {'cc_current': 20, 'cv_voltage': 4.2},
        'description': 'Two-stage: 20A CC → 4.2V CV (optimal for speed/thermal)'
    },

    'CCCVPulse_20A_4.2V': {
        'class': CCCVPulse,
        'params': {'cc_current': 20, 'cv_voltage': 4.2, 'pulse_current': 5, 'pulse_freq': 1},
        'description': 'Three-stage: 20A CC → 4.2V CV → 5A pulse (optimized)'
    },
    
    
    # ========== PARAMETER SWEEP EXAMPLES ==========
    # Uncomment these for sensitivity analysis or testing
    
    # CC currents
    # 'CC_10A': {'class': CC, 'params': {'current': 10}, 'description': 'CC at 10A'},
    # 'CC_15A': {'class': CC, 'params': {'current': 15}, 'description': 'CC at 15A'},
    # 'CC_25A': {'class': CC, 'params': {'current': 25}, 'description': 'CC at 25A'},
    
    # CV voltages
    # 'CV_3.7V': {'class': CV, 'params': {'voltage': 3.7}, 'description': 'CV at 3.7V'},
    # 'CV_4.2V': {'class': CV, 'params': {'voltage': 4.2}, 'description': 'CV at 4.2V'},
    
    # CCCV with different thresholds
    # 'CCCV_20A_3.8V': {'class': CCCV, 'params': {'cc_current': 20, 'cv_voltage': 3.8}, 'description': 'CCCV at 3.8V'},
    # 'CCCV_20A_4.2V': {'class': CCCV, 'params': {'cc_current': 20, 'cv_voltage': 4.2}, 'description': 'CCCV at 4.2V'},
}


# ============================================================================
# SIMULATION CONFIGURATION
# ============================================================================
# Runtime parameters for simulations
#
# PERFORMANCE TIPS:
#   dt = 0.1  → High accuracy, slow (~20 sec per policy)
#   dt = 0.5  → Good balance, medium speed (~4 sec per policy)
#   dt = 1.0  → Fast testing, decent accuracy (~2 sec per policy)
#
# For quick testing, use dt=0.5 or dt=1.0
# For final results/publication, use dt=0.1

SIMULATION_CONFIG = {
    'dt': 0.1,                       # Time step (seconds) - smaller = more accurate but slower
                                      # Use 0.5 for balance, 0.1 for high accuracy, 1.0 for speed
    'cycles': 10,                     # Number of charging cycles per policy
    'initial_conditions': {
        'voltage': 3.0,              # Initial open circuit voltage (V)
        'current': 0.0,              # Initial current (A)
        'resistance': 0.03,          # Initial internal resistance (Ω)
        'temperature': 298,          # Initial temperature (K)
        'soc': 0.0,                  # Initial state of charge (0-1)
        'SEI': 0.0,                  # Initial SEI thickness
        'transient voltage': 0.0,    # Initial transient voltage (V)
    }
}


# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================
# Select which policies to run. Edit this to run different experiments.

EXPERIMENT_CONFIG = {
    'name': 'Fair Comparison: Optimized Policies',
    'description': 'Comparing optimal configuration of each policy type',
    'policies': [
        'CC_20A',
        'CV_4.2V',
        'CCCV_20A_4.2V',
        'CCCVPulse_20A_4.2V',
        'CVPulse_4.2V',
    ],
    'save_logs': True,
    'save_metrics': True,
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
# These functions extract configs and instantiate policies

def get_battery_config():
    """Get battery configuration dictionary"""
    return BATTERY_CONFIG.copy()


def get_mechanism_config():
    """Get mechanism configuration dictionary"""
    return MECHANISM_CONFIG.copy()


def get_simulation_config():
    """Get simulation configuration dictionary"""
    return SIMULATION_CONFIG.copy()


def get_policies(policy_names=None):
    """
    Instantiate charging policies from configuration.
    
    Args:
        policy_names: List of policy names to instantiate. If None, uses EXPERIMENT_CONFIG.
        
    Returns:
        dict: {policy_name: policy_instance}
    """
    if policy_names is None:
        policy_names = EXPERIMENT_CONFIG['policies']
    
    policies = {}
    for name in policy_names:
        if name not in POLICY_DEFINITIONS:
            raise ValueError(f"Policy '{name}' not defined in config.py")
        
        policy_def = POLICY_DEFINITIONS[name]
        policy_class = policy_def['class']
        policy_params = policy_def['params']
        
        policies[name] = policy_class(**policy_params)
    
    return policies


def list_available_policies():
    """Print all available policies with descriptions"""
    print("\nAvailable Policies in config.py:\n")
    for name, definition in POLICY_DEFINITIONS.items():
        print(f"  {name:30} - {definition['description']}")
    print()


def print_config_summary():
    """Print summary of current configuration"""
    print("\n" + "="*70)
    print("SIMULATION CONFIGURATION SUMMARY")
    print("="*70)
    
    print("\nBATTERY:")
    for key, val in BATTERY_CONFIG.items():
        if key != 'description':
            print(f"  {key:20} = {val}")
    
    print("\nMECHANISMS:")
    for mechanism, params in MECHANISM_CONFIG.items():
        print(f"  {mechanism}:")
        for key, val in params.items():
            print(f"    {key:18} = {val}")
    
    print("\nSIMULATION:")
    for key, val in SIMULATION_CONFIG.items():
        if key != 'initial_conditions':
            print(f"  {key:20} = {val}")
    
    print(f"\nEXPERIMENT: {EXPERIMENT_CONFIG['name']}")
    print(f"  Policies ({len(EXPERIMENT_CONFIG['policies'])}):")
    for policy in EXPERIMENT_CONFIG['policies']:
        print(f"    • {policy}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Test: Print all configs
    print_config_summary()
    list_available_policies()
    
    # Test: Get policies
    policies = get_policies()
    print(f"Successfully instantiated {len(policies)} policies")
