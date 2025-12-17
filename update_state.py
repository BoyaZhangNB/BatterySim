from utils import *

class UpdateState:
    def __init__(self):
        self.ref_Temp = 298
        self.ea = 0.7  # activation energy in eV; change with SoC
        self.k = 8.314  # gas constant in eV/k
        pass

    def update_y(self, initial_conditions, y, v_source):
        voltage, current, resistance, temp, soc, sei, transient = unpack_state(y)

        updated_current = (v_source - voltage - transient) / resistance  # update current based on overpotential, resistance
        updated_resistance = initial_conditions['resistance'] * np.exp((self.ea / self.k) * 
                                (1/temp - 1/self.ref_Temp))
        updated_voltage = get_ocv_from_soc(soc)  # get OCV from SOC percentage

        return pack_state(updated_voltage, updated_current, updated_resistance, temp, soc, sei, transient)
            
if __name__ == "__main__":
    updater = UpdateState()
    soc_test = 75.0
    ocv = updater.get_ocv_from_soc(soc_test)
    print(f"OCV for SOC {soc_test}% is {ocv} V per cell")