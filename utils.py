import numpy as np


def pack_state(voltage, current, resistance, temperature, soc, sei):
    return np.array([voltage, current, resistance, temperature, soc, sei], dtype=float)

def unpack_state(y):
    return tuple(y)

import matplotlib.pyplot as plt

def plot_simulation_data(log_data, variables_to_plot):
    """
    Plot logged simulation data over time.
    
    Args:
        log_data: List of tuples (t, voltage, current, resistance, temperature, soc, sei)
        variables_to_plot: List of indices specifying which variables to plot
                            0: voltage, 1: current, 2: resistance, 3: temperature, 4: soc, 5: sei
    """
    if not log_data:
        print("No data to plot")
        return
    
    # Extract time and convert log data to numpy array for easier indexing
    data = np.array(log_data)
    time = data[:, 0]
    
    variable_names = ['Voltage (V)', 'Current (A)', 'Resistance (Ω)', 'Temperature (K)', 'SOC', 'SEI']
    
    plt.figure(figsize=(10, 6))
    
    for var_idx in variables_to_plot:
        if 0 <= var_idx < len(variable_names):
            plt.plot(time, data[:, var_idx + 1], label=variable_names[var_idx])
    
    plt.xlabel('Time (s)')
    plt.ylabel('Value')
    plt.title('Battery Simulation Results')
    plt.legend()
    plt.grid(True)
    plt.show()