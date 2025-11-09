from utils import *
class UpdateState:
    def __init__(self):
        self.ref_Temp = 298
        self.ea = 5000  # activation energy
        self.k = 8.314  # gas constant
        
        pass

        def update_y(self, initial_conditions, y, v_source):
            updated_current = (v_source - y[0]) / y[2]  # update current based on v_source, voltage, resistance
            updated_resistance = initial_conditions['resistance'] * np.exp((self.ea / self.k) * 
                                    (1/y[3] - 1/self.ref_Temp))
            return pack_state(y[0], updated_current, updated_resistance, y[3], y[4], y[5])
        