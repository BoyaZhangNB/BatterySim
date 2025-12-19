"""
Thermal Dynamics Mechanism

This module implements the thermal behavior of the battery, including:
    - Ohmic heating from current flow
    - Cooling via Newton's law of cooling

All mechanisms must implement:
    - get_gradient(y, t, v_source): Returns dy/dt for their state variables
    - Return format: pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)

Physics:
    Heat Generation: Q̇ = I²R (Joule heating from current and resistance)
    Temperature Rise: dT/dt = Q̇/(mc) where m is mass, c is specific heat
    Cooling: dT/dt = -k(T - T_ambient) (Newton's law of cooling)
"""
from utils import *

class Thermo:
    """
    Thermal dynamics mechanism for battery temperature modeling.
    
    Models battery temperature changes from internal heating and environmental cooling.
    The temperature affects other properties like resistance (see UpdateState) and
    SEI growth rate.
    
    Attributes:
        mass (float): Battery mass in kg
        c (float): Specific heat capacity in J/(kg·K)
        k (float): Cooling constant in 1/s (larger = faster cooling)
        ambient_temp (float): Ambient/environmental temperature in K
        
    Args:
        mass (float): Mass of the battery in kg
        c (float): Specific heat capacity in J/(kg·K)
        k (float): Cooling constant in 1/s
        ambient_temp (float, optional): Ambient temperature in K. Default: 298K (25°C)
        
    Example:
        >>> thermo = Thermo(mass=1.0, c=0.5, k=3, ambient_temp=298)
        >>> gradient = thermo.get_gradient(state_vector, time, v_source)
    """

    def __init__(self, mass, c, k, ambient_temp=298):
        self.mass = mass  # Mass of the battery in kg
        self.c = c  # Specific heat capacity in J/(kg·K)
        self.k = k  # Cooling constant in 1/s
        self.ambient_temp = ambient_temp  # Ambient temperature in K

    def ohmic_heating(self, y, t, v_source):
        """
        Calculate temperature rise from ohmic (Joule) heating.
        
        When current flows through the battery's internal resistance, electrical
        energy is dissipated as heat according to Joule's law: P = I²R
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds (unused)
            v_source (float): Applied voltage (unused)
            
        Returns:
            float: Rate of temperature change from heating in K/s
            
        Physics:
            dT/dt = Q̇/(mc) = I²R/(mc)
            where:
                I = current (A)
                R = internal resistance (Ω)
                m = mass (kg)
                c = specific heat capacity (J/(kg·K))
        """
        # y[1] is current, y[2] is resistance
        grad_T = (y[1]**2 * y[2]) / (self.mass * self.c)
        return grad_T

    def cooling_law(self, y, t, v_source):
        """
        Calculate temperature decrease from Newton's law of cooling.
        
        The battery exchanges heat with the environment. The rate of cooling
        is proportional to the temperature difference between battery and ambient.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds (unused)
            v_source (float): Applied voltage (unused)
            
        Returns:
            float: Rate of temperature change from cooling in K/s (negative value)
            
        Physics:
            dT/dt = -k(T - T_ambient)
            where:
                k = cooling constant (1/s)
                T = battery temperature (K)
                T_ambient = environmental temperature (K)
                
        Note:
            Positive k means cooling towards ambient. Larger k = faster heat transfer.
        """
        # y[3] is temperature
        grad_T = -self.k * (y[3] - self.ambient_temp)
        return grad_T

    def get_gradient(self, y, t, v_source):
        """
        Calculate total temperature gradient from all thermal effects.
        
        Combines ohmic heating and environmental cooling to determine the
        net rate of temperature change.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds
            v_source (float): Applied source voltage
            
        Returns:
            np.array: Gradient vector with only temperature component non-zero
                     Format: [0, 0, 0, dT/dt, 0, 0, 0]
                     
        Note:
            Only the temperature component (index 3) is non-zero. Other mechanisms
            handle the other state variables.
        """
        grad_T = 0
        
        # Add heating contribution
        grad_T += self.ohmic_heating(y, t, v_source)
        
        # Add cooling contribution
        grad_T += self.cooling_law(y, t, v_source)
        
        return pack_state(0, 0, 0, grad_T, 0, 0, 0)