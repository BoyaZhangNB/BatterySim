"""
Charging Mechanism

This module implements the state of charge (SoC) dynamics during battery charging.

The SoC represents the fraction of the battery's capacity that is currently charged,
ranging from 0 (empty) to 1 (full). It increases as current flows into the battery.

All mechanisms must implement:
    - get_gradient(y, t, v_source): Returns dy/dt for their state variables
    - Return format: pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)

Physics:
    The rate of SoC change is determined by integrating current over time,
    normalized by the battery's nominal capacity:
    dSoC/dt = I / C_nominal
    where I is current (A) and C_nominal is capacity (Ah)
"""

from utils import *

class Charging:
    """
    Charging mechanism for battery state of charge modeling.
    
    Tracks how the battery's state of charge changes as current flows in (charging)
    or out (discharging). Every battery has a characteristic voltage-SoC curve that
    depends on the chemistry (e.g., LiFePO4, NMC, LTO).
    
    Attributes:
        C_nominal (float): Nominal battery capacity in ampere-hours (Ah)
        
    Args:
        C_nominal (float, optional): Nominal capacity in Ah. Default: 2.0 Ah
        
    Example:
        >>> charging = Charging(C_nominal=200)  # 200 Ah battery
        >>> gradient = charging.get_gradient(state_vector, time, v_source)
    """

    def __init__(self, C_nominal=2.0):
        self.C_nominal = C_nominal  # Nominal capacity in Ah

    def get_SOC(self, y, t, v_source):
        """
        Calculate the rate of change of state of charge.
        
        The SoC changes according to the current flowing and the battery's capacity.
        Positive current (charging) increases SoC, negative current (discharging) decreases it.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds (unused)
            v_source (float): Applied voltage (unused)
            
        Returns:
            float: Rate of SoC change in 1/s (dimensionless rate)
            
        Physics:
            dSoC/dt = I / C_nominal
            where:
                I = current in amperes (A)
                C_nominal = nominal capacity in ampere-hours (Ah)
                
        Note:
            - Current (y[1]) is in amperes
            - C_nominal is in ampere-hours, so we multiply by 3600 to convert to ampere-seconds
            - SoC is dimensionless (0 to 1), so dSoC/dt has units of 1/s
            - 1 Ah = 3600 coulombs (As)
        """
        # y[1] is current in amperes
        grad_soc = y[1] / (self.C_nominal * 3600)  # dSoC/dt in 1/s
        return grad_soc
    
    def get_gradient(self, y, t, v_source):
        """
        Calculate gradient vector for the charging mechanism.
        
        Returns the rate of change for all state variables, with only the SoC
        component being non-zero.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds
            v_source (float): Applied source voltage
            
        Returns:
            np.array: Gradient vector with only SoC component non-zero
                     Format: [0, 0, 0, 0, dSoC/dt, 0, 0]
                     
        Note:
            Only the SoC component (index 4) is non-zero. Other mechanisms
            handle the other state variables.
        """
        grad_soc = self.get_SOC(y, t, v_source)
        return pack_state(0, 0, 0, 0, grad_soc, 0, 0)