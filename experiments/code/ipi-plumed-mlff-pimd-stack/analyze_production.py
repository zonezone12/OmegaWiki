#!/usr/bin/env python3
"""Analyze and plot WT-MetaD PIMD production results."""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
TS_CV = 0.0
BASIN_A = -1.5
BASIN_B = 1.5

def load_colvar(path):
    """Load COLVAR file: time(fs), cv, metad.bias."""
    steps, t_ps, cv, bias = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                t_ps.append(float(parts[0]) / 1000)  # fs → ps
                cv.append(float(parts[1]))
                if len(parts) >= 4:
                    bias.append(float(parts[2]))
            except ValueError:
                continue
    return np.array(t_ps), np.array(cv), np.array(bias) if bias else np.zeros_like(cv)

def load_hills(path):
    """Load HILLS file: time, cv, sigma, height, biasf."""
    t_ps, cv, sigma, height = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                t_ps.append(float(parts[0]) / 1000)  # fs → ps
                cv.append(float(parts[1]))
                sigma.append(float(parts[2]))
                height.append(float(parts[3]))
            except ValueError:
                continue
    return np.array(t_ps), np.array(cv), np.array(sigma), np.array(height)

def reconstruct_fes(cv_grid, hills_t, hills_cv, hills_sigma, hills_height, time_limit=None):
    """Reconstruct FES from HILLS up to optional time_limit."""
    if time_limit is not None:
        mask = hills_t <= time_limit
        hills_cv = hills_cv[mask]
        hills_sigma = hills_sigma[mask]
        hills_height = hills_height[mask]

    fes = np.zeros_like(cv_grid)
    for h_cv, h_sigma, h_height in zip(hills_cv, hills_sigma, hills_height):
        fes += h_height * np.exp(-((cv_grid - h_cv) / h_sigma) ** 2 / 2)
    return fes

def main():
    colvar_path = RESULTS_DIR / "COLVAR"
    hills_path = RESULTS_DIR / "HILLS"

    if not colvar_path.exists() or not hills_path.exists():
        print(f"Error: {colvar_path} or {hills_path} not found")
        return

    # Load data
    t_ps, cv, bias = load_colvar(colvar_path)
    hills_t, hills_cv, hills_sigma, hills_height = load_hills(hills_path)

    print(f"COLVAR: {len(t_ps)} points, {t_ps[-1]:.1f} ps")
    print(f"HILLS: {len(hills_t)} Gaussians, final time {hills_t[-1]:.1f} ps")
    print(f"CV range: [{cv.min():.3f}, {cv.max():.3f}] Å")
    print(f"Bias accumulated: {bias[-1]:.1f} kJ/mol")

    # Create figure with 4 subplots
    fig = plt.figure(figsize=(14, 10))

    # ─────────────────────────────────────────────────────────────────────
    # 1. CV trajectory
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(t_ps, cv, lw=0.8, color="#1f77b4", alpha=0.85, label="CV(t)")
    ax1.axhline(TS_CV, color="red", lw=1.2, ls="--", label="TS (CV=0)")
    ax1.axhline(BASIN_A, color="gray", lw=0.8, ls=":", alpha=0.6)
    ax1.axhline(BASIN_B, color="gray", lw=0.8, ls=":", alpha=0.6, label="Basins")
    ax1.set_xlabel("Time (ps)", fontsize=10)
    ax1.set_ylabel("CV (Å)", fontsize=10)
    ax1.set_title("Collective Variable Trajectory", fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8)
    ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ─────────────────────────────────────────────────────────────────────
    # 2. Metadynamics bias buildup
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(t_ps, bias, lw=1.0, color="#ff7f0e", alpha=0.85)
    ax2.fill_between(t_ps, 0, bias, alpha=0.3, color="#ff7f0e")
    ax2.set_xlabel("Time (ps)", fontsize=10)
    ax2.set_ylabel("Cumulative Bias (kJ/mol)", fontsize=10)
    ax2.set_title("Metadynamics Bias Buildup", fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ─────────────────────────────────────────────────────────────────────
    # 3. Free energy surface (early, mid, final)
    ax3 = plt.subplot(2, 2, 3)
    cv_grid = np.linspace(cv.min() - 0.2, cv.max() + 0.2, 200)

    times_to_plot = [50, 150, 300]  # ps
    colors = ["#d62728", "#2ca02c", "#1f77b4"]

    for t_target, color in zip(times_to_plot, colors):
        fes = reconstruct_fes(cv_grid, hills_t, hills_cv, hills_sigma, hills_height, time_limit=t_target)
        ax3.plot(cv_grid, fes, lw=1.2, color=color, alpha=0.8, label=f"FES @ t={t_target} ps")

    # Final FES
    fes_final = reconstruct_fes(cv_grid, hills_t, hills_cv, hills_sigma, hills_height)
    ax3.plot(cv_grid, fes_final, lw=2, color="black", alpha=0.9, label="FES @ t=300 ps")

    ax3.axvline(TS_CV, color="red", lw=1, ls="--", alpha=0.5)
    ax3.set_xlabel("CV (Å)", fontsize=10)
    ax3.set_ylabel("Free Energy (kJ/mol)", fontsize=10)
    ax3.set_title("Free Energy Surface Reconstruction", fontweight="bold")
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=8, loc="upper right")
    ax3.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax3.xaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ─────────────────────────────────────────────────────────────────────
    # 4. Convergence: CV distribution + hill deposition rate
    ax4 = plt.subplot(2, 2, 4)
    ax4_twin = ax4.twinx()

    # Histogram of CV visits
    counts, bins, _ = ax4.hist(cv, bins=50, alpha=0.6, color="#1f77b4", edgecolor="black", linewidth=0.5)
    ax4.set_xlabel("CV (Å)", fontsize=10)
    ax4.set_ylabel("Visits (count)", fontsize=10, color="#1f77b4")
    ax4.tick_params(axis="y", labelcolor="#1f77b4")

    # Hill deposition rate
    bin_edges = np.linspace(0, t_ps[-1], 30)
    hills_per_bin = np.histogram(hills_t, bins=bin_edges)[0]
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    ax4_twin.plot(bin_centers, hills_per_bin, "o-", color="#ff7f0e", linewidth=1.5, markersize=4, label="Hills/50ps")
    ax4_twin.set_ylabel("Hill deposition rate", fontsize=10, color="#ff7f0e")
    ax4_twin.tick_params(axis="y", labelcolor="#ff7f0e")

    ax4.set_title("Convergence & Sampling", fontweight="bold")
    ax4.grid(True, alpha=0.3, axis="x")
    ax4.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    fig.suptitle("WT-MetaD PIMD Production — PhysNet FAD  |  600k steps (300 ps)",
                 fontsize=13, fontweight="bold", y=0.995)
    fig.tight_layout()

    out_path = RESULTS_DIR / "analysis_production.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\n✅ Saved: {out_path}")

    # Also save a high-res version
    out_path_hires = RESULTS_DIR / "analysis_production_hires.png"
    fig.savefig(out_path_hires, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {out_path_hires}")

    plt.close()

if __name__ == "__main__":
    main()
