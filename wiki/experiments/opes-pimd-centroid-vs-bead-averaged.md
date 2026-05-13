---
title: "Ablation: Centroid CV vs. Bead-Averaged Reweighting for OPES-PIMD Bias"
slug: "opes-pimd-centroid-vs-bead-averaged"
status: planned
target_claim: "centroid-cv-biasing-accurate-opes-enhanced"
hypothesis: "OPES bias applied to the centroid collective variable (mean bead position) produces a FES barrier within 0.2 kcal/mol of the barrier obtained from full bead-averaged path-integral reweighting, while being computationally cheaper (no reweighting step per frame)."
tags: [pimd, opes, collective-variables, centroid, ablation, free-energy]
domain: "ML Systems"
setup:
  model: "MolCT-GFN (FAD system)"
  dataset: "Formic acid dimer"
  hardware: "NVIDIA A100 80GB GPU"
  framework: "AIMS framework"
metrics: ["FES barrier height (kcal/mol) for centroid vs. bead-averaged", "FES profile shape overlap", "per-step overhead (ms)"]
baseline: "OPES-PIMD with bead-averaged reweighting (full quantum FES)"
outcome: ""
key_result: ""
linked_idea: "opes-pimd-quantum-free-energy-enhanced"
date_planned: 2026-05-08
date_completed: ""
run_log: ""
started: ""
estimated_hours: 8
remote:
  server: ""
  gpu: ""
  session: ""
  started: ""
  completed: ""
---

## Objective

Isolate the contribution of the CV biasing strategy: centroid approximation vs. full path-integral reweighting. This determines whether the simpler centroid biasing (lower overhead, no per-frame reweighting) is accurate enough for practical use.

## Setup

- **Condition A** (centroid): OPES bias applied to centroid CV = (1/P) sum_k s(r_k)
- **Condition B** (bead-averaged): OPES bias applied to centroid CV; FES reconstructed via path-integral reweighting: F_quantum(s) = -(1/beta) ln[(1/P) sum_k exp(-beta * F^(k)(s))]
- Both conditions: 150 ps, 3 seeds, same OPES parameters
- Reference: FP-PIMD result from Fan et al. (barrier = 1.52 kcal/mol)

## Procedure

1. Run 3x 150ps OPES-PIMD simulations with CVdimer (FAD system)
2. From same trajectory: reconstruct FES via (A) centroid and (B) bead-averaged reweighting
3. Extract barrier from both FES reconstructions
4. Compare to FP-PIMD reference (1.52 kcal/mol)
5. Measure overhead of bead-averaged reweighting (per-frame cost)
6. Note: conditions A and B can use the same OPES trajectory (only FES reconstruction differs)

## Results

(to be filled after /exp-run)

## Analysis

- **Success criterion**: |barrier_centroid - barrier_bead_averaged| < 0.2 kcal/mol
- **Accuracy vs. reference**: both within 0.3 kcal/mol of FP-PIMD 1.52 kcal/mol
- If centroid and bead-averaged agree: recommend centroid biasing for practical OPES-PIMD (lower overhead)
- If centroid shows systematic bias: quantify as a correction factor or recommend bead-averaged always

## Claim updates

(to be filled after /exp-eval)

## Follow-up

- **Agreement** → centroid biasing is default; add note to OPES-PIMD workflow
- **Systematic centroid error** → bead-averaged reweighting is required; update idea approach
