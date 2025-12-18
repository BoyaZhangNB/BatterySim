"""
Simplified SEI Mechanism

This module implements a simplified version of the SEI layer growth dynamics
in lithium-ion batteries, using empirical relationships instead of detailed
electrochemical models.

The simplified model captures the essential temperature and electrochemical
dependencies using straightforward mathematical functions that are easier to
parameterize and compute.

All mechanisms must implement:
    - get_gradient(y, t, v_source): Returns dy/dt for their state variables
    - Return format: pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)

Physics:
    SEI growth: dδ/dt = k₀ * exp(-Ea/(RT)) * f(SoC, I)
    where f(SoC, I) is a simplified empirical stress function

Differences from full SEI model:
    - Simpler stress function (polynomial vs. exponential)
    - Fewer parameters to tune
    - Faster computation
    - Still captures key temperature and current dependencies
"""
from utils import *

import numpy as np
from utils import pack_state

R = 8.314  # Universal gas constant [J/(mol·K)]

class SEI:
    """
    Simplified SEI (Solid Electrolyte Interphase) layer growth mechanism.
    
    This is a simplified version of the SEI model that uses empirical relationships
    to capture the essential physics without the complexity of detailed electrochemical
    models. Suitable for system-level simulations where computational efficiency
    is important.
    
    The growth rate depends on:
        1. Temperature (Arrhenius relationship)
        2. State of charge (polynomial approximation)
        3. Current magnitude (linear approximation)
    
    Attributes:
        k0 (float): Base rate constant for SEI growth [m/s or arbitrary units]
        Ea (float): Activation energy for SEI growth [J/mol]
        
    Args:
        k0 (float, optional): Pre-exponential rate constant. Default: 1e-12
        Ea (float, optional): Activation energy [J/mol]. Default: 3.0e4 (30 kJ/mol)
        
    Example:
        >>> sei = SEI(k0=1e-12, Ea=3.0e4)
        >>> gradient = sei.get_gradient(state_vector, time, v_source)
        
    Note:
        The simplified stress function uses polynomial terms rather than
        exponential relationships, making it easier to tune to experimental data.
    """
    
    def __init__(self, k0=1e-12, Ea=3.0e4):
        self.k0 = k0  # Pre-exponential rate constant
        self.Ea = Ea  # Activation energy [J/mol]

    def arrhenius_factor(self, T):
        """
        Calculate temperature-dependent rate factor using Arrhenius equation.
        
        The Arrhenius equation describes how reaction rates increase exponentially
        with temperature. This is the same temperature dependence as in the full
        SEI model.
        
        Args:
            T (float): Temperature in Kelvin
            
        Returns:
            float: Temperature-dependent multiplier (dimensionless)
            
        Physics:
            k(T) = exp(-Ea/(RT))
            where:
                Ea = activation energy [J/mol]
                R = 8.314 [J/(mol·K)] (universal gas constant)
                T = temperature [K]
                
        Note:
            Higher temperature → larger factor → faster SEI growth
            Typical activation energies: 20-60 kJ/mol for SEI formation
        """
        return np.exp(-self.Ea / (R * T))

    def stress_function(self, soc, I):
        """
        Calculate simplified electrochemical stress factor for SEI growth.
        
        This simplified function uses polynomial relationships rather than
        exponential terms, making it easier to parameterize from experimental data
        while still capturing the key dependencies.
        
        Args:
            soc (float): State of charge (0 to 1)
            I (float): Current in amperes (A)
            
        Returns:
            float: Stress factor (dimensionless multiplier)
            
        Physics:
            f(SoC, I) = (1 + 2*SoC²) * (1 + 0.1*|I|)
            
            Components:
            1. SoC term: (1 + 2*SoC²)
               - High SoC → strong electric field at anode → more electrolyte breakdown
               - Quadratic dependence captures accelerating effect near full charge
               - At SoC=0: factor=1, At SoC=1: factor=3
               
            2. Current term: (1 + 0.1*|I|)
               - High current → faster electrochemical reactions → more side reactions
               - Linear dependence is a simplification of more complex kinetics
               - For 10A: factor=2, For 50A: factor=6
               
        Note:
            This empirical relationship is derived from simplifying detailed
            electrochemical models (Doyle-Fuller-Newman framework) into a
            computationally efficient ODE-level model.
        """
        # Clip SoC to valid range [0, 1] to prevent extrapolation
        soc_factor = np.clip(soc, 0, 1)
        current_factor = np.abs(I)  # Use absolute value (growth during charge/discharge)
        
        return (1 + 2 * soc_factor**2) * (1 + 0.1 * current_factor)

    def get_gradient(self, y, t, v_source):
        """
        Calculate the rate of SEI layer growth using simplified model.
        
        Combines temperature dependence (Arrhenius) with simplified electrochemical
        stress (SoC and current effects) to determine SEI growth rate.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds (unused)
            v_source (float): Applied source voltage (unused)
            
        Returns:
            np.array: Gradient vector with only SEI component non-zero
                     Format: [0, 0, 0, 0, 0, dδ/dt, 0]
                     
        Physics:
            dδ/dt = k₀ * exp(-Ea/(RT)) * (1 + 2*SoC²) * (1 + 0.1*|I|)
            where:
                δ = SEI layer thickness
                k₀ = base rate constant
                T = temperature
                SoC = state of charge
                I = current
                
        Note:
            - SEI growth is irreversible and cumulative
            - This simplified model requires less computation than the full model
            - Only the SEI component (index 5) is non-zero
            - Other state variables are handled by other mechanisms
        """
        # Unpack state variables
        voltage, current, resistance, temperature, soc, sei, transient = unpack_state(y)

        # Calculate temperature-dependent rate constant
        k_T = self.k0 * self.arrhenius_factor(temperature)
        
        # Calculate electrochemical stress factor (simplified)
        f_QI = self.stress_function(soc, current)
        
        # Combine factors for total SEI growth rate
        d_sei = k_T * f_QI

        # Initialize other derivatives to zero (handled by other mechanisms)
        d_voltage = 0
        d_current = 0
        d_resistance = 0
        d_temperature = 0
        d_soc = 0
        d_transient = 0

        return pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)
