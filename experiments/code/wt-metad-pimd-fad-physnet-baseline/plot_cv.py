"""Plot CV(t) for all completed/running seeds in results_physnet/."""
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results_physnet")
TS_CV       = 0.0
BASIN_CV    = -1.5

SEED_COLORS = {42: "#1f77b4", 123: "#ff7f0e", 7: "#2ca02c"}

def load_colvar(path):
    steps, t_ps, cv, bias = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            steps.append(int(parts[0]))
            t_ps.append(float(parts[1]))
            cv.append(float(parts[2]))
            if len(parts) >= 4:
                bias.append(float(parts[3]))
    return np.array(t_ps), np.array(cv), np.array(bias) if bias else None


def main():
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "colvar_seed*.dat")))
    if not files:
        print("No colvar files found in", RESULTS_DIR)
        return

    fig, axes = plt.subplots(
        len(files), 1,
        figsize=(12, 3.5 * len(files)),
        sharex=False,
        squeeze=False,
    )

    for ax_row, path in zip(axes, files):
        ax = ax_row[0]
        seed = int(os.path.basename(path).replace("colvar_seed", "").replace(".dat", ""))
        t, cv, _ = load_colvar(path)

        color = SEED_COLORS.get(seed, "steelblue")
        ax.plot(t, cv, lw=0.6, color=color, alpha=0.85, label=f"seed {seed}")

        # Reference lines
        ax.axhline(TS_CV,   color="red",    lw=1.2, ls="--", label="TS (CV=0)")
        ax.axhline(BASIN_CV, color="gray",  lw=0.8, ls=":",  label="reactant basin")
        ax.axhline(-BASIN_CV, color="gray", lw=0.8, ls=":",  label="product basin")

        # Annotate max CV reached
        cv_max = cv.max()
        t_max  = t[cv.argmax()]
        ax.scatter([t_max], [cv_max], color="red", s=30, zorder=5)
        ax.annotate(f"cv_max={cv_max:+.3f} Å\nt={t_max:.1f} ps",
                    xy=(t_max, cv_max), xytext=(8, 6),
                    textcoords="offset points", fontsize=8, color="red")

        status = "complete" if t[-1] >= 299.5 else f"running ({t[-1]:.1f} ps)"
        ax.set_title(f"Seed {seed}  —  {status}", fontsize=11, fontweight="bold")
        ax.set_ylabel("CV (Å)", fontsize=10)
        ax.set_xlim(0, max(t[-1] * 1.02, 5))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.grid(True, which="major", alpha=0.3)
        ax.grid(True, which="minor", alpha=0.1)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.7)

    axes[-1][0].set_xlabel("Simulation time (ps)", fontsize=10)
    fig.suptitle("WT-MetaD PIMD — PhysNet FAD  |  CVdimer vs time", fontsize=13, y=1.01)
    fig.tight_layout()

    out = os.path.join(RESULTS_DIR, "cv_vs_time.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.show()


if __name__ == "__main__":
    main()
