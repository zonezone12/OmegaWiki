#!/usr/bin/env python
"""
MLFF comparison: PIMD + WT-MetaD on FAD proton transfer.
Supports --ff physnet | ani2x | xtb2.
FES via exp(-bias/kT) reweighting, same as WT-MetaD v3.
"""
import argparse, json, os, sys, time
import numpy as np
import yaml

# -- constants ------------------------------------------------------------------
KCAL_PER_KJ = 0.239006
KB_KCAL = 1.987204e-3   # kcal/(mol*K)

# -- CV atom indices (0-based) --------------------------------------------------
# Atom order: H1(0) C1(1) O1(2) O2(3) H2(4) H3(5) C2(6) O3(7) O4(8) H4(9)
# CVdimer = (d_O2H1 - d_O3H1) + (d_O4H3 - d_O1H3)
IDX_H1, IDX_O2, IDX_O3 = 0, 3, 7
IDX_H3, IDX_O4, IDX_O1 = 5, 8, 2


def make_fad():
    """
    C2h FAD: r_OH=0.990, r_OO=2.720 Ang. Inversion center at (1.502, 1.127, 0).
    H-bond 1: O2(idx3)-H1(idx0)...O3(idx7)  r_O2H1=0.990, r_H1O3=1.730
    H-bond 2: O4(idx8)-H3(idx5)...O1(idx2)  r_O4H3=0.990, r_H3O1=1.730
    """
    from ase import Atoms
    pos = np.array([
        [ 0.990,  0.000, 0.000],  # H1(0) transferring, covalent to O2
        [-0.423,  1.272, 0.000],  # C1(1)
        [ 0.285,  2.253, 0.000],  # O1(2) carbonyl mol1, acceptor for H3
        [ 0.000,  0.000, 0.000],  # O2(3) hydroxyl mol1, donor for H1
        [-1.520,  1.217, 0.000],  # H2(4) formyl H mol1
        [ 2.015,  2.254, 0.000],  # H3(5) transferring, covalent to O4
        [ 3.427,  0.982, 0.000],  # C2(6)
        [ 2.720,  0.000, 0.000],  # O3(7) carbonyl mol2, acceptor for H1
        [ 3.005,  2.254, 0.000],  # O4(8) hydroxyl mol2, donor for H3
        [ 4.524,  1.037, 0.000],  # H4(9) formyl H mol2
    ])
    return Atoms(symbols="HCOOHHCOOH", positions=pos)


def compute_cv(pos):
    """CVdimer = (d_O2H1 - d_O3H1) + (d_O4H3 - d_O1H3)."""
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
    return np.stack([g / P] * P, 0)  # chain rule: d(CV_centroid)/d(q_k) = (1/P)*grad


# -- Fallback FF: double-well in (r_donor - r_acceptor) space + harmonic frame --
# V_DW(s) = A*(s^2 - s0^2)^2  where s = r_donor - r_acceptor
# V_conf(t) = k_c*(t - R_OO)^2  where t = r_donor + r_acceptor  (keeps H on O-O axis)
# Classical barrier = 2 * A * s0^4 = 4.53 kcal/mol (per-pair, factor 2 for concerted)
# s0 = 0.99 - 1.73 = 0.74 Ang; A = 4.53 / (2*0.74^4) = 7.57 kcal/(mol*Ang^4)
_FAD_EQ = np.array([
    [ 0.990,  0.000, 0.000],  # H1
    [-0.423,  1.272, 0.000],  # C1
    [ 0.285,  2.253, 0.000],  # O1
    [ 0.000,  0.000, 0.000],  # O2
    [-1.520,  1.217, 0.000],  # H2
    [ 2.015,  2.254, 0.000],  # H3
    [ 3.427,  0.982, 0.000],  # C2
    [ 2.720,  0.000, 0.000],  # O3
    [ 3.005,  2.254, 0.000],  # O4
    [ 4.524,  1.037, 0.000],  # H4
])

class FallbackFF:
    masses  = np.array([1, 12, 16, 16, 1, 1, 12, 16, 16, 1], dtype=float)
    numbers = np.array([1,  6,  8,  8, 1, 1,  6,  8,  8, 1])
    EQ      = _FAD_EQ.copy()
    # double-well params (calibrated to give classical barrier ~4.53 kcal/mol)
    _s0 = 0.74   # equilibrium |r_donor - r_acceptor|  (Ang)
    _A  = 7.57   # kcal/(mol*Ang^4)
    _kc = 60.0   # confinement  kcal/(mol*Ang^2)
    _kh = 50.0   # heavy-atom harmonic  kcal/(mol*Ang^2)

    def _dw_force(self, pos, h_idx, d_idx, a_idx):
        """Double-well + confinement forces on (H, donor, acceptor) triplet."""
        r1v = pos[h_idx] - pos[d_idx]
        r2v = pos[h_idx] - pos[a_idx]
        r1  = np.linalg.norm(r1v) + 1e-12
        r2  = np.linalg.norm(r2v) + 1e-12
        s   = r1 - r2    # double-well coordinate
        t   = r1 + r2    # confinement coordinate

        # R_OO from current positions (not frozen, allows breathing)
        R_OO = np.linalg.norm(pos[a_idx] - pos[d_idx]) + 1e-12

        # double-well gradient: dV/ds = 4*A*s*(s^2 - s0^2)
        dVds = 4 * self._A * s * (s**2 - self._s0**2)
        # confinement: dV/dt = 2*k_c*(t - R_OO)
        dVdt = 2 * self._kc * (t - R_OO)

        # chain rule: d(r1)/d(pos_H) = r1v/r1;  d(r2)/d(pos_H) = r2v/r2
        dr1_dH =  r1v / r1
        dr2_dH =  r2v / r2

        # d(s)/d(H) = dr1/dH - dr2/dH;  d(t)/d(H) = dr1/dH + dr2/dH
        f_H  = -(dVds * (dr1_dH - dr2_dH) + dVdt * (dr1_dH + dr2_dH))
        f_D  = -(dVds * (-dr1_dH) + dVdt * (-dr1_dH))
        f_A  = -(dVds * ( dr2_dH) + dVdt * ( dr2_dH))
        return f_H, f_D, f_A

    def get_forces(self, pos, _):
        f = np.zeros((10, 3))
        # proton pair 1: H1 between O2 (donor) and O3 (acceptor)
        fH, fD, fA = self._dw_force(pos, IDX_H1, IDX_O2, IDX_O3)
        f[IDX_H1] += fH; f[IDX_O2] += fD; f[IDX_O3] += fA
        # proton pair 2: H3 between O4 (donor) and O1 (acceptor)
        fH, fD, fA = self._dw_force(pos, IDX_H3, IDX_O4, IDX_O1)
        f[IDX_H3] += fH; f[IDX_O4] += fD; f[IDX_O1] += fA
        # harmonic restraints on heavy + non-transferring atoms
        for i in [1, 2, 3, 4, 6, 7, 8, 9]:
            f[i] += -self._kh * (pos[i] - self.EQ[i])
        return f


# -- GFN force field wrapper ----------------------------------------------------
class GFNForceField:
    def __init__(self, ckpt):
        self._fb = FallbackFF()
        self.masses = self._fb.masses
        self.numbers = self._fb.numbers
        self._m = None
        if os.path.exists(ckpt):
            try:
                import torch
                self._m = torch.load(ckpt, map_location="cpu")
                print(f"[GFN] loaded {ckpt}")
            except Exception as e:
                print(f"[GFN] load failed ({e}), using fallback FF")
        else:
            print(f"[GFN] checkpoint not found ({ckpt}), using fallback FF")

    def get_forces(self, pos, numbers):
        if self._m is None:
            return self._fb.get_forces(pos, numbers)
        raise NotImplementedError("GFN inference requires MindSPONGE runtime")


# -- Ring-polymer PIMD (PILE-L thermostat) -------------------------------------
class PIMD:
    def __init__(self, atoms, cfg, ff):
        self.P  = cfg["pimd"]["n_beads"]
        self.T  = cfg["pimd"]["temperature"]
        self.dt = cfg["pimd"]["timestep"] * 1e-3   # fs -> ps
        self.g  = cfg["pimd"]["friction"]
        self.ff = ff
        self.rng = np.random.default_rng(cfg["pimd"]["seed"])
        self.m   = ff.masses
        self.Z   = ff.numbers
        self.N   = len(self.m)
        q0 = atoms.positions.copy()
        self.q = np.stack([q0 + self.rng.normal(0, .02, q0.shape) for _ in range(self.P)], 0)
        self.p = self.rng.normal(0, 1, (self.P, self.N, 3)) * np.sqrt(self.m * self.T * KB_KCAL)[None, :, None]
        self.bf = np.zeros((self.P, self.N, 3))

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


# -- Well-tempered metadynamics -------------------------------------------------
class WTMetaD:
    def __init__(self, cfg):
        wt = cfg["wt_metad"]
        self.h   = wt["height"] * KCAL_PER_KJ
        self.s   = wt["sigma"]
        self.gam = wt["biasfactor"]
        self.stride = wt["stride"]
        self.T   = cfg["pimd"]["temperature"]
        self.kT  = KB_KCAL * self.T
        self.cv_min = wt["cv_min"]
        self.cv_max = wt["cv_max"]
        self.bins   = wt["cv_bins"]
        self.hs, self.hc = [], []
        self._sample_cvs    = []  # trajectory samples for exp(-bias/kT) reweighting
        self._sample_biases = []
        self.fh = open(cfg["output"]["hills_file"], "w")
        self.fh.write("# step cv h sig\n")

    def bias_e(self, cv):
        if not self.hc:
            return 0.0
        c = np.array(self.hc); h = np.array(self.hs)
        return float(np.sum(h * np.exp(-0.5 * ((cv - c) / self.s) ** 2)))

    def update(self, step, cv):
        if step % self.stride:
            return
        be = self.bias_e(cv)
        w  = self.h * np.exp(-be / (KB_KCAL * self.T * (self.gam - 1)))
        self.hc.append(cv); self.hs.append(w)
        self.fh.write(f"{step} {cv:.6f} {w:.6f} {self.s:.4f}\n")
        self.fh.flush()

    def forces(self, bq):
        cv = centroid_cv(bq)
        be = self.bias_e(cv)
        if not self.hc:
            return np.zeros_like(bq), cv, 0.0
        c = np.array(self.hc); h = np.array(self.hs)
        gauss   = h * np.exp(-0.5 * ((cv - c) / self.s) ** 2)
        dVdcv   = float(np.sum(gauss * (-(cv - c) / self.s ** 2)))
        return -dVdcv * centroid_cv_grad(bq), cv, be

    def record_sample(self, cv, be):
        self._sample_cvs.append(cv)
        self._sample_biases.append(be)

    def fes(self):
        grid = np.linspace(self.cv_min, self.cv_max, self.bins)
        fval = np.zeros(self.bins)
        if self.hc:
            c = np.array(self.hc); h = np.array(self.hs)
            for i, cv in enumerate(grid):
                fval[i] = np.sum(h * np.exp(-0.5 * ((cv - c) / self.s) ** 2))
        fval = -fval * (self.gam / (self.gam - 1))
        fval -= fval.min()
        return grid, fval

    def fes_reweight(self):
        """Reweight trajectory with exp(-bias/kT) — same formula as OPES Run 9."""
        if len(self._sample_cvs) < 10:
            return self.fes()
        cvs    = np.array(self._sample_cvs)
        biases = np.array(self._sample_biases)
        weights = np.exp(-biases / self.kT)
        weights /= weights.sum()
        grid = np.linspace(self.cv_min, self.cv_max, self.bins)
        bw = self.s * 2  # 2x hills sigma for KDE smoothness
        kde = np.array([np.sum(weights * np.exp(-0.5 * ((g - cvs) / bw) ** 2))
                        for g in grid])
        kde = np.maximum(kde, 1e-300)
        fval = -self.kT * np.log(kde)
        fval -= fval.min()
        return grid, fval

    def close(self):
        self.fh.close()


# -- FES analysis ---------------------------------------------------------------
def extract_barrier(grid, fes):
    """Energy barrier = TS max - reactant min.

    Uses midpoint split to find left/right minima and the saddle between them.
    This is robust to asymmetric FES where the wells are not at fixed CV values
    (e.g. after WT-MetaD has partially filled the reactant well).
    """
    mid = len(grid) // 2
    if mid < 2:
        return float("nan")
    l  = int(np.argmin(fes[:mid]))
    r  = mid + int(np.argmin(fes[mid:]))
    if l >= r:
        return float("nan")
    ts = l + int(np.argmax(fes[l:r]))
    return float(fes[ts] - fes[l])


# -- Main -----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="MLFF PIMD FAD barrier comparison")
    ap.add_argument("--config",  default="config_physnet.yaml")
    ap.add_argument("--ff",      default="physnet",
                    choices=["physnet", "ani2x", "xtb2", "mace"])
    ap.add_argument("--sanity",  action="store_true")
    ap.add_argument("--seed",    type=int, default=None)
    ap.add_argument("--out-dir", default="results_physnet")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.seed is not None:
        cfg["pimd"]["seed"] = args.seed
    seed = cfg["pimd"]["seed"]
    os.makedirs(args.out_dir, exist_ok=True)
    cfg["output"]["hills_file"] = os.path.join(args.out_dir, f"hills_seed{seed}.dat")
    n = cfg["sanity"]["n_steps"] if args.sanity else cfg["pimd"]["n_steps"]

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from force_fields import load_ff
    ff = load_ff(args.ff, cfg)

    atoms = make_fad()
    pimd  = PIMD(atoms, cfg, ff)
    metad = WTMetaD(cfg)

    cv0 = centroid_cv(pimd.q)
    print(f"[init] FF={args.ff}  CV0={cv0:.4f} Ang  n_steps={n}  T={cfg['pimd']['temperature']}K")

    col = open(os.path.join(args.out_dir, f"colvar_seed{seed}.dat"), "w")
    col.write("# step t_ps cv bias_e\n")
    t0 = time.time()

    for step in range(n):
        bf, cv, be = metad.forces(pimd.q)
        pimd.bf = bf
        pimd.step()
        metad.update(step, cv)
        if step % cfg["output"]["colvar_stride"] == 0:
            col.write(f"{step} {step * 0.5e-3:.4f} {cv:.6f} {be:.6f}\n")
            metad.record_sample(cv, be)
        if step % 5000 == 0 and step > 0:
            spd = step / (time.time() - t0) * 86400 / 1e6
            g, fv = metad.fes_reweight()
            b = extract_barrier(g, fv)
            print(f"step {step:7d}  t={step*0.5e-3:.1f}ps  cv={cv:+.3f}  "
                  f"barrier={b:.2f} kcal/mol  {spd:.1f}M steps/day")

    col.close()
    metad.close()

    g, fv = metad.fes_reweight()
    b   = extract_barrier(g, fv)
    spd = n / (time.time() - t0) * 86400 / 1e6

    print(f"\n=== RESULTS ({args.ff.upper()}) ===")
    print(f"Barrier : {b:.4f} kcal/mol  (target: 1.52 +/- 0.15)")
    print(f"Speed   : {spd:.2f} M steps/day")
    print(f"pass_barrier = {abs(b - 1.52) < 0.15}")

    res = {
        "ff":               args.ff,
        "barrier_kcal_mol": b,
        "speed_M_steps_day": spd,
        "n_steps":          n,
        "sim_time_ps":      n * 0.5e-3,
        "seed":             seed,
        "pass_barrier":     bool(abs(b - 1.52) < 0.15),
        "fes_cv":           g.tolist(),
        "fes_kcal_mol":     fv.tolist(),
    }
    rp = os.path.join(args.out_dir, f"seed_{seed}.json")
    with open(rp, "w") as fj:
        json.dump(res, fj, indent=2)
    print(f"Saved: {rp}")

    if args.sanity:
        print(f"[sanity] FF={args.ff} OK  |  CV computable: True  |  PIMD step OK: True")


if __name__ == "__main__":
    main()
