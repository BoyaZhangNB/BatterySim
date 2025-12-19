"""
Battery Simulation Main Module (Refactored with Centralized Config)

This module simulates battery charging behavior under different charging policies,
accounting for various physical mechanisms including thermal dynamics, SEI layer growth,
and transient response.

IMPORTANT: All parameters are now centralized in config.py
To run different experiments:
  1. Edit config.py (only file you need to modify!)
  2. Run: python main.py

NO NEED to edit main.py, charging_policy.py, or other modules.

State Variables:
    - t (seconds): time
    - voltage (V): open circuit voltage of the battery (varies with soc)
    - current (A): current into the battery
    - resistance (Ohm): internal resistance of the battery
    - temperature (K): temperature of the battery (assume uniform)
    - soc: state of charge (0.0 to 1.0)
    - SEI: solid-electrolyte interphase thickness that permanently reduces battery capacity
    - transient voltage (V): voltage drop due to RC circuit dynamics
    - v_source (V): supplied voltage from source

Usage:
    $ python main.py
    
    Simulates charging with policies configured in config.py
    Results saved to log/ directory as CSV files
"""
import os
import numpy as np
import pandas as pd
import gc  # Add garbage collection

from mechanism.thermo import Thermo
from mechanism.charging import Charging
from mechanism.sei import SEI
from mechanism.transient import Transient

from update_state import UpdateState
from utils import *
from config import (
    get_battery_config,
    get_mechanism_config,
    get_simulation_config,
    get_policies,
    EXPERIMENT_CONFIG,
    print_config_summary
)

# ==================== Load Configuration from config.py ====================
# All parameters are now centralized for easy modification
battery_cfg = get_battery_config()
mech_cfg = get_mechanism_config()
sim_cfg = get_simulation_config()

# Initialize physical mechanisms from centralized config
_thermo = Thermo(
    mass=mech_cfg['thermal']['mass'],
    c=mech_cfg['thermal']['specific_heat'],
    k=mech_cfg['thermal']['heat_transfer'],
    ambient_temp=mech_cfg['thermal']['ambient_temp']
)
_charging = Charging(C_nominal=battery_cfg['C_nominal'])
_sei = SEI()
_transient = Transient(
    R=mech_cfg['transient']['R'],
    C=mech_cfg['transient']['C']
)

updatestate = UpdateState()

# Initialize simulation parameters from centralized config
mechanisms = [_thermo, _charging, _sei, _transient]
dt = sim_cfg['dt']
cycles = sim_cfg['cycles']
initial_conditions = sim_cfg['initial_conditions'].copy()
initial_sei = initial_conditions.get('SEI', 0)

# Get policies from centralized config
policies_dict = get_policies()
policies = list(policies_dict.values())


def total_derivative(y, t, v_source):
    """
    Calculate the total rate of change for all state variables.
    
    Combines gradients from all physical mechanisms (thermal, charging, SEI, transient)
    to compute the total derivative dy/dt for numerical integration.
    
    Args:
        y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
        t (float): Current time in seconds
        v_source (float): Applied source voltage in volts
    
    Returns:
        np.array: Total derivative vector dy/dt with same shape as y
        
    Note:
        Each mechanism's get_gradient() method returns derivatives for the entire state vector,
        with zeros for state variables it doesn't affect. The total derivative is the sum of
        all mechanism contributions.
    """
    # Initialize derivative vector with zeros
    dydt = np.zeros_like(y)
    
    # Sum contributions from all mechanisms
    for mech in mechanisms:
        # Each mechanism returns derivatives for the whole state (or subset)
        # Ensure mech_grad is an array with same shape as y
        mech_grad = mech.get_gradient(y, t, v_source)
        dydt += np.asarray(mech_grad)
    
    # Note: Direct contributions from policy (e.g., control law) could be added here if needed
    return dydt

def rk4_step(y, t, dt, v_source):
    """
    Perform a single Runge-Kutta 4th order integration step.
    
    RK4 is a numerical method for solving ordinary differential equations (ODEs)
    that provides better accuracy than simpler methods like Euler integration.
    It evaluates the derivative at four points within the time step and combines
    them with weighted averaging.
    
    Args:
        y (np.array): Current state vector
        t (float): Current time in seconds
        dt (float): Time step size in seconds
        v_source (float): Applied source voltage in volts
    
    Returns:
        np.array: New state vector after time step dt
        
    Algorithm:
        k1 = f(y, t)                    # Slope at beginning
        k2 = f(y + dt*k1/2, t + dt/2)   # Slope at midpoint using k1
        k3 = f(y + dt*k2/2, t + dt/2)   # Slope at midpoint using k2
        k4 = f(y + dt*k3, t + dt)       # Slope at end using k3
        y_new = y + (dt/6)*(k1 + 2*k2 + 2*k3 + k4)  # Weighted average
    """
    k1 = total_derivative(y, t, v_source)
    k2 = total_derivative(y + 0.5*dt*k1, t + 0.5*dt, v_source)
    k3 = total_derivative(y + 0.5*dt*k2, t + 0.5*dt, v_source)
    k4 = total_derivative(y + dt*k3, t + dt, v_source)
    return y + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def simulate_charging(sei, policy):
    """
    Simulate a single charging cycle until battery reaches 100% state of charge.
    
    This function integrates the battery state equations over time using the RK4 method,
    applying the specified charging policy and accounting for all physical mechanisms.
    The simulation continues until SoC reaches 1.0 (100%) or until charging current
    drops below a threshold (indicating battery is fully charged).
    
    Args:
        sei (float): Initial SEI layer thickness at start of this cycle
        policy (ChargingPolicy): Charging policy object that determines v_source via get_voltage()
    
    Returns:
        list: Log of simulation data, where each entry is a tuple:
              (time, voltage, current, resistance, temperature, soc, sei, transient_voltage)
              
    Note:
        - Initial conditions are reset at the start of each cycle (except SEI)
        - The simulation runs until soc >= 1.0 or current < 0.01A (charging termination)
        - Time step dt is defined globally
        - Safety timeout at 100,000 steps to prevent infinite loops
    """
    # Initialize state from initial conditions
    t = 0.0
    y = pack_state(initial_conditions['voltage'], 
                   initial_conditions['current'], 
                   initial_conditions['resistance'], 
                   initial_conditions['temperature'], 
                   initial_conditions['soc'], 
                   sei,  # SEI persists from previous cycles
                   initial_conditions['transient voltage'])
    
    log = []
    max_steps = 100000  # Safety limit: prevent infinite loops
    steps = 0
    last_progress = 0
    
    # Run simulation until battery is fully charged or current drops to zero
    while y[4] < 1.0 and steps < max_steps:
        # Get voltage from charging policy
        v_source = policy.get_voltage(t, y)
        
        # Update algebraic state variables (voltage, current, resistance)
        y = updatestate.update_y(initial_conditions, y, v_source)
        
        # Termination condition: if current drops to near-zero, battery is charged
        # This handles CV policies where OCV reaches CV target before 100% SOC
        if abs(y[1]) < 0.01:  # Current < 10 mA
            y = pack_state(y[0], 0, y[2], y[3], 1.0, y[5], y[6])  # Set SOC to 1.0
            log.append((t + dt, *y))
            break
        
        # Integrate differential equations using RK4
        y = rk4_step(y, t, dt, v_source)
        
        t += dt
        steps += 1
        
        # Log current state
        log.append((t, *y))
        
        # Show progress every 20% of max_steps to indicate it's not hanging
        progress_threshold = max_steps // 5
        if steps >= last_progress + progress_threshold:
            # Print nothing to keep output clean - just prevent timeout
            last_progress = steps

    return log

def simulate_charging_cycle(cycles, policy):
    """
    Simulate multiple consecutive charging cycles with a given policy.
    
    Runs multiple charging cycles while tracking SEI layer growth across cycles.
    SEI accumulates across cycles (simulating battery degradation), while other
    state variables reset to initial conditions at the start of each cycle.
    
    Args:
        cycles (int): Number of charging cycles to simulate
        policy (ChargingPolicy): Charging policy to apply
    
    Returns:
        list: List of cycle logs, where each cycle log is a list of tuples
              Format: [[cycle1_data], [cycle2_data], ...]
              Each cycle_data contains (t, voltage, current, resistance, temperature, soc, sei, transient)
              
    Note:
        - Progress is printed every 100 cycles
        - SEI layer persists and grows across cycles
        - All other state variables reset each cycle
    """
    log = []
    
    # Initialize SEI at starting value
    sei = initial_sei

    # Run multiple charging cycles
    for cycle in range(cycles):
        # Print progress for long simulations
        if cycle % 100 == 0:
            print(f"Starting cycle {cycle+1}")
        
        # Simulate single cycle and append to log
        cycle_log = simulate_charging(sei, policy)
        log.append(cycle_log)
        sei = cycle_log[-1][6]  # Update SEI for next cycle (index 6 in log tuple)

    return log

# ==================== Data Format ====================
# Log structure: [[cycle1_data], [cycle2_data], ...]
# Each cycle_data is a list of tuples: (t, voltage, current, resistance, temperature, soc, sei, transient)


def main():
    """
    Main execution function for battery simulation.
    
    Simulates battery charging for all configured policies and saves results to CSV files.
    Each policy generates a separate log file in the log/ directory.
    Also generates a metrics summary file comparing policies on key metrics.
    
    ALL PARAMETERS ARE READ FROM config.py - No need to edit this function!
    
    Output Files:
        - log/log_{policy_name}_cycle{i}.csv: CSV file with columns:
          time, voltage, current, resistance, temperature, soc, sei, transient_voltage
        - log/policy_metrics_summary.csv: Comparison metrics for all policies
    """
    print("\n" + "="*70)
    print("BATTERY CHARGING SIMULATION")
    print("="*70)
    print(f"\nExperiment: {EXPERIMENT_CONFIG['name']}")
    print(f"Description: {EXPERIMENT_CONFIG['description']}\n")
    
    os.makedirs("log", exist_ok=True)
    
    # Clean up old log files to save disk space
    import glob
    old_logs = glob.glob("log/log_*.csv")
    for old_file in old_logs:
        try:
            os.remove(old_file)
        except:
            pass
    
    metrics_list = []
    
    for policy_idx, policy in enumerate(policies, 1):
        print(f"[{policy_idx}/{len(policies)}] Simulating {policy.name}...", end=" ", flush=True)
        
        # Simulate charging cycles for this policy
        policy_log = simulate_charging_cycle(cycles, policy)

        headers = "time,voltage,current,resistance,temperature,soc,sei,transient_voltage"

        # Save each cycle and compute metrics
        for i, cycle_log in enumerate(policy_log, start=1):
            arr = np.array(cycle_log)
            filename = f"log/log_{policy.name}_cycle{i}.csv"
            np.savetxt(filename, arr, delimiter=",", header=headers, comments='')
            
            # Compute metrics from last cycle
            if i == cycles:
                cycle_arr = np.array(cycle_log)
                time_col = cycle_arr[:, 0]
                temp_col = cycle_arr[:, 4]
                sei_col = cycle_arr[:, 6]
                
                charging_time = time_col[-1] / 3600  # Convert to hours
                peak_temp = np.max(temp_col)
                avg_temp = np.mean(temp_col)
                final_sei = sei_col[-1]
                
                metrics_list.append({
                    'Policy': policy.name,
                    'Charging_Time_Hours': charging_time,
                    'Peak_Temp_K': peak_temp,
                    'Avg_Temp_K': avg_temp,
                    'Final_SEI': final_sei,
                    'SEI_Growth': final_sei,
                })
            
            # Clear arrays to free memory
            del arr, cycle_log
        
        # Clear policy log and force garbage collection
        del policy_log
        gc.collect()
        
        print(f"✓")
    
    # Save metrics summary
    if metrics_list:
        metrics_df = pd.DataFrame(metrics_list)
        metrics_file = "log/policy_metrics_summary.csv"
        metrics_df.to_csv(metrics_file, index=False)
        print(f"\n✓ Metrics summary saved to {metrics_file}")
        print("\nPolicy Comparison:")
        print(metrics_df.to_string(index=False))
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70 + "\n")
    
if __name__ == "__main__":
    main()