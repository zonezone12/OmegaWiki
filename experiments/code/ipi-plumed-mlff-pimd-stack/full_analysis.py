#!/usr/bin/env python3
"""Full analysis: convergence validation, FES reconstruction, OPES comparison."""
import numpy as np
from pathlib import Path
import json

RESULTS_DIR = Path(__file__).parent / "results"
TS_CV = 0.0
BASIN_A = -1.5
BASIN_B = 1.5
KT = 1.380649e-23 * 200 * 6.02214076e23 / 1000  # kJ/mol at 200K ≈ 1.664

def load_colvar(path):
    """Load COLVAR: time(fs), cv, metad.bias."""
    t_ps, cv, bias = [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    t_ps.append(float(parts[0]) / 1000)
                    cv.append(float(parts[1]))
                    bias.append(float(parts[2]) if len(parts) >= 4 else 0.0)
                except ValueError:
                    continue
    return np.array(t_ps), np.array(cv), np.array(bias)

def load_hills(path):
    """Load HILLS: time, cv, sigma, height, biasf."""
    t_ps, cv, sigma, height = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 5:
                try:
                    t_ps.append(float(parts[0]) / 1000)
                    cv.append(float(parts[1]))
                    sigma.append(float(parts[2]))
                    height.append(float(parts[3]))
                except ValueError:
                    continue
    return np.array(t_ps), np.array(cv), np.array(sigma), np.array(height)

def reconstruct_fes(cv_grid, hills_t, hills_cv, hills_sigma, hills_height, time_limit=None):
    """Reconstruct FES from HILLS up to time_limit."""
    if time_limit is not None:
        mask = hills_t <= time_limit
        hills_cv_slice = hills_cv[mask]
        hills_sigma_slice = hills_sigma[mask]
        hills_height_slice = hills_height[mask]
    else:
        hills_cv_slice = hills_cv
        hills_sigma_slice = hills_sigma
        hills_height_slice = hills_height

    fes = np.zeros_like(cv_grid)
    for h_cv, h_sigma, h_height in zip(hills_cv_slice, hills_sigma_slice, hills_height_slice):
        fes += h_height * np.exp(-((cv_grid - h_cv) / h_sigma) ** 2 / 2)
    return fes

def get_barrier_height(fes, cv_grid, cv_ts=0.0):
    """Get barrier height relative to a point near TS."""
    idx_ts = np.argmin(np.abs(cv_grid - cv_ts))
    barrier = fes[idx_ts]
    return barrier

def main():
    colvar_path = RESULTS_DIR / "COLVAR"
    hills_path = RESULTS_DIR / "HILLS"

    if not colvar_path.exists() or not hills_path.exists():
        print(f"Error: files not found")
        return

    # Load all data
    t_ps, cv, bias = load_colvar(colvar_path)
    hills_t, hills_cv, hills_sigma, hills_height = load_hills(hills_path)

    print("=" * 70)
    print("FULL ANALYSIS: WT-MetaD PIMD PRODUCTION RUN")
    print("=" * 70)

    # ─────────────────────────────────────────────────────────────────────
    print("\n[A] CONVERGENCE VALIDATION")
    print("-" * 70)

    # Split into 3 blocks
    t_split = [0, 100, 200, 300]
    blocks = []
    for i in range(len(t_split) - 1):
        mask = (t_ps >= t_split[i]) & (t_ps < t_split[i+1])
        cv_block = cv[mask]
        t_block = t_ps[mask]
        blocks.append((t_split[i], t_split[i+1], cv_block, t_block))

    cv_grid = np.linspace(-3, 3, 300)
    fes_blocks = []
    barriers = []

    for t_start, t_end, cv_block, t_block in blocks:
        # Get hills up to midpoint of block
        t_mid = (t_start + t_end) / 2
        fes = reconstruct_fes(cv_grid, hills_t, hills_cv, hills_sigma, hills_height, time_limit=t_mid)
        fes_blocks.append((t_mid, fes))
        barrier = get_barrier_height(fes, cv_grid, TS_CV)
        barriers.append(barrier)

        print(f"\n Block {t_start:3.0f}–{t_end:3.0f} ps  (n_hills={len(hills_t[hills_t <= t_mid])})")
        print(f"   CV range: [{cv_block.min():.3f}, {cv_block.max():.3f}] Å")
        print(f"   CV mean:  {cv_block.mean():.3f} Å")
        print(f"   CV std:   {cv_block.std():.3f} Å")
        print(f"   FES barrier (TS): {barrier:.1f} kJ/mol")
        print(f"   Samples: {len(cv_block)}")

    # Convergence criterion
    barrier_drift = abs(barriers[-1] - barriers[0]) / max(abs(barriers[0]), 1)
    converged = barrier_drift < 0.05  # <5% change
    print(f"\n Barrier drift: {barrier_drift*100:.1f}%  {'✅ CONVERGED' if converged else '⚠️  DRIFTING'}")
    print(f" Recommendation: {'Full 300ps ready for publication' if converged else 'Extend to 600ps for convergence'}")

    # ─────────────────────────────────────────────────────────────────────
    print("\n[B] FREE ENERGY SURFACE RECONSTRUCTION")
    print("-" * 70)

    fes_final = reconstruct_fes(cv_grid, hills_t, hills_cv, hills_sigma, hills_height)

    # Find minima and saddle point
    barrier_idx = np.argmin(np.abs(cv_grid - TS_CV))
    fes_at_ts = fes_final[barrier_idx]

    idx_left = np.argmin(np.abs(cv_grid - (-1.5)))
    idx_right = np.argmin(np.abs(cv_grid - 1.5))
    fes_left = fes_final[idx_left]
    fes_right = fes_final[idx_right]

    print(f"\n Final FES Statistics:")
    print(f"   Free energy @ reactant (CV≈-1.5Å): {fes_left:+.1f} kJ/mol")
    print(f"   Free energy @ transition state:    {fes_at_ts:+.1f} kJ/mol")
    print(f"   Free energy @ product (CV≈+1.5Å): {fes_right:+.1f} kJ/mol")
    print(f"   Forward barrier (R→TS): {fes_at_ts - fes_left:.1f} kJ/mol")
    print(f"   Reverse barrier (P→TS): {fes_at_ts - fes_right:.1f} kJ/mol")
    print(f"   Well separation: {abs(fes_left - fes_right):.1f} kJ/mol")

    # Save FES for plotting
    fes_out = RESULTS_DIR / "fes_final.txt"
    with open(fes_out, "w") as f:
        f.write("# CV (Å)  FES (kJ/mol)\n")
        for x, y in zip(cv_grid, fes_final):
            f.write(f"{x:.6f}  {y:.6f}\n")
    print(f"\n✅ Saved FES: {fes_out}")

    # ─────────────────────────────────────────────────────────────────────
    print("\n[C] COMPARISON WITH OPES BASELINE")
    print("-" * 70)

    # Look for OPES results in wiki experiments
    wiki_dir = Path(__file__).parent.parent.parent.parent / "wiki" / "experiments"
    opes_exp_files = list(wiki_dir.glob("*opes*pimd*.md")) if wiki_dir.exists() else []

    print(f"\n Searching for OPES results...")
    if opes_exp_files:
        print(f" Found {len(opes_exp_files)} OPES experiment files")
        for f in opes_exp_files:
            print(f"   - {f.name}")
    else:
        print(f" ⚠️  No OPES results found in wiki/experiments/")

    # Summary comparison table
    print(f"\n Barrier Comparison Table:")
    print(f" ┌──────────────────┬──────────────────────┐")
    print(f" │ Method           │ Forward Barrier      │")
    print(f" ├──────────────────┼──────────────────────┤")
    print(f" │ WT-MetaD (300ps) │ {fes_at_ts - fes_left:6.1f} kJ/mol (300ps)  │")
    print(f" │ OPES             │ [see wiki/experiments/opes-pimd*] │")
    print(f" │ Classical MD     │ [need baseline]      │")
    print(f" └──────────────────┴──────────────────────┘")

    # Save summary
    summary = {
        "method": "WT-MetaD PIMD",
        "duration_ps": float(t_ps[-1]),
        "n_beads": 32,
        "temperature_k": 200,
        "forward_barrier_kj_mol": float(fes_at_ts - fes_left),
        "reverse_barrier_kj_mol": float(fes_at_ts - fes_right),
        "barrier_asymmetry_kj_mol": float(abs((fes_at_ts - fes_left) - (fes_at_ts - fes_right))),
        "n_hills": int(len(hills_t)),
        "final_bias_kj_mol": float(bias[-1]),
        "cv_range": [float(cv.min()), float(cv.max())],
        "converged": bool(converged),
        "barrier_drift_percent": float(barrier_drift * 100),
    }
    summary_out = RESULTS_DIR / "analysis_summary.json"
    with open(summary_out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n✅ Saved summary: {summary_out}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
