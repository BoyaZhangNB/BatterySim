"""
The charging mechaism uses the applied voltage and current to update the state of charge (SOC)

Every battery has different voltage to SOC charge curves
"""

from utils import *

class Charging:
    """get open circuit voltage and update SOC accordingly"""

    def __init__(self, C_nominal=2.0):
        self.C_nominal = C_nominal  # nominal capacity in Ah

    def get_SOC(self, y, t, v_source):
        """dSOC/dt = I / C_nominal
        where C_nominal is the nominal capacity of the battery in Ah
        I is current in A
        SOC is unitless (0 to 1)
        """
        grad_soc = y[1] / (self.C_nominal * 3600)  # dSOC/dt

        return grad_soc
    
    def get_gradient(self, y, t, v_source):
        grad_soc = self.get_SOC(y, t, v_source)

        return pack_state(0, 0, 0, 0, grad_soc, 0, 0)