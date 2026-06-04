"""
Force field wrappers for the MLFF comparison experiment.
All get_forces(pos, numbers) take positions in Angstrom and return
forces in kcal/(mol*Ang), matching the FallbackFF convention used
by the PIMD integrator.
"""
import os, sys
import numpy as np

KCAL_PER_EV   = 23.0605
KCAL_PER_HA   = 627.509474
ANG_PER_BOHR  = 0.52917390
KCAL_PER_HA_BOHR = KCAL_PER_HA / ANG_PER_BOHR   # 1185.82

FAD_MASSES  = np.array([1, 12, 16, 16, 1, 1, 12, 16, 16, 1], dtype=float)
FAD_NUMBERS = np.array([1,  6,  8,  8, 1, 1,  6,  8,  8, 1])


class PhysNetFF:
    """PhysNet NNP -- MP2/aug-cc-pVTZ, 58069 FAD structures. Batched ~4 M steps/day."""
    masses  = FAD_MASSES
    numbers = FAD_NUMBERS

    def __init__(self, physnet_base):
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
        os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
        if physnet_base not in sys.path:
            sys.path.insert(0, physnet_base)
        import tensorflow as tf
        # Enable GPU memory growth so TF doesn't grab all VRAM at init
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print(f"[PhysNetFF] GPU(s) found: {[g.name for g in gpus]}")
        else:
            print("[PhysNetFF] WARNING: no GPU detected — running on CPU")
        from ase import Atoms as AseAtoms
        from physnet_fad.physnet import PhysNet
        ckpt = os.path.join(physnet_base, "physnet_fad", "Final_Fit", "best", "best_model")
        cfg  = os.path.join(physnet_base, "physnet_fad", "Final_Fit", "config.txt")
        _dummy = AseAtoms(symbols="HCOOHHCOOH", positions=np.zeros((10, 3)))
        self._calc  = PhysNet(_dummy, ckpt, cfg)
        self._atoms = _dummy
        self._atoms.calc = self._calc
        self._tf = tf
        self._device = "/GPU:0" if gpus else "/CPU:0"
        print(f"[PhysNetFF] loaded: {ckpt}  (device={self._device})")

        # Pre-build batch-inference tensors (32 beads × 10 atoms)
        self._setup_batch(32, 10)

    def _setup_batch(self, P, N):
        tf = self._tf
        idx_i_np = self._calc.idx_i.numpy()   # all-pairs for N atoms
        idx_j_np = self._calc.idx_j.numpy()
        self._R_batch = tf.Variable(
            np.zeros((P * N, 3), dtype=np.float32), trainable=False, name="R_batch")
        self._Z_batch  = tf.constant(np.tile(FAD_NUMBERS.astype(np.int32), P))
        self._idx_i_b  = tf.constant(
            np.concatenate([idx_i_np + b * N for b in range(P)]), dtype=tf.int32)
        self._idx_j_b  = tf.constant(
            np.concatenate([idx_j_np + b * N for b in range(P)]), dtype=tf.int32)
        self._bseg     = tf.constant(np.repeat(np.arange(P, dtype=np.int32), N))
        self._Q_tot_b  = tf.constant(np.zeros(P, dtype=np.float32))
        self._batch_P  = P

    def get_forces(self, pos, numbers):
        self._atoms.set_positions(pos)
        return self._atoms.get_forces() * KCAL_PER_EV   # kcal/(mol*Ang)

    def get_forces_batch(self, beads, numbers):
        """All P beads in a single TF forward pass via batch_seg."""
        P, N, _ = beads.shape
        if P != self._batch_P:
            self._setup_batch(P, N)
        self._R_batch.assign(beads.reshape(P * N, 3).astype(np.float32))
        tf = self._tf
        with tf.device(self._device):
            _, forces, _ = self._calc.model.energy_and_forces_and_charges(
                self._Z_batch, self._R_batch,
                self._idx_i_b, self._idx_j_b,
                Q_tot=self._Q_tot_b, batch_seg=self._bseg, offsets=None)
        return tf.convert_to_tensor(forces).numpy().reshape(P, N, 3) * KCAL_PER_EV


class ANI2xFF:
    """ANI-2x NNP -- wB97X/6-31G*, H/C/N/O/S/F/Cl. Batched GPU. ~1.8 M steps/day."""
    masses  = FAD_MASSES
    numbers = FAD_NUMBERS

    def __init__(self):
        import torch, torchani
        self._torch  = torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model  = torchani.models.ANI2x(periodic_table_index=True).to(self._device)
        self._Z      = torch.tensor([FAD_NUMBERS.tolist()], dtype=torch.long,
                                    device=self._device)
        print(f"[ANI2xFF] ANI-2x on {self._device}")

    def get_forces(self, pos, numbers):
        th = self._torch
        pos_t = th.tensor(pos[None], dtype=th.float32,
                           device=self._device, requires_grad=True)
        res = self._model((self._Z, pos_t))
        res.energies.sum().backward()
        return -pos_t.grad[0].cpu().numpy().astype(float) * KCAL_PER_HA

    def get_forces_batch(self, beads, numbers):
        th = self._torch
        P  = beads.shape[0]
        Z_b  = self._Z.repeat(P, 1)
        pos_b = th.tensor(beads, dtype=th.float32,
                           device=self._device, requires_grad=True)
        res = self._model((Z_b, pos_b))
        res.energies.sum().backward()
        return -pos_b.grad.cpu().numpy().astype(float) * KCAL_PER_HA


class MACEOFF23FF:
    """MACE-OFF23 small -- B3LYP-D3BJ/def2-TZVPD (SPICE). Batched GPU. ~0.24 M steps/day."""
    masses  = FAD_MASSES
    numbers = FAD_NUMBERS

    def __init__(self, model_size="small"):
        import torch
        from mace.calculators import mace_off
        from mace.data import AtomicData, config_from_atoms
        from mace.tools.torch_geometric import Batch
        from ase import Atoms as AseAtoms
        self._torch = torch
        self._AtomicData = AtomicData
        self._config_from_atoms = config_from_atoms
        self._Batch = Batch
        self._AseAtoms = AseAtoms
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        calc = mace_off(model=model_size, device=self._device)
        self._model  = calc.models[0]
        self._cutoff = float(self._model.r_max)
        self._z_table = calc.z_table
        self._ref_atoms = AseAtoms("HCOOHHCOOH", positions=np.zeros((10, 3)))
        self._batch_template = None
        print(f"[MACEOFF23FF] {model_size} on {self._device}, cutoff={self._cutoff:.1f} Ang")

    def _build_batch(self, beads):
        P = beads.shape[0]
        dl = []
        for b in range(P):
            a = self._ref_atoms.copy()
            a.set_positions(beads[b])
            cfg = self._config_from_atoms(a)
            dl.append(self._AtomicData.from_config(cfg, z_table=self._z_table,
                                                    cutoff=self._cutoff))
        return self._Batch.from_data_list(dl).to(self._device)

    def get_forces(self, pos, numbers):
        batch = self._build_batch(pos[None])
        out = self._model(batch, training=False, compute_force=True)
        return out["forces"].detach().cpu().numpy() * (23060.5 / 1000)  # eV/Ang → kcal/(mol·Ang)

    def get_forces_batch(self, beads, numbers):
        th = self._torch
        P, N, _ = beads.shape
        # Rebuild graph only when shape changes; cache otherwise
        if self._batch_template is None or self._batch_template.num_graphs != P:
            self._batch_template = self._build_batch(beads)
        else:
            self._batch_template.positions = th.tensor(
                beads.reshape(-1, 3).astype(np.float32), device=self._device)
        out = self._model(self._batch_template, training=False, compute_force=True)
        F = out["forces"].detach().cpu().numpy().reshape(P, N, 3)
        return F * KCAL_PER_EV


class XTB2FF:
    """GFN2-xTB via xtb.interface (CPU). ~0.12 M steps/day at 32 beads."""
    masses  = FAD_MASSES
    numbers = FAD_NUMBERS
    _ANG2BOHR = 1.0 / ANG_PER_BOHR

    def __init__(self):
        from xtb.interface import Calculator, Param  # smoke-test import
        print("[XTB2FF] GFN2-xTB via xtb.interface (CPU)")

    def get_forces(self, pos, numbers):
        from xtb.interface import Calculator, Param
        calc = Calculator(Param.GFN2xTB, numbers, pos * self._ANG2BOHR)
        calc.set_verbosity(0)
        res = calc.singlepoint()
        return -res.get_gradient() * KCAL_PER_HA_BOHR

    def get_forces_batch(self, beads, numbers):
        F = np.zeros_like(beads)
        for i in range(beads.shape[0]):
            F[i] = self.get_forces(beads[i], numbers)
        return F


def load_ff(name, cfg):
    name = name.lower()
    if name == "physnet":
        base = cfg.get("model", {}).get("physnet_base", "")
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), base))
        return PhysNetFF(base)
    elif name == "ani2x":
        return ANI2xFF()
    elif name == "mace":
        size = cfg.get("model", {}).get("mace_size", "small")
        return MACEOFF23FF(model_size=size)
    elif name == "xtb2":
        return XTB2FF()
    else:
        raise ValueError(f"Unknown FF: {name!r}")
