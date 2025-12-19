"""
Utility Functions Module

This module provides helper functions for state management, data visualization,
and battery parameter lookups.

Key Functions:
    - pack_state/unpack_state: Convert between vector and named variables
    - plot_simulation_data: Visualize simulation results
    - get_ocv_from_soc: Convert state of charge to open circuit voltage

Usage:
    from utils import pack_state, unpack_state, get_ocv_from_soc
"""
import numpy as np


def pack_state(voltage, current, resistance, temperature, soc, sei, transient):
    """
    Pack individual state variables into a single numpy array.
    
    This function creates a state vector from individual battery parameters,
    which is used throughout the simulation for numerical integration.
    
    Args:
        voltage (float): Open circuit voltage (V)
        current (float): Current (A)
        resistance (float): Internal resistance (Ω)
        temperature (float): Temperature (K)
        soc (float): State of charge (0.0 to 1.0)
        sei (float): SEI layer thickness (arbitrary units)
        transient (float): Transient voltage from RC circuit (V)
        
    Returns:
        np.array: State vector [voltage, current, resistance, temperature, soc, sei, transient]
        
    Example:
        >>> state = pack_state(3.5, 25.0, 0.03, 298, 0.5, 0.001, 0.02)
        >>> print(state)
        [3.5 25.0 0.03 298.0 0.5 0.001 0.02]
    """
    return np.array([voltage, current, resistance, temperature, soc, sei, transient], dtype=float)

def unpack_state(y):
    """
    Unpack state vector into individual named variables.
    
    Converts the state vector back into a tuple of named variables for
    easier access in mechanism calculations.
    
    Args:
        y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
        
    Returns:
        tuple: (voltage, current, resistance, temperature, soc, sei, transient)
        
    Example:
        >>> voltage, current, resistance, temp, soc, sei, transient = unpack_state(y)
        >>> print(f"Battery voltage: {voltage}V, Current: {current}A")
    """
    return tuple(y)

import matplotlib.pyplot as plt

def plot_simulation_data(log_data, variables_to_plot):
    """
    Plot logged simulation data over time.
    
    Visualizes battery state variables during charging simulation. Useful for
    analyzing charging behavior, identifying trends, and comparing different
    charging policies.
    
    Args:
        log_data (list): List of tuples containing simulation data.
                        Each tuple: (t, voltage, current, resistance, temperature, soc, sei, transient)
        variables_to_plot (list): List of variable indices to plot:
                                  0: voltage (V)
                                  1: current (A)
                                  2: resistance (Ω)
                                  3: temperature (K)
                                  4: soc (0-1)
                                  5: sei (arbitrary units)
                                  6: transient voltage (V)
    
    Returns:
        None: Displays a matplotlib plot
        
    Example:
        >>> # Plot voltage, current, and temperature
        >>> plot_simulation_data(log_data, variables_to_plot=[0, 1, 3])
        
    Note:
        All selected variables are plotted on the same axes. For variables
        with very different scales, consider plotting separately.
    """
    if not log_data:
        print("No data to plot")
        return
    
    # Convert log data to numpy array for easier indexing
    data = np.array(log_data)
    time = data[:, 0]  # First column is time
    
    # Variable names for legend
    variable_names = [
        'Voltage (V)', 
        'Current (A)', 
        'Resistance (Ω)', 
        'Temperature (K)', 
        'SOC', 
        'SEI',
        'Transient Voltage (V)'
    ]
    
    # Create plot
    plt.figure(figsize=(10, 6))
    
    # Plot each requested variable
    for var_idx in variables_to_plot:
        if 0 <= var_idx < len(variable_names):
            # Data columns are offset by 1 because first column is time
            plt.plot(time, data[:, var_idx + 1], label=variable_names[var_idx])
    
    plt.xlabel('Time (s)')
    plt.ylabel('Value')
    plt.title('Battery Simulation Results')
    plt.legend()
    plt.grid(True)
    plt.show()



def get_ocv_from_soc(soc):
    """
    Get Open Circuit Voltage (OCV) for a given State of Charge (SOC).
    
    Converts battery state of charge to open circuit voltage using linear
    interpolation between empirical data points for LiFePO4 (Lithium Iron Phosphate)
    batteries. This voltage-SoC relationship is characteristic of the battery
    chemistry and is critical for accurate simulation.
    
    Args:
        soc (float): State of charge as a fraction (0.0 to 1.0)
                    0.0 = fully discharged, 1.0 = fully charged
    
    Returns:
        float: Open circuit voltage per cell in volts
        
    Raises:
        ValueError: If soc is outside the range [0.0, 1.0]
        ValueError: If interpolation fails (shouldn't happen for valid input)
        
    Example:
        >>> ocv = get_ocv_from_soc(0.5)  # 50% charged
        >>> print(f"OCV at 50% SoC: {ocv:.3f}V")
        OCV at 50% SoC: 3.260V
        
    Data Source:
        LiFePO4 voltage chart from:
        https://powmr.com/blogs/news/lifepo4-voltage-chart-and-soc
        
    Note:
        - Data is for a single cell (nominal 3.2V LiFePO4)
        - For multi-cell packs, multiply by number of cells in series
        - Linear interpolation is used between data points
        - Voltage plateau is characteristic of LiFePO4 chemistry
    """
    # Empirical data points (SOC percentage, voltage per cell)
    # Data represents typical LiFePO4 discharge curve
    data = [
        (100.0, 3.65),  # Fully charged
        (99.5, 3.45),
        (99.0, 3.38),
        (90.0, 3.35),
        (80.0, 3.33),
        (70.0, 3.30),
        (60.0, 3.28),
        (50.0, 3.26),  # Characteristic voltage plateau region
        (40.0, 3.25),
        (30.0, 3.23),
        (20.0, 3.20),
        (15.0, 3.05),
        (9.5, 3.00),
        (5.0, 2.80),
        (0.5, 2.54),
        (0.0, 2.50)    # Fully discharged (cutoff voltage)
    ]

    # Convert fraction to percentage for lookup
    soc_percent = soc * 100

    # Validate input range
    if soc_percent > 100.0 or soc_percent < 0.0:
        raise ValueError("SOC out of range (must be between 0.0 and 1.0)")

    # Find the two data points that bracket the requested SoC
    # Data is sorted in descending order by SoC
    for i in range(len(data) - 1):
        soc_high, v_high = data[i]
        soc_low, v_low = data[i + 1]
        
        if soc_low <= soc_percent <= soc_high:
            # Perform linear interpolation
            # V = V_low + (V_high - V_low) * (SoC - SoC_low) / (SoC_high - SoC_low)
            fraction = (soc_percent - soc_low) / (soc_high - soc_low)
            ocv = v_low + fraction * (v_high - v_low)
            return ocv

    # Handle exact match at minimum SoC
    if soc_percent == data[-1][0]:
        return data[-1][1]

    # This should never be reached for valid input
    raise ValueError("Unable to interpolate SOC")