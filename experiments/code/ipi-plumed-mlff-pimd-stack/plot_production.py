#!/usr/bin/env python3
"""
Publication-quality 4-panel analysis of WT-MetaD PIMD production run.

IMPORTANT: CV units are PLUMED nm throughout (SIGMA=0.005 nm = 0.05 Ang).
Physical FAD basins at CV = ±0.15 nm (±1.5 Ang). TS at 0 nm.

Known issue: PLUMED was called once per bead (not per centroid), so hills
were deposited at per-bead CV positions → system escaped physical range.
Early-time FES (|CV|<0.3 nm, first ~32k hills) is the physically meaningful
portion; everything beyond that is bead-driven artefact.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

T  = 200.0                # K
KB = 8.314e-3             # kJ/(mol K)
KT = KB * T               # 1.6628 kJ/mol
GAMMA = 100.0             # biasfactor
PHYS_CV_MAX = 0.30        # nm — physical CV range
N_BEADS = 32
DT_FS = 0.5               # femtoseconds per MD step

# PLUMED step to MD step: PLUMED called N_BEADS times per MD step
PLUMED_TO_PS = DT_FS / (N_BEADS * 1000.0)   # PLUMED_step * this = ps


def load_colvar(path, stride=1):
    """COLVAR cols: plumed_step, cv(nm), metad.bias(kJ/mol)."""
    t_ps, cv, bias = [], [], []
    with open(path, encoding="utf-8") as f:
        count = 0
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            count += 1
            if count % stride != 0:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                t_ps.append(float(parts[0]) * PLUMED_TO_PS)
                cv.append(float(parts[1]))
                bias.append(float(parts[2]))
            except ValueError:
                continue
    return np.array(t_ps), np.array(cv), np.array(bias)


def load_hills(path):
    """HILLS cols: plumed_step, cv(nm), sigma(nm), height(kJ/mol), biasf."""
    t_ps, cv_h, sigma_h, height_h = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 5:
                try:
                    t_ps.append(float(parts[0]) * PLUMED_TO_PS)
                    cv_h.append(float(parts[1]))
                    sigma_h.append(float(parts[2]))
                    height_h.append(float(parts[3]))
                except ValueError:
                    continue
    return np.array(t_ps), np.array(cv_h), np.array(sigma_h), np.array(height_h)


def fes_from_hills(cv_grid, hills_cv, hills_sigma, hills_height, phys_only=True):
    """Sum Gaussians. If phys_only, skip hills outside physical CV range."""
    if phys_only:
        mask = np.abs(hills_cv) < PHYS_CV_MAX
        hills_cv    = hills_cv[mask]
        hills_sigma = hills_sigma[mask]
        hills_height = hills_height[mask]

    dx = (cv_grid[:, None] - hills_cv[None, :]) / hills_sigma[None, :]
    V  = np.sum(hills_height[None, :] * np.exp(-0.5 * dx**2), axis=1)
    # WT-MetaD: F = -gamma/(gamma-1) * V  (at convergence)
    F  = -(GAMMA / (GAMMA - 1.0)) * V
    F -= F.min()
    return F


def main():
    colvar_path = RESULTS_DIR / "COLVAR"
    hills_path  = RESULTS_DIR / "HILLS"

    # Stride: one sample per MD step = N_BEADS PLUMED calls; COLVAR stride=10
    # so we want every (N_BEADS // gcd(N_BEADS, 10)) entries = every 16 entries
    print("Loading COLVAR (one sample per ~MD step)...")
    t_ps_s, cv_s, bias_s = load_colvar(colvar_path, stride=16)
    print(f"  {len(t_ps_s)} independent frames  t=[{t_ps_s[0]:.1f}, {t_ps_s[-1]:.1f}] ps")
    print(f"  CV range: [{cv_s.min():.3f}, {cv_s.max():.3f}] nm")
    print(f"  Bias range: [{bias_s.min():.2f}, {bias_s.max():.2f}] kJ/mol")

    # Physical-range frames
    phys_mask = np.abs(cv_s) < PHYS_CV_MAX
    t_phys  = t_ps_s[phys_mask]
    cv_phys = cv_s[phys_mask]
    print(f"  Physical (|CV|<{PHYS_CV_MAX} nm) frames: {phys_mask.sum()} / {len(cv_s)}")

    print("Loading HILLS...")
    hills_t, hills_cv, hills_sigma, hills_height = load_hills(hills_path)
    print(f"  {len(hills_t)} hills  t=[{hills_t[0]:.3f}, {hills_t[-1]:.1f}] ps")
    n_phys_hills = (np.abs(hills_cv) < PHYS_CV_MAX).sum()
    print(f"  Physical hills (|CV|<{PHYS_CV_MAX} nm): {n_phys_hills}")

    # FES from physical hills only
    cv_grid = np.linspace(-0.30, 0.30, 200)
    F_phys  = fes_from_hills(cv_grid, hills_cv, hills_sigma, hills_height, phys_only=True)

    print("\n--- FES BARRIER (physical hills only) ---")
    left_m = cv_grid < -0.05;  right_m = cv_grid > 0.05;  mid_m = np.abs(cv_grid) <= 0.05
    F_left = F_phys[left_m].min() if left_m.any() else np.nan
    F_right = F_phys[right_m].min() if right_m.any() else np.nan
    F_ts   = F_phys[mid_m].max()  if mid_m.any()  else np.nan
    fwd = F_ts - F_left;  rev = F_ts - F_right
    print(f"  Reactant basin min: {F_left:.2f} kJ/mol  (CV<-0.05 nm)")
    print(f"  TS (approx):        {F_ts:.2f} kJ/mol  (|CV|<0.05 nm)")
    print(f"  Product basin min:  {F_right:.2f} kJ/mol  (CV>0.05 nm)")
    print(f"  Forward barrier:    {fwd:.2f} kJ/mol  ({fwd/4.184:.2f} kcal/mol)")
    print(f"  Reverse barrier:    {rev:.2f} kJ/mol  ({rev/4.184:.2f} kcal/mol)")
    print(f"  Reference (baseline, 3 seeds): 3.90 kcal/mol = 16.3 kJ/mol")

    # Save FES
    out_fes = RESULTS_DIR / "fes_physical.dat"
    with open(out_fes, "w", encoding="utf-8") as f:
        f.write("# WT-MetaD FES (physical hills only, |CV|<0.30 nm)\n")
        f.write("# CV (nm)  F (kJ/mol)\n")
        for x, y in zip(cv_grid, F_phys):
            f.write(f"{x:.6f}  {y:.6f}\n")
    print(f"\nSaved FES: {out_fes}")

    # ── FIGURE ─────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    (ax1, ax2), (ax3, ax4) = axes
    fig.subplots_adjust(hspace=0.40, wspace=0.32)

    BLUE = "#1f77b4"; ORG = "#ff7f0e"; GREEN = "#2ca02c"; RED = "#d62728"

    # ── Panel 1: Full CV trajectory (downsampled) ──────────────────────────
    ax1.plot(t_ps_s, cv_s, lw=0.4, color=BLUE, alpha=0.6, label="CV per bead (nm)")
    ax1.axhline(0.0,              color=RED,    lw=1.2, ls="--", alpha=0.8, label="TS (0 nm)")
    ax1.axhline(-0.15,            color="gray", lw=0.8, ls=":", alpha=0.7)
    ax1.axhline(+0.15,            color="gray", lw=0.8, ls=":", alpha=0.7, label="Basins (+-0.15 nm)")
    ax1.axhline(+PHYS_CV_MAX,     color=ORG,   lw=1.0, ls="-.", alpha=0.8, label=f"Physical limit ({PHYS_CV_MAX} nm)")
    ax1.axhline(-PHYS_CV_MAX,     color=ORG,   lw=1.0, ls="-.", alpha=0.8)
    ax1.set_xlabel("Simulation time (ps)", fontsize=10)
    ax1.set_ylabel("CV (nm)", fontsize=10)
    ax1.set_title("CV Trajectory — per-bead (all 300 ps)", fontweight="bold")
    ax1.legend(fontsize=8, loc="upper left", framealpha=0.75)
    ax1.grid(True, alpha=0.2)
    ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ── Panel 2: Zoom — first 5 ps (physical range, barrier crossing) ──────
    early_mask = t_ps_s < 5.0
    ax2.plot(t_ps_s[early_mask], cv_s[early_mask], lw=0.8, color=BLUE, alpha=0.9)
    ax2.axhline(0.0,    color=RED,    lw=1.2, ls="--", alpha=0.8, label="TS")
    ax2.axhline(-0.15,  color="gray", lw=0.8, ls=":", alpha=0.7, label="Basins")
    ax2.axhline(+0.15,  color="gray", lw=0.8, ls=":", alpha=0.7)
    ax2.axhline(+PHYS_CV_MAX, color=ORG, lw=1.0, ls="-.", alpha=0.8, label="Physical limit")
    ax2.set_xlabel("Time (ps)", fontsize=10)
    ax2.set_ylabel("CV (nm)", fontsize=10)
    ax2.set_title("CV Trajectory — early 5 ps (physical region)", fontweight="bold")
    ax2.legend(fontsize=8, framealpha=0.75)
    ax2.grid(True, alpha=0.2)

    # ── Panel 3: FES from physical hills ──────────────────────────────────
    ax3.plot(cv_grid, F_phys, lw=2.0, color="black", label="FES (physical hills)")
    ax3.fill_between(cv_grid, F_phys, F_phys.max() * 1.05, alpha=0.06, color="black")
    ax3.axvline(0,     color=RED,    lw=1.2, ls="--", alpha=0.7, label="TS")
    ax3.axvline(-0.15, color="gray", lw=0.8, ls=":", alpha=0.6, label="Basin centres")
    ax3.axvline(+0.15, color="gray", lw=0.8, ls=":", alpha=0.6)
    if not np.isnan(fwd):
        ax3.annotate(f"Fwd barrier\n{fwd:.1f} kJ/mol\n({fwd/4.184:.2f} kcal/mol)",
                     xy=(0.01, F_ts), xytext=(0.08, F_ts + 2),
                     fontsize=9, color=RED, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
    ax3.set_xlabel("CV (nm)", fontsize=10)
    ax3.set_ylabel("Free Energy (kJ/mol)", fontsize=10)
    ax3.set_title(f"Free Energy Surface\n(physical hills only, |CV|<{PHYS_CV_MAX} nm)", fontweight="bold")
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.2)
    ax3.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax3.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ── Panel 4: CV histogram — physical vs escaped frames ─────────────────
    bins_p = np.linspace(-0.30, 0.30, 50)
    bins_f = np.linspace(-0.30, cv_s.max() * 1.05, 80)

    ax4.hist(cv_s, bins=np.linspace(-0.4, cv_s.max() * 1.01, 80),
             alpha=0.35, color=ORG, density=True, label="All frames (artefact visible)")
    ax4.hist(cv_phys, bins=bins_p,
             alpha=0.65, color=BLUE, density=True, label=f"Physical frames (|CV|<{PHYS_CV_MAX} nm)")
    ax4.axvline(0,     color=RED,    lw=1.2, ls="--", alpha=0.8, label="TS")
    ax4.axvline(-0.15, color="gray", lw=0.8, ls=":", alpha=0.6)
    ax4.axvline(+0.15, color="gray", lw=0.8, ls=":", alpha=0.6)
    ax4.axvline(+PHYS_CV_MAX, color=ORG, lw=1.0, ls="-.", alpha=0.8,
                label="Physical limit")
    n_phys_pct = 100.0 * phys_mask.sum() / len(cv_s)
    ax4.set_xlabel("CV (nm)", fontsize=10)
    ax4.set_ylabel("Probability density", fontsize=10)
    ax4.set_title(f"CV Distribution\n({n_phys_pct:.1f}% frames in physical range)", fontweight="bold")
    ax4.legend(fontsize=8, framealpha=0.75)
    ax4.grid(True, alpha=0.2)
    ax4.xaxis.set_minor_locator(ticker.AutoMinorLocator())

    fig.suptitle(
        "WT-MetaD PIMD Production — PhysNet FAD Proton Transfer, 200 K, 32 beads\n"
        "600k MD steps (300 ps) | 96k Gaussians | 29.2 h  |  NOTE: per-bead CV (not centroid)",
        fontsize=11, fontweight="bold", y=0.998
    )

    out = RESULTS_DIR / "production_analysis.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nSaved figure: {out}")
    out_hi = RESULTS_DIR / "production_analysis_300dpi.png"
    fig.savefig(out_hi, dpi=300, bbox_inches="tight")
    print(f"Saved hi-res: {out_hi}")
    plt.close()


if __name__ == "__main__":
    main()
