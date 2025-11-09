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
        updated_soc = self.get_ocv_from_soc(y[4]*100.0)  # get OCV from SOC percentage

        return pack_state(y[0], updated_current, updated_resistance, y[3], y[4], y[5])
    
    def get_ocv_from_soc(self, soc):
        """
        Function to get the Open Circuit Voltage (OCV) for a given State of Charge (SOC) percentage.
        Uses linear interpolation between data points from the provided chart.
        Assumes the output voltage is the 24V pack voltage.
        SOC should be between 5.0 and 100.0 percent.
        """
        # Data points from the chart (SOC %, 24V pack voltage)
        # Corrected the first volt per cell to 3.65 based on consistency with pack voltage (3.65 * 8 = 29.2)
        data = [
            (100.0, 3.65),
            (99.5, 3.45),
            (99.0, 3.38),
            (90.0, 3.35),
            (80.0, 3.33),
            (70.0, 3.30),
            (60.0, 3.28),
            (50.0, 3.26),
            (40.0, 3.25),
            (30.0, 3.23),
            (20.0, 3.20),
            (15.0, 3.05),
            (9.5, 3.00),
            (5.0, 2.80),
            (0.5, 2.54),
            (0.0, 2.50)
        ]

        if soc > 100.0 or soc < 5.0:
            raise ValueError("SOC out of range (must be between 5.0 and 100.0)")

        # Since data is sorted descending by SOC, loop to find interval
        for i in range(len(data) - 1):
            soc_high, v_high = data[i]
            soc_low, v_low = data[i + 1]
            if soc_low <= soc <= soc_high:
                # Linear interpolation
                fraction = (soc - soc_low) / (soc_high - soc_low)
                ocv = v_low + fraction * (v_high - v_low)
                return ocv

        # If exact match at the last point
        if soc == data[-1][0]:
            return data[-1][1]

        raise ValueError("Unable to interpolate SOC")
            
if __name__ == "__main__":
    updater = UpdateState()
    soc_test = 75.0
    ocv = updater.get_ocv_from_soc(soc_test)
    print(f"OCV for SOC {soc_test}% is {ocv} V per cell")