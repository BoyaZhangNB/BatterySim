'''
Parameters:
    - t (seconds): time
    - voltage (V): open circuit voltage of the battery (varies with soc)
    - current (A): current into the battery
    - resistance (Ohm): internal resistance of the battery
    - temperature (K): temperature of the battery (assume uniform)
    - soc: state of charge
    - SEI: solid-electrolyte interphase that permanently reduces battery capacity
    - v_source: supplied voltage from source
'''
import os
import numpy as np

from mechanism.thermo import Thermo
from mechanism.charging import Charging
from mechanism.sei import SEI
from mechanism.transient import Transient

from charging_policy import *

from update_state import UpdateState
from utils import *


_thermo = Thermo(mass=1.0, c=0.5, k=3, ambient_temp=298)  # mass=1kg, c=0.5 J/(kg*K), k=0.1 1/s
_charging = Charging(C_nominal=200) # nominal capacity 2Ah
_sei = SEI()
_transient = Transient(R=0.008, C=5000) # polarization resistence = 8 mOhm, capacitance = 5000 Farads

_cv = CV(voltage=3.7) # constant voltage charging policy at 7V
_cc = CC(current=25)
_pulse = PulseCharging(current=50, pulse_time=2, rest_time=0.25)
_sinusoidal = SinusoidalCharging(current=60, frequency=4)

updatestate = UpdateState()

mechanisms = [_thermo, _charging, _sei, _transient]  # list of mechanism instances from mechanism/*.py
policies = [_pulse]  # instance of charging policy from charging_policy.py
dt = 0.1  # time step
cycles = 1  # number of charging cycles to simulate

# initial conditions
initial_conditions = {
    'voltage': 3.0,      # initial voltage (V)
    'current': 0.0,      # initial current (A)
    'resistance': 0.03,  # initial internal resistance (Ohm)
    'temperature': 298,  # initial temperature (K)
    'soc': 0.0,          # initial state of charge (0 to 1)
    'transient voltage': 0.0
}
initial_sei = 0 # Note that initial conditions are reset every charging cycle
# but sei only resets once at the start of the simulation


def total_derivative(y, t, v_source):
    """Sum gradients from all mechanisms. Return dy/dt vector."""
    # initialize derivative vector
    dydt = np.zeros_like(y)
    for mech in mechanisms:
        # each mechanism returns derivatives for the whole state (or subset as agreed)
        # ensure mech_grad is an array with same shape as y
        mech_grad = mech.get_gradient(y, t, v_source)
        dydt += np.asarray(mech_grad)
    # you may also include direct contributions from policy, e.g. current from control law
    return dydt

def rk4_step(y, t, dt, v_source):
    """Perform a single Runge-Kutta 4th order step. Essentially better numerical integration."""
    k1 = total_derivative(y, t, v_source)
    k2 = total_derivative(y + 0.5*dt*k1, t + 0.5*dt, v_source)
    k3 = total_derivative(y + 0.5*dt*k2, t + 0.5*dt, v_source)
    k4 = total_derivative(y + dt*k3, t + dt, v_source)
    return y + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def simulate_charging(sei, policy):
    """Simulate a single charging cycle until soc reaches 100%."""
    # initial state
    t = 0.0
    y = pack_state(initial_conditions['voltage'], 
                   initial_conditions['current'], 
                   initial_conditions['resistance'], 
                   initial_conditions['temperature'], 
                   initial_conditions['soc'], 
                   sei,
                   initial_conditions['transient voltage']) # pack states into a single vector    
    log = []
    while y[4] < 1.0: # while soc < 100%
        v_source = policy.get_voltage(t, y)
        y = updatestate.update_y(initial_conditions, y, v_source)
        y = rk4_step(y, t, dt, v_source) # update state
        t += dt

        log.append((t, *y))  # log time and state

    return log

def simulate_charging_cycle(cycles, policy):
    """Simulate multiple charging cycles for a given policy."""
    log = []
    # reset sei
    sei = initial_sei

    for cycle in range(cycles):
        if cycle % 100 == 0:
            print(f"Starting cycle {cycle+1}")
        cycle_log = simulate_charging(sei, policy)
        log.append(cycle_log)

    return log

# [[y1, y2, y3],[y1, y2, y3],...]
# Each yi is a list of (t, voltage, current, resistance, temperature, soc, sei)

def main():
    for policy in policies:
        policy_log = simulate_charging_cycle(cycles, policy)
        # save log to file
        os.makedirs("log", exist_ok=True)
        headers = "time,voltage,current,resistance,temperature,soc,sei,transient voltage"
        np.savetxt(f"log/log_{policy.name}.csv", np.array(*policy_log), delimiter=",", header=headers, comments='')
        print(f"Simulation with policy {policy.name} completed. Log saved to log_{policy.name}.csv")
    
if __name__ == "__main__":
    main()