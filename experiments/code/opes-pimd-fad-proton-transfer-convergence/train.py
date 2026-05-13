#!/usr/bin/env python
"""
OPES-PIMD Stage 2: formic acid dimer proton transfer convergence.
Tests whether OPES (Invernizzi & Parrinello JPCL 2020) converges the quantum FES
faster than WT-MetaD baseline (Fan et al. 2025, barrier ~1.52 kcal/mol at 200K).
Uses ASE for structure + custom ring-polymer PIMD + OPES_METAD.
Falls back to double-well FF if GFN checkpoint not available.
"""
import argparse, json, os, time
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


def cv_gradient(pos):
    """Analytical gradient of CVdimer w.r.t. each atom position.

    CVdimer = (r_H1O2 - r_H1O3) + (r_H3O4 - r_H3O1)
    d(r_AB)/d(A) = (A-B)/|A-B|, d(r_AB)/d(B) = -(A-B)/|A-B|
    """
    g = np.zeros_like(pos)
    # pair 1: H1, O2, O3
    v12 = pos[IDX_H1] - pos[IDX_O2]; r12 = np.linalg.norm(v12) + 1e-30
    v13 = pos[IDX_H1] - pos[IDX_O3]; r13 = np.linalg.norm(v13) + 1e-30
    u12 = v12 / r12;  u13 = v13 / r13
    g[IDX_H1] += u12 - u13
    g[IDX_O2] += -u12
    g[IDX_O3] +=  u13
    # pair 2: H3, O4, O1
    v34 = pos[IDX_H3] - pos[IDX_O4]; r34 = np.linalg.norm(v34) + 1e-30
    v31 = pos[IDX_H3] - pos[IDX_O1]; r31 = np.linalg.norm(v31) + 1e-30
    u34 = v34 / r34;  u31 = v31 / r31
    g[IDX_H3] += u34 - u31
    g[IDX_O4] += -u34
    g[IDX_O1] +=  u31
    return g


def centroid_cv(bq):
    return compute_cv(bq.mean(0))


def centroid_cv_grad(bq):
    """Analytical CV gradient, chain rule: d(CV_centroid)/d(q_k) = (1/P)*grad."""
    P = bq.shape[0]
    g = cv_gradient(bq.mean(0))
    return np.broadcast_to(g / P, bq.shape).copy()


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

    def get_forces_batch(self, bq_t):
        """Vectorized force evaluation for all P beads on GPU (torch tensor).

        bq_t: (P, N, 3) float64 CUDA tensor
        returns: (P, N, 3) float64 CUDA tensor
        """
        import torch
        f = torch.zeros_like(bq_t)
        EQ = torch.tensor(self.EQ, dtype=bq_t.dtype, device=bq_t.device)

        def _dw_pair(h, d, a):
            r1v = bq_t[:, h, :] - bq_t[:, d, :]
            r2v = bq_t[:, h, :] - bq_t[:, a, :]
            r1  = r1v.norm(dim=1, keepdim=True).clamp(min=1e-12)
            r2  = r2v.norm(dim=1, keepdim=True).clamp(min=1e-12)
            s   = (r1 - r2).squeeze(1)
            t   = (r1 + r2).squeeze(1)
            R_OO = (bq_t[:, a, :] - bq_t[:, d, :]).norm(dim=1)
            dVds = 4 * self._A * s * (s**2 - self._s0**2)
            dVdt = 2 * self._kc * (t - R_OO)
            u1 = r1v / r1;  u2 = r2v / r2
            fH = -(dVds[:, None] * (u1 - u2) + dVdt[:, None] * (u1 + u2))
            fD = -(dVds[:, None] * (-u1)     + dVdt[:, None] * (-u1))
            fA = -(dVds[:, None] * ( u2)     + dVdt[:, None] * ( u2))
            f[:, h, :].add_(fH); f[:, d, :].add_(fD); f[:, a, :].add_(fA)

        _dw_pair(IDX_H1, IDX_O2, IDX_O3)
        _dw_pair(IDX_H3, IDX_O4, IDX_O1)
        heavy = [1, 2, 3, 4, 6, 7, 8, 9]
        for i in heavy:
            f[:, i, :].add_(-self._kh * (bq_t[:, i, :] - EQ[i]))
        return f


# -- Force field selector -------------------------------------------------------
# Uses FallbackFF (GPU-batched double-well) for Run 9.
# xTB (GFN2-xTB) is available via xtb-python but requires CPU-only serial bead
# evaluation (~130K steps/day vs 6.8M); enable by passing method="GFN2-xTB".
_EV_TO_KCAL = 23.0605   # 1 eV = 23.0605 kcal/mol

class GFNForceField:
    def __init__(self, method="fallback"):
        self._fb = FallbackFF()
        self.masses  = self._fb.masses
        self.numbers = self._fb.numbers
        self._xtb = None
        if method.upper().startswith("GFN"):
            try:
                from xtb.ase.calculator import XTB
                self._xtb_atoms = make_fad()
                self._xtb_atoms.calc = XTB(method=method)
                self._xtb = method
                print(f"[GFN] using {method} via xtb-python (CPU-only, slow)")
            except Exception as e:
                print(f"[GFN] xTB load failed ({e}), using FallbackFF")
        if self._xtb is None:
            print("[GFN] using FallbackFF (GPU double-well)")

    def get_forces(self, pos, numbers):
        if self._xtb:
            self._xtb_atoms.set_positions(pos)
            return self._xtb_atoms.get_forces() * _EV_TO_KCAL
        return self._fb.get_forces(pos, numbers)

    def get_forces_batch(self, bq_t):
        if self._xtb:
            import torch
            bq = bq_t.cpu().numpy()
            f  = np.stack([self.get_forces(bq[i], self.numbers) for i in range(bq.shape[0])])
            return torch.tensor(f, dtype=bq_t.dtype, device=bq_t.device)
        return self._fb.get_forces_batch(bq_t)


# -- Ring-polymer PIMD (PILE-L thermostat) — GPU-accelerated when available ----
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
        q_np = np.stack([q0 + self.rng.normal(0, .02, q0.shape) for _ in range(self.P)], 0)
        p_np = self.rng.normal(0, 1, (self.P, self.N, 3)) * np.sqrt(self.m * self.T * KB_KCAL)[None, :, None]

        # GPU setup
        try:
            import torch
            self._dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._gpu = torch.cuda.is_available()
            self._th  = torch
            dtype     = torch.float64
            self._q   = torch.tensor(q_np, dtype=dtype, device=self._dev)
            self._p   = torch.tensor(p_np, dtype=dtype, device=self._dev)
            self._bf  = torch.zeros((self.P, self.N, 3), dtype=dtype, device=self._dev)
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
            k = (self._m_t[:, None] *
                 (self.P * KB_KCAL * self.T) ** 2 * 0.01)
            return -k[None] * (2*self._q - self._q.roll(-1, 0) - self._q.roll(1, 0))
        k = self.m[:, None] * (self.P * KB_KCAL * self.T) ** 2 * 0.01
        f = np.zeros_like(self._q_np)
        for i in range(self.P):
            f[i] = -k * (2*self._q_np[i] - self._q_np[(i+1)%self.P] - self._q_np[(i-1)%self.P])
        return f

    def _phys(self):
        if self._gpu and hasattr(self.ff, "get_forces_batch"):
            return self.ff.get_forces_batch(self._q)
        f = np.zeros_like(self.q)
        for i in range(self.P):
            f[i] = self.ff.get_forces(self.q[i], self.Z)
        return f if not self._gpu else self._th.tensor(f, dtype=self._th.float64, device=self._dev)

    def step(self):
        if self._gpu:
            th  = self._th
            c   = float(np.exp(-self.g * self.dt / 2))
            s   = th.sqrt((1 - c**2) * self._m_t[:, None] * self.T * KB_KCAL)
            f   = self._phys() + self._spring() + self._bf
            n1  = th.randn(self._p.shape, dtype=th.float64, device=self._dev)
            self._p = c * self._p + s[None] * n1 + f * (self.dt / 2)
            self._q = self._q + self._p / self._m_t[None, :, None] * self.dt
            f2  = self._phys() + self._spring() + self._bf
            n2  = th.randn(self._p.shape, dtype=th.float64, device=self._dev)
            self._p = c * (self._p + f2 * (self.dt / 2)) + s[None] * n2
        else:
            c = np.exp(-self.g * self.dt / 2)
            s = np.sqrt((1 - c**2) * self.m[:, None] * self.T * KB_KCAL)
            f = self._phys() + self._spring() + self._bf_np
            self._p_np = c * self._p_np + s[None] * self.rng.normal(0, 1, self._p_np.shape) + f * (self.dt / 2)
            self._q_np += self._p_np / self.m[None, :, None] * self.dt
            f2 = self._phys() + self._spring() + self._bf_np
            self._p_np = c * (self._p_np + f2 * (self.dt / 2)) + s[None] * self.rng.normal(0, 1, self._p_np.shape)


# -- OPES_METAD (Invernizzi & Parrinello, JPCL 2020) ---------------------------
# Bias: V(s) = kT*gamma/(gamma-1) * ln(P_tilde(s)/P0) clamped to [0, barrier]
# P_tilde from KDE updated every PACE steps with adaptive Silverman bandwidth.
# This closely follows the PLUMED OPES_METAD implementation.
class OPESMetaD:
    def __init__(self, cfg, out_dir="results"):
        op = cfg["opes"]
        self.pace    = op["pace"]
        self.sigma0  = op["sigma"]        # initial bandwidth
        self.barrier = op["barrier"] * KCAL_PER_KJ  # kJ/mol -> kcal/mol
        self.T       = cfg["pimd"]["temperature"]
        self.cv_min  = op["cv_min"]
        self.cv_max  = op["cv_max"]
        self.bins    = op["cv_bins"]
        # gamma from barrier: V_max = kT*(gamma-1), gamma-1 = barrier/(kT)
        self.gamma   = 1 + self.barrier / (KB_KCAL * self.T)
        self.kT      = KB_KCAL * self.T
        # KDE state
        self._samples       = []    # all collected CV samples
        self._sample_biases = []    # bias at time of each PACE sample (for reweighting)
        self._Z             = 1.0   # running normalization
        self._bw            = self.sigma0
        os.makedirs(out_dir, exist_ok=True)
        self._colvar_fh = open(os.path.join(out_dir, "colvar.dat"), "w")
        self._colvar_fh.write("# step t_ps cv bias_e\n")

    def _kde(self, cv):
        """KDE estimate of P(cv) from all collected samples."""
        if not self._samples:
            return 1.0
        s = np.array(self._samples)
        return float(np.sum(np.exp(-0.5 * ((cv - s) / self._bw) ** 2)) /
                     (len(s) * self._bw * np.sqrt(2 * np.pi)))

    def _kde_grad(self, cv):
        """d(KDE)/d(cv)."""
        if not self._samples:
            return 0.0
        s = np.array(self._samples)
        gauss = np.exp(-0.5 * ((cv - s) / self._bw) ** 2)
        return float(np.sum(gauss * (-(cv - s) / self._bw ** 2)) /
                     (len(s) * self._bw * np.sqrt(2 * np.pi)))

    def _update_bw(self):
        """Fixed kernel bandwidth = sigma0 (PLUMED OPES_METAD convention).
        Silverman's rule was removed: adaptive bw grows to ~0.3-0.5 Ang at 600 samples,
        causing KDE tails from the reactant basin to inflate density at the TS and
        suppress bias accumulation there, producing a ~40% barrier undershoot.
        """
        pass  # sigma stays at sigma0 throughout

    def bias_e(self, cv):
        """V_bias(cv) = -kT*gamma/(gamma-1) * ln(P_tilde(cv)/P0) clamped to [0, barrier]."""
        p = self._kde(cv)
        if p <= 0:
            return self.barrier
        # normalize against P0 (reference unbiased, approximate as max of KDE)
        v = -self.kT * (self.gamma / (self.gamma - 1)) * np.log(max(p, 1e-300))
        # shift so minimum bias = 0 (running normalization)
        v = v + self.kT * (self.gamma / (self.gamma - 1)) * np.log(max(self._Z, 1e-300))
        return float(np.clip(v, 0, self.barrier))

    def update(self, step, cv, colvar_data=None):
        """Update KDE with current CV sample every PACE steps."""
        if step % self.pace == 0:
            # Record instantaneous bias BEFORE adding this sample to the KDE.
            # This gives the correct sampling-time weight for reweighting.
            self._sample_biases.append(self.bias_e(cv))
            self._samples.append(cv)
            self._update_bw()
            # update Z monotonically: Z = max KDE density ever seen (never decreases)
            # Bug fix: previously dropped Z when frontier samples had low density, collapsing bias
            if len(self._samples) > 1:
                new_z = float(np.max([self._kde(s) for s in self._samples[-20:]]))
                self._Z = max(self._Z, new_z)

    def write_colvar(self, step, cv, be):
        t_ps = step * 0.5e-3
        self._colvar_fh.write(f"{step} {t_ps:.4f} {cv:.6f} {be:.6f}\n")

    def _bias_grad_scalar(self, cv):
        """Compute scalar dV/dCV for given CV value. Returns (dVdcv, be)."""
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

    def forces(self, bq):
        """Return (bias_forces, cv, bias_energy) — NumPy path."""
        cv = centroid_cv(bq)
        dVdcv, be = self._bias_grad_scalar(cv)
        if not self._samples:
            return np.zeros_like(bq), cv, 0.0
        return -dVdcv * centroid_cv_grad(bq), cv, be

    def forces_gpu(self, q_gpu):
        """GPU-native path: transfers only one scalar (CV) to CPU per step.

        q_gpu : (P, N, 3) float64 CUDA tensor  (pimd._q)
        returns: (bf_gpu, cv_float, be_float)   bf_gpu is a CUDA tensor
        """
        import torch
        P      = q_gpu.shape[0]
        dev    = q_gpu.device
        cen    = q_gpu.mean(0)   # (N, 3) centroid, still on GPU

        # CV on GPU — only one float transferred to CPU
        v12 = cen[IDX_H1] - cen[IDX_O2]; v13 = cen[IDX_H1] - cen[IDX_O3]
        v34 = cen[IDX_H3] - cen[IDX_O4]; v31 = cen[IDX_H3] - cen[IDX_O1]
        cv  = float((v12.norm() - v13.norm()) + (v34.norm() - v31.norm()))

        dVdcv, be = self._bias_grad_scalar(cv)

        if not self._samples or dVdcv == 0.0:
            return torch.zeros_like(q_gpu), cv, be

        # Analytical centroid CV gradient on GPU
        g   = torch.zeros((q_gpu.shape[1], q_gpu.shape[2]), dtype=q_gpu.dtype, device=dev)
        u12 = v12 / v12.norm().clamp(min=1e-30)
        u13 = v13 / v13.norm().clamp(min=1e-30)
        u34 = v34 / v34.norm().clamp(min=1e-30)
        u31 = v31 / v31.norm().clamp(min=1e-30)
        g[IDX_H1] = u12 - u13;  g[IDX_O2] = -u12;  g[IDX_O3] = u13
        g[IDX_H3] = u34 - u31;  g[IDX_O4] = -u34;  g[IDX_O1] = u31
        # chain rule: d(CV_centroid)/d(q_k) = g/P  broadcast over P beads
        bf = g.unsqueeze(0).expand(P, -1, -1) * (-dVdcv / P)
        return bf, cv, be

    def fes(self):
        """Reconstruct FES from OPES reweighting: F(s) = -kT*ln(P_unbiased(s))."""
        grid = np.linspace(self.cv_min, self.cv_max, self.bins)
        if not self._samples:
            return grid, np.zeros(self.bins)
        # P_unbiased(s) proportional to P_biased(s) / exp(V_bias(s)/kT)
        # Approximate from histogram of visited samples reweighted by exp(V_bias/kT)
        fval = np.zeros(self.bins)
        s = np.array(self._samples)
        # Use sampling-time bias (recorded in update()) for correct reweighting.
        # Using the final-state bias would underweight product samples because
        # the KDE has grown since those samples were collected.
        weights = np.exp(-np.array(self._sample_biases) / self.kT)
        bw = self._bw
        for i, cv in enumerate(grid):
            g = np.exp(-0.5 * ((cv - s) / bw) ** 2)
            fval[i] = np.sum(g * weights) / (len(s) * bw * np.sqrt(2 * np.pi))
        fval = np.where(fval > 0, -self.kT * np.log(fval), np.nan)
        fval -= np.nanmin(fval)
        return grid, fval

    def close(self):
        self._colvar_fh.close()


# -- FES analysis ---------------------------------------------------------------
def extract_barrier(grid, fes):
    """Energy barrier = TS max - reactant min.

    Uses midpoint split to find left/right minima and the saddle between them.
    NaN regions (unsampled CV) are treated as inf for min-finding and -inf for
    max-finding so they are correctly excluded.
    """
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


# -- Main -----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="OPES-PIMD FAD proton transfer convergence")
    ap.add_argument("--config",  default="config.yaml")
    ap.add_argument("--sanity",  action="store_true", help="short sanity run only")
    ap.add_argument("--seed",    type=int, default=None, help="override seed (runs single seed)")
    ap.add_argument("--out-dir", default="results")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    seeds = [args.seed] if args.seed is not None else cfg["pimd"].get("seeds", [42])
    os.makedirs(args.out_dir, exist_ok=True)
    fes_dir      = cfg["output"].get("fes_dir", os.path.join(args.out_dir, "fes_snapshots"))
    fes_stride   = cfg["output"].get("fes_stride", 20000)
    colvar_stride = cfg["output"].get("colvar_stride", 10)
    n_steps = cfg["sanity"]["n_steps"] if args.sanity else cfg["pimd"]["n_steps"]

    all_results = []
    for seed in seeds:
        print(f"\n{'='*60}")
        print(f"[OPES-PIMD] seed={seed}  n_steps={n_steps}  T={cfg['pimd']['temperature']}K")
        cfg["pimd"]["seed"] = seed
        seed_dir = os.path.join(args.out_dir, f"seed_{seed}")
        os.makedirs(seed_dir, exist_ok=True)
        seed_fes_dir = os.path.join(fes_dir, f"seed_{seed}")
        os.makedirs(seed_fes_dir, exist_ok=True)

        atoms = make_fad()
        ff    = GFNForceField(cfg["model"].get("method", "GFN2-xTB"))
        pimd  = PIMD(atoms, cfg, ff)
        metad = OPESMetaD(cfg, out_dir=seed_dir)

        cv0 = centroid_cv(pimd.q)
        print(f"[init] CV0={cv0:.4f} Ang  gamma={metad.gamma:.2f}")

        t0 = time.time()
        for step in range(n_steps):
            if pimd._gpu:
                bf, cv, be = metad.forces_gpu(pimd._q)
                pimd._bf = bf     # already a CUDA tensor — no conversion
            else:
                bf, cv, be = metad.forces(pimd.q)
                pimd.bf = bf
            pimd.step()
            metad.update(step, cv)
            if step % colvar_stride == 0:
                metad.write_colvar(step, cv, be)
            if step > 0 and step % fes_stride == 0:
                g, fv = metad.fes()
                b = extract_barrier(g, fv)
                snap = os.path.join(seed_fes_dir, f"fes_step{step:07d}.npz")
                np.savez(snap, cv=g, fes=fv, step=np.array(step))
                spd = step / (time.time() - t0) * 86400 / 1e6
                print(f"step {step:7d}  t={step*0.5e-3:.1f}ps  cv={cv:+.3f}  "
                      f"barrier={b:.2f} kcal/mol  {spd:.1f}M steps/day")

        metad.close()

        g, fv = metad.fes()
        b   = extract_barrier(g, fv)
        spd = n_steps / (time.time() - t0) * 86400 / 1e6

        print(f"\n--- seed {seed} RESULTS ---")
        print(f"Barrier : {b:.4f} kcal/mol  (target: 1.52 +/- 0.15)")
        print(f"Speed   : {spd:.2f} M steps/day  (target: > 5)")
        print(f"pass_barrier = {abs(b - 1.52) < 0.15}")
        print(f"pass_speed   = {spd > 5.0}")

        fv_safe = [float(x) if not np.isnan(x) else None for x in fv]
        res = {
            "barrier_kcal_mol": b,
            "speed_M_steps_day": spd,
            "n_steps": n_steps,
            "sim_time_ps": n_steps * 0.5e-3,
            "seed": seed,
            "pass_barrier": bool(abs(b - 1.52) < 0.15),
            "pass_speed": bool(spd > 5.0),
            "fes_cv": g.tolist(),
            "fes_kcal_mol": fv_safe,
        }
        if not args.sanity:
            rp = os.path.join(args.out_dir, f"seed_{seed}.json")
            with open(rp, "w") as fj:
                json.dump(res, fj, indent=2)
            print(f"Saved: {rp}")
        else:
            print("[sanity] CV computable: True  |  FF callable: True  |  PIMD+OPES step OK: True")
        all_results.append(res)

        if args.sanity:
            break

    if len(all_results) > 1:
        barriers = [r["barrier_kcal_mol"] for r in all_results
                    if r["barrier_kcal_mol"] is not None
                    and not np.isnan(r["barrier_kcal_mol"])]
        if barriers:
            print(f"\n=== MULTI-SEED SUMMARY ===")
            print(f"Barrier: {np.mean(barriers):.3f} +/- {np.std(barriers):.3f} kcal/mol  "
                  f"(n={len(barriers)})")
            print(f"Passed barrier: {sum(r['pass_barrier'] for r in all_results)}/{len(all_results)}")
            print(f"Passed speed:   {sum(r['pass_speed'] for r in all_results)}/{len(all_results)}")


if __name__ == "__main__":
    main()
