'''
Every mechanism should have a get_gradient function that returns the gradient of its state variables according to ODEs
pack_state(voltage, current, resistance, temperature, soc, sei)

MechanismClass.get_gradient(y, t, v_source):

should return dy/dt = pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei)

The SEI layer forms on the anode surface during charging, consuming lithium ions
    and increasing internal resistance over time. Its growth rate depends on:
      • Temperature (Arrhenius law)
      • State of Charge (SoC) / electrode potential
      • Applied current magnitude

    References:
      [1] von Kolzenberg et al., "Solid–Electrolyte Interphase During Battery Cycling:
          Theory of Growth Regimes", *ChemSusChem*, 2020.
      [2] Attia et al., "Electrochemical Kinetics of SEI Growth on Carbon Black", 2019.
      [3] von Kolzenberg et al., "A Four-Parameter Model for the Solid-Electrolyte Interphase
          to Predict Battery Aging During Operation", 2021.
      [4] Liu et al., "A Thermal–Electrochemical Model that gives Spatial-Dependent Growth of
          Solid Electrolyte Interphase in a Li-ion Battery", *J. Power Sources*, 2014.
'''
from utils import *

import numpy as np
from utils import pack_state

R = 8.314  # universal gas constant [J/mol·K]
F = 96485.0    # Faraday's constant [C/mol]

class SEI:
    """
    Models SEI layer growth dynamics
    """
    def __init__(self,
                 k0=1e-7,        # Base rate constant for SEI growth [m/s or arbitrary units]
                 Ea=3.0e4,        # Activation energy for SEI growth [J/mol]
                 A=1.0,           # Scaling factor for stress function (dimensionless)
                 gamma_soc=0.5,   # Sensitivity of SEI growth to SoC / potential
                 beta_I=0.1,      # Scaling factor for current influence
                 nu=1.0,          # Power-law exponent for current influence
                 U_ref=0.1):      # Reference anode potential [V] (for exponential dependence)
        self.k0 = k0
        self.Ea = Ea
        self.A = A
        self.gamma_soc = gamma_soc
        self.beta_I = beta_I
        self.nu = nu
        self.U_ref = U_ref
        
        """
        k0 : float
            Pre-exponential rate constant for SEI formation.
        Ea : float
            Activation energy [J/mol] governing temperature sensitivity (Arrhenius dependence).
        A : float
            Prefactor scaling the stress function output.
        gamma_soc : float
            Exponential sensitivity of SEI growth to SoC (linked to overpotential dependence).
        beta_I : float
            Weight of current magnitude in stress function.
        nu : float
            Exponent controlling nonlinearity of current effect (ν = 1 → linear).
        U_ref : float
            Reference anode potential [V]; defines "high stress" potential at full charge.
        """

    def arrhenius_factor(self, T):
        """computes temp sensitivity part of Arrhenius equation"""
        return np.exp(-self.Ea / (R * T))

    def stress_function(self, soc, current, U_ocv=None):
        """
        ->Exponential dependence on (U_ref - U(SoC)) follows lit. (von Kol...), representing the
        overpotential-driven increase in SEI formation rate.
        ->Current term (1 + β_I * |I|)^ν captures increased SEI growth under high charging currents
        due to larger electrochemical activity and overpotential
        """
    
        if U_ocv is None:
            U = self.U_ref * soc # Otherwise U ~ U_ref * SoC 
        else:
            U = U_ocv   #U_ocv is open-circuit voltage of cell or anode potential (if value is provided)

        exponent = self.gamma_soc * (self.U_ref - U)
        current_term = (1.0 + self.beta_I * abs(current)) ** self.nu

        return self.A * np.exp(exponent) * current_term  #dimensionless multiplier applied to SEI rate constant

    def get_gradient(self, y, t, v_source):
        """
        Compute d(SEI)/dt
        """
        voltage, current, resistance, temperature, soc, sei = unpack_state(y)

        k_T = self.k0 * self.arrhenius_factor(temperature)
        f_QI = self.stress_function(soc, current, U_ocv=voltage) # Compute SoC- and current-dependent stress term
        d_sei = k_T * f_QI

        d_voltage = 0
        d_current = 0
        d_resistance = 0
        d_temperature = 0
        d_soc = 0

        return pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei)
