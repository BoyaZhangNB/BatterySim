'''
Every mechanism should have a get_gradient function that returns the gradient of its state variables according to ODEs
pack_state(voltage, current, resistance, temperature, soc, sei)

MechanismClass.get_gradient(y, t, v_source):

should return dy/dt = pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei)
'''
from utils import *

class Transient:
    """Returns the gradient of overpotential (voltage)
    Implements the RC circuit dynamics: V̇c,i(t) = -1/(Ri*Ci) * Vc,i(t) + 1/Ci * I(t)
    
    Args:
        R: Resistance in Ohms
        C: Capacitance in Farads
    """

    def __init__(self, R, C):
        self.R = R  # resistance
        self.C = C  # capacitance

    def rc_dynamics(self, y, t, v_source):
        """dV/dt = -1/(R*C) * V + 1/C * I
        
        where:
        - V is the overpotential (y[6])
        - I is the current (y[1])
        """
        grad_V = (-1.0 / (self.R * self.C)) * y[6] + (1.0 / self.C) * y[1]
        return grad_V

    def get_gradient(self, y, t, v_source):
        grad_V = 0

        grad_V += self.rc_dynamics(y, t, v_source)
        
        return pack_state(0, 0, 0, 0, 0, 0, grad_V)
