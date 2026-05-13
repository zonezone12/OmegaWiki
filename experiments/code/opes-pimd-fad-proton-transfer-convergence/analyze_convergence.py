#!/usr/bin/env python
"""Convergence analysis for OPES-PIMD FAD proton transfer.
Loads fes_snapshots/seed_*/fes_step*.npz, computes barrier vs time,
finds t_conv (first t where barrier is within 0.1 kcal/mol of final value)
and compares against WT-MetaD baseline (Fan et al. 2025, t_conv=150 ps).

Usage:
  python analyze_convergence.py
  python analyze_convergence.py --results-dir results_v2 --plot
"""
import argparse, json, os, sys
from glob import glob
import numpy as np

TIMESTEP_FS    = 0.5
FS_PER_PS      = 1000.0
TARGET_BARRIER = 1.52
TARGET_TOL     = 0.15
CONV_TOL       = 0.10
WTMETAD_TCONV  = 150.0


def extract_barrier(grid, fes):
    valid = ~np.isnan(fes)
    if valid.sum() < 10:
        return float("nan")
    mid = len(grid) // 2
    if mid < 2:
        return float("nan")
    fl = fes[:mid].copy(); fl[np.isnan(fl)] = np.inf
    fr = fes[mid:].copy(); fr[np.isnan(fr)] = np.inf
    l  = int(np.argmin(fl))
    r  = mid + int(np.argmin(fr))
    if l >= r:
        return float("nan")
    seg = fes[l:r].copy(); seg[np.isnan(seg)] = -np.inf
    ts  = l + int(np.argmax(seg))
    if np.isnan(fes[ts]) or np.isnan(fes[l]):
        return float("nan")
    return float(fes[ts] - fes[l])


def load_seed(seed_dir):
    """Load FES snapshots + optional final-step result from seed_*.json.

    The snapshots go up to step (n_steps - fes_stride); the final barrier
    at step n_steps is only in seed_*.json.  We merge them so t_conv can be
    detected all the way to the end of the simulation.
    """
    files = sorted(glob(os.path.join(seed_dir, "fes_step*.npz")))
    if not files:
        return np.array([]), np.array([])
    steps, barriers = [], []
    for fp in files:
        d = np.load(fp)
        steps.append(int(d["step"]))
        barriers.append(extract_barrier(d["cv"], d["fes"]))

    # try to append final result from seed_*.json (one directory up)
    seed_name = os.path.basename(seed_dir)
    parent    = os.path.dirname(os.path.dirname(seed_dir))  # results/
    json_path = os.path.join(parent, seed_name + ".json")
    if os.path.exists(json_path):
        try:
            with open(json_path) as jf:
                info = json.load(jf)
            final_step = int(info.get("n_steps", 0))
            final_b    = info.get("barrier_kcal_mol")
            # only use JSON if it represents a full simulation (not a sanity run)
            min_valid_steps = max(steps) if len(steps) > 0 else 50000
            if (final_step >= min_valid_steps and final_b is not None
                    and final_step not in steps):
                steps.append(final_step)
                barriers.append(float(final_b))
        except Exception:
            pass

    order = np.argsort(steps)
    return np.array(steps)[order], np.array(barriers)[order]


def find_tconv(steps_ps, barriers, tol=None):
    if tol is None: tol = CONV_TOL
    valid = ~np.isnan(barriers)
    if valid.sum() < 2:
        return float("nan")
    b_final = barriers[valid][-1]
    t_conv  = np.inf
    for i in range(len(steps_ps) - 1, -1, -1):
        if np.isnan(barriers[i]):
            continue
        if abs(barriers[i] - b_final) < tol:
            t_conv = steps_ps[i]
        else:
            break
    return t_conv


def is_stalled(barriers, threshold=10.0):
    valid = barriers[~np.isnan(barriers)]
    return len(valid) == 0 or float(valid[-1]) > threshold


def wilcoxon_vs_baseline(tconv_values, baseline=None):
    if baseline is None: baseline = WTMETAD_TCONV
    try:
        from scipy.stats import wilcoxon
        diffs = np.array(tconv_values) - baseline
        stat, p = wilcoxon(diffs, alternative="less")
        return float(stat), float(p)
    except Exception:
        return None, None


def _plot(per_seed, results_dir):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [plot] matplotlib not available"); return
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63"]
    for i, (sn, v) in enumerate(sorted(per_seed.items())):
        ts = np.array(v["steps_ps"]); bs = np.array(v["barriers"])
        ax.plot(ts, bs, marker="o", markersize=4, label=sn,
                color=colors[i % len(colors)], linewidth=1.5)
    ax.axhline(TARGET_BARRIER, color="black", ls="--", lw=1,
               label="Target %.2f kcal/mol" % TARGET_BARRIER)
    ax.axhline(TARGET_BARRIER + TARGET_TOL, color="gray", ls=":", lw=0.8)
    ax.axhline(TARGET_BARRIER - TARGET_TOL, color="gray", ls=":", lw=0.8)
    ax.axvline(WTMETAD_TCONV, color="red", ls="--", lw=1,
               label="WT-MetaD t_conv %.0f ps" % WTMETAD_TCONV)
    ax.set_xlabel("Simulation time (ps)"); ax.set_ylabel("Barrier (kcal/mol)")
    ax.set_title("OPES-PIMD: FES barrier convergence")
    ax.legend(fontsize=9); ax.set_ylim(bottom=0); ax.grid(True, alpha=0.3)
    out = os.path.join(results_dir, "convergence_plot.png")
    plt.tight_layout(); plt.savefig(out, dpi=150); plt.close()
    print("  Saved plot: %s" % out)



def analyze(results_dir, plot=False, out_json=None):
    snap_dir = os.path.join(results_dir, "fes_snapshots")
    if not os.path.isdir(snap_dir):
        print("[ERROR] fes_snapshots not found under %s" % results_dir)
        sys.exit(1)
    seed_dirs = sorted(glob(os.path.join(snap_dir, "seed_*")))
    if not seed_dirs:
        print("[ERROR] No seed_* dirs in %s" % snap_dir); sys.exit(1)
    print("")
    print("==============================================================")
    print("  OPES-PIMD Convergence Analysis")
    print("  Results: %s" % results_dir)
    print("  Conv. tolerance: %.2f kcal/mol" % CONV_TOL)
    print("  WT-MetaD baseline: %.0f ps" % WTMETAD_TCONV)
    print("==============================================================")
    per_seed, all_tconv = {}, []
    for sd in seed_dirs:
        sn = os.path.basename(sd)
        steps, barriers = load_seed(sd)
        if len(steps) == 0:
            print("[%s] No snapshots -- skipping" % sn); continue
        steps_ps = steps * TIMESTEP_FS / FS_PER_PS
        t_conv   = find_tconv(steps_ps, barriers)
        valid_b  = barriers[~np.isnan(barriers)]
        b_final  = float(valid_b[-1]) if len(valid_b) > 0 else float("nan")
        stalled  = is_stalled(barriers)
        ever_xd  = any(abs(b - TARGET_BARRIER) < TARGET_TOL for b in valid_b)
        per_seed[sn] = {
            "steps_ps": steps_ps.tolist(), "barriers": barriers.tolist(),
            "b_final": b_final, "t_conv_ps": float(t_conv),
            "stalled": stalled, "ever_crossed": ever_xd,
        }
        print("")
        print("[%s]" % sn)
        print("  Snapshots  : %d  (%.0f - %.0f ps)" % (len(steps), steps_ps[0], steps_ps[-1]))
        print("  b_final    : %.3f kcal/mol" % b_final)
        print("  stalled    : %s" % stalled)
        print("  ever_crossed: %s" % ever_xd)
        if np.isinf(t_conv):
            print("  t_conv     : NOT CONVERGED within %.0f ps" % steps_ps[-1])
        elif np.isnan(t_conv):
            print("  t_conv     : insufficient data")
        else:
            print("  t_conv     : %.1f ps" % t_conv)
            all_tconv.append(t_conv)
        print("  Barrier time series (ps -> kcal/mol):")
        for t, b in zip(steps_ps, barriers):
            bs = "nan" if np.isnan(b) else "%.3f" % b
            fl = " <-- CONV" if (not np.isnan(b) and abs(b - b_final) < CONV_TOL) else ""
            print("    %6.1f ps  ->  %8s kcal/mol%s" % (t, bs, fl))
    print("")
    print("==============================================================")
    print("  AGGREGATE SUMMARY")
    print("==============================================================")
    ns  = len(per_seed)
    nst = sum(1 for v in per_seed.values() if v["stalled"])
    nc  = len(all_tconv)
    print("  Seeds analysed : %d" % ns)
    print("  Stalled        : %d / %d" % (nst, ns))
    print("  Converged      : %d / %d" % (nc, ns))
    if nc > 0:
        mt = float(np.mean(all_tconv))
        st = float(np.std(all_tconv, ddof=0))
        sp = WTMETAD_TCONV / mt if mt > 0 else float("nan")
        af = all(t < WTMETAD_TCONV for t in all_tconv)
        print("  t_conv mean    : %.1f +/- %.1f ps" % (mt, st))
        print("  WT-MetaD t_conv: %.1f ps" % WTMETAD_TCONV)
        print("  Speed-up       : %.2fx" % sp)
        print("  All faster     : %s" % af)
        if nc >= 3:
            stat, p = wilcoxon_vs_baseline(all_tconv)
            if p is not None:
                sig = "SIGNIFICANT" if p < 0.05 else "not significant"
                print("  Wilcoxon p     : %.4f  (%s)" % (p, sig))
            else:
                print("  Wilcoxon: scipy not available")
        else:
            print("  Wilcoxon: need n>=3, have %d" % nc)
    else:
        print("  No seeds converged -- check OPES BARRIER param, sim length")
    print("")
    print("  %-12s %10s %12s %14s" % ("Seed", "b_final", "t_conv", "vs WT-MetaD"))
    print("  --------------------------------------------------")
    for sn, v in sorted(per_seed.items()):
        bs = "%.3f" % v["b_final"] if not np.isnan(v["b_final"]) else "nan"
        tc = v["t_conv_ps"]
        if np.isnan(tc):   ts2, vs2 = "no data", "--"
        elif np.isinf(tc): ts2, vs2 = "NOT CONV", "slower"
        else:              ts2 = "%.1f ps" % tc; vs2 = "%.2fx" % (WTMETAD_TCONV / tc)
        sf = " [STALLED]" if v["stalled"] else ""
        print("  %-12s %10s %12s %14s%s" % (sn, bs, ts2, vs2, sf))
    print("")
    print("  Target: barrier = %.2f +/- %.2f kcal/mol, t_conv < %.0f ps" % (
        TARGET_BARRIER, TARGET_TOL, WTMETAD_TCONV))
    if plot: _plot(per_seed, results_dir)
    report = {
        "results_dir": results_dir, "conv_tol_kcal": CONV_TOL,
        "target_barrier": TARGET_BARRIER, "target_tol": TARGET_TOL,
        "wtmetad_tconv_ps": WTMETAD_TCONV, "seeds": per_seed,
        "summary": {
            "n_seeds": ns, "n_stalled": nst, "n_converged": nc,
            "tconv_values": all_tconv,
            "mean_tconv": float(np.mean(all_tconv)) if all_tconv else None,
            "std_tconv":  float(np.std(all_tconv, ddof=0)) if all_tconv else None,
        },
    }
    if out_json is None:
        out_json = os.path.join(results_dir, "convergence_report.json")
    with open(out_json, "w") as f: json.dump(report, f, indent=2)
    print("")
    print("  Saved: %s" % out_json)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="OPES-PIMD convergence analysis")
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--conv-tol", type=float, default=CONV_TOL)
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()
    CONV_TOL = args.conv_tol
    analyze(args.results_dir, plot=args.plot, out_json=args.out_json)
