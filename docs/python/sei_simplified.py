'''
Every mechanism should have a get_gradient function that returns the gradient of its state variables according to ODEs
pack_state(voltage, current, resistance, temperature, soc, sei)

MechanismClass.get_gradient(y, t, v_source):

should return dy/dt = pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei)
'''
from utils import *

import numpy as np
from utils import pack_state

R = 8.314  # universal gas constant [J/mol·K]

class SEI:
    """
    Models SEI layer growth dynamics
    """
    def __init__(self, k0=1e-12, Ea=3.0e4):
        """
        Parameters:
        k0 : float
            Pre-exponential rate constant for SEI growth (m/s or arbitrary units)
        Ea : float
            Activation energy for SEI formation [J/mol]
        """
        self.k0 = k0
        self.Ea = Ea

    def arrhenius_factor(self, T):
        """
        Computes temp sensitivity part of Arrhenius equation
        
        Equation: exp(-Ea / (R * T))
        where:
            Ea = activation energy [J/mol]
            R = 8.314 [J/mol·K] (universal gas constant)
            T = temperature [K]
        """
        return np.exp(-self.Ea / (R * T))

    def stress_function(self, soc, I):
        """
        How SEI growth increases at high charge levels and currents
        -> high SoC means strong electric field across anode, leading to more electrolyte breakdown
        -> high current means faster electro-chem rxns, and more side reactions that form SEI
        chat derived from more advanced electro-chem model (Doyle-Fuller-Newman) and simplified it into an ODE-level model
        
        Equation: (1 + 2 * soc^2) * (1 + 0.1 * |I|)
        where:
            soc = state of charge [0, 1]
            I = current [A]
        """
        soc_factor = np.clip(soc, 0, 1)
        current_factor = np.abs(I)
        return (1 + 2 * soc_factor**2) * (1 + 0.1 * current_factor)

    def get_gradient(self, y, t, v_source):
        """
        Compute d(SEI)/dt
        
        Equation: d(SEI)/dt = k_T * f_QI
        where:
            k_T = k0 * exp(-Ea / (R * T))  (temperature-dependent rate constant)
            f_QI = (1 + 2 * soc^2) * (1 + 0.1 * |I|)  (stress function)
        """
        voltage, current, resistance, temperature, soc, sei = unpack_state(y)

        k_T = self.k0 * self.arrhenius_factor(temperature)
        f_QI = self.stress_function(soc, current)
        d_sei = k_T * f_QI

        d_voltage = 0
        d_current = 0
        d_resistance = 0
        d_temperature = 0
        d_soc = 0

        return pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei)