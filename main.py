'''
Where the main simulation loop will take place

A numerical solver would get gradient functions

Parameters:
    - t: time
    - voltage: open circuit voltage of the battery (varies with soc)
    - current: current into the battery
    - resistance: internal resistance of the battery
    - soc: state of charge
    - temperature: temperature of the battery (assume uniform)
    - SEI: solid-electrolyte interphase that permanently reduces battery capacity
    - v_source: supplied voltage from source
'''