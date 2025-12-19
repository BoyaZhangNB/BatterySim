// plot.js
// Responsible ONLY for plotting and metric calculation
// NO calls back into simulation or Pyodide

// -------------------- CONFIG --------------------
const MAX_POINTS = 5000; // safety cap to prevent browser crashes

// -------------------- METRICS --------------------
function computeMetrics(data) {
    const soc = data.soc;
    const temp = data.temperature;
    const current = data.current;

    return {
        finalSOC: soc[soc.length - 1],
        maxTemp: Math.max(...temp),
        avgCurrent:
            current.reduce((a, b) => a + b, 0) / current.length
    };
}

// -------------------- PLOTTING --------------------
function plotResults(data) {
    const time = data.time;

    Plotly.newPlot("soc-plot", [{
        x: time,
        y: data.soc,
        name: "SOC",
        type: "scatter"
    }], {
        title: "State of Charge",
        xaxis: { title: "Time (s)" },
        yaxis: { title: "SOC" }
    });

    Plotly.newPlot("current-plot", [{
        x: time,
        y: data.current,
        name: "Current (A)",
        type: "scatter"
    }], {
        title: "Current",
        xaxis: { title: "Time (s)" },
        yaxis: { title: "Current (A)" }
    });

    Plotly.newPlot("temperature-plot", [{
        x: time,
        y: data.temperature,
        name: "Temperature (K)",
        type: "scatter"
    }], {
        title: "Temperature",
        xaxis: { title: "Time (s)" },
        yaxis: { title: "Temperature (K)" }
    });

    Plotly.newPlot("sei-plot", [{
        x: time,
        y: data.sei,
        name: "SEI Thickness",
        type: "scatter"
    }], {
        title: "SEI Growth",
        xaxis: { title: "Time (s)" },
        yaxis: { title: "SEI" }
    });
}
function plotAllPoliciesSOC(containerId, datasets) {
    const traces = [];

    datasets.forEach(entry => {
        if (!entry.data.time || !entry.data.soc) return;

        traces.push({
            x: entry.data.time,
            y: entry.data.soc,
            mode: "lines",
            name: entry.label,
            line: { width: 2 }
        });
    });

    if (traces.length === 0) {
        console.error("plotAllPoliciesSOC: no valid traces");
        return;
    }
}




// -------------------- UI OUTPUT --------------------
function displayMetrics(metrics) {
    const el = document.getElementById("metrics");
    if (!el) return;

    el.innerHTML = `
        <h3>Simulation Metrics</h3>
        <p><b>Final SOC:</b> ${(metrics.finalSOC * 100).toFixed(2)}%</p>
        <p><b>Max Temperature:</b> ${metrics.maxTemp.toFixed(2)} K</p>
        <p><b>Average Current:</b> ${metrics.avgCurrent.toFixed(2)} A</p>
    `;
}

// -------------------- ENTRY POINT --------------------
// This is the ONLY function pyodide_loader.js should call
window.handleSimulationResults = function (pythonResult) {
    /*
      pythonResult must be:
      {
        time: [...],
        voltage: [...],
        current: [...],
        resistance: [...],
        temperature: [...],
        soc: [...],
        sei: [...],
        transient: [...]
      }
    */
    plotResults(pythonResult);
};
