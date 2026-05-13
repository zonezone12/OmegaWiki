---
title: "Ablation: OPES vs. WT-MetaD Hyperparameter Sensitivity in PIMD"
slug: "opes-vs-wt-metad-hyperparameter-sensitivity"
status: planned
target_claim: "opes-hyperparameter-sensitivity-lower-than-wt"
hypothesis: "The coefficient of variation (CV = std/mean) of the converged FES barrier across a hyperparameter grid is at least 2x smaller for OPES than for WT-MetaD in PIMD simulations."
tags: [pimd, opes, metadynamics, hyperparameter-sensitivity, ablation, reproducibility]
domain: "ML Systems"
setup:
  model: "MolCT-GFN (FAD system)"
  dataset: "Formic acid dimer"
  hardware: "NVIDIA A100 80GB GPU"
  framework: "AIMS framework"
metrics: ["FES barrier height (kcal/mol) per hyperparameter setting", "CV (std/mean) of barrier across grid", "fraction of runs that converge within 150ps"]
baseline: "WT-MetaD baseline on 3x3 grid: height in [0.5, 1.0, 2.0] kJ/mol, sigma in [0.03, 0.05, 0.10]"
outcome: ""
key_result: ""
linked_idea: "opes-pimd-quantum-free-energy-enhanced"
date_planned: 2026-05-08
date_completed: ""
run_log: ""
started: ""
estimated_hours: 20
remote:
  server: ""
  gpu: ""
  session: ""
  started: ""
  completed: ""
---

## Objective

Systematically compare hyperparameter sensitivity between OPES and WT-MetaD in PIMD. This isolates the practical robustness advantage claimed for OPES: fewer parameters to tune means more reproducible results across users and systems.

## Setup

- **OPES grid** (2x2 = 4 conditions):
  - PACE: 200, 500 steps
  - BARRIER: 3.0, 8.0 kJ/mol
  - (SIGMA fixed at initial 0.05, auto-adapts)
- **WT-MetaD grid** (3x3 = 9 conditions):
  - HEIGHT: 0.5, 1.0, 2.0 kJ/mol
  - SIGMA: 0.03, 0.05, 0.10
  - BIASFACTOR: 10 (fixed)
- Each condition: 1 run × 150 ps on FAD system
- Total: 4 + 9 = 13 runs × 150 ps = ~13 GPU-hours

## Procedure

1. Run all OPES grid points (4 runs) and WT-MetaD grid points (9 runs) on FAD PIMD
2. Reconstruct FES for each run; extract barrier height
3. Compute: CV(OPES) = std(barrier_OPES_grid) / mean(barrier_OPES_grid)
4. Compute: CV(WT-MetaD) = std(barrier_WTMetaD_grid) / mean(barrier_WTMetaD_grid)
5. Count convergence failures: runs where FES does not stabilize within 150 ps
6. Report: CV ratio, failure rates, range of barrier heights per method

## Results

(to be filled after /exp-run)

## Analysis

- **Success criterion**: CV(OPES) < CV(WT-MetaD) / 2, i.e., at least 2x lower sensitivity
- **Secondary**: fewer convergence failures in OPES grid than WT-MetaD grid
- Report best/worst case barrier for each method (range)
- If CV(OPES) ~ CV(WT-MetaD): OPES robustness advantage does not transfer to PIMD; revise claim

## Claim updates

(to be filled after /exp-eval)

## Follow-up

- **OPES more robust** → strong practical argument; include in paper introduction
- **Comparable sensitivity** → downgrade claim to "similar sensitivity" rather than "lower"
