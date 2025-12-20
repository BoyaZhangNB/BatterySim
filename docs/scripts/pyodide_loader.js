/* =========================================================
   PYODIDE LOADER + BATTERY SIMULATION ENGINE
   Mirrors batterycode Python logic inside the browser
========================================================= */

let pyodide = null;
let pyodideReady = false;

/* -----------------------------
   UI helpers
----------------------------- */
const simStatus = () => document.getElementById("sim-status");
const metricStrip = () => document.getElementById("metric-strip");

/* -----------------------------
   Initialize Pyodide
----------------------------- */
async function initPyodide() {
    if (pyodideReady) return pyodide;

    simStatus().textContent = "Loading Python runtime…";
    pyodide = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/"
    });

    await pyodide.loadPackage("numpy");
    simStatus().textContent = "Initializing battery model…";

    await pyodide.runPythonAsync(`
import numpy as np
import math
import json

# =====================================================
# Utility functions
# =====================================================

def ocv_from_soc(soc):
    data = [
        (1.00, 3.65),(0.995,3.45),(0.99,3.38),(0.9,3.35),
        (0.8,3.33),(0.7,3.30),(0.6,3.28),(0.5,3.26),
        (0.4,3.25),(0.3,3.23),(0.2,3.20),(0.15,3.05),
        (0.095,3.00),(0.05,2.80),(0.005,2.54),(0.0,2.50)
    ]
    soc = max(0,min(1,soc))
    for i in range(len(data)-1):
        s1,v1 = data[i]
        s2,v2 = data[i+1]
        if s2 <= soc <= s1:
            f = (soc-s2)/(s1-s2)
            return v2 + f*(v1-v2)
    return data[-1][1]

# =====================================================
# Charging policies
# =====================================================

def policy_voltage(policy, t, y, params):
    V,I,R,T,soc,sei,Vc = y
    ocv = ocv_from_soc(soc)

    if policy == "CV":
        return params["Vset"]

    if policy == "CC":
        return params["Iset"] * R + ocv

    if policy == "CCCV":
        if ocv < params["Vset"]:
            return params["Iset"] * R + ocv
        return params["Vset"]

    if policy == "CCVPulse":
        cycle = params["ton"] + params["toff"]
        if (t % cycle) < params["ton"]:
            return min(params["Vset"], params["Iset"] * R + ocv)
        return ocv

    return ocv

# =====================================================
# Derivatives (mechanisms)
# =====================================================

def derivatives(y, t, policy, params):
    V,I,R,T,soc,sei,Vc = y

    Vsrc = policy_voltage(policy,t,y,params)
    I = (Vsrc - V - Vc)/R

    dSOC = I/(params["C_nom"]*3600)
    dT = (I*I*R)/(params["mass"]*params["c"]) - params["k_cool"]*(T-params["Tamb"])

    # SEI
    if params["sei_model"] == "full":
        kT = params["k0"] * math.exp(-params["Ea"]/(8.314*T))
        stress = math.exp(0.5*(params["Vset"]-V))*(1+0.1*abs(I))
        dSEI = kT * stress
    else:
        kT = params["k0"] * math.exp(-params["Ea"]/(8.314*T))
        dSEI = kT * (1 + 2*soc*soc)*(1 + 0.1*abs(I))

    # Transient RC
    dVc = (-Vc/(params["Rtr"]*params["Ctr"])) + I/params["Ctr"]

    return np.array([
        0, 0, 0, dT, dSOC, dSEI, dVc
    ], dtype=float), Vsrc, I

# =====================================================
# RK4 Integrator
# =====================================================

def rk4(y,t,dt,policy,params):
    k1,_ ,_ = derivatives(y,t,policy,params)
    k2,_ ,_ = derivatives(y+0.5*dt*k1,t+0.5*dt,policy,params)
    k3,_ ,_ = derivatives(y+0.5*dt*k2,t+0.5*dt,policy,params)
    k4,_ ,_ = derivatives(y+dt*k3,t+dt,policy,params)
    return y + (dt/6)*(k1+2*k2+2*k3+k4)

# =====================================================
# Main simulation
# =====================================================

def run_simulation(policy, params_json):
    p = json.loads(params_json)
    dt = p["dt"]

    y = np.array([
        ocv_from_soc(p["soc0"]), 0,
        p["R0"], p["T0"],
        p["soc0"], 0, 0
    ], dtype=float)

    t = 0
    out = {
    "time": [],
    "voltage": [],
    "current": [],
    "temperature": [],
    "soc": [],
    "sei": [],
    "transient": []
}


    while y[4] < 0.9:
        dydt, Vsrc, I = derivatives(y,t,policy,p)
        y = rk4(y,t,dt,policy,p)
        y[1] = I
        y[0] = ocv_from_soc(y[4])

        out["time"].append(t)
        out["voltage"].append(y[0])
        out["current"].append(y[1])
        out["temperature"].append(y[3])
        out["soc"].append(y[4])
        out["sei"].append(y[5])
        out["transient"].append(y[6])


        t += dt

    return json.dumps(out)
    `);

    pyodideReady = true;
    simStatus().textContent = "Ready";
    return pyodide;
}

/* -----------------------------
   Collect parameters
----------------------------- */
function collectParams() {
    return {
        soc0: parseFloat(document.getElementById("initial-soc").value),
        T0: parseFloat(document.getElementById("initial-temp").value),
        R0: parseFloat(document.getElementById("R0").value),
        C_nom: parseFloat(document.getElementById("C_nom").value),
        dt: 0.2,
        mass: 1.0,
        c: 0.5,
        k_cool: 3.0,
        Tamb: 298,
        k0: 1e-7,
        Ea: 30000,
        Vset: parseFloat(document.getElementById("voltage-input").value),
        Iset: parseFloat(document.getElementById("current-input").value),
        ton: parseFloat(document.getElementById("pulse-on").value),
        toff: parseFloat(document.getElementById("pulse-off").value),
        sei_model: document.getElementById("sei-model").value,
        Rtr: 0.008,
        Ctr: 5000
    };
}

/* -----------------------------
   Single run
----------------------------- */
async function runSimulation() {
    await initPyodide();
    simStatus().textContent = "Running simulation…";

    const policy = document.getElementById("policy-select").value;
    const params = collectParams();

    const res = await pyodide.runPythonAsync(
        `run_simulation("${policy}", '${JSON.stringify(params)}')`
    );

    const data = JSON.parse(res);

    // ONLY update the main 4 plots
    plotResults(data);

    simStatus().textContent = `Simulation complete (${policy})`;
}




