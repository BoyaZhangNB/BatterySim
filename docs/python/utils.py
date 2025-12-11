import numpy as np


def pack_state(voltage, current, resistance, temperature, soc, sei, transient):
    return np.array([voltage, current, resistance, temperature, soc, sei, transient], dtype=float)

def unpack_state(y):
    """unpacks a state into tuple
    Args:        y: state vector
    Returns:    voltage, current, resistance, temperature, soc, sei, trasient
    """
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



def get_ocv_from_soc(self, soc):
    """
    Function to get the Open Circuit Voltage (OCV) for a given State of Charge (SOC) percentage for a lithium ion battery.
    Uses linear interpolation between data points from the provided chart.
    SOC should be between 0.0 and 100.0 percent.

    https://powmr.com/blogs/news/lifepo4-voltage-chart-and-soc#gf
    """
    # Data points from the chart (SOC %, 24V pack voltage)
    # Corrected the first volt per cell to 3.65 based on consistency with pack voltage (3.65 * 8 = 29.2)
    data = [
        (100.0, 3.65),
        (99.5, 3.45),
        (99.0, 3.38),
        (90.0, 3.35),
        (80.0, 3.33),
        (70.0, 3.30),
        (60.0, 3.28),
        (50.0, 3.26),
        (40.0, 3.25),
        (30.0, 3.23),
        (20.0, 3.20),
        (15.0, 3.05),
        (9.5, 3.00),
        (5.0, 2.80),
        (0.5, 2.54),
        (0.0, 2.50)
    ]

    soc = soc * 100

    if soc > 100.0 or soc < 0.0:
        raise ValueError("SOC out of range (must be between 5.0 and 100.0)")

    # Since data is sorted descending by SOC, loop to find interval
    for i in range(len(data) - 1):
        soc_high, v_high = data[i]
        soc_low, v_low = data[i + 1]
        if soc_low <= soc <= soc_high:
            # Linear interpolation
            fraction = (soc - soc_low) / (soc_high - soc_low)
            ocv = v_low + fraction * (v_high - v_low)
            return ocv

    # If exact match at the last point
    if soc == data[-1][0]:
        return data[-1][1]

    raise ValueError("Unable to interpolate SOC")