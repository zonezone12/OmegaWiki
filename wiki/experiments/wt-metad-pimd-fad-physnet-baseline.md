---
title: "WT-MetaD-PIMD PhysNet Baseline: FAD Proton Transfer with Aggressive Settings"
slug: "wt-metad-pimd-fad-physnet-baseline"
status: planned
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "Well-tempered MetaD-PIMD with BIASFACTOR=50 and height=3 kJ/mol can overcome the PhysNet FAD proton-transfer barrier within 300 ps (3 seeds), establishing a converged quantum FES barrier reference for the OPES comparison."
tags: [pimd, metadynamics, formic-acid-dimer, physnet, mlff, nuclear-quantum-effects, baseline]
domain: "ML Systems"
setup:
  model: "PhysNet (MP2/aug-cc-pVTZ, 58069 FAD structures) — batched 32-bead TF inference"
  dataset: "Formic acid dimer (FAD), 10 atoms"
  hardware: "NVIDIA RTX 4060 Laptop GPU 8GB"
  framework: "Custom PIMD + WT-MetaD (ASE-based); force_fields.PhysNetFF"
metrics:
  - "proton transfer energy barrier (kcal/mol)"
  - "first TS crossing time (ps)"
  - "FES profile shape"
  - "simulation speed (M steps/day)"
baseline: "Fan et al. 2025: barrier = 1.52 kcal/mol (GFN2-xTB); mlff-pimd-fad-barrier-comparison PhysNet artifact: 27.4 kcal/mol (unphysical — zero TS crossings)"
outcome: ""
key_result: ""
linked_idea: ""
date_planned: 2026-05-14
date_completed: ""
run_log: ""
---

## Objective

Establish the true converged PhysNet quantum FES barrier for FAD proton transfer using much more aggressive WT-MetaD settings than the failed `mlff-pimd-fad-barrier-comparison`. The prior attempt (h=1 kJ/mol, γ=10, 150 ps) achieved zero TS crossings; this experiment uses γ=50, h=3 kJ/mol, 300 ps to drive through the unknown PhysNet quantum barrier. The result serves as the mandatory baseline for the OPES vs WT-MetaD comparison on PhysNet.

## Setup

- **System**: Formic acid dimer (10 atoms), CVdimer = (d_O2H1 − d_O3H1) + (d_O4H3 − d_O1H3)
- **Force field**: PhysNetFF from `experiments/code/mlff-pimd-fad-barrier-comparison/force_fields.py`
  - PhysNet checkpoint: `experiments/code/opes-pimd-fad-proton-transfer-convergence/physnet_fad/Final_Fit/best/best_model`
  - Batched: all 32 beads in one TF forward pass via `get_forces_batch`
- **PIMD**: 32 beads, PILE-L thermostat, 0.5 fs timestep, 200K, friction=1.0
- **WT-MetaD**:
  - CV: CVdimer (centroid of beads)
  - height: **3.0 kJ/mol** (3× prior experiment)
  - sigma: 0.05 Å
  - biasfactor: **50** (γ=50; max bias → 49/50 × ΔF ≈ 98% of barrier; handles unknown barriers up to ~30 kcal/mol)
  - PACE: 200 steps
  - cv_min: −2.0, cv_max: 2.0, cv_bins: 400
- **Reweighting**: `exp(−bias/kT)` — same correct formula as wt-metad v3
- **Simulation**: 300 ps × 3 seeds (seeds: 42, 123, 7)
- **Escalation path**: If 0/3 seeds cross TS in 300 ps → extend to 500 ps; if still 0/3 → escalate to γ=100, h=5 kJ/mol

## Procedure

1. **Sanity check (10 ps, seed 42)**: verify PhysNet loads, forces are finite, CV initializes at ~−1.3 Å, no integration crashes
2. **Run 3 × 300 ps WT-MetaD simulations** (seeds 42, 123, 7 sequentially on GPU):
   - Config: `experiments/code/wt-metad-pimd-fad-physnet-baseline/config.yaml`
   - Base code: reuse `experiments/code/mlff-pimd-fad-barrier-comparison/train.py` with new config
   - Output: `results_physnet/seed_{42,123,7}.json`, `hills_seed{42,123,7}.dat`, `colvar_seed{42,123,7}.dat`
3. **Track CV max** at 50 ps intervals; abort early if all seeds stall at same CV for >100 ps (escalate params)
4. **Extract barrier** using exp(−bias/kT) reweighting + midpoint-split estimator at each 50 ps snapshot
5. **Record first TS crossing time** (first step where centroid CV > 0.0 Å)
6. **Convergence check**: barrier is converged when |barrier(t) − barrier(t−50ps)| < 0.2 kcal/mol for last 3 checkpoints

## Results

(to be filled after /exp-run)

## Analysis

Success criterion: **≥ 2 of 3 seeds cross TS within 300 ps AND 3-seed barrier std < 0.5 kcal/mol**.

Key diagnostics:
- First TS crossing time per seed — establishes WT-MetaD reference for OPES comparison
- PhysNet quantum barrier (converged mean ± std) — primary result
- Convergence trajectory (barrier vs. time) — shows if 300 ps is sufficient
- Speed measurement (M steps/day) — secondary metric for `opes-per-step-kde-overhead-does`

If **0/3 seeds** cross TS:
- Check CV max progression; if advancing (even slowly), escalate to 500 ps
- If CV frontier is stuck (advance rate < 0.001 Å/ps), escalate to γ=100, h=5 kJ/mol

If **1/3 seeds** crosses TS:
- Use the crossing seed to establish a preliminary barrier estimate
- Proceed cautiously to `opes-pimd-fad-physnet-validation` with the preliminary barrier × 2 as OPES BARRIER parameter

## Claim updates

(to be filled after /exp-eval)

## Follow-up

**Success (≥ 2 TS crossings)** → immediately proceed to `opes-pimd-fad-physnet-validation`; set OPES BARRIER = 3.5 × PhysNet_barrier_kcal × 4.184 kJ/mol

**Partial (1 TS crossing)** → proceed with caution; set OPES BARRIER conservatively at 5 × preliminary_barrier

**Failure (0 TS crossings, 300 ps)** → extend to 500 ps or escalate to γ=100, h=5 kJ/mol; do NOT proceed to OPES experiment until baseline is established

**Barrier matches Fan et al. (1.2–1.8 kcal/mol)** → OPES comparison is directly applicable to the original claim; high scientific value

**Barrier >> Fan et al. (> 5 kcal/mol)** → OPES comparison still valid but results apply to MP2-level chemistry, not GFN2-xTB; note this limitation in claim update
