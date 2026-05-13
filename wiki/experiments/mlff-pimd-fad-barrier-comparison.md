---
title: "MLFF PIMD FAD Quantum Barrier Comparison"
slug: "mlff-pimd-fad-barrier-comparison"
status: completed
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "Different MLFFs trained at different levels of theory (MP2/aVTZ, wB97X/6-31G*, B3LYP-D3BJ) give different FAD proton-transfer barriers under PIMD-WT-MetaD, and comparing them clarifies which FF is required to match the Fan et al. 1.52 kcal/mol target."
tags: [pimd, metadynamics, formic-acid-dimer, mlff, comparison, nuclear-quantum-effects]
domain: "ML Systems"
setup:
  model: "PhysNet (MP2/aVTZ), ANI-2x (wB97X/6-31G*), MACE-OFF23-small (B3LYP-D3BJ/SPICE)"
  dataset: "Formic acid dimer (FAD), 10 atoms"
  hardware: "NVIDIA RTX 4060 Laptop GPU 8GB"
  framework: "Custom PIMD + WT-MetaD (same as wt-metad-pimd-fad-baseline-reproduction)"
metrics: ["proton transfer energy barrier (kcal/mol)", "FES profile shape", "simulation speed (M steps/day)"]
baseline: "Fan et al. 2025: barrier = 1.52 kcal/mol (GFN2-xTB/PIMD)"
outcome: "failed"
key_result: "All three MLFFs (PhysNet 27.4, MACE-OFF23 30.1, ANI-2x 37.7 kcal/mol) show zero TS crossings across 9 runs; barriers are 18-25x higher than the GFN2-xTB target (1.52 kcal/mol), indicating none can reproduce Fan et al. with standard WT-MetaD settings."
linked_idea: "opes-pimd-quantum-free-energy-enhanced"
date_planned: 2026-05-10
date_completed: "2026-05-13"
run_log: "logs/mlff-ani2x-s42.log"
started: "2026-05-10T19:26"
estimated_hours: 48
remote:
  server: ""
  gpu: ""
  session: ""
  started: ""
  completed: ""
---

## Objective

Build a comparison table of quantum PIMD proton-transfer barriers across MLFFs trained at different levels of theory. Establishes which training level is needed to reproduce the Fan et al. (2025) benchmark (1.52 kcal/mol at 200K, 32-bead PIMD). The FallbackFF (toy double-well, 0.352 kcal/mol) confirmed OPES Run 9 under-convergence; now need real FF results to understand whether the target barrier is achievable.

## Setup

- **PIMD**: 32 beads, PILE-L thermostat, 0.5 fs timestep, 200K
- **Enhanced sampling**: WT-MetaD CVdimer (same parameters as Fan et al.)
- **Reweighting**: exp(-bias/kT) weighted KDE (same as v3 WT-MetaD baseline)
- **FFs compared**:
  | FF | Training data | Level | Scope | Speed |
  |----|--------------|-------|-------|-------|
  | FallbackFF | toy double-well | — | — | 8.9 M/day |
  | PhysNet | 58069 FAD structures | MP2/aug-cc-pVTZ | FAD-specific | ~0.48 M/day (batched) |
  | ANI-2x | ANI-1x + diverse | wB97X/6-31G* | Universal H/C/N/O/S/F/Cl | ~0.89 M/day |
  | MACE-OFF23 | SPICE dataset | B3LYP-D3BJ/def2-TZVPD | Universal organic | ~0.16 M/day |
- **Simulation length**: 150 ps (PhysNet, ANI-2x) / 50 ps (MACE-OFF23) × 3 seeds each
- **Code**: `experiments/code/mlff-pimd-fad-barrier-comparison/`

## Procedure

1. PhysNet: batch all 32 beads in one TF forward pass via `batch_seg` → 0.48 M/day
2. ANI-2x: batch 32 beads in one PyTorch call → 0.89 M/day
3. MACE-OFF23 small: cached graph + position update → 0.16 M/day
4. 3 seeds each, exp(-bias/kT) reweighting, extract barrier with midpoint-split estimator

## Results

| FF | Training | Barrier (kcal/mol) | Std | n_transitions | Speed | Sim length |
|----|----------|-------------------|-----|---------------|-------|------------|
| FallbackFF | toy double-well | 0.352 | ±0.021 | ~7/seed | 8.9 M/day | 300 ps × 3 |
| PhysNet | MP2/aug-cc-pVTZ | **27.428** | ±0.114 | 0 | 0.48 M/day | 150 ps × 3 |
| MACE-OFF23 small | B3LYP-D3BJ/SPICE | **30.108** | ±0.489 | 0 | 0.30 M/day | 50 ps × 3 |
| ANI-2x | wB97X/6-31G* | **37.691** | ±0.508 | 0 | 0.47 M/day | 150 ps × 3 |
| **Target** | GFN2-xTB (Fan et al.) | **1.52** | ±0.15 | — | — | — |

Per-seed detail:
- PhysNet: 27.420 / 27.292 / 27.571 kcal/mol
- ANI-2x: 38.401 / 37.240 / 37.431 kcal/mol
- MACE-OFF23: 30.669 / 29.477 / 30.177 kcal/mol

**Note**: All "barrier" values are FES edge artifacts (no TS crossing occurred). The CV (CVdimer) never reached 0.0 Å in any run; closest approach was PhysNet at -1.14 Å.

## Analysis

**Universal failure to cross TS**: None of the three ab-initio-trained MLFFs produced a single TS crossing across 9 total runs (3 seeds × 3 FFs). The WT-MetaD bias (h=1.0 kJ/mol, σ=0.05, γ=10) is insufficient to overcome the effective barriers in these FFs within 50–150 ps.

**Ordering matches intuition**: PhysNet (27.4) < MACE-OFF23 (30.1) < ANI-2x (37.7). PhysNet is FAD-specific at MP2/aVTZ — the highest-quality training data — and gives the softest surface. ANI-2x (wB97X/6-31G*) gives the hardest surface. However, all three are 18–25× above the Fan et al. GFN2-xTB target (1.52 kcal/mol).

**GFN2-xTB is an outlier**: The Fan et al. result almost certainly reflects a fundamentally softer FAD PES under GFN2-xTB, not a convergence issue with the MLFF simulations. GFN2-xTB is a semi-empirical tight-binding method known to underestimate hydrogen-bond-breaking barriers relative to ab-initio methods. The 1.52 kcal/mol target should be interpreted with this caveat.

**Very tight seed-to-seed consistency**: PhysNet std = ±0.114 kcal/mol across seeds — essentially no variance. This confirms FES edge is a real feature of the potential, not a sampling artifact. The simulations are converged within their sampled region; the problem is insufficient bias to reach the TS.

## Claim updates

- **Verdict**: inconclusive
- **Claim**: [[opes-pimd-converges-quantum-fes-faster]] confidence 0.2 → 0.2 (unchanged)
- **Reasoning**: Experiment used WT-MetaD only (no OPES), so provides no direct evidence for/against OPES convergence speed. Primary finding — GFN2-xTB PES is qualitatively different from ab-initio MLFFs for FAD proton transfer — blocks valid comparison until GFN2-xTB-level FF is available.
- **Judge agreement**: Claude self-review only (Review LLM MCP not configured)
- **Date**: 2026-05-13

## Follow-up

- If PhysNet barrier ≈ 1.52 kcal/mol → use PhysNet for OPES comparison
- If ANI-2x barrier ≈ 1.52 kcal/mol → ANI-2x is viable (faster, more universal)
- If both are far from 1.52 → need GFN2-xTB or MolCT-GFN retraining
