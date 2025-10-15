"""All policies should have a get_voltage(t, y) method and a name attribute."""
import math

class CV:
    '''
    Supplies a constant voltage
    Args:
        voltage: the desired voltage supply
    '''

    def __init__(self, voltage):
        self.voltage = voltage
        self.name = f"CV_{voltage}V"

    def get_voltage(self, t, y):
        return self.voltage

class CC:
    '''
    Supplies a constant current by modifying the supply voltage. Note in real life constant current is done through adaptively changing voltage according to the monitored current
    Args:
        current: the desired current supply
    '''

    def __init__(self, current):
        self.current = current
        self.name = f"CC_{current}A"

    def get_voltage(self, t, y):
        resistance = y[2]
        return self.current/resistance
    

class PulseCharging:
    '''
    Supplies a pulsed current by modifying the supply voltage. Note in real life constant current is done through adaptively changing voltage according to the monitored current
    Args:
        current: the desired current supply
        pulse_time: time duration of each pulse
        rest_time: time duration of rest between pulses
    '''

    def __init__(self, current, pulse_time, rest_time):
        self.current = current
        self.pulse_time = pulse_time
        self.rest_time = rest_time
        self.cycle_time = pulse_time + rest_time
        self.name = f"Pulse_{current}A_{pulse_time}s_on_{rest_time}s_off"

    def get_voltage(self, t, y):
        resistance = y[2]
        if (t % self.cycle_time) < self.pulse_time:
            return self.current/resistance
        else:
            return 0
        
class SinusoidalCharging:
    '''
    Supplies a sinusoidal current by modifying the supply voltage. Note in real life constant current is done through adaptively changing voltage according to the monitored current
    Args:
        current: the desired current supply
        frequency: frequency of the sinusoidal wave
    '''

    def __init__(self, current, frequency):
        self.current = current
        self.frequency = frequency
        self.name = f"Sine_{current}A_{frequency}Hz"

    def get_voltage(self, t, y):
        resistance = y[2]
        return (self.current * math.sin(2 * math.pi * self.frequency * t))/resistance