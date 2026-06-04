# Build Guide — i-PI + PLUMED + PhysNet PIMD Enhanced-Sampling Stack

> A step-by-step account of how this simulation stack is assembled, from an empty
> directory to a running quantum free-energy calculation. Companion to
> `DEBUG_RECORD.md` (which logs the bugs we hit and fixed during bring-up).

---

## 0. What we are building and why

**Scientific goal:** compute the free-energy barrier for the **double proton transfer
in the formic acid dimer (FAD)**, including **nuclear quantum effects** (proton
tunnelling / zero-point energy), using a **machine-learned force field** at
near-CCSD(T) accuracy instead of expensive ab-initio forces.

Three hard requirements, each met by one component:

| Requirement | Component | Role |
|-------------|-----------|------|
| Nuclear quantum effects | **i-PI** | Path-integral MD (PIMD): each atom → ring polymer of 32 "beads" |
| Accurate, cheap forces | **PhysNet** | Neural-network force field (TensorFlow/GPU), trained on MP2 data |
| Cross a high barrier in finite time | **PLUMED** | Metadynamics (WT-MetaD / OPES) biasing along the proton-transfer coordinate |

The pieces are glued together over a **UNIX socket**: i-PI drives the dynamics and
asks an external "client" for forces; our **driver** is that client, wrapping PhysNet.
PLUMED is loaded inside i-PI as a second force that adds the metadynamics bias.

```
        ┌─────────────────────────── Docker container (Linux + CUDA) ──────────────────────────────┐
        │                                                                                          │
        │   i-PI  (PIMD integrator, 32 beads, PILE-L thermostat)                                   │
        │     │                                                                                    │
        │     ├── force "physnet-ff"  ──UNIX socket /tmp/ipi_physnet──►  physnet_ipi_driver.py     │
        │     │                                                              │  (BeadCompute)      │ 
        │     │                                                              ▼                     │
        │     │                                                         PhysNet (TF / GPU)         │
        │     │                                                                                    │
        │     └── force "plumed-bias" ──in-process (ctypes)──►  PLUMED 2.9.2                       │
        │                                                          │  CV = proton-transfer coord   │
        │                                                          ▼  deposits HILLS, writes COLVAR│
        └──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1 — The container image (`Dockerfile`)

Everything runs in one Docker image so the CUDA / PLUMED / i-PI / TensorFlow
versions are pinned and reproducible on any machine with an NVIDIA GPU.

Base: `nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04` (the **devel** image, not runtime —
PLUMED's `configure` needs the CUDA headers).

Layers, in cache-friendly order (most expensive first):

1. **System build deps** — `build-essential cmake gfortran`, FFTW/LAPACK/BLAS, OpenMPI, git.
2. **PLUMED 2.9.2 compiled from source** (the ~20-min layer) with:
   - `--enable-python` → builds the Python wrapper + `libplumedKernel.so` that i-PI loads via ctypes.
   - `--enable-modules=+opes` → enables the OPES sampling method (newer alternative to WT-MetaD).
   - Sets `PLUMED_KERNEL=/usr/local/lib/libplumedKernel.so` (i-PI reads this env var).
3. **i-PI** — `pip3 install ipi` (the Python PIMD orchestrator).
4. **PLUMED Python wrapper** — `pip3 install plumed` (used by i-PI's `FFPlumed`).
5. **ML stack** — `tensorflow==2.10.1`, `numpy<1.24` (TF 2.10 compat), `ase`, `pyyaml`.

Build it:

```bash
docker build -t ipi-plumed-mlff:latest .        # see build.bat on Windows
```

> Pitfall pinned here: `numpy<1.24` and `tensorflow==2.10.1` must match — newer NumPy
> breaks TF 2.10's C API.

---

## Step 2 — The molecular system (`init_fad.xyz`)

A 10-atom formic acid dimer, gas phase, in Ångström:

```
H C O O H   H C O O H      (atoms 1–5 = monomer A, 6–10 = monomer B)
```

The two transferring protons are **H1 (atom 1)** and **H3 (atom 6)**. This single
structure is replicated into a 32-bead ring polymer by i-PI at startup.

---

## Step 3 — The force field (`force_fields.py` → `PhysNetFF`)

`PhysNetFF` wraps a trained PhysNet model (`physnet_fad/Final_Fit/best/best_model`,
trained on 58 069 FAD structures at MP2/aug-cc-pVTZ).

Key design point — **batched inference**: instead of one GPU call per bead, it
evaluates **all 32 beads in a single forward pass** using PhysNet's `batch_seg`
mechanism (`get_forces_batch`). `_setup_batch(P, N)` pre-builds the TF tensors for a
fixed `(P beads × N atoms)` shape.

> ⚠️ **Critical performance property:** the TF graph is **specialized to the batch
> size P**. Calling `get_forces_batch` with a *different* P triggers a multi-second
> graph **retrace**. This is the root of `DEBUG_RECORD.md` ISSUE-10 and dictates the
> driver's "always pad to a fixed P" design (Step 4).

Units: PhysNet works in Å and kcal/(mol·Å); i-PI speaks Bohr and Ha/Bohr. The driver
converts at the boundary.

---

## Step 4 — The force server / driver (`physnet_ipi_driver.py`)

This is the custom glue: an i-PI socket client that serves PhysNet forces for all 32
beads. It is the most-iterated file in the project (see ISSUE-08/09/10).

### 4a. The i-PI socket protocol
i-PI is the server; each bead connects as a client and runs a tiny state machine over
a 12-byte-header binary protocol:

```
i-PI → STATUS     client → (its state: NEEDINIT / READY / HAVEDATA)
i-PI → INIT       client consumes init payload, → READY
i-PI → POSDATA    client reads cell + positions (Bohr); computes forces
i-PI → GETFORCE   client → FORCEREADY + energy + forces (Ha/Bohr) + virial
i-PI → FLUSH      one-way hint, no reply  (ISSUE-07)
i-PI → EXIT       end of run; socket closes
```

`recv_header / recv_posdata / send_forceready` implement this; `bead_loop` is the
per-bead state machine (one thread per bead).

### 4b. `BeadCompute` — the deadlock-free hybrid synchronizer
32 bead threads must be combined into **one** batched GPU call. The challenge: i-PI
does **not** guarantee it sends `POSDATA` to all 32 beads before it starts collecting
forces. The design went through three versions:

| Version | Idea | Result |
|---------|------|--------|
| v1 `threading.Barrier(32)` | wait for all 32, then batch | **deadlocks** on a partial dispatch sweep (ISSUE-09) |
| v2 per-bead lock | each bead computes alone under a lock | safe but **~20× too slow** (~0.4 steps/s) |
| **v3 hybrid (shipped)** | leader waits up to `batch_timeout` for a full sweep, then batches whoever arrived; **always pads to a fixed P=32** | **deadlock-free + 8.3 steps/s** |

How v3 works (one MD step):
1. The first bead to arrive becomes the **leader**; the rest are **followers**.
2. The leader waits on a condition variable until either all 32 have arrived **or**
   `batch_timeout = 0.3 s` elapses.
3. The leader builds a **fixed (32 × 10 × 3)** position array — real positions for the
   beads that arrived, padded with a valid geometry for any that didn't — runs **one**
   `get_forces_batch`, and stores forces for the real arrivals (padded results discarded).
4. The leader publishes results, opens the next "generation", and wakes the followers.
5. Beads that missed the sweep form the next generation and get batched in turn — so a
   partial sweep can never hang (the wait is always bounded).

Padding to a constant P keeps the TF graph from retracing (Step 3 / ISSUE-10).

### 4c. Startup warmup
Before i-PI connects, the driver runs one dummy `get_forces_batch` at **P=32** to
force the TF graph compile up front — otherwise the first real step would pay the
compile cost and trip i-PI's socket timeout.

---

## Step 5 — i-PI configuration (`input_fad_pimd.xml`)

Defines the physics and wiring:

- **`<total_steps>600000</total_steps>`** — 300 ps at 0.5 fs/step (production).
- **`<initialize nbeads='32'>`** — build the 32-bead ring polymer from `init_fad.xyz`,
  thermal velocities at 200 K.
- **`<forces>`** — two additive forces:
  - `physnet-ff` → the socket force field (our driver),
  - `plumed-bias` → the PLUMED metadynamics bias.
- **`<dynamics mode='nvt'>`** with a **PILE-L thermostat** (`tau=500 fs`): the standard
  PIMD thermostat — exact sampling of the internal ring-polymer modes, gentle coupling
  on the centroid.
- **`<cell>`** — a large 30 Å box with `pbc='false'` (gas phase; the box is just a
  container, no periodic images).
- **`<ffsocket mode='unix' ... slots='32' timeout='5.0'>`** — opens `/tmp/ipi_physnet`,
  one slot per bead. `timeout=5 s` (reduced from 60 s — ISSUE-04) so a dead run fails
  fast.
- **`<ffplumed plumed_dat='plumed_fad_wtmetad.dat'>`** — loads PLUMED in-process.
- **`<smotion mode='metad'>`** — the hook that makes PLUMED actually deposit hills each
  step (see Step 7 for the subtlety; the **sanity** runs strip this block and use the
  `evaluate()` patch instead).

---

## Step 6 — PLUMED configuration (`plumed_fad_wtmetad.dat`, `plumed_fad_opes.dat`)

Defines the **collective variable (CV)** and the **bias**.

The CV is the symmetric double-proton-transfer coordinate:

```
d_H1_O2 = DISTANCE ATOMS=1,4        d_H1_O3 = DISTANCE ATOMS=1,8
d_H3_O4 = DISTANCE ATOMS=6,9        d_H3_O1 = DISTANCE ATOMS=6,3
cv      = (d_H1_O2 − d_H1_O3) + (d_H3_O4 − d_H3_O1)      # COMBINE, COEFFICIENTS=1,-1,1,-1
```

`cv ≈ 0` at the transition state; its sign tells you which tautomer you're in.

**WT-MetaD bias** (`plumed_fad_wtmetad.dat`):
```
metad: METAD ARG=cv PACE=200 HEIGHT=5.0 SIGMA=0.005 BIASFACTOR=100 TEMP=200 FILE=/tmp/HILLS
PRINT ARG=cv,metad.bias STRIDE=10 FILE=/tmp/COLVAR
```
- Deposit a Gaussian every `PACE=200` steps, height 5 kJ/mol, width 0.005 nm, well-tempered with `BIASFACTOR=100`.
- **`FILE=/tmp/HILLS` / `/tmp/COLVAR`** — written to container tmpfs, **never** the Windows
  bind-mount (ISSUE-01/02). Copied back to the workspace at the end of the run.
- No `FLUSH` action (ISSUE-02).

`plumed_fad_opes.dat` is the OPES variant (`OPES_METAD`, `PACE=500`, `BARRIER=81.6`) —
a newer, more self-tuning sampling scheme; same CV.

---

## Step 7 — The i-PI patch (applied at launch, inside `launch.sh`)

**The subtle bug this solves (ISSUE-03):** PLUMED's `PRINT` output and `METAD`
deposition only fire during `performCalcAndUpdate`, which i-PI normally calls **only**
from the `smotion` hook. The plain force evaluation calls `performCalcNoUpdate` (forces
only) — so without intervention, `HILLS`/`COLVAR` stay empty and no bias is deposited.

`launch.sh` patches i-PI's `engine/forcefields.py` `FFPlumed.evaluate()` to, each step:
1. increment the PLUMED step counter, and
2. call `plumed.cmd("update")` after `performCalcNoUpdate`,

so one full PLUMED cycle (bias + deposit + PRINT) runs per MD step. The **sanity** runs
also strip `<smotion>` from the XML so the cycle happens exactly once per step (the
earlier attempt to keep both produced dangling-pointer crashes — ISSUE-06).

The patch also clears the cached `.pyc` so the edit takes effect.

---

## Step 8 — Launch orchestration (`launch.sh`, `launch_opes.sh`)

The in-container entry point. `bash launch.sh [--sanity]`:

1. `mkdir results/`; remove stale outputs **and the previous `run_status.txt`** (ISSUE-05
   stale-sentinel fix).
2. If `--sanity`: rewrite `total_steps → 400` and delete `<smotion>` into a temp XML.
3. Apply the `FFPlumed.evaluate()` patch (Step 7).
4. Start **i-PI** in the background → `results/ipi.log`; wait 5 s for it to open the socket.
5. Start the **PhysNet driver** in the background → `results/driver.log`.
6. `wait` for i-PI; the driver exits when i-PI disconnects.
7. Copy `/tmp/HILLS`, `/tmp/COLVAR` back to the workspace.
8. Read the last completed step and write the **sentinel** `results/run_status.txt`:
   `SUCCESS steps=400` or `FAILED steps=N`.

---

## Step 9 — Running it

**Sanity run** (400 steps, ~1–2 min — proves the whole stack end-to-end):
```bash
docker run --gpus all -d \
  -v "<host path>:/workspace" \
  -v "<repo root>:/repo:ro" \
  -w /workspace --name ipi-plumed-sanity ipi-plumed-mlff:latest \
  bash launch.sh --sanity
```
> On Windows, set `MSYS_NO_PATHCONV=1` so Git Bash doesn't mangle the `/workspace` paths.

**Monitor** (poll the container, not the buffered bind-mount files):
```bash
docker exec ipi-plumed-sanity sh -c 'cat results/run_status.txt; tail -1 ipi_out.md; wc -l /tmp/COLVAR'
```

**Production run** (600k steps, ~20 h at 8.3 steps/s): same command without `--sanity`
and with the production XML.

**Expected healthy output:**
- `results/run_status.txt` → `SUCCESS steps=400`
- `ipi.log` → `Average timings ... t/step: ~0.12` and `SOFTEXIT ... Exiting cleanly`
- `driver.log` → `~N MD steps done` lines, ending `[driver] done`
- `COLVAR` grows steadily; `HILLS` accumulates Gaussians

---

## Step 10 — Data flow per MD step (the mental model)

```
i-PI proposes bead positions (step N)
   │  POSDATA × 32  (Bohr)
   ▼
driver: 32 threads → BeadCompute leader gathers them → ONE PhysNet batch (GPU)
   │  FORCEREADY × 32  (Ha/Bohr)          [physical forces]
   ▼
i-PI also calls PLUMED in-process:
   PLUMED reads CV(positions) → adds bias force → (every PACE) deposits a Gaussian
   │
   ▼
i-PI sums physnet + plumed forces → PILE-L thermostat → integrates → positions (step N+1)
   │
   ▼
every 10 steps: PRINT cv,bias → /tmp/COLVAR ;  properties → ipi_out.md
```

Run long enough and the deposited hills flatten the free-energy surface along the CV;
the negative of the converged bias **is** the free-energy profile, from which the
proton-transfer barrier (with quantum effects, since this is PIMD) is read off.

---

## Outputs

| File | Content |
|------|---------|
| `ipi_out.md` | step, time (ps), potential, temperature (every 10 steps) |
| `ipi_out.pos_00.xyz` | bead-0 trajectory (every 100 steps) |
| `COLVAR` | CV value + instantaneous bias (every 10 steps) — the sampling record |
| `HILLS` | deposited Gaussians — reconstruct the FES with `plumed sum_hills` |
| `results/run_status.txt` | `SUCCESS`/`FAILED` sentinel |
| `results/{ipi,driver}.log` | engine and force-server logs |

---

## Known limitations / gotchas (read before analyzing)

- **Potential energy is not reported.** The driver returns `energy = 0.0` (forces are
  all NVT dynamics needs, and the FES comes from the CV histogram). The `potential`
  column in `ipi_out.md` reflects only the PLUMED bias, **not** the physical PE — do not
  use it for energetics.
- **All PLUMED output must go to `/tmp`** (container tmpfs), never the Windows bind-mount,
  or file writes hang the whole simulation (ISSUE-01/02).
- **Never vary the batch size** seen by PhysNet — always pad to P=32 (ISSUE-10).
- **`timeout=5 s`** in the XML means any per-step stall >5 s will make i-PI drop clients;
  keep the force path fast.
- For the full debugging history behind each of these, see **`DEBUG_RECORD.md`**.

---

## File index

| File | Purpose |
|------|---------|
| `Dockerfile` | reproducible CUDA + PLUMED + i-PI + TF image |
| `init_fad.xyz` | 10-atom FAD starting geometry |
| `force_fields.py` | `PhysNetFF` — batched GPU force field |
| `physnet_ipi_driver.py` | i-PI socket client; `BeadCompute` hybrid synchronizer |
| `input_fad_pimd.xml` | i-PI config — WT-MetaD production (600k steps) |
| `input_fad_opes.xml` | i-PI config — OPES variant |
| `plumed_fad_wtmetad.dat` | CV + WT-MetaD bias |
| `plumed_fad_opes.dat` | CV + OPES bias |
| `launch.sh` / `launch_opes.sh` | in-container orchestration + i-PI patch + sentinel |
| `DEBUG_RECORD.md` | issue log (10 tickets) from bring-up |
| `BUILD_GUIDE.md` | this document |
