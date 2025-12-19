"""
Transient Voltage Mechanism

This module implements the transient voltage response of the battery using an
RC (resistor-capacitor) circuit model.

The RC circuit captures polarization effects - temporary voltage changes that occur
when current flows, representing:
    - Charge transfer resistance at electrode-electrolyte interface
    - Diffusion limitations in the electrodes
    - Double-layer capacitance effects

All mechanisms must implement:
    - get_gradient(y, t, v_source): Returns dy/dt for their state variables
    - Return format: pack_state(d_voltage, d_current, d_resistance, d_temperature, d_soc, d_sei, d_transient)

Physics:
    RC Circuit Dynamics: dVc/dt = -1/(RC) * Vc + 1/C * I
    where:
        Vc = capacitor voltage (transient voltage)
        R = polarization resistance (Ω)
        C = double-layer capacitance (F)
        I = current (A)
"""
from utils import *

class Transient:
    """
    Transient voltage mechanism for battery polarization modeling.
    
    Models the time-dependent voltage response of the battery using an RC circuit.
    This captures the overpotential that develops during current flow and relaxes
    when current stops.
    
    The RC circuit creates a voltage drop that:
        - Builds up when current flows (charging/discharging)
        - Decays exponentially when current stops
        - Has a time constant τ = RC
    
    Attributes:
        R (float): Polarization resistance in ohms (Ω)
        C (float): Double-layer capacitance in farads (F)
        
    Args:
        R (float): Resistance in Ohms
        C (float): Capacitance in Farads
        
    Example:
        >>> transient = Transient(R=0.008, C=5000)  # 8 mΩ, 5000 F
        >>> # Time constant: τ = RC = 0.008 * 5000 = 40 seconds
        >>> gradient = transient.get_gradient(state_vector, time, v_source)
    """

    def __init__(self, R, C):
        self.R = R  # Polarization resistance in Ω
        self.C = C  # Double-layer capacitance in F

    def rc_dynamics(self, y, t, v_source):
        """
        Calculate the rate of change of transient voltage using RC circuit dynamics.
        
        The transient voltage follows first-order RC circuit behavior with two terms:
        1. Decay term: -Vc/(RC) represents voltage relaxation
        2. Charging term: I/C represents voltage buildup from current
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds (unused)
            v_source (float): Applied voltage (unused)
            
        Returns:
            float: Rate of change of transient voltage in V/s
            
        Physics:
            dVc/dt = -1/(RC) * Vc + 1/C * I
            where:
                Vc = transient voltage (y[6])
                I = current (y[1])
                R = polarization resistance
                C = capacitance
                
        Behavior:
            - When current flows: Voltage builds up with time constant τ = RC
            - When current stops: Voltage decays exponentially to zero
            - Larger C = slower response (more capacitive behavior)
            - Larger R = larger steady-state voltage drop
        """
        voltage, current, resistance, temperature, soc, sei, transient = unpack_state(y)
        
        # Calculate dVc/dt = -Vc/(RC) + I/C
        grad_Vc = (-1.0 / (self.R * self.C)) * transient + (1.0 / self.C) * current
        return grad_Vc

    def get_gradient(self, y, t, v_source):
        """
        Calculate gradient vector for the transient mechanism.
        
        Returns the rate of change for all state variables, with only the transient
        voltage component being non-zero.
        
        Args:
            y (np.array): State vector [voltage, current, resistance, temperature, soc, sei, transient]
            t (float): Current time in seconds
            v_source (float): Applied source voltage
            
        Returns:
            np.array: Gradient vector with only transient voltage component non-zero
                     Format: [0, 0, 0, 0, 0, 0, dVc/dt]
                     
        Note:
            Only the transient voltage component (index 6) is non-zero. Other mechanisms
            handle the other state variables.
        """
        grad_Vc = 0
        
        # Calculate RC dynamics contribution
        grad_Vc += self.rc_dynamics(y, t, v_source)
        
        return pack_state(0, 0, 0, 0, 0, 0, grad_Vc)
