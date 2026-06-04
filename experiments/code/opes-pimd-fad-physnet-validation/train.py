#!/usr/bin/env python
"""
OPES-PIMD PhysNet FAD validation: OPES vs WT-MetaD comparison.
BARRIER=81.6 kJ/mol, PACE=100, sigma=0.10 Ang fixed, 300 ps x 3 seeds.
Direct head-to-head comparison against wt-metad-pimd-fad-physnet-baseline
(WT-MetaD reference: barrier=3.90 kcal/mol, first TS crossing=163.1 ps).
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


def cv_gradient(pos):
    g = np.zeros_like(pos)
    v12 = pos[IDX_H1] - pos[IDX_O2]; r12 = np.linalg.norm(v12) + 1e-30
    v13 = pos[IDX_H1] - pos[IDX_O3]; r13 = np.linalg.norm(v13) + 1e-30
    u12 = v12 / r12; u13 = v13 / r13
    g[IDX_H1] += u12 - u13
    g[IDX_O2] += -u12
    g[IDX_O3] +=  u13
    v34 = pos[IDX_H3] - pos[IDX_O4]; r34 = np.linalg.norm(v34) + 1e-30
    v31 = pos[IDX_H3] - pos[IDX_O1]; r31 = np.linalg.norm(v31) + 1e-30
    u34 = v34 / r34; u31 = v31 / r31
    g[IDX_H3] += u34 - u31
    g[IDX_O4] += -u34
    g[IDX_O1] +=  u31
    return g


def centroid_cv(bq):
    return compute_cv(bq.mean(0))


def centroid_cv_grad(bq):
    P = bq.shape[0]
    g = cv_gradient(bq.mean(0))
    return np.broadcast_to(g / P, bq.shape).copy()


# -- PIMD (PILE-L thermostat, GPU-accelerated) ----------------------------------
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
        q0 = atoms.positions.copy()
        q_np = np.stack([q0 + self.rng.normal(0, .02, q0.shape) for _ in range(self.P)], 0)
        p_np = self.rng.normal(0, 1, (self.P, self.N, 3)) * np.sqrt(self.m * self.T * KB_KCAL)[None, :, None]
        try:
            import torch
            self._dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._gpu = torch.cuda.is_available()
            self._th  = torch
            dtype = torch.float64
            self._q  = torch.tensor(q_np, dtype=dtype, device=self._dev)
            self._p  = torch.tensor(p_np, dtype=dtype, device=self._dev)
            self._bf = torch.zeros((self.P, self.N, 3), dtype=dtype, device=self._dev)
            self._m_t = torch.tensor(self.m, dtype=dtype, device=self._dev)
        except ImportError:
            self._gpu = False
            self._q_np  = q_np
            self._p_np  = p_np
            self._bf_np = np.zeros((self.P, self.N, 3))
        print(f"[PIMD] device={'GPU (CUDA)' if self._gpu else 'CPU'}")

    @property
    def q(self):
        return self._q.cpu().numpy() if self._gpu else self._q_np

    @property
    def bf(self):
        return self._bf.cpu().numpy() if self._gpu else self._bf_np

    @bf.setter
    def bf(self, v):
        if self._gpu:
            self._bf = self._th.tensor(v, dtype=self._th.float64, device=self._dev)
        else:
            self._bf_np = v

    def _spring(self):
        if self._gpu:
            k = self._m_t[:, None] * (self.P * KB_KCAL * self.T) ** 2 * 0.01
            return -k[None] * (2*self._q - self._q.roll(-1, 0) - self._q.roll(1, 0))
        k = self.m[:, None] * (self.P * KB_KCAL * self.T) ** 2 * 0.01
        f = np.zeros_like(self._q_np)
        for i in range(self.P):
            f[i] = -k * (2*self._q_np[i] - self._q_np[(i+1)%self.P] - self._q_np[(i-1)%self.P])
        return f

    def _phys(self):
        if self._gpu and hasattr(self.ff, "get_forces_batch"):
            return self.ff.get_forces_batch(self._q)      # GPU path: pass CUDA tensor
        if hasattr(self.ff, "get_forces_batch"):
            return self.ff.get_forces_batch(self.q, self.Z)  # CPU path: numpy batch (32x faster)
        f = np.zeros_like(self.q)
        for i in range(self.P):
            f[i] = self.ff.get_forces(self.q[i], self.Z)
        return f

    def step(self):
        if self._gpu:
            th = self._th
            c  = float(np.exp(-self.g * self.dt / 2))
            s  = th.sqrt((1 - c**2) * self._m_t[:, None] * self.T * KB_KCAL)
            f  = self._phys() + self._spring() + self._bf
            self._p = c * self._p + s[None] * th.randn_like(self._p) + f * (self.dt / 2)
            self._q = self._q + self._p / self._m_t[None, :, None] * self.dt
            f2 = self._phys() + self._spring() + self._bf
            self._p = c * (self._p + f2 * (self.dt / 2)) + s[None] * th.randn_like(self._p)
        else:
            c = np.exp(-self.g * self.dt / 2)
            s = np.sqrt((1 - c**2) * self.m[:, None] * self.T * KB_KCAL)
            f = self._phys() + self._spring() + self._bf_np
            self._p_np = c * self._p_np + s[None] * self.rng.normal(0, 1, self._p_np.shape) + f * (self.dt / 2)
            self._q_np += self._p_np / self.m[None, :, None] * self.dt
            f2 = self._phys() + self._spring() + self._bf_np
            self._p_np = c * (self._p_np + f2 * (self.dt / 2)) + s[None] * self.rng.normal(0, 1, self._p_np.shape)


# -- OPES_METAD (Invernizzi & Parrinello, JPCL 2020) ---------------------------
class OPESMetaD:
    def __init__(self, cfg, colvar_path):
        op = cfg["opes"]
        self.pace    = op["pace"]
        self.sigma0  = op["sigma"]
        self.barrier = op["barrier"] * KCAL_PER_KJ   # kJ/mol -> kcal/mol
        self.T       = cfg["pimd"]["temperature"]
        self.cv_min  = op["cv_min"]
        self.cv_max  = op["cv_max"]
        self.bins    = op["cv_bins"]
        self.gamma   = 1 + self.barrier / (KB_KCAL * self.T)
        self.kT      = KB_KCAL * self.T
        self._bw     = self.sigma0
        self._samples       = []
        self._sample_biases = []
        self._Z             = 1.0
        self._fh = open(colvar_path, "w", encoding="utf-8")
        self._fh.write("# step t_ps cv bias_kcal\n")

    def _kde(self, cv):
        if not self._samples:
            return 1.0
        s = np.array(self._samples)
        return float(np.sum(np.exp(-0.5 * ((cv - s) / self._bw) ** 2)) /
                     (len(s) * self._bw * np.sqrt(2 * np.pi)))

    def _kde_grad(self, cv):
        if not self._samples:
            return 0.0
        s = np.array(self._samples)
        gauss = np.exp(-0.5 * ((cv - s) / self._bw) ** 2)
        return float(np.sum(gauss * (-(cv - s) / self._bw**2)) /
                     (len(s) * self._bw * np.sqrt(2 * np.pi)))

    def bias_e(self, cv):
        p = self._kde(cv)
        if p <= 0:
            return self.barrier
        v = -self.kT * (self.gamma / (self.gamma - 1)) * np.log(max(p, 1e-300))
        v = v + self.kT * (self.gamma / (self.gamma - 1)) * np.log(max(self._Z, 1e-300))
        return float(np.clip(v, 0, self.barrier))

    def _bias_grad_scalar(self, cv):
        be = self.bias_e(cv)
        if not self._samples:
            return 0.0, 0.0
        p  = self._kde(cv)
        dp = self._kde_grad(cv)
        if p <= 1e-300:
            dVdcv = 0.0
        else:
            dVdcv = -self.kT * (self.gamma / (self.gamma - 1)) * dp / p
        if be >= self.barrier * 0.99:
            dVdcv = 0.0
        return dVdcv, be

    def update(self, step, cv):
        if step % self.pace == 0:
            self._sample_biases.append(self.bias_e(cv))
            self._samples.append(cv)
            if len(self._samples) > 1:
                new_z = float(np.max([self._kde(s) for s in self._samples[-20:]]))
                self._Z = max(self._Z, new_z)

    def record_colvar(self, step, cv, be):
        self._fh.write(f"{step} {step*0.5e-3:.4f} {cv:.6f} {be:.6f}\n")

    def forces(self, bq):
        cv = centroid_cv(bq)
        dVdcv, be = self._bias_grad_scalar(cv)
        if not self._samples:
            return np.zeros_like(bq), cv, 0.0
        return -dVdcv * centroid_cv_grad(bq), cv, be

    def forces_gpu(self, q_gpu):
        import torch
        P   = q_gpu.shape[0]
        dev = q_gpu.device
        cen = q_gpu.mean(0)
        v12 = cen[IDX_H1] - cen[IDX_O2]; v13 = cen[IDX_H1] - cen[IDX_O3]
        v34 = cen[IDX_H3] - cen[IDX_O4]; v31 = cen[IDX_H3] - cen[IDX_O1]
        cv  = float((v12.norm() - v13.norm()) + (v34.norm() - v31.norm()))
        dVdcv, be = self._bias_grad_scalar(cv)
        if not self._samples or dVdcv == 0.0:
            return torch.zeros_like(q_gpu), cv, be
        g = torch.zeros((q_gpu.shape[1], 3), dtype=q_gpu.dtype, device=dev)
        u12 = v12 / v12.norm().clamp(min=1e-30); u13 = v13 / v13.norm().clamp(min=1e-30)
        u34 = v34 / v34.norm().clamp(min=1e-30); u31 = v31 / v31.norm().clamp(min=1e-30)
        g[IDX_H1] = u12 - u13; g[IDX_O2] = -u12; g[IDX_O3] = u13
        g[IDX_H3] = u34 - u31; g[IDX_O4] = -u34; g[IDX_O1] = u31
        bf = g.unsqueeze(0).expand(P, -1, -1) * (-dVdcv / P)
        return bf, cv, be

    def fes_reweight(self):
        grid = np.linspace(self.cv_min, self.cv_max, self.bins)
        if not self._samples:
            return grid, np.zeros(self.bins)
        s = np.array(self._samples)
        weights = np.exp(-np.array(self._sample_biases) / self.kT)
        fval = np.zeros(self.bins)
        bw = self._bw
        for i, cv in enumerate(grid):
            g = np.exp(-0.5 * ((cv - s) / bw) ** 2)
            fval[i] = np.sum(g * weights) / (len(s) * bw * np.sqrt(2 * np.pi))
        fval = np.where(fval > 0, -self.kT * np.log(fval), np.nan)
        fval -= np.nanmin(fval)
        return grid, fval

    def close(self):
        self._fh.close()


def extract_barrier(grid, fes):
    valid = ~np.isnan(fes)
    if valid.sum() < 10:
        return float("nan")
    mid = len(grid) // 2
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


def main():
    ap = argparse.ArgumentParser(description="OPES-PIMD PhysNet FAD validation")
    ap.add_argument("--config",  default="config.yaml")
    ap.add_argument("--sanity",  action="store_true")
    ap.add_argument("--seed",    type=int, default=None)
    ap.add_argument("--out-dir", default="results_physnet")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.seed is not None:
        cfg["pimd"]["seed"] = args.seed
    seed = cfg["pimd"]["seed"]

    out_dir = os.path.join(os.path.dirname(os.path.abspath(args.config)), args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    colvar_path = os.path.join(out_dir, f"colvar_seed{seed}.dat")
    n = cfg["sanity"]["n_steps"] if args.sanity else cfg["pimd"]["n_steps"]
    checkpoint_interval = 100000   # 50 ps

    # Load PhysNetFF via load_ff (resolves physnet_base relative to force_fields.py location)
    mlff_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "..", "mlff-pimd-fad-barrier-comparison"))
    if mlff_dir not in sys.path:
        sys.path.insert(0, mlff_dir)
    from force_fields import load_ff
    ff = load_ff("physnet", cfg)

    atoms = make_fad()
    pimd  = PIMD(atoms, cfg, ff)
    opes  = OPESMetaD(cfg, colvar_path)

    cv0 = centroid_cv(pimd.q)
    print(f"[init/FRESH] seed={seed}  CV0={cv0:.4f} Ang  steps={n}  sim={n*0.5e-3:.1f}ps  T={cfg['pimd']['temperature']}K")
    print(f"[init] BARRIER={cfg['opes']['barrier']:.1f} kJ/mol  pace={cfg['opes']['pace']}  sigma={cfg['opes']['sigma']}  gamma={opes.gamma:.1f}")

    cv_max = cv0
    first_ts_step = None
    barrier_history = []
    t0 = time.time()

    for step in range(n):
        if pimd._gpu:
            bf, cv, be = opes.forces_gpu(pimd._q)
            pimd._bf = bf
        else:
            bf, cv, be = opes.forces(pimd.q)
            pimd.bf = bf
        pimd.step()
        opes.update(step, cv)

        if step % cfg["output"]["colvar_stride"] == 0:
            opes.record_colvar(step, cv, be)

        if cv > cv_max:
            cv_max = cv
        if first_ts_step is None and cv > 0.0:
            first_ts_step = step
            print(f"*** TS CROSSING at step {step}  t={step*0.5e-3:.1f}ps  cv={cv:+.4f} ***")

        if step % 10000 == 0 and step > 0:
            spd = step / (time.time() - t0) * 86400 / 1e6
            g, fv = opes.fes_reweight()
            b = extract_barrier(g, fv)
            print(f"step {step:7d}  t={step*0.5e-3:.1f}ps  cv={cv:+.3f}  cv_max={cv_max:+.3f}  "
                  f"barrier={b:.2f} kcal/mol  {spd:.2f}M/day")

        if step % checkpoint_interval == 0 and step > 0:
            g, fv = opes.fes_reweight()
            b = extract_barrier(g, fv)
            t_ps = step * 0.5e-3
            barrier_history.append((t_ps, b))
            print(f"[checkpoint] t={t_ps:.0f}ps  barrier={b:.4f} kcal/mol  cv_max={cv_max:+.4f}  "
                  f"ts_crossed={'YES' if first_ts_step is not None else 'NO'}")

    opes.close()

    g, fv = opes.fes_reweight()
    b     = extract_barrier(g, fv)
    spd   = n / (time.time() - t0) * 86400 / 1e6
    first_ts_ps = first_ts_step * 0.5e-3 if first_ts_step is not None else None

    converged = False
    convergence_time_ps = None
    if len(barrier_history) >= 3:
        recent = [bh[1] for bh in barrier_history[-3:] if not np.isnan(bh[1])]
        if len(recent) == 3 and max(recent) - min(recent) < 0.2:
            converged = True
            convergence_time_ps = barrier_history[-3][0]

    print(f"\n=== RESULTS (PhysNet OPES, seed={seed}) ===")
    print(f"Barrier          : {b:.4f} kcal/mol")
    if first_ts_ps is not None:
        print(f"First TS crossing: {first_ts_ps:.1f} ps  (WT-MetaD ref: 163.1 ps)")
    else:
        print(f"First TS crossing: NONE (cv_max={cv_max:+.4f})")
    print(f"Converged        : {converged}  (convergence_time={convergence_time_ps} ps)")
    print(f"Speed (this run) : {spd:.2f} M steps/day  (WT-MetaD ref: 0.97)")
    print(f"Total sim time   : {n * 0.5e-3:.1f} ps")

    res = {
        "ff":                   "physnet",
        "method":               "opes",
        "seed":                 seed,
        "barrier_kcal_mol":     b,
        "first_ts_crossing_ps": first_ts_ps,
        "ts_crossed":           first_ts_step is not None,
        "cv_max_ang":           float(cv_max),
        "convergence_time_ps":  convergence_time_ps,
        "converged":            converged,
        "speed_M_steps_day":    spd,
        "n_steps":              n,
        "sim_time_ps":          n * 0.5e-3,
        "barrier_history":      [[t, bv] for t, bv in barrier_history],
        "fes_cv":               g.tolist(),
        "fes_kcal_mol":         [float(x) if not np.isnan(x) else None for x in fv],
        "wt_metad_ref":         {"barrier_kcal_mol": 3.90, "first_ts_crossing_ps": 163.1},
    }
    rp = os.path.join(out_dir, f"seed_{seed}.json")
    with open(rp, "w", encoding="utf-8") as fj:
        json.dump(res, fj, indent=2)
    print(f"Saved: {rp}")

    if args.sanity:
        print(f"[sanity] PhysNet load OK | CV0={cv0:.4f} | PIMD+OPES step OK | sanity PASSED")


if __name__ == "__main__":
    main()
