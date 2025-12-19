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


class CCCV:
    """
    Constant Current → Constant Voltage (CC-CV) Charging Policy
    
    A two-stage charging strategy commonly used in real Li-ion batteries:
    1. Constant Current (CC) stage: High current until reaching target voltage
    2. Constant Voltage (CV) stage: Fixed voltage with decreasing current
    
    This mimics the behavior of real phone and EV chargers, balancing speed
    and safety by preventing overcharging.
    
    Attributes:
        cc_current (float): Constant current in CC phase (A)
        cv_voltage (float): Constant voltage in CV phase (V)
        name (str): Policy identifier for logging
        
    Args:
        cc_current (float, optional): CC phase current in amperes. Default: 50
        cv_voltage (float, optional): CV phase voltage in volts. Default: 4.2
        
    Example:
        >>> cccv = CCCV(cc_current=50, cv_voltage=4.2)
        >>> v_source = cccv.get_voltage(t=10.0, y=state_vector)
    """
    
    def __init__(self, cc_current=20, cv_voltage=4.0):
        self.cc_current = cc_current
        self.cv_voltage = cv_voltage
        self.name = f"CCCV_{cc_current}A_{cv_voltage}V"
    
    def get_voltage(self, t, y):
        """
        Calculate required source voltage based on CC-CV strategy.
        
        Switches from constant current to constant voltage mode based on
        state of charge (SOC). This provides more robust transitions than
        using voltage, which can respond unpredictably to transient effects.
        
        Args:
            t (float): Current time in seconds (unused for CCCV)
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Source voltage in volts
            
        Physics:
            Stage 1 (CC, 0-80% SOC): V_source = I_cc * R + V_battery (constant current mode)
            Stage 2 (CV, 80-100% SOC): V_source = V_cv (constant voltage mode)
            
        Note:
            Transition at 80% SOC ensures meaningful CC phase with decreasing current
            in the CV phase, matching real battery charging behavior.
        """
        soc = y[4]  # State of charge
        battery_voltage = y[0]  # Current battery voltage
        resistance = y[2]  # Current internal resistance

        # If still below 50% SOC, stay in CC mode
        if soc < 0.50:
            # CC mode: supply voltage needed to maintain constant current
            return self.cc_current * resistance + battery_voltage
        else:
            # CV mode: maintain constant voltage
            return self.cv_voltage


class CCCVPulse:
    """
    Three-Stage Charging Policy: Constant Current → Constant Voltage → Pulse
    
    An advanced charging strategy that combines multiple techniques to optimize
    charging speed, heat generation, and battery degradation:
    
    1. CC Stage (0-80% SoC): High current (50A) for fast initial charging
    2. CV Stage (80-95% SoC): Constant 4.2V with decreasing current for safety
    3. Pulse Stage (95-100% SoC): Low-frequency pulse charging to gently top off
    
    This mimics premium phone chargers and EV fast-charging systems that adapt
    the charging profile based on state of charge.
    
    Attributes:
        cc_current (float): CC phase current in amperes
        cv_voltage (float): CV phase voltage in volts
        pulse_current (float): Pulse charging current in amperes
        pulse_freq (float): Pulse frequency in Hz (cycles per second)
        name (str): Policy identifier for logging
        
    Args:
        cc_current (float, optional): CC current (A). Default: 50
        cv_voltage (float, optional): CV voltage (V). Default: 4.2
        pulse_current (float, optional): Pulse current (A). Default: 20
        pulse_freq (float, optional): Pulse frequency (Hz). Default: 1
        
    Example:
        >>> cccp = CCCVPulse(cc_current=20, cv_voltage=4.0, pulse_current=5, pulse_freq=1)
        >>> v_source = cccp.get_voltage(t=100.0, y=state_vector)
    """
    
    def __init__(self, cc_current=20, cv_voltage=4.0, pulse_current=20, pulse_freq=1):
        self.cc_current = cc_current
        self.cv_voltage = cv_voltage
        self.pulse_current = pulse_current
        self.pulse_freq = pulse_freq
        self.name = f"CCCVPulse_{cc_current}A_{cv_voltage}V"
    
    def get_voltage(self, t, y):
        """
        Calculate source voltage for three-stage adaptive charging.
        
        Implements intelligent switching between CC, CV, and pulse modes
        based on state of charge and operating conditions.
        
        Args:
            t (float): Current time in seconds (used for pulse timing)
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Source voltage in volts
            
        Physics:
            Stage 1 (0-80% SoC): CC mode with 50A
                V_source = 50 * R + V_battery
                
            Stage 2 (80-95% SoC): CV mode at 4.2V
                V_source = 4.2V (constant)
                
            Stage 3 (95-100% SoC): Pulse mode with 0.5 Hz frequency
                I(t) = pulse_current * |sin(2π * pulse_freq * t)|
                V_source = I(t) * R + V_battery
        """
        battery_voltage = y[0]  # Current battery voltage
        resistance = y[2]  # Current internal resistance
        soc = y[4]  # State of charge (0-1)

        # Stage 1: Constant Current until 50% SoC
        if soc < 0.50:
            # CC mode: maintain constant current
            return self.cc_current * resistance + battery_voltage
        
        # Stage 2: Constant Voltage from 80-95% SoC
        elif soc < 0.80:
            # CV mode: maintain constant voltage
            return self.cv_voltage
        
        # Stage 3: Pulse charging for final 5% (95-100% SoC)
        else:
            # Pulse mode: low frequency pulses to gently top off
            instantaneous_current = self.pulse_current * abs(math.sin(2 * math.pi * self.pulse_freq * t))
            return instantaneous_current * resistance + battery_voltage


class CVPulse:
    """
    Constant Voltage with Pulse Charging Policy
    
    A pulse-based charging strategy that starts at a fixed high voltage and applies
    low-frequency current pulses. This strategy:
    1. Quickly reaches high voltage to initiate charging
    2. Uses pulsed current to allow electrochemical relaxation
    3. Reduces thermal stress through pulse intervals
    
    This mimics some premium chargers that use voltage-controlled pulse charging
    for better thermal management and cycle life.
    
    Attributes:
        cv_voltage (float): Constant voltage to maintain (V)
        pulse_current (float): Peak pulse current (A)
        pulse_freq (float): Pulse frequency in Hz
        name (str): Policy identifier for logging
        
    Args:
        cv_voltage (float, optional): CV voltage (V). Default: 4.2
        pulse_current (float, optional): Pulse amplitude (A). Default: 5
        pulse_freq (float, optional): Pulse frequency (Hz). Default: 1
        
    Example:
        >>> cvp = CVPulse(cv_voltage=4.2, pulse_current=5, pulse_freq=1)
        >>> v_source = cvp.get_voltage(t=10.0, y=state_vector)
    """
    
    def __init__(self, cv_voltage=4.2, pulse_current=20, pulse_freq=1):
        self.cv_voltage = cv_voltage
        self.pulse_current = pulse_current
        self.pulse_freq = pulse_freq
        self.name = f"CVPulse_{cv_voltage}V"
    
    def get_voltage(self, t, y):
        """
        Calculate source voltage using constant voltage with pulse modulation.
        
        Strategy: Maintain CV voltage while modulating current through pulse waves.
        This allows the battery to relax between pulses, reducing thermal stress
        and potentially improving cycle life.
        
        Args:
            t (float): Current time in seconds (used for pulse timing)
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Source voltage in volts
            
        Physics:
            V_source = V_cv (constant, maintained throughout)
            
            The current naturally varies as:
            I(t) = (V_cv - V_battery) / R
            
            With pulse modulation (optional external control):
            I_pulse(t) = I_base * |sin(2π * f * t)|
            
        Note:
            The CV voltage is held constant, but effective current varies because
            the battery voltage rises during charging (V_cv - V_battery decreases).
            This naturally creates a "self-pulslng" effect without explicit control.
        """
        # Simply maintain constant voltage - current decay is natural from Ohm's law
        return self.cv_voltage


class CVPulse:
    """
    Constant Voltage with Pulse Charging (CV-Pulse)
    
    A strategy that starts with constant voltage and uses pulse charging 
    throughout to manage current decay and thermal stress. This differs from 
    CCCVPulse by starting immediately at the CV voltage rather than beginning 
    with a constant current phase.
    
    Attributes:
        cv_voltage (float): CV voltage in volts
        pulse_current (float): Pulse charging current in amperes
        pulse_freq (float): Pulse frequency in Hz
        name (str): Policy identifier for logging
        
    Args:
        cv_voltage (float, optional): CV voltage (V). Default: 4.2
        pulse_current (float, optional): Pulse current (A). Default: 5
        pulse_freq (float, optional): Pulse frequency (Hz). Default: 1
        
    Example:
        >>> cvp = CVPulse(cv_voltage=4.2, pulse_current=5, pulse_freq=1)
        >>> v_source = cvp.get_voltage(t=50.0, y=state_vector)
    """
    
    def __init__(self, cv_voltage=4.2, pulse_current=20, pulse_freq=1):
        self.cv_voltage = cv_voltage
        self.pulse_current = pulse_current
        self.pulse_freq = pulse_freq
        self.name = f"CVPulse_{cv_voltage}V"
    
    def get_voltage(self, t, y):
        """
        Calculate source voltage for CV-Pulse strategy.
        
        Uses constant voltage with pulsed current throughout entire charge.
        This allows for better thermal management compared to pure CV, while
        maintaining a fixed voltage limit.
        
        Args:
            t (float): Current time in seconds (used for pulse timing)
            y (np.array): Current state vector [voltage, current, resistance, temperature, soc, sei, transient]
            
        Returns:
            float: Source voltage in volts
            
        Physics:
            Strategy: Hold cv_voltage, apply pulsed current overlay
            V_source = cv_voltage (constant base)
            I(t) = pulse_current * |sin(2π * pulse_freq * t)|
            
            Result: Current varies sinusoidally while voltage is constant,
            allowing rest periods for diffusion and heat dissipation
        """
        resistance = y[2]  # Current internal resistance
        
        # Pulse charging with fixed CV voltage
        instantaneous_current = self.pulse_current * abs(math.sin(2 * math.pi * self.pulse_freq * t))
        
        # Voltage adjusted for resistance drop during pulse
        return self.cv_voltage + instantaneous_current * resistance