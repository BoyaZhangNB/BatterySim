"""
Parameter Sweep and Pareto Optimization

This module systematically tests different charging policies with optimized parameters
to find the best policy architecture when each is tuned to its potential.

Hypothesis: Each policy type has different physics, so the optimal voltage/current for one
policy might differ from another. By optimizing each independently, we can compare
policy architectures fairly.

Parameter Search Space:
  - CC (Constant Current): Test currents 10A, 15A, 20A, 25A
  - CV (Constant Voltage): Test voltages 3.7V, 4.0V, 4.2V
  - CCCV (Two-stage): Test CV thresholds 3.5V, 3.8V, 4.0V, 4.2V (with 20A CC phase)
  - CCCVPulse (Two-stage + pulse): Test CV thresholds 3.5V, 3.8V, 4.0V, 4.2V (20A CC, 5A pulse @ 1Hz)

Output:
  - sweep_results.csv: All test results with metrics
  - Pareto frontiers for each policy type
  - Optimized policy comparison plot
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from charging_policy import CC, CV, CCCV, CCCVPulse
from mechanism.thermo import Thermo
from mechanism.charging import Charging
from mechanism.sei import SEI
from mechanism.transient import Transient
from update_state import UpdateState


class PolicySweep:
    """Systematic parameter optimization for each charging policy"""
    
    def __init__(self, cycles=3, dt=0.1):
        """
        Initialize sweep system
        
        Args:
            cycles: Number of charging cycles per configuration (3 for speed, 10 for accuracy)
            dt: Time step in seconds
        """
        self.cycles = cycles
        self.dt = dt
        self.results = []
        
    def run_simulation(self, policy, policy_name):
        """
        Run simulation for a single policy configuration using main.py's framework
        
        Returns:
            dict with metrics: charging_time, peak_temp, avg_temp, final_sei, sei_growth
        """
        try:
            # Use main.py's simulation framework
            from main import simulate_charging_cycle, pack_state, unpack_state
            
            # Run cycles
            all_cycles = simulate_charging_cycle(self.cycles, policy)
            
            temps = []
            times = []
            charging_times = []
            final_sei = 0
            
            # Process all cycles
            for cycle_idx, cycle_log in enumerate(all_cycles):
                if not cycle_log:
                    continue
                
                cycle_temps = [row[4] for row in cycle_log]  # temperature is at index 4
                cycle_times = [row[0] for row in cycle_log]  # time is at index 0
                temps.extend(cycle_temps)
                times.extend(cycle_times)
                
                # Charging time is last time in cycle (convert to hours)
                if cycle_times:
                    charging_times.append(cycle_times[-1] / 3600.0)
                
                # SEI is at index 6
                if cycle_log:
                    final_sei = cycle_log[-1][6]
            
            # Compile metrics
            avg_charging_time = np.mean(charging_times) if charging_times else 0
            
            metrics = {
                'policy': policy_name,
                'charging_time_hours': avg_charging_time,
                'peak_temp_K': max(temps) if temps else 298,
                'avg_temp_K': np.mean(temps) if temps else 298,
                'final_sei': final_sei,
                'sei_growth': final_sei,
                'thermal_stress': np.sum(np.array(temps) - 298) * self.dt if temps else 0,
            }
            return metrics
            
        except Exception as e:
            print(f"  ⚠ Error simulating {policy_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sweep_cc(self):
        """Test CC policy with different currents"""
        print("\n" + "="*70)
        print("SWEEPING CC POLICY - Constant Current")
        print("="*70)

        currents = [3, 6, 9]

        for current in currents:
            policy_name = f"CC_{current}A"
            print(f"  Testing {policy_name}...", end=" ", flush=True)
            
            policy = CC(current=current)
            metrics = self.run_simulation(policy, policy_name)
            
            if metrics:
                self.results.append(metrics)
                print(f"✓ {metrics['charging_time_hours']:.3f}h, {metrics['peak_temp_K']:.1f}K, SEI: {metrics['final_sei']:.2e}")
    
    def sweep_cv(self):
        """Test CV policy with different voltages"""
        print("\n" + "="*70)
        print("SWEEPING CV POLICY - Constant Voltage")
        print("="*70)
        
        voltages = [3.8, 4.0, 4.2]
        
        for voltage in voltages:
            policy_name = f"CV_{voltage:.1f}V"
            print(f"  Testing {policy_name}...", end=" ", flush=True)
            
            policy = CV(voltage=voltage)
            metrics = self.run_simulation(policy, policy_name)
            
            if metrics:
                self.results.append(metrics)
                print(f"✓ {metrics['charging_time_hours']:.3f}h, {metrics['peak_temp_K']:.1f}K, SEI: {metrics['final_sei']:.2e}")
    
    def sweep_cccv(self):
        """Test CCCV policy with different CV thresholds"""
        print("\n" + "="*70)
        print("SWEEPING CCCV POLICY - Two-Stage CC-CV")
        print("="*70)
        
        cv_thresholds = [4.2, 4.6, 5.0]
        cc_current = 9
        
        for cv_voltage in cv_thresholds:
            policy_name = f"CCCV_{cc_current}A_{cv_voltage:.1f}V"
            print(f"  Testing {policy_name}...", end=" ", flush=True)
            
            policy = CCCV(cc_current=cc_current, cv_voltage=cv_voltage)
            metrics = self.run_simulation(policy, policy_name)
            
            if metrics:
                self.results.append(metrics)
                print(f"✓ {metrics['charging_time_hours']:.3f}h, {metrics['peak_temp_K']:.1f}K, SEI: {metrics['final_sei']:.2e}")
    
    def sweep_cccv_pulse(self):
        """Test CCCVPulse policy with different CV thresholds and pulse params"""
        print("\n" + "="*70)
        print("SWEEPING CCCVPulse POLICY - Two-Stage with Pulse")
        print("="*70)

        cv_thresholds = [4.2, 4.6, 5.0]
        cc_current = 9
        pulse_current = 1
        pulse_freq = 1
        
        for cv_voltage in cv_thresholds:
            policy_name = f"CCCVPulse_{cc_current}A_{cv_voltage:.1f}V"
            print(f"  Testing {policy_name}...", end=" ", flush=True)
            
            policy = CCCVPulse(
                cc_current=cc_current,
                cv_voltage=cv_voltage,
                pulse_current=pulse_current,
                pulse_freq=pulse_freq
            )
            metrics = self.run_simulation(policy, policy_name)
            
            if metrics:
                self.results.append(metrics)
                print(f"✓ {metrics['charging_time_hours']:.3f}h, {metrics['peak_temp_K']:.1f}K, SEI: {metrics['final_sei']:.2e}")
    
    def run_full_sweep(self):
        """Execute complete parameter sweep"""
        print("\n\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "COMPREHENSIVE POLICY PARAMETER SWEEP" + " "*17 + "║")
        print("╚" + "="*68 + "╝")
        print(f"\nConfiguration: {self.cycles} cycles, dt={self.dt}s")
        print("Objective: Optimize each policy independently, then compare")
        
        self.sweep_cc()
        self.sweep_cv()
        self.sweep_cccv()
        self.sweep_cccv_pulse()
        
        return pd.DataFrame(self.results)
    
    def analyze_pareto(self, df):
        """
        Analyze Pareto frontiers for each policy type
        
        Two objectives: minimize charging_time and minimize sei_growth
        """
        print("\n\n" + "="*70)
        print("PARETO FRONTIER ANALYSIS")
        print("="*70)
        
        # Normalize metrics for Pareto comparison
        df_norm = df.copy()
        df_norm['time_norm'] = (df['charging_time_hours'] - df['charging_time_hours'].min()) / (df['charging_time_hours'].max() - df['charging_time_hours'].min())
        df_norm['sei_norm'] = (df['final_sei'] - df['final_sei'].min()) / (df['final_sei'].max() - df['final_sei'].min())
        df_norm['temp_norm'] = (df['peak_temp_K'] - df['peak_temp_K'].min()) / (df['peak_temp_K'].max() - df['peak_temp_K'].min())
        
        # Extract policy type
        df_norm['policy_type'] = df_norm['policy'].apply(lambda x: x.split('_')[0])
        
        # Find Pareto optimal for each policy type
        pareto_policies = []
        
        for policy_type in ['CC', 'CV', 'CCCV', 'CCCVPulse']:
            subset = df_norm[df_norm['policy_type'] == policy_type].copy()
            
            if len(subset) == 0:
                continue
            
            # Simple Pareto: dominated if worse in both time AND sei AND temp
            is_dominated = np.zeros(len(subset), dtype=bool)
            for i in range(len(subset)):
                for j in range(len(subset)):
                    if i != j:
                        if (subset.iloc[j]['time_norm'] <= subset.iloc[i]['time_norm'] and
                            subset.iloc[j]['sei_norm'] <= subset.iloc[i]['sei_norm'] and
                            subset.iloc[j]['temp_norm'] <= subset.iloc[i]['temp_norm']):
                            if not (subset.iloc[j]['time_norm'] == subset.iloc[i]['time_norm'] and
                                    subset.iloc[j]['sei_norm'] == subset.iloc[i]['sei_norm'] and
                                    subset.iloc[j]['temp_norm'] == subset.iloc[i]['temp_norm']):
                                is_dominated[i] = True
                                break
            
            pareto_subset = subset[~is_dominated]
            print(f"\n{policy_type} Policy - Pareto Optimal Configurations:")
            print(f"  Count: {len(pareto_subset)} out of {len(subset)}")
            
            for _, row in pareto_subset.iterrows():
                print(f"    • {row['policy']}: {row['charging_time_hours']:.3f}h, "
                      f"{row['peak_temp_K']:.1f}K, SEI: {row['final_sei']:.2e}")
                pareto_policies.append(row['policy'])
        
        return pareto_policies
    
    def find_best_policies(self, df):
        """Find best policy from each type (by different metrics)"""
        print("\n\n" + "="*70)
        print("POLICY TYPE WINNERS")
        print("="*70)
        
        df['policy_type'] = df['policy'].apply(lambda x: x.split('_')[0])
        
        best_by_type = {}
        
        for policy_type in ['CC', 'CV', 'CCCV', 'CCCVPulse']:
            subset = df[df['policy_type'] == policy_type]
            
            if len(subset) == 0:
                continue
            
            # Multi-objective score: balanced between speed and SEI
            subset_copy = subset.copy()
            subset_copy['score'] = (
                0.4 * (subset_copy['charging_time_hours'] / subset_copy['charging_time_hours'].max()) +
                0.3 * (subset_copy['final_sei'] / subset_copy['final_sei'].max()) +
                0.3 * ((subset_copy['peak_temp_K'] - 298) / (subset_copy['peak_temp_K'].max() - 298))
            )
            
            best = subset_copy.loc[subset_copy['score'].idxmin()]
            best_by_type[policy_type] = best
            
            print(f"\n{policy_type}: {best['policy']}")
            print(f"  Charging time: {best['charging_time_hours']:.3f}h")
            print(f"  Peak temp: {best['peak_temp_K']:.1f}K")
            print(f"  SEI growth: {best['final_sei']:.2e}")
            print(f"  Score: {best['score']:.3f}")
        
        return best_by_type
    
    def save_results(self, df):
        """Save all results to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        os.makedirs("log", exist_ok=True)
        filename = f"log/sweep_results_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✓ Results saved to {filename}")
        return filename


def main():
    """Run full parameter sweep"""
    sweep = PolicySweep(cycles=3, dt=0.1)
    
    # Run sweep
    df = sweep.run_full_sweep()
    
    # Analyze
    pareto_policies = sweep.analyze_pareto(df)
    best_by_type = sweep.find_best_policies(df)
    
    # Save
    filename = sweep.save_results(df)
    
    print("\n\n" + "="*70)
    print("SWEEP COMPLETE")
    print("="*70)
    print(f"Total configurations tested: {len(df)}")
    print(f"Results saved to: {filename}")
    
    return df, best_by_type


if __name__ == "__main__":
    df, best_policies = main()
