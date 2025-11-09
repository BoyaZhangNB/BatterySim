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
import numpy as np

from utils import *

mechanisms = []  # list of mechanism instances from mechanism/*.py
policies = []  # instance of charging policy from charging_policy.py
dt = 0.01  # time step
cycles = 5  # number of charging cycles to simulate

# initial conditions
initial_conditions = {
    'voltage': 3.0,      # initial voltage (V)
    'current': 0.0,      # initial current (A)
    'resistance': 0.05,  # initial internal resistance (Ohm)
    'temperature': 298,  # initial temperature (K)
    'soc': 0.0,          # initial state of charge (0 to 1)
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
                   sei=sei) # pack states into a single vector
    
    log = []
    while not y[4] < 1.0: # while soc < 100%
        v_source = policy.get_voltage(t, y)
        
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
        print(f"Starting cycle {cycle+1}")
        cycle_log = simulate_charging(sei, policy)
        log.append(cycle_log)

    return log

def main():
    ### TODO load and initialize mechanisms and policy here ###


    for policy in policies:
        policy_log = simulate_charging_cycle(cycles, policy)
        # save log to file
        np.savetxt(f"log/log_{policy.name}.csv", np.array(policy_log), delimiter=",")
        print(f"Simulation with policy {policy.name} completed. Log saved to log_{policy.name}.csv")
    
if __name__ == "__main__":
    main()