"""
Charging Policy Module

This module defines various battery charging policies that control how voltage
is supplied to the battery during charging.

All charging policies must implement:
    - get_voltage(t, y): Returns the source voltage at time t for state y
    - name: A string attribute for logging and identification

Available Policies:
    - CV (Constant Voltage): Maintains a fixed voltage throughout charging
    - CC (Constant Current): Adjusts voltage to maintain constant current
    - PulseCharging: Alternates between high current pulses and rest periods
    - SinusoidalCharging: Applies sinusoidally varying current

Note:
    In real systems, constant current is achieved by adaptive voltage control
    based on monitored current. This is simulated here by calculating the
    required voltage from Ohm's law: V = I*R + V_battery
"""
import math
from utils import *

class CV:
    """
    Constant Voltage (CV) Charging Policy
    
    Supplies a fixed voltage throughout the charging process. This is commonly
    used in the final stage of Li-ion battery charging to safely top off the
    battery without exceeding voltage limits.
    
    Attributes:
        voltage (float): The constant voltage to supply (in volts)
        name (str): Policy identifier for logging
        
    Args:
        voltage (float): The desired constant voltage supply (in volts)
        
    Example:
        >>> cv_policy = CV(voltage=4.2)  # 4.2V constant voltage
        >>> v_source = cv_policy.get_voltage(t=10.0, y=state_vector)
    """

    def __init__(self, voltage):
        self.voltage = voltage
        self.name = f"CV_{voltage}V"

    def get_voltage(self, t, y):
        """
        Get the source voltage for constant voltage charging.
        
        Args:
            t (float): Current time in seconds (unused for CV)
            y (np.array): Current state vector (unused for CV)
            
        Returns:
            float: Constant voltage in volts
        """
        return self.voltage

class CC:
    """
    Constant Current (CC) Charging Policy
    
    Maintains a constant charging current by dynamically adjusting the supply voltage.
    The voltage is calculated based on Ohm's law and the battery's current state.
    This simulates real-world CC charging where a control system monitors current
    and adjusts voltage accordingly.
    
    Attributes:
        current (float): Target charging current in amperes
        name (str): Policy identifier for logging
        
    Args:
        current (float): The desired constant current (in amperes)
        
    Example:
        >>> cc_policy = CC(current=25.0)  # 25A constant current
        >>> v_source = cc_policy.get_voltage(t=10.0, y=state_vector)
        
    Note:
        The required source voltage is: V_source = I*R + V_battery
        where I is desired current, R is internal resistance, and V_battery
        is the open circuit voltage.
    """

    def __init__(self, current):
        self.current = current
        self.name = f"CC_{current}A"

    def get_voltage(self, t, y):
        """
        Calculate required source voltage to maintain constant current.
        
        Args:
            t (float): Current time in seconds (unused for CC)
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Required source voltage in volts
            
        Note:
            Uses y[4] (soc) to get battery voltage and y[2] (resistance) for voltage drop calculation
        """
        battery_voltage = get_ocv_from_soc(y[4])  # Get open circuit voltage from state of charge
        resistance = y[2]  # Internal resistance
        desired_voltage = self.current * resistance  # Voltage drop across resistance
        return desired_voltage + battery_voltage
    

class PulseCharging:
    """
    Pulse Charging Policy
    
    Applies high-current pulses followed by rest periods. This advanced charging
    method can reduce heat generation and potentially extend battery life by
    allowing the battery chemistry to equilibrate during rest periods.
    
    Attributes:
        current (float): Peak current during pulse (in amperes)
        pulse_time (float): Duration of each current pulse (in seconds)
        rest_time (float): Duration of rest between pulses (in seconds)
        cycle_time (float): Total time for one pulse + rest cycle (in seconds)
        name (str): Policy identifier for logging
        
    Args:
        current (float): The desired peak current during pulses (in amperes)
        pulse_time (float): Time duration of each current pulse (in seconds)
        rest_time (float): Time duration of rest between pulses (in seconds)
        
    Example:
        >>> pulse_policy = PulseCharging(current=50, pulse_time=2.0, rest_time=0.25)
        >>> # Charges with 50A for 2s, then rests for 0.25s, repeating
        
    Note:
        During rest periods, the voltage is set to match the battery's open
        circuit voltage (zero current flow).
    """

    def __init__(self, current, pulse_time, rest_time):
        self.current = current
        self.pulse_time = pulse_time
        self.rest_time = rest_time
        self.cycle_time = pulse_time + rest_time  # Total cycle duration
        self.name = f"Pulse_{current}A_{pulse_time}s_on_{rest_time}s_off"

    def get_voltage(self, t, y):
        """
        Calculate source voltage for pulse charging pattern.
        
        Args:
            t (float): Current time in seconds
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Source voltage in volts (high during pulse, battery voltage during rest)
            
        Note:
            Uses modulo operation to determine position within pulse cycle:
            - If t % cycle_time < pulse_time: Apply high current
            - Otherwise: Rest period with zero current
        """
        battery_voltage = get_ocv_from_soc(y[4])
        resistance = y[2]
        
        # Determine if we're in pulse or rest phase
        if (t % self.cycle_time) < self.pulse_time:
            # Pulse phase: apply high current
            return self.current * resistance + battery_voltage
        else:
            # Rest phase: no current flow
            return battery_voltage
        
class SinusoidalCharging:
    """
    Sinusoidal Charging Policy
    
    Applies a sinusoidally varying current, which can help reduce polarization
    effects and potentially improve charging efficiency. The current varies
    smoothly according to a rectified sine wave (absolute value).
    
    Attributes:
        current (float): Peak current amplitude (in amperes)
        frequency (float): Frequency of sinusoidal variation (in Hz)
        name (str): Policy identifier for logging
        
    Args:
        current (float): The peak current amplitude (in amperes)
        frequency (float): Frequency of the sinusoidal wave (in Hz)
        
    Example:
        >>> sine_policy = SinusoidalCharging(current=60, frequency=4)
        >>> # Charges with current varying as 60*|sin(2π*4*t)| amperes
        
    Note:
        Uses absolute value of sine to ensure current is always positive (charging).
        The current formula is: I(t) = I_peak * |sin(2π * f * t)|
    """

    def __init__(self, current, frequency):
        self.current = current
        self.frequency = frequency
        self.name = f"Sine_{current}A_{frequency}Hz"

    def get_voltage(self, t, y):
        """
        Calculate source voltage for sinusoidal charging pattern.
        
        Args:
            t (float): Current time in seconds
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Source voltage in volts, varying sinusoidally
            
        Note:
            Voltage varies according to instantaneous current demand:
            V_source = I(t)*R + V_battery
            where I(t) = I_peak * |sin(2π * f * t)|
        """
        battery_voltage = get_ocv_from_soc(y[4])
        resistance = y[2]
        
        # Calculate instantaneous current from rectified sine wave
        instantaneous_current = self.current * abs(math.sin(2 * math.pi * self.frequency * t))
        
        return instantaneous_current * resistance + battery_voltage