---
title: "OPES-PIMD Validation: Water-Ice Phase Transition at 315K"
slug: "opes-pimd-water-ice-phase-transition"
status: planned
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "OPES-PIMD correctly predicts the quantum-corrected free energy difference between water and ice phases at 315K (DeltaF consistent with Fan et al. ~0 at melting point), converging faster than the WT-MetaD baseline (75 ns simulation time)."
tags: [pimd, opes, water-ice, phase-transition, nuclear-quantum-effects, validation]
domain: "ML Systems"
setup:
  model: "MolCT-GFN water force field (64 H2O molecules, SCAN functional training data)"
  dataset: "64 water molecules in orthogonal periodic box"
  hardware: "NVIDIA A100 80GB GPU"
  framework: "AIMS framework with OPES_METAD module"
metrics: ["free energy difference DeltaF = F_ice - F_water (kJ/mol)", "convergence time (ns) to stable DeltaF", "melting point (K) from DeltaF vs. temperature", "per-step wall-clock time"]
baseline: "Fan et al. 2025: WT-MetaD-PIMD 75ns runs at 315K; DeltaF approximately 0 at melting point ~285K"
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

Validate OPES-PIMD on the water-ice phase transition system from Fan et al. (2025). The 75 ns simulation time required for WT-MetaD convergence is the primary target to beat. Success demonstrates OPES-PIMD is not only faster on simple reactions but also on complex bulk phase transitions.

## Setup

- **System**: 64 water molecules in periodic box, NVT ensemble
- **Force field**: MolCT-GFN water (from Fan et al.; 100k parameters, SCAN functional)
- **PIMD**: 32 beads, PILE-L thermostat, 0.5 fs timestep
- **Temperature**: 315K (near melting point) — single temperature run
- **Enhanced sampling**: OPES_METAD applied to XRD-based CV (s_water = XRD intensity)
  - Same CV as Fan et al.; PACE = 100 steps
- **Simulation budget**: up to 75 ns (same as Fan et al. WT-MetaD baseline)
- **Seeds**: 2 independent runs (long simulation; limit to 2 for compute budget)

## Procedure

1. Set up 64-water system with GFN force field and PIMD (32 beads)
2. Configure OPES_METAD with XRD CV (theta=11.95°, lambda=1.54 Angstrom)
3. Run OPES-PIMD for up to 75 ns; save FES reconstruction every 5 ns
4. Track convergence: first t_conv where DeltaF (315K) stabilizes within 2 kJ/mol
5. Compare t_conv(OPES) vs. t_conv(WT-MetaD) = Fan et al. 75 ns
6. Estimate melting point from DeltaF at 315K (should show DeltaF > 0 if T > Tm)

## Results

(to be filled after /exp-run)

## Analysis

- **Primary criterion**: t_conv(OPES) < 75 ns with correct DeltaF sign at 315K
- **Accuracy criterion**: DeltaF(315K) consistent with quantum melting point ~285K (DeltaF > 0 at 315K)
- **Secondary**: per-step overhead vs WT-MetaD (document absolute overhead fraction)
- If DeltaF sign incorrect: check OPES convergence, try longer BARRIER estimate

## Claim updates

(to be filled after /exp-eval)

## Follow-up

- **Faster convergence**: strong evidence for opes-pimd-converges-quantum-fes-faster
- **Same convergence time**: OPES and WT-MetaD equivalent for bulk phase transitions; revise claim
- **Longer required**: OPES disadvantaged for bulk systems; constrain claim to small molecules only
