---
title: "Robustness: OPES-PIMD Multi-Temperature Water Melting Point Prediction"
slug: "opes-pimd-temperature-robustness-water-melting"
status: planned
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "OPES-PIMD correctly reproduces the temperature dependence of the water-ice free energy difference across 270-315K, predicting a quantum melting point of ~285K consistent with Fan et al. and more efficiently than WT-MetaD."
tags: [pimd, opes, water-ice, temperature-robustness, phase-transition, nuclear-quantum-effects]
domain: "ML Systems"
setup:
  model: "MolCT-GFN water force field"
  dataset: "64 water molecules, 4 temperatures: 270K, 285K, 300K, 315K"
  hardware: "NVIDIA A100 80GB GPU"
  framework: "AIMS framework with OPES_METAD"
metrics: ["DeltaF(T) = F_ice - F_water for each temperature", "quantum melting point (K) from DeltaF = 0 crossing", "convergence time per temperature"]
baseline: "Fan et al. 2025 WT-MetaD-PIMD: Tm ~285K (quantum), ~295K (classical)"
outcome: ""
key_result: ""
linked_idea: "opes-pimd-quantum-free-energy-enhanced"
date_planned: 2026-05-08
date_completed: ""
run_log: ""
started: ""
estimated_hours: 40
remote:
  server: ""
  gpu: ""
  session: ""
  started: ""
  completed: ""
---

## Objective

Stress-test OPES-PIMD across multiple temperatures to verify: (1) the full quantum-corrected melting point curve is recovered, not just a single temperature, (2) OPES convergence is consistently faster across all temperatures, (3) the predicted Tm matches Fan et al. within 5K.

## Setup

- **4 temperatures**: 270K, 285K, 300K, 315K
- **Enhanced sampling**: OPES_METAD with XRD CV (best settings from water-ice validation experiment)
- **Run length**: 50 ns per temperature (reduced from 75 ns for compute budget; OPES faster convergence)
- **Seeds**: 1 run per temperature (limited budget; 40 GPU-hours total estimate)
- Comparison: Fan et al. WT-MetaD-PIMD DeltaF vs. temperature

## Procedure

1. Run 4 OPES-PIMD simulations at 270, 285, 300, 315K simultaneously (if 4 GPUs available)
2. Reconstruct FES and compute DeltaF at each temperature
3. Plot DeltaF vs. T; fit linear interpolation to find Tm (DeltaF = 0 crossing)
4. Compare to Fan et al.: Tm ~285K (quantum), ~295K (classical)
5. Compare convergence time per temperature to Fan et al. 75ns WT-MetaD runs

## Results

(to be filled after /exp-run)

## Analysis

- **Primary criterion**: |Tm(OPES) - 285K| < 5K
- **Robustness criterion**: OPES correctly predicts DeltaF sign at all 4 temperatures (negative at 270K, positive at 315K)
- **Convergence criterion**: OPES reaches stable DeltaF in < 50 ns at all temperatures
- If Tm is off by > 5K: check force field accuracy (DFT-level systematic error may dominate)

## Claim updates

(to be filled after /exp-eval)

## Follow-up

- **Full temperature curve correct** → publish OPES-PIMD as drop-in replacement for WT-MetaD-PIMD
- **Off at specific temperatures** → document temperature-dependent limitations; recommend validation run
- **Tm very different from classical (295K)** → enhanced quantum effect; worth investigating separately
