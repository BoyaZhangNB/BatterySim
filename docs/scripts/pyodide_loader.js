// docs/scripts/pyodide_loader.js

let pyodide = null;
let pyodideReadyPromise = null;

const simStatusEl = () => document.getElementById("sim-status");
const metricStripEl = () => document.getElementById("metric-strip");

/**
 * Initialize Pyodide and load our Python simulation code.
 */
async function initPyodide() {
    if (pyodideReadyPromise) return pyodideReadyPromise;

    pyodideReadyPromise = (async () => {
        if (simStatusEl()) simStatusEl().textContent = "Loading Python runtime (Pyodide)...";
        pyodide = await loadPyodide({
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/"
        });

        if (simStatusEl()) simStatusEl().textContent = "Loading NumPy...";
        await pyodide.loadPackage("numpy");

        const pythonCode = `
import numpy as np
import math
import json

def ocv_from_soc(soc):
    "Simplified OCV–SOC curve for fractional SOC in [0,1]."
    data = [
        (1.00, 3.65),
        (0.995, 3.45),
        (0.99, 3.38),
        (0.90, 3.35),
        (0.80, 3.33),
        (0.70, 3.30),
        (0.60, 3.28),
        (0.50, 3.26),
        (0.40, 3.25),
        (0.30, 3.23),
        (0.20, 3.20),
        (0.15, 3.05),
        (0.095, 3.00),
        (0.05, 2.80),
        (0.005, 2.54),
        (0.0, 2.50),
    ]
    s = max(0.0, min(1.0, float(soc)))
    for i in range(len(data) - 1):
        s_high, v_high = data[i]
        s_low, v_low = data[i+1]
        if s_low <= s <= s_high:
            frac = (s - s_low) / (s_high - s_low)
            return v_low + frac * (v_high - v_low)
    return data[-1][1]

def policy_voltage(policy_name, t, V, R, soc, params):
    "Implements CV, CC, Pulse, and Sine charging policies."
    name = str(policy_name)
    ocv = ocv_from_soc(soc)

    if name.startswith("CV"):
        Vset = params.get("Vset", 3.7)
        return Vset

    elif name.startswith("CC"):
        Iset = params.get("Iset", 25.0)
        return Iset * R + ocv

    elif name.startswith("Pulse"):
        Iset = params.get("Iset", 50.0)
        t_on = params.get("t_on", 2.0)
        t_off = params.get("t_off", 0.25)
        cycle = t_on + t_off
        if (t % cycle) < t_on:
            return Iset * R + ocv
        else:
            return ocv

    elif name.startswith("Sine"):
        Iamp = params.get("Iamp", 60.0)
        freq = params.get("freq", 4.0)
        I = abs(Iamp * math.sin(2 * math.pi * freq * t))
        return I * R + ocv

    return ocv

def derivatives(y, t, policy_name, params):
    "Compute dy/dt and instantaneous source/current."
    V, I, R, T, soc, sei = [float(v) for v in y]

    m = params.get("mass", 1.0)
    c = params.get("c", 0.5)
    k_cool = params.get("k_cool", 3.0)
    C_nom = params.get("C_nom", 200.0)  # Ah
    T_amb = params.get("T_amb", 298.0)

    k0_sei = params.get("k0", 1e-7)
    Ea = params.get("Ea", 3.0e4)
    Rgas = 8.314

    Vsource = policy_voltage(policy_name, t, V, R, soc, params)
    I_inst = (Vsource - V) / R if R > 1e-9 else 0.0

    dSOCdt = I_inst / (C_nom * 3600.0)

    dTdt = (I_inst**2 * R)/(m*c) + (I_inst * (Vsource - V))/(m*c) - k_cool*(T - T_amb)

    soc_clip = max(0.0, min(1.0, soc))
    kT = k0_sei * math.exp(-Ea / (Rgas * T))
    fQI = (1 + 2 * soc_clip**2) * (1 + 0.1 * abs(I_inst))
    dSEIdt = kT * fQI

    dVdt = 0.0
    dIdt = 0.0
    dRdt = 0.0

    dydt = np.array([dVdt, dIdt, dRdt, dTdt, dSOCdt, dSEIdt], dtype=float)
    return dydt, Vsource, I_inst

def rk4_step(y, t, dt, policy_name, params):
    k1, _, _ = derivatives(y, t, policy_name, params)
    k2, _, _ = derivatives(y + 0.5*dt*k1, t + 0.5*dt, policy_name, params)
    k3, _, _ = derivatives(y + 0.5*dt*k2, t + 0.5*dt, policy_name, params)
    k4, _, _ = derivatives(y + dt*k3, t + dt, policy_name, params)
    return y + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

def run_simulation(policy_name, params_json):
    "Run ODE simulation with parameters passed from JS as JSON."
    p = json.loads(params_json)
    policy_name = str(policy_name)

    soc0 = float(p.get("soc0", 0.0))
    T0 = float(p.get("T0", 298.0))
    t_max = float(p.get("t_max", 4000.0))
    dt = float(p.get("dt", 0.5))

    R0 = float(p.get("R0", 0.03))

    mass = float(p.get("mass", 1.0))
    c = float(p.get("c", 0.5))
    k_cool = float(p.get("k_cool", 3.0))
    C_nom = float(p.get("C_nom", 200.0))
    T_amb = float(p.get("T_amb", 298.0))
    k0 = float(p.get("k0", 1e-7))
    Ea = float(p.get("Ea", 3.0e4))
    Vset = float(p.get("Vset", 3.7))
    Iset = float(p.get("Iset", 25.0))
    t_on = float(p.get("t_on", 2.0))
    t_off = float(p.get("t_off", 0.25))
    Iamp = float(p.get("Iamp", 60.0))
    freq = float(p.get("freq", 4.0))

    params = {
        "mass": mass,
        "c": c,
        "k_cool": k_cool,
        "C_nom": C_nom,
        "T_amb": T_amb,
        "k0": k0,
        "Ea": Ea,
        "Vset": Vset,
        "Iset": Iset,
        "t_on": t_on,
        "t_off": t_off,
        "Iamp": Iamp,
        "freq": freq,
    }

    V0 = ocv_from_soc(soc0)
    I0 = 0.0
    sei0 = 0.0

    N = int(t_max / dt)
    t_vals = []
    V_vals = []
    I_vals = []
    R_vals = []
    T_vals = []
    soc_vals = []
    sei_vals = []

    y = np.array([V0, I0, R0, T0, soc0, sei0], dtype=float)
    t = 0.0

    for _ in range(N):
        if y[4] >= 0.999:
            break

        t_vals.append(float(t))
        V_vals.append(float(y[0]))
        I_vals.append(float(y[1]))
        R_vals.append(float(y[2]))
        T_vals.append(float(y[3]))
        soc_vals.append(float(y[4]))
        sei_vals.append(float(y[5]))

        y = rk4_step(y, t, dt, policy_name, params)
        _, Vsource, I_inst = derivatives(y, t, policy_name, params)
        y[1] = I_inst
        y[0] = ocv_from_soc(y[4])
        t += dt

    result = {
        "t": t_vals,
        "V": V_vals,
        "I": I_vals,
        "R": R_vals,
        "T": T_vals,
        "SOC": soc_vals,
        "SEI": sei_vals,
    }
    return json.dumps(result)
        `;
        await pyodide.runPythonAsync(pythonCode);

        if (simStatusEl()) simStatusEl().textContent = "Ready. Choose parameters and run the simulation.";
        return pyodide;
    })();

    return pyodideReadyPromise;
}

/**
 * Collect parameters from the UI.
 */
function collectParams() {
    const val = id => document.getElementById(id)?.value;

    const soc0 = parseFloat(val("initial-soc") || "0");
    const T0 = parseFloat(val("initial-temp") || "298");
    const t_max = parseFloat(val("tmax") || "4000");
    const dt = parseFloat(val("dt") || "0.5");
    const R0 = parseFloat(val("R0") || "0.03");
    const mass = parseFloat(val("mass") || "1.0");
    const c = parseFloat(val("c") || "0.5");
    const k_cool = parseFloat(val("k_cool") || "3.0");
    const T_amb = parseFloat(val("Tamb") || "298");
    const C_nom = parseFloat(val("C_nom") || "200");
    const k0 = parseFloat(val("k0") || "1e-7");
    const Ea = parseFloat(val("Ea") || "30000");
    const Vset = parseFloat(val("Vset") || "3.7");
    const Iset = parseFloat(val("Iset") || "25");
    const t_on = parseFloat(val("t_on") || "2");
    const t_off = parseFloat(val("t_off") || "0.25");
    const Iamp = parseFloat(val("Iamp") || "60");
    const freq = parseFloat(val("freq") || "4");

    return {
        soc0, T0, t_max, dt,
        R0, mass, c, k_cool, T_amb,
        C_nom, k0, Ea, Vset, Iset,
        t_on, t_off, Iamp, freq,
    };
}

/**
 * Run simulation on button click.
 */
async function runSimulation() {
    try {
        const policySelect = document.getElementById("policy-select");
        const policyShort = policySelect.value;

        let policy_name = "";
        if (policyShort === "CV") policy_name = "CV_3.7V";
        else if (policyShort === "CC") policy_name = "CC_25A";
        else if (policyShort === "Pulse") policy_name = "Pulse_50A";
        else if (policyShort === "Sine") policy_name = "Sine_60A";

        const params = collectParams();
        const paramsJson = JSON.stringify(params);

        if (simStatusEl()) simStatusEl().textContent = "Running simulation in Python...";

        const py = await initPyodide();
        py.globals.set("policy_name_js", policy_name);
        py.globals.set("params_json_js", paramsJson);

        const jsonStr = await py.runPythonAsync(`
result = run_simulation(policy_name_js, params_json_js)
result
        `);

        const data = JSON.parse(jsonStr);
        if (simStatusEl()) {
            if (data.SOC && data.SOC.length) {
                const finalSOC = data.SOC[data.SOC.length - 1];
                const maxT = Math.max(...data.T);
                simStatusEl().textContent =
                    "Done. Final SOC ≈ " + finalSOC.toFixed(3) +
                    ", peak T ≈ " + maxT.toFixed(1) + " K";
            } else {
                simStatusEl().textContent = "Done, but no data returned.";
            }
        }

        fillMetricStrip(data);
        if (typeof plotResults === "function") {
            plotResults(data);
        }
    } catch (err) {
        console.error(err);
        if (simStatusEl()) simStatusEl().textContent = "Error: " + err;
    }
}

/**
 * Update the metric pills above the first plot.
 */
function fillMetricStrip(data) {
    const el = metricStripEl();
    if (!el) return;
    el.innerHTML = "";

    if (!data || !data.t || !data.t.length) return;

    const duration = data.t[data.t.length - 1] - data.t[0];
    const maxT = Math.max(...data.T);
    const maxI = Math.max(...data.I);
    const finalSOC = data.SOC[data.SOC.length - 1];
    const maxSEI = Math.max(...data.SEI);

    const makePill = text => {
        const span = document.createElement("span");
        span.className = "metric-pill";
        span.textContent = text;
        return span;
    };

    el.appendChild(makePill("Duration: " + duration.toFixed(0) + " s"));
    el.appendChild(makePill("Final SOC: " + finalSOC.toFixed(3)));
    el.appendChild(makePill("Max T: " + maxT.toFixed(1) + " K"));
    el.appendChild(makePill("Max I: " + maxI.toFixed(1) + " A"));
    el.appendChild(makePill("Max SEI: " + maxSEI.toExponential(2)));
}

// Start loading Pyodide as soon as page is loaded
initPyodide();
