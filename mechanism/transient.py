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
        """dVc/dt = -1/(RC) * Vc + 1/C * I
        
        where:
        - Vc is the transient voltage
        - I is the current
        """
        voltage, current, resistance, temperature, soc, sei, transient = unpack_state(y)

        grad_Vc = (-1.0 / (self.R * self.C)) * transient + (1.0 / self.C) * current
        return grad_Vc

    def get_gradient(self, y, t, v_source):
        grad_Vc = 0

        grad_Vc += self.rc_dynamics(y, t, v_source)
        
        return pack_state(0, 0, 0, 0, 0, 0, grad_Vc)
