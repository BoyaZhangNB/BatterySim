'''
Every mechanism should have a get_gradient function that returns the gradient of its state variables according to ODEs
pack_state(voltage, current, resistance, temperature, soc, sei)

MechanismClass.get_gradient(y, t, v_source):

should return dy/dt = pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei)
'''
from utils import *

class Thermo:
    """Returns the gradient of temperature"""

    def __init__(self):
        self.mass = 1
        self.c = 0.5
        self.k = 0.1  # cooling constant
        self.ambient_temp = 298

    def ohmic_heating(self, y, t, v_source):
        """dT/dt = dQ/dt / mc
        = I^2 * resistance / mc
        """
        grad_T = (y[1]**2 * y[2]) / (self.mass * self.c)

        return grad_T
    
    def overpotential(self, y, t, v_source):
        """dT/dt = I * (V_source - V) / mc"""

        grad_T = y[1] * (v_source - y[0]) / (self.mass * self.c)
        return grad_T
    
    def last_term(self, y, t, v_source):
        pass

    def cooling_law(self, y, t, v_source):
        """dT/dt = -k * (T - T_ambient)"""
        grad_T = -self.k * (y[3] - self.ambient_temp)  # cool towards ambient 25C
        return grad_T

    def get_gradient(self, y, t, v_source):
        grad_T = 0

        grad_T += self.ohmic_heating(self, y, t, v_source)
        grad_T += self.overpotential(self, y, t, v_source)
        grad_T += self.cooling_law(self, y, t, v_source)
        
        return pack_state(0, 0, 0, grad_T, 0, 0)