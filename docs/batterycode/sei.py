"""
Solid Electrolyte Interphase (SEI) Mechanism

This module implements the SEI layer growth dynamics in lithium-ion batteries.

The SEI layer forms on the anode surface during charging, consuming lithium ions
and increasing internal resistance over time. Its growth rate depends on:
    - Temperature (Arrhenius law)
    - State of Charge (SoC) / electrode potential
    - Applied current magnitude

All mechanisms must implement:
    - get_gradient(y, t, v_source): Returns dy/dt for their state variables
    - Return format: pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)

Physics:
    SEI growth follows: dδ/dt = k(T) * f(SoC, I)
    where:
        k(T) = k₀ * exp(-Ea/(RT)) [Arrhenius temperature dependence]
        f(SoC, I) = stress function combining potential and current effects

References:
    [1] von Kolzenberg et al., "Solid–Electrolyte Interphase During Battery Cycling:
        Theory of Growth Regimes", ChemSusChem, 2020.
    [2] Attia et al., "Electrochemical Kinetics of SEI Growth on Carbon Black", 2019.
    [3] von Kolzenberg et al., "A Four-Parameter Model for the Solid-Electrolyte Interphase
        to Predict Battery Aging During Operation", 2021.
    [4] Liu et al., "A Thermal–Electrochemical Model that gives Spatial-Dependent Growth of
        Solid Electrolyte Interphase in a Li-ion Battery", J. Power Sources, 2014.
"""
from utils import *

import numpy as np
from utils import pack_state

# Physical constants
R = 8.314  # Universal gas constant [J/(mol·K)]
F = 96485.0  # Faraday's constant [C/mol]

class SEI:
    """
    SEI (Solid Electrolyte Interphase) layer growth mechanism.
    
    Models the irreversible formation and growth of the SEI layer on the anode
    surface. The SEI is a passivation layer that forms during the first charge
    cycles and continues to grow slowly, consuming active lithium and increasing
    resistance, leading to capacity fade over battery lifetime.
    
    The growth rate combines:
        1. Temperature dependence (Arrhenius)
        2. Electrochemical stress from SoC/potential
        3. Current-induced acceleration
    
    Attributes:
        k0 (float): Base rate constant for SEI growth [m/s or arbitrary units]
        Ea (float): Activation energy for SEI growth [J/mol]
        A (float): Scaling factor for stress function (dimensionless)
        gamma_soc (float): Sensitivity of SEI growth to SoC/potential
        beta_I (float): Scaling factor for current influence
        nu (float): Power-law exponent for current influence
        U_ref (float): Reference anode potential [V]
        
    Args:
        k0 (float, optional): Pre-exponential rate constant. Default: 1e-7
        Ea (float, optional): Activation energy [J/mol]. Default: 3.0e4
        A (float, optional): Stress function scaling factor. Default: 1.0
        gamma_soc (float, optional): SoC sensitivity parameter. Default: 0.5
        beta_I (float, optional): Current scaling factor. Default: 0.1
        nu (float, optional): Current power-law exponent. Default: 1.0
        U_ref (float, optional): Reference potential [V]. Default: 0.1
        
    Example:
        >>> sei = SEI(k0=1e-7, Ea=3.0e4, gamma_soc=0.5)
        >>> gradient = sei.get_gradient(state_vector, time, v_source)
        
    Note:
        Parameter values should be tuned to experimental data for specific
        battery chemistries and operating conditions.
    """
    
    def __init__(self,
                 k0=1e-7,        # Base rate constant for SEI growth [m/s or arbitrary units]
                 Ea=3.0e4,       # Activation energy for SEI growth [J/mol]
                 A=1.0,          # Scaling factor for stress function (dimensionless)
                 gamma_soc=0.5,  # Sensitivity of SEI growth to SoC / potential
                 beta_I=0.1,     # Scaling factor for current influence
                 nu=1.0,         # Power-law exponent for current influence
                 U_ref=0.1):     # Reference anode potential [V] (for exponential dependence)
        self.k0 = k0
        self.Ea = Ea
        self.A = A
        self.gamma_soc = gamma_soc
        self.beta_I = beta_I
        self.nu = nu
        self.U_ref = U_ref

    def arrhenius_factor(self, T):
        """
        Calculate temperature-dependent rate factor using Arrhenius equation.
        
        The Arrhenius equation describes how reaction rates increase exponentially
        with temperature. Higher temperatures accelerate SEI formation.
        
        Args:
            T (float): Temperature in Kelvin
            
        Returns:
            float: Temperature-dependent multiplier (dimensionless)
            
        Physics:
            k(T) = exp(-Ea/(RT))
            where:
                Ea = activation energy [J/mol]
                R = gas constant [J/(mol·K)]
                T = temperature [K]
                
        Note:
            - At reference temperature (typically ~298K), factor ≈ exp(-Ea/RT)
            - Higher T → larger factor → faster SEI growth
            - Typical Ea for SEI: 20-60 kJ/mol
        """
        return np.exp(-self.Ea / (R * T))

    def stress_function(self, soc, current, U_ocv=None):
        """
        Calculate electrochemical stress factor for SEI growth.
        
        Combines the effects of electrode potential (via SoC) and current magnitude
        on SEI formation rate. High SoC and high current both accelerate SEI growth.
        
        Args:
            soc (float): State of charge (0 to 1)
            current (float): Current in amperes (A)
            U_ocv (float, optional): Open circuit voltage [V]. If None, estimated from SoC
            
        Returns:
            float: Stress factor (dimensionless multiplier)
            
        Physics:
            f(SoC, I) = A * exp(γ*(U_ref - U)) * (1 + β*|I|)^ν
            
            Components:
            1. Exponential potential term: exp(γ*(U_ref - U))
               - Higher voltage (higher SoC) → more SEI growth
               - Based on overpotential-driven formation (von Kolzenberg et al.)
               
            2. Current term: (1 + β*|I|)^ν
               - Larger current → more electrochemical activity → faster SEI growth
               - Linear when ν=1, nonlinear otherwise
               
        Note:
            - U can be provided directly as U_ocv or estimated as U_ref * SoC
            - gamma_soc controls sensitivity to voltage/SoC
            - beta_I and nu control sensitivity to current
        """
        # Estimate anode potential from SoC or use provided value
        if U_ocv is None:
            U = self.U_ref * soc  # Simple linear approximation
        else:
            U = U_ocv  # Use provided open-circuit voltage
        
        # Exponential dependence on potential difference
        exponent = self.gamma_soc * (self.U_ref - U)
        
        # Power-law dependence on current magnitude
        current_term = (1.0 + self.beta_I * abs(current)) ** self.nu
        
        # Combine terms with scaling factor
        return self.A * np.exp(exponent) * current_term

    def get_gradient(self, y, t, v_source):
        """
        Calculate the rate of SEI layer growth.
        
        Combines temperature dependence (Arrhenius) with electrochemical stress
        (SoC and current effects) to determine SEI growth rate.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds (unused)
            v_source (float): Applied source voltage (unused)
            
        Returns:
            np.array: Gradient vector with only SEI component non-zero
                     Format: [0, 0, 0, 0, 0, dδ/dt, 0]
                     
        Physics:
            dδ/dt = k₀ * exp(-Ea/(RT)) * f(SoC, I)
            where:
                δ = SEI layer thickness
                k₀ = base rate constant
                T = temperature
                f(SoC, I) = stress function
                
        Note:
            - SEI growth is irreversible and accumulates over battery lifetime
            - Growth rate slows over time as SEI layer thickens (not modeled here)
            - Only the SEI component (index 5) is non-zero
        """
        # Unpack state variables
        voltage, current, resistance, temperature, soc, sei, transient = unpack_state(y)

        # Calculate temperature-dependent rate constant
        k_T = self.k0 * self.arrhenius_factor(temperature)
        
        # Calculate electrochemical stress factor
        f_QI = self.stress_function(soc, current, U_ocv=voltage)
        
        # Combine factors for total SEI growth rate
        d_sei = k_T * f_QI

        # Return gradient vector (only SEI changes)
        d_voltage = 0
        d_current = 0
        d_resistance = 0
        d_temperature = 0
        d_soc = 0
        d_transient = 0

        return pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)
