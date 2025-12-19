import matplotlib.pyplot as plt
import pandas as pd
import glob
import numpy as np
from datetime import datetime
import os

# ==============================
# CONFIGURATION
# ==============================
LOG_DIR = "log"
POLICY_NAME = "CVPulse_4.0V_5A_1Hz"   # change to CV_4.0V, CCCV_20A_4.0V, CCCVPulse_20A_4.0V, CVPulse_4.0V, etc.
FILE_PATTERN = f"{LOG_DIR}/log_{POLICY_NAME}_cycle*.csv"

VARIABLES = ["voltage", "current", "temperature", "soc"]
Y_LABELS = ["Voltage (V)", "Current (A)", "Temperature (K)", "SOC"]

# ==============================
# LOAD DATA
# ==============================
file_list = sorted(glob.glob(FILE_PATTERN))

if len(file_list) == 0:
    raise FileNotFoundError(f"No files found matching {FILE_PATTERN}")

print(f"Found {len(file_list)} cycles for policy {POLICY_NAME}")

# ==============================
# PLOT 1: TIME SERIES PER CYCLE
# ==============================
plt.style.use("seaborn-v0_8-darkgrid")
fig, axes = plt.subplots(len(VARIABLES), 1, figsize=(12, 12), sharex=True)

for cycle_idx, file in enumerate(file_list, start=1):
    df = pd.read_csv(file)
    label = f"Cycle {cycle_idx}"

    axes[0].plot(df["time"], df["voltage"], label=label)
    axes[1].plot(df["time"], df["current"], label=label)
    axes[2].plot(df["time"], df["temperature"], label=label)
    axes[3].plot(df["time"], df["soc"], label=label)

# Label axes
for ax, ylabel in zip(axes, Y_LABELS):
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=8)

axes[-1].set_xlabel("Time (s)")

plt.suptitle(f"{POLICY_NAME}: Charging Dynamics Per Cycle", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96])

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
timeseries_path = f"{LOG_DIR}/timeseries_{POLICY_NAME}_{timestamp}.png"
plt.savefig(timeseries_path, dpi=300)
plt.show()

print(f"Saved time-series plot → {timeseries_path}")

# ==============================
# PLOT 2: SEI ACCUMULATION
# ==============================
sei_per_cycle = []

for file in file_list:
    df = pd.read_csv(file)
    sei_per_cycle.append(df["sei"].iloc[-1])  # end-of-cycle SEI

cycles = np.arange(1, len(sei_per_cycle) + 1)

plt.figure(figsize=(8, 5))
plt.plot(cycles, sei_per_cycle, marker="o", linewidth=2)
plt.xlabel("Cycle Number")
plt.ylabel("Accumulated SEI")
plt.title(f"{POLICY_NAME}: SEI Growth vs Cycle Count")
plt.grid(True)

sei_path = f"{LOG_DIR}/sei_accumulation_{POLICY_NAME}_{timestamp}.png"
plt.savefig(sei_path, dpi=300)
plt.show()

print(f"Saved SEI accumulation plot → {sei_path}")