#!/usr/bin/env python
"""
WT-MetaD PIMD baseline on PhysNet FAD: aggressive settings to overcome unknown barrier.
h=3 kJ/mol, biasfactor=50, PACE=200, 300 ps x 3 seeds.
Establishes reference barrier for OPES vs WT-MetaD comparison (opes-pimd-fad-physnet-validation).
"""
import argparse, json, os, sys, time
import numpy as np
import yaml

KCAL_PER_KJ = 0.239006
KB_KCAL     = 1.987204e-3   # kcal/(mol*K)

# Atom order: H1(0) C1(1) O1(2) O2(3) H2(4) H3(5) C2(6) O3(7) O4(8) H4(9)
IDX_H1, IDX_O2, IDX_O3 = 0, 3, 7
IDX_H3, IDX_O4, IDX_O1 = 5, 8, 2


def make_fad():
    from ase import Atoms
    pos = np.array([
        [ 0.990,  0.000, 0.000],
        [-0.423,  1.272, 0.000],
        [ 0.285,  2.253, 0.000],
        [ 0.000,  0.000, 0.000],
        [-1.520,  1.217, 0.000],
        [ 2.015,  2.254, 0.000],
        [ 3.427,  0.982, 0.000],
        [ 2.720,  0.000, 0.000],
        [ 3.005,  2.254, 0.000],
        [ 4.524,  1.037, 0.000],
    ])
    return Atoms(symbols="HCOOHHCOOH", positions=pos)


def compute_cv(pos):
    d1 = np.linalg.norm(pos[IDX_H1] - pos[IDX_O2])
    d2 = np.linalg.norm(pos[IDX_H1] - pos[IDX_O3])
    d3 = np.linalg.norm(pos[IDX_H3] - pos[IDX_O4])
    d4 = np.linalg.norm(pos[IDX_H3] - pos[IDX_O1])
    return (d1 - d2) + (d3 - d4)


def cv_gradient(pos, eps=1e-4):
    g = np.zeros_like(pos)
    for i in range(pos.shape[0]):
        for j in range(3):
            pp = pos.copy(); pp[i, j] += eps
            pm = pos.copy(); pm[i, j] -= eps
            g[i, j] = (compute_cv(pp) - compute_cv(pm)) / (2 * eps)
    return g


def centroid_cv(bq):
    return compute_cv(bq.mean(0))


def centroid_cv_grad(bq, eps=1e-4):
    P = bq.shape[0]
    g = cv_gradient(bq.mean(0), eps)
    return np.stack([g / P] * P, 0)


class PIMD:
    def __init__(self, atoms, cfg, ff):
        self.P   = cfg["pimd"]["n_beads"]
        self.T   = cfg["pimd"]["temperature"]
        self.dt  = cfg["pimd"]["timestep"] * 1e-3
        self.g   = cfg["pimd"]["friction"]
        self.ff  = ff
        self.rng = np.random.default_rng(cfg["pimd"]["seed"])
        self.m   = ff.masses
        self.Z   = ff.numbers
        self.N   = len(self.m)
        q0       = atoms.positions.copy()
        self.q   = np.stack([q0 + self.rng.normal(0, .02, q0.shape) for _ in range(self.P)], 0)
        self.p   = self.rng.normal(0, 1, (self.P, self.N, 3)) * np.sqrt(self.m * self.T * KB_KCAL)[None, :, None]
        self.bf  = np.zeros((self.P, self.N, 3))

    def _spring(self):
        k = self.m[:, None] * (self.P * KB_KCAL * self.T) ** 2 * 0.01
        f = np.zeros_like(self.q)
        for i in range(self.P):
            f[i] = -k * (2 * self.q[i] - self.q[(i+1) % self.P] - self.q[(i-1) % self.P])
        return f

    def _phys(self):
        if hasattr(self.ff, "get_forces_batch"):
            return self.ff.get_forces_batch(self.q, self.Z)
        f = np.zeros_like(self.q)
        for i in range(self.P):
            f[i] = self.ff.get_forces(self.q[i], self.Z)
        return f

    def step(self):
        c = np.exp(-self.g * self.dt / 2)
        s = np.sqrt((1 - c**2) * self.m[:, None] * self.T * KB_KCAL)
        f = self._phys() + self._spring() + self.bf
        self.p = c * self.p + s[None] * self.rng.normal(0, 1, self.p.shape) + f * (self.dt / 2)
        self.q += self.p / self.m[None, :, None] * self.dt
        f2 = self._phys() + self._spring() + self.bf
        self.p = c * (self.p + f2 * (self.dt / 2)) + s[None] * self.rng.normal(0, 1, self.p.shape)


class WTMetaD:
    def __init__(self, cfg, resume=False):
        wt          = cfg["wt_metad"]
        self.h      = wt["height"] * KCAL_PER_KJ
        self.s      = wt["sigma"]
        self.gam    = wt["biasfactor"]
        self.stride = wt["stride"]
        self.T      = cfg["pimd"]["temperature"]
        self.kT     = KB_KCAL * self.T
        self.cv_min = wt["cv_min"]
        self.cv_max = wt["cv_max"]
        self.bins   = wt["cv_bins"]
        self.hs, self.hc = [], []
        self._sample_cvs    = []
        self._sample_biases = []
        mode = "a" if resume else "w"
        self.fh = open(cfg["output"]["hills_file"], mode, encoding="utf-8")
        if not resume:
            self.fh.write("# step cv h sig\n")

    def load_hills(self, hills_file):
        """Restore accumulated hills from a previous run for warm-start resume."""
        loaded = 0
        with open(hills_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split()
                if len(parts) < 4:
                    continue
                self.hc.append(float(parts[1]))
                self.hs.append(float(parts[2]))
                loaded += 1
        print(f"[resume] loaded {loaded} hills from {hills_file}")

    def bias_e(self, cv):
        if not self.hc:
            return 0.0
        c = np.array(self.hc); h = np.array(self.hs)
        return float(np.sum(h * np.exp(-0.5 * ((cv - c) / self.s) ** 2)))

    def update(self, step, cv, step_offset=0):
        if step % self.stride:
            return
        be = self.bias_e(cv)
        w  = self.h * np.exp(-be / (KB_KCAL * self.T * (self.gam - 1)))
        self.hc.append(cv); self.hs.append(w)
        self.fh.write(f"{step + step_offset} {cv:.6f} {w:.6f} {self.s:.4f}\n")
        self.fh.flush()

    def forces(self, bq):
        cv = centroid_cv(bq)
        be = self.bias_e(cv)
        if not self.hc:
            return np.zeros_like(bq), cv, 0.0
        c = np.array(self.hc); h = np.array(self.hs)
        gauss  = h * np.exp(-0.5 * ((cv - c) / self.s) ** 2)
        dVdcv  = float(np.sum(gauss * (-(cv - c) / self.s ** 2)))
        return -dVdcv * centroid_cv_grad(bq), cv, be

    def record_sample(self, cv, be):
        self._sample_cvs.append(cv)
        self._sample_biases.append(be)

    def fes_reweight(self):
        if len(self._sample_cvs) < 10:
            return self._fes_hills()
        cvs     = np.array(self._sample_cvs)
        biases  = np.array(self._sample_biases)
        weights = np.exp(-biases / self.kT)
        weights /= weights.sum()
        grid = np.linspace(self.cv_min, self.cv_max, self.bins)
        bw   = self.s * 2
        kde  = np.array([np.sum(weights * np.exp(-0.5 * ((g - cvs) / bw) ** 2))
                         for g in grid])
        kde  = np.maximum(kde, 1e-300)
        fval = -self.kT * np.log(kde)
        fval -= fval.min()
        return grid, fval

    def _fes_hills(self):
        grid = np.linspace(self.cv_min, self.cv_max, self.bins)
        fval = np.zeros(self.bins)
        if self.hc:
            c = np.array(self.hc); h = np.array(self.hs)
            for i, cv in enumerate(grid):
                fval[i] = np.sum(h * np.exp(-0.5 * ((cv - c) / self.s) ** 2))
        fval = -fval * (self.gam / (self.gam - 1))
        fval -= fval.min()
        return grid, fval

    def close(self):
        self.fh.close()


def extract_barrier(grid, fes):
    mid = len(grid) // 2
    if mid < 2:
        return float("nan")
    l  = int(np.argmin(fes[:mid]))
    r  = mid + int(np.argmin(fes[mid:]))
    if l >= r:
        return float("nan")
    ts = l + int(np.argmax(fes[l:r]))
    return float(fes[ts] - fes[l])


def _read_step_offset(colvar_path):
    """Return the last step number recorded in an existing colvar file, or 0."""
    last_step = 0
    try:
        with open(colvar_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                try:
                    last_step = int(line.split()[0])
                except (ValueError, IndexError):
                    pass
    except FileNotFoundError:
        pass
    return last_step


def main():
    ap = argparse.ArgumentParser(description="WT-MetaD PIMD PhysNet baseline: aggressive settings")
    ap.add_argument("--config",   default="config.yaml")
    ap.add_argument("--sanity",   action="store_true")
    ap.add_argument("--seed",     type=int, default=None)
    ap.add_argument("--out-dir",  default="results_physnet")
    ap.add_argument("--resume",   action="store_true",
                    help="Warm-start: load existing hills, append to output files, run remaining steps")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.seed is not None:
        cfg["pimd"]["seed"] = args.seed
    seed = cfg["pimd"]["seed"]

    out_dir = os.path.join(os.path.dirname(os.path.abspath(args.config)), args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    hills_path  = os.path.join(out_dir, f"hills_seed{seed}.dat")
    colvar_path = os.path.join(out_dir, f"colvar_seed{seed}.dat")
    cfg["output"]["hills_file"] = hills_path

    # Determine step offset and remaining steps for resume mode
    step_offset = 0
    if args.resume:
        step_offset = _read_step_offset(colvar_path)
        print(f"[resume] detected step_offset={step_offset}  ({step_offset * 0.5e-3:.2f} ps already done)")

    # Import PhysNetFF from the mlff experiment directory
    mlff_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "..", "mlff-pimd-fad-barrier-comparison"))
    if mlff_dir not in sys.path:
        sys.path.insert(0, mlff_dir)
    from force_fields import load_ff
    ff = load_ff("physnet", cfg)

    total_n = cfg["sanity"]["n_steps"] if args.sanity else cfg["pimd"]["n_steps"]
    n       = total_n - step_offset  # remaining steps
    if n <= 0:
        print(f"[resume] already completed {step_offset} / {total_n} steps — nothing to do.")
        return

    atoms = make_fad()
    pimd  = PIMD(atoms, cfg, ff)
    metad = WTMetaD(cfg, resume=args.resume)

    if args.resume and os.path.exists(hills_path):
        metad.load_hills(hills_path)

    cv0 = centroid_cv(pimd.q)
    mode_tag = "RESUME" if args.resume else "FRESH"
    print(f"[init/{mode_tag}] seed={seed}  CV0={cv0:.4f} Ang  steps_remaining={n}  "
          f"sim_remaining={n*0.5e-3:.1f}ps  T={cfg['pimd']['temperature']}K")
    print(f"[init] h={cfg['wt_metad']['height']} kJ/mol  biasfactor={cfg['wt_metad']['biasfactor']}  "
          f"sigma={cfg['wt_metad']['sigma']}  PACE={cfg['wt_metad']['stride']}")

    col_mode = "a" if args.resume else "w"
    col = open(colvar_path, col_mode, encoding="utf-8")
    if not args.resume:
        col.write("# step t_ps cv bias_e\n")
    t0 = time.time()

    checkpoint_interval = 100000  # 50 ps at 0.5 fs/step
    barrier_history     = []
    first_ts_step       = None
    cv_max              = cv0

    for step in range(n):
        bf, cv, be = metad.forces(pimd.q)
        pimd.bf = bf
        pimd.step()
        metad.update(step, cv, step_offset=step_offset)

        global_step = step + step_offset
        if step % cfg["output"]["colvar_stride"] == 0:
            col.write(f"{global_step} {global_step * 0.5e-3:.4f} {cv:.6f} {be:.6f}\n")
            metad.record_sample(cv, be)

        if cv > cv_max:
            cv_max = cv
        if first_ts_step is None and cv > 0.0:
            first_ts_step = global_step
            print(f"*** TS CROSSING at step {global_step}  t={global_step*0.5e-3:.1f}ps  cv={cv:+.4f} ***")

        if step % 10000 == 0 and step > 0:
            spd = step / (time.time() - t0) * 86400 / 1e6
            g, fv = metad.fes_reweight()
            b = extract_barrier(g, fv)
            print(f"step {global_step:7d}  t={global_step*0.5e-3:.1f}ps  cv={cv:+.3f}  cv_max={cv_max:+.3f}  "
                  f"barrier={b:.2f} kcal/mol  {spd:.2f}M/day")

        if step % checkpoint_interval == 0 and step > 0:
            g, fv = metad.fes_reweight()
            b = extract_barrier(g, fv)
            t_ps = global_step * 0.5e-3
            barrier_history.append((t_ps, b))
            print(f"[checkpoint] t={t_ps:.0f}ps  barrier={b:.4f} kcal/mol  cv_max={cv_max:+.4f}  "
                  f"ts_crossed={'YES' if first_ts_step is not None else 'NO'}")

    col.close()
    metad.close()

    g, fv = metad.fes_reweight()
    b     = extract_barrier(g, fv)
    spd   = n / (time.time() - t0) * 86400 / 1e6
    total_steps_done = step_offset + n

    first_ts_ps = first_ts_step * 0.5e-3 if first_ts_step is not None else None

    converged = False
    convergence_time_ps = None
    if len(barrier_history) >= 3:
        recent = [bh[1] for bh in barrier_history[-3:] if not np.isnan(bh[1])]
        if len(recent) == 3 and max(recent) - min(recent) < 0.2:
            converged = True
            convergence_time_ps = barrier_history[-3][0]

    print(f"\n=== RESULTS (PhysNet WT-MetaD, seed={seed}) ===")
    print(f"Barrier          : {b:.4f} kcal/mol")
    if first_ts_ps is not None:
        print(f"First TS crossing: {first_ts_ps:.1f} ps")
    else:
        print(f"First TS crossing: NONE (cv_max={cv_max:+.4f})")
    print(f"Converged        : {converged}  (convergence_time={convergence_time_ps} ps)")
    print(f"Speed (this run) : {spd:.2f} M steps/day")
    print(f"Total sim time   : {total_steps_done * 0.5e-3:.1f} ps / {total_n * 0.5e-3:.1f} ps planned")

    res = {
        "ff":                   "physnet",
        "seed":                 seed,
        "barrier_kcal_mol":     b,
        "first_ts_crossing_ps": first_ts_ps,
        "ts_crossed":           first_ts_step is not None,
        "cv_max_ang":           float(cv_max),
        "convergence_time_ps":  convergence_time_ps,
        "converged":            converged,
        "speed_M_steps_day":    spd,
        "n_steps":              total_steps_done,
        "sim_time_ps":          total_steps_done * 0.5e-3,
        "barrier_history":      [[t, bv] for t, bv in barrier_history],
        "fes_cv":               g.tolist(),
        "fes_kcal_mol":         fv.tolist(),
    }
    rp = os.path.join(out_dir, f"seed_{seed}.json")
    with open(rp, "w", encoding="utf-8") as fj:
        json.dump(res, fj, indent=2)
    print(f"Saved: {rp}")

    if args.sanity:
        print(f"[sanity] PhysNet load OK | CV0={cv0:.4f} | PIMD step OK | sanity PASSED")


if __name__ == "__main__":
    main()
