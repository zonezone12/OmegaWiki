---
title: "i-PI + PLUMED + ML Force Server Stack for Fast PIMD Enhanced Sampling"
slug: ipi-plumed-mlff-pimd-stack
status: in_progress
origin: "Infrastructure bottleneck identified during wt-metad-pimd-fad-physnet-baseline: current ASE-based Python PIMD loop yields ~0.9 M steps/day due to Python↔GPU overhead, not GPU compute. i-PI + PLUMED removes per-step Python overhead."
origin_gaps: [opes-per-step-kde-overhead-does]
tags: [infrastructure, pimd, enhanced-sampling, opes, metadynamics, mlff, i-pi, plumed, docker]
domain: ML Systems
priority: 4
pilot_result: ""
failure_reason: ""
linked_experiments: [wt-metad-pimd-fad-physnet-baseline]
date_proposed: 2026-05-29
date_resolved: ""
---

## Motivation

The current PIMD + WT-MetaD setup (ASE-based Python loop + PhysNet TF 2.10 + custom WT-MetaD) achieves only ~0.9 M steps/day for 32-bead PIMD on a 10-atom molecule (FAD). The bottleneck is not GPU compute — PhysNet forward pass on 10 atoms × 32 beads takes microseconds — but Python overhead: ~1 million Python function calls per day, plus NumPy↔TF tensor transfer on every step.

Properly optimized PIMD codes (i-PI, LAMMPS) handle the ring polymer integration in compiled C++/Fortran and call the force provider once per step via a socket protocol. PLUMED, compiled as a C++ plugin, handles collective variables and bias natively with negligible overhead. Switching to this stack is expected to give 5–20× throughput improvement for the same hardware.

## Hypothesis

Running i-PI (PIMD) + PLUMED (OPES/WT-MetaD) + a socket-based ML force server (PhysNet or GFN) inside a Docker container will achieve ≥5 M steps/day for 32-bead FAD PIMD, compared to ~0.9 M steps/day in the current Python stack.

## Approach sketch

### Deployment: Docker Desktop (Windows host)

Use Docker Desktop (already available) rather than WSL2 for better reproducibility and environment control:

```
Docker container (Ubuntu 22.04):
  - i-PI 3.x          (PIMD ring polymer, C++/Python)
  - PLUMED 2.9+       (OPES + WT-MetaD + CVs, compiled plugin)
  - i-PI ↔ PLUMED     (via i-PI's PLUMED patch or driver interface)

Force server (can be inside or outside container):
  - PhysNet: Python TF 2.x server, socket interface to i-PI
  - OR GFN: PyTorch server, socket interface to i-PI
  - GPU passthrough: Docker Desktop supports NVIDIA GPU via WSL2 backend
```

### Integration architecture

```
i-PI (ring polymer integrator)
  │  socket (INET or UNIX)
  ▼
ML force server (Python)     ← PhysNet / GFN model
  │  forces per bead
  ▼
i-PI ← PLUMED patch          ← OPES or WT-MetaD bias
  │  biased forces returned to beads
  ▼
PILE-L thermostat (in i-PI)
```

### Implementation steps

1. **Docker image**: build Ubuntu 22.04 image with i-PI + PLUMED compiled from source; pin versions for reproducibility
2. **Force server**: wrap PhysNet (or GFN) as an i-PI-compatible force server using `ipi-driver` socket protocol (template in i-PI docs: `drivers/py/driver.py`)
3. **PLUMED input**: write `plumed.dat` for CVdimer + OPES_METAD / METAD action — straightforward translation of current Python WT-MetaD config
4. **i-PI input**: write `input.xml` for PIMD (32 beads, PILE-L, 200K, 0.5 fs)
5. **GPU passthrough**: configure Docker Desktop NVIDIA runtime for GPU access inside container
6. **Validation**: run 10 ps on FAD with PhysNet, verify CV trajectory matches current Python output within numerical tolerance

### Docker image sketch

```dockerfile
FROM ubuntu:22.04
RUN apt-get install -y cmake g++ python3 python3-pip libfftw3-dev
# PLUMED
RUN git clone https://github.com/plumed/plumed2 && cd plumed2 && \
    ./configure --enable-python && make -j4 && make install
# i-PI
RUN pip install ipi
```

## Expected outcome

- Throughput: ≥5 M steps/day (5× improvement) for 32-bead FAD PIMD on RTX 4060
- Enables 300 ps runs in ~1.4h instead of ~15h
- Makes multi-seed, multi-condition sweeps practical (e.g. 10 seeds × 300 ps in <2 days)
- Cleaner separation of concerns: i-PI owns PIMD, PLUMED owns enhanced sampling, Python owns ML force evaluation

## Risks

- **Docker GPU passthrough**: NVIDIA Container Toolkit + Docker Desktop WSL2 backend required; needs setup and testing
- **PLUMED compile**: usually straightforward on Ubuntu but can have dependency issues; pin to a tested version
- **PhysNet TF 2.10 in Linux container**: TF 2.10 Linux wheels are available on PyPI; GPU support on Linux is native (no CUDA 11.x restriction unlike Windows)
- **CV definition**: must re-express CVdimer in PLUMED syntax (DISTANCE + COMBINE); straightforward

## Pilot results

(fill after testing)

## Lessons learned

(fill after testing)
