"""
State Update Module

This module handles algebraic state variable updates that don't follow differential
equations but are instead computed directly from other state variables.

The UpdateState class computes:
    - Current from applied voltage and resistance (Ohm's law)
    - Temperature-dependent resistance (Arrhenius relationship)
    - Open circuit voltage from state of charge

Note:
    These updates happen at each time step before the differential equations are integrated.
"""
from utils import *

class UpdateState:
    """
    Updates algebraic state variables based on current conditions.
    
    Some battery properties are computed directly from other variables rather than
    integrated over time. This class handles those algebraic relationships, including
    temperature-dependent resistance and voltage-to-current conversion.
    
    Attributes:
        ref_Temp (float): Reference temperature for resistance calculation (K)
        ea (float): Activation energy for resistance-temperature relationship (eV)
        k (float): Boltzmann constant (eV/K)
        
    Example:
        >>> updater = UpdateState()
        >>> new_state = updater.update_y(initial_conditions, current_state, v_source)
    """
    
    def __init__(self):
        self.ref_Temp = 298  # Reference temperature in Kelvin (25°C)
        self.ea = 0.7  # Activation energy in eV (varies with SoC in real systems)
        self.k = 8.314  # Gas constant in eV/K
        pass

    def update_y(self, initial_conditions, y, v_source):
        """
        Update algebraic state variables based on current conditions.
        
        This method computes state variables that are determined algebraically rather
        than through differential equations:
        1. Current: Calculated from voltage difference and resistance (Ohm's law)
        2. Resistance: Temperature-dependent via Arrhenius equation
        3. Voltage: Open circuit voltage determined by state of charge
        
        Args:
            initial_conditions (dict): Dictionary of initial battery conditions
                                       (used for reference resistance value)
            y (np.array): Current state vector [voltage, current, resistance, 
                          temperature, soc, sei, transient]
            v_source (float): Applied source voltage (V)
            
        Returns:
            np.array: Updated state vector with new algebraic values
            
        Physics:
            - Current: I = (V_source - V_battery - V_transient) / R
            - Resistance: R(T) = R_0 * exp(E_a/k * (1/T - 1/T_ref))
            - Voltage: V = f(SoC) from lookup table
            
        Note:
            Transient voltage (from RC circuit) is subtracted in current calculation
            to account for polarization effects.
        """
        # Unpack current state
        voltage, current, resistance, temp, soc, sei, transient = unpack_state(y)

        # Update current using Ohm's law with transient voltage effect
        updated_current = (v_source - voltage - transient) / resistance
        
        # Update resistance using Arrhenius equation for temperature dependence
        # R(T) = R_0 * exp(E_a/k * (1/T - 1/T_ref))
        updated_resistance = initial_conditions['resistance'] * np.exp((self.ea / self.k) * 
                                (1/temp - 1/self.ref_Temp))
        
        # Update open circuit voltage based on state of charge
        updated_voltage = get_ocv_from_soc(soc)

        return pack_state(updated_voltage, updated_current, updated_resistance, temp, soc, sei, transient)
            
if __name__ == "__main__":
    """
    Test script for UpdateState functionality.
    
    Demonstrates how to get open circuit voltage for a given state of charge.
    """
    updater = UpdateState()
    soc_test = 75.0  # Test at 75% state of charge
    ocv = get_ocv_from_soc(soc_test / 100.0)  # Convert percentage to fraction
    print(f"OCV for SOC {soc_test}% is {ocv:.3f} V per cell")