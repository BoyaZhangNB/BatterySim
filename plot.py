import matplotlib.pyplot as plt
import pandas as pd
import glob
from datetime import datetime

# Load all cycle CSVs
file_list = sorted(glob.glob("log/log_CV_3.7V_cycle*.csv"))

# Variables we want to plot
variables = ["voltage", "current", "temperature", "soc"]

plt.style.use("seaborn-v0_8-darkgrid")
fig, axes = plt.subplots(len(variables), 1, figsize=(12, 12), sharex=True)

# Loop over cycles
for cycle_idx, file in enumerate(file_list, start=1):
    df = pd.read_csv(file)
    label = f"Cycle {cycle_idx}"

    axes[0].plot(df["time"], df["voltage"], label=label)
    axes[1].plot(df["time"], df["current"], label=label)
    axes[2].plot(df["time"], df["temperature"], label=label)
    axes[3].plot(df["time"], df["soc"], label=label)

# Label each subplot
axes[0].set_ylabel("Voltage (V)")
axes[1].set_ylabel("Current (A)")
axes[2].set_ylabel("Temp (K)")
axes[3].set_ylabel("SOC")
axes[3].set_xlabel("Time (s)")

# Add legends
for ax in axes:
    ax.legend()

plt.tight_layout()

# === SAVE THE PLOT ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f"log/plot_CV_3.7V_cycles_{timestamp}.png", dpi=300)

plt.show()