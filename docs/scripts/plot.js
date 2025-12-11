// docs/scripts/plot.js

function plotResults(data) {
    const t = data.t || data.T || [];

    const layoutCommon = {
        margin: { l: 50, r: 10, t: 10, b: 40 },
        xaxis: { title: "Time (s)" },
    };

    // Voltage
    Plotly.newPlot(
        "voltage-plot",
        [
            {
                x: t,
                y: data.V || [],
                mode: "lines",
                name: "V",
            },
        ],
        {
            ...layoutCommon,
            yaxis: { title: "Voltage (V)" },
        },
        { responsive: true }
    );

    // Current
    Plotly.newPlot(
        "current-plot",
        [
            {
                x: t,
                y: data.I || [],
                mode: "lines",
                name: "I",
            },
        ],
        {
            ...layoutCommon,
            yaxis: { title: "Current (A)" },
        },
        { responsive: true }
    );

    // Temperature
    Plotly.newPlot(
        "temperature-plot",
        [
            {
                x: t,
                y: data.T || [],
                mode: "lines",
                name: "T",
            },
        ],
        {
            ...layoutCommon,
            yaxis: { title: "Temperature (K)" },
        },
        { responsive: true }
    );

    // SOC
    Plotly.newPlot(
        "soc-plot",
        [
            {
                x: t,
                y: data.SOC || [],
                mode: "lines",
                name: "SOC",
            },
        ],
        {
            ...layoutCommon,
            yaxis: { title: "SOC (fraction)" },
        },
        { responsive: true }
    );

    // SEI
    Plotly.newPlot(
        "sei-plot",
        [
            {
                x: t,
                y: data.SEI || [],
                mode: "lines",
                name: "SEI",
            },
        ],
        {
            ...layoutCommon,
            yaxis: { title: "SEI (arb. units)" },
        },
        { responsive: true }
    );
}
