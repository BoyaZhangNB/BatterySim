"""
Battery Simulation Main Module

This module simulates battery charging behavior under different charging policies,
accounting for various physical mechanisms including thermal dynamics, SEI layer growth,
and transient response.

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
    1. Configure mechanisms, policies, and initial conditions
    2. Run main() to simulate charging cycles
    3. Results are saved to log/ directory as CSV files
    
Example:
    $ python main.py
    
    Simulates charging with configured policies and saves results to log/log_*.csv
"""
import os
import numpy as np
import pandas as pd

from charging_policy import CVPulse
from mechanism.thermo import Thermo
from mechanism.charging import Charging
from mechanism.sei import SEI
from mechanism.transient import Transient

from charging_policy import *

from update_state import UpdateState
from utils import *


# ==================== Mechanism Initialization ====================
# Initialize physical mechanisms that govern battery behavior
_thermo = Thermo(mass=1.0, c=0.5, k=3, ambient_temp=298)  # Thermal dynamics: 1kg mass, 0.5 J/(kg*K) specific heat
_charging = Charging(C_nominal=3) # Charging dynamics: 3 Ah nominal capacity (3000 mAh)
_sei = SEI()  # Solid-Electrolyte Interphase layer growth
_transient = Transient(R=0.008, C=5000) # RC circuit dynamics: 8 mΩ resistance, 5000 F capacitance

# ==================== Charging Policy Selection ====================
# Define available charging policies (uncomment to use different policies)
# FAIR COMPARISON: All policies use 20A max current, same 3 Ah battery, same 100% SoC target
# CV voltage: 4.0V for CV/CVPulse, 3.5V for CCCV/CCCVPulse (two-stage policies)

_cc = CC(current=20)                                           # Pure constant current at 20A
_cv = CV(voltage=3.7)                                          # Pure constant voltage at 4.0V
_cccv = CCCV(cc_current=20, cv_voltage=4.0)                   # CC-CV: 20A until 4.0V, then constant 4.0V
_cccp = CCCVPulse(cc_current=20, cv_voltage=4.0, pulse_current=20, pulse_freq=1)  # CC-CV-Pulse: 20A→4.0V→pulse
_cvp = CVPulse(cv_voltage=4.0, pulse_current=20, pulse_freq=1) # CV-Pulse: start at 4.0V with pulses

_pulse = PulseCharging(current=50, pulse_time=2, rest_time=0.25)  # Pulse charging: 50A for 2s, rest 0.25s
_sinusoidal = SinusoidalCharging(current=60, frequency=4)  # Sinusoidal charging: 60A amplitude, 4Hz frequency

updatestate = UpdateState()

# ==================== Simulation Configuration ====================
mechanisms = [_thermo, _charging, _sei, _transient]  # List of mechanism instances from mechanism/*.py
policies = [_cc, _cv, _cccv, _cccp, _cvp]  # Fair comparison: 5 distinct strategies at 20A
dt = 0.1  # Time step in seconds (smaller = more accurate but slower)
cycles = 10  # Number of charging cycles to simulate per policy

# ==================== Initial Conditions ====================
# Starting state for each charging cycle
initial_conditions = {
    'voltage': 3.0,      # Initial open circuit voltage (V)
    'current': 0.0,      # Initial current (A) - typically starts at zero
    'resistance': 0.03,  # Initial internal resistance (Ω)
    'temperature': 298,  # Initial temperature (K) - room temperature
    'soc': 0.0,          # Initial state of charge (0.0 = empty, 1.0 = full)
    'transient voltage': 0.0  # Initial transient voltage from RC circuit (V)
}
initial_sei = 0  # Initial SEI layer thickness (persists across cycles)
# Note: initial_conditions reset every charging cycle, but SEI only resets at simulation start


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
    The simulation continues until SoC reaches 1.0 (100%).
    
    Args:
        sei (float): Initial SEI layer thickness at start of this cycle
        policy (ChargingPolicy): Charging policy object that determines v_source via get_voltage()
    
    Returns:
        list: Log of simulation data, where each entry is a tuple:
              (time, voltage, current, resistance, temperature, soc, sei, transient_voltage)
              
    Note:
        - Initial conditions are reset at the start of each cycle (except SEI)
        - The simulation runs until soc >= 1.0
        - Time step dt is defined globally
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
    
    # Run simulation until battery is fully charged
    while y[4] < 1.0:  # y[4] is soc
        # Get voltage from charging policy
        v_source = policy.get_voltage(t, y)
        
        # Update algebraic state variables (voltage, current, resistance)
        y = updatestate.update_y(initial_conditions, y, v_source)
        
        # Integrate differential equations using RK4
        y = rk4_step(y, t, dt, v_source)
        
        t += dt
        
        # Log current state
        log.append((t, *y))

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
    
    Output Files:
        - log/log_{policy_name}_cycle{i}.csv: CSV file with columns:
          time, voltage, current, resistance, temperature, soc, sei, transient_voltage
        - log/policy_metrics_summary.csv: Comparison metrics for all policies
          
    Process:
        1. Iterates through all policies defined in the 'policies' list
        2. Runs simulate_charging_cycle() for each policy
        3. Saves results to CSV with descriptive filename
        4. Computes and saves metrics (charging time, peak temp, final SEI, etc.)
        5. Prints completion message for each policy
    """
    metrics_list = []
    
    for policy in policies:
        # Simulate charging cycles for this policy
        policy_log = simulate_charging_cycle(cycles, policy)

        os.makedirs("log", exist_ok=True)
        headers = "time,voltage,current,resistance,temperature,soc,sei,transient voltage"

        # Save each cycle separately and compute metrics
        for i, cycle_log in enumerate(policy_log, start=1):

            # Convert list of tuples into array
            arr = np.array(cycle_log)

            filename = f"log/log_{policy.name}_cycle{i}.csv"
            np.savetxt(filename, arr, delimiter=",", header=headers, comments='')

            print(f"Saved {filename}")
            
            # Compute metrics for this cycle
            if i == 1:  # Only analyze first cycle for consistency
                cycle_arr = np.array(cycle_log)
                
                # Extract columns: t, voltage, current, resistance, temperature, soc, sei, transient
                time_col = cycle_arr[:, 0]
                temp_col = cycle_arr[:, 4]
                sei_col = cycle_arr[:, 6]
                
                charging_time = time_col[-1]  # Total charging time in seconds
                peak_temp = np.max(temp_col)  # Maximum temperature
                avg_temp = np.mean(temp_col)  # Average temperature
                final_sei = sei_col[-1]  # Final SEI thickness
                sei_growth = final_sei - initial_sei  # SEI growth in this cycle
                
                metrics_list.append({
                    'Policy': policy.name,
                    'Charging_Time_Hours': charging_time / 3600,
                    'Peak_Temp_K': peak_temp,
                    'Avg_Temp_K': avg_temp,
                    'Final_SEI': final_sei,
                    'SEI_Growth': sei_growth
                })

        print(f"Simulation with policy {policy.name} completed.")
    
    # Save metrics summary
    if metrics_list:
        metrics_df = pd.DataFrame(metrics_list)
        metrics_file = "log/policy_metrics_summary.csv"
        metrics_df.to_csv(metrics_file, index=False)
        print(f"\nMetrics summary saved to {metrics_file}")
        print("\nPolicy Comparison:")
        print(metrics_df.to_string(index=False))
    
if __name__ == "__main__":
    main()