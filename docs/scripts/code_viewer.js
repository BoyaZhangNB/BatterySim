// docs/scripts/code_viewer.js

const fileDescriptions = {
    "charging.py": "Implements the charging mechanism that updates SOC based on applied current and nominal capacity.",
    "charging_policies.py": "Defines CV, CC, pulse, and sinusoidal charging policies via get_voltage(t, y).",
    "thermo.py": "Thermal mechanism: ohmic heating, cooling to ambient, and temperature ODE.",
    "sei.py": "Full SEI growth model using Arrhenius dependence plus stress function in SOC and current.",
    "sei_simplified.py": "Simplified SEI model capturing temperature and SOC/current stress with a reduced formulation.",
    "transient.py": "Transient RC overpotential model with V̇ = -V/(RC) + I/C to capture dynamic voltage behaviour.",
    "update_state.py": "Algebraic updates for current, resistance, and voltage before ODE integration.",
    "utils.py": "Helper functions including state packing/unpacking, plotting, and OCV–SOC interpolation.",
    "main.py": "Top-level driver that configures mechanisms and policies and runs the charging simulation.",
};

async function loadCodeFile(filename) {
    const codeElement = document.getElementById("code-content");
    const titleElement = document.getElementById("code-title");
    const explainerElement = document.getElementById("code-explainer");

    if (!codeElement || !titleElement) return;

    titleElement.textContent = filename;

    const explain = fileDescriptions[filename] || "Python module used in the battery simulation.";
    explainerElement.textContent = explain;

    try {
        const response = await fetch(`python/${filename}`);
        if (!response.ok) {
            codeElement.textContent = "# Unable to load " + filename + " (HTTP " + response.status + ")";
        } else {
            const text = await response.text();
            codeElement.textContent = text;
        }
    } catch (err) {
        console.error(err);
        codeElement.textContent = "# Error loading file: " + err;
    }

    if (window.Prism) {
        Prism.highlightElement(codeElement);
    }
}

function setupFileButtons() {
    const buttons = document.querySelectorAll(".file-btn");
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            buttons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const filename = btn.getAttribute("data-file");
            loadCodeFile(filename);
        });
    });

    // Auto-load main.py on first visit
    const mainBtn = document.querySelector('.file-btn[data-file="main.py"]');
    if (mainBtn) {
        mainBtn.classList.add("active");
        loadCodeFile("main.py");
    }
}

document.addEventListener("DOMContentLoaded", setupFileButtons);
