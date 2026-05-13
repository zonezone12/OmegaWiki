---
title: "OPES-PIMD: Replace Well-Tempered MetaD with OPES as Enhanced Sampling Driver in Quantum PIMD"
slug: "opes-pimd-quantum-free-energy-enhanced"
status: failed
origin: "ideate"
origin_gaps: ["ml-pimd-aims-framework-achieves-quantum", "opes-unified-enhanced-sampling-framework"]
tags: [pimd, opes, enhanced-sampling, nuclear-quantum-effects, free-energy, metadynamics]
domain: "ML Systems"
priority: 5
pilot_result: "Run 8 (300 ps, FallbackFF, PACE=500, sigma=0.15, BARRIER=60 kJ/mol): 3-seed mean barrier 2.579 ± 1.247 kcal/mol; OPES needed 215+ ps for first TS crossing vs WT-MetaD 150 ps."
failure_reason: "OPES on FallbackFF (quantum barrier ~5.9 kcal/mol, 3.9× higher than GFN target) was 1.43× slower than WT-MetaD for FAD proton transfer. Three code/setup issues prevent valid evaluation: (1) FES reweighting sign bug — exp(+bias/kT) instead of exp(−bias/kT) corrupts barrier measurements for both methods; (2) FallbackFF quantum barrier ~5.9 kcal/mol ≠ GFN target ~1.52 kcal/mol, making 1.52 kcal/mol target irrelevant; (3) PACE=500 too slow for steep FallbackFF barrier. Re-test requires: fix sign bug in OPESMetaD.fes(), obtain GFN checkpoint, reduce PACE to 100–200, and establish WT-MetaD baseline on the same FF for fair comparison."
linked_experiments:
  - wt-metad-pimd-fad-baseline-reproduction
  - opes-pimd-fad-proton-transfer-convergence
  - opes-pimd-water-ice-phase-transition
  - opes-pimd-centroid-vs-bead-averaged
  - opes-vs-wt-metad-hyperparameter-sensitivity
  - opes-pimd-temperature-robustness-water-melting
date_proposed: 2026-05-08
date_resolved: "2026-05-09"
---

## Motivation

Fan et al. (2025, our wiki) implemented PIMD in the AIMS framework with well-tempered metadynamics (WT-MetaD) as the enhanced sampling driver. Meanwhile, OPES (the Invernizzi-Parrinello group) has superseded WT-MetaD as the state-of-the-art CV-based enhanced sampling method, offering faster convergence, fewer hyperparameters, and a principled probabilistic framework. No paper has yet combined OPES with PIMD — the two most recent advances in their respective domains sit side by side in this wiki without being connected.

## Hypothesis

Replacing WT-MetaD with OPES as the enhanced sampling driver within PIMD simulations (using the AIMS framework) will yield faster convergence of quantum-corrected free energy surfaces with fewer tunable hyperparameters, particularly for systems where the current WT-MetaD approach requires long simulations to converge (e.g., water-ice phase transitions).

## Approach sketch

1. **Integration**: Implement OPES (OPES_METAD variant) as a pluggable enhanced sampling module in the AIMS framework, applying the bias to the centroid CV (average over bead positions) or to individual bead CVs with path-integral reweighting.
2. **Key design choice**: CV definition for PIMD — bias the centroid coordinate (quasi-classical approximation, fast) vs. bead-averaged free energy via path-integral reweighting (fully quantum, slower but exact). Test both.
3. **Benchmark system 1**: Formic acid dimer proton transfer — compare convergence rate of OPES-PIMD vs. WT-MetaD-PIMD (Fan et al. baseline) to reach FES within 0.1 kcal/mol accuracy.
4. **Benchmark system 2**: Water-ice phase transition — compare convergence time and FES accuracy at 315 K.
5. **Metrics**: convergence time to 0.1 kcal/mol FES accuracy, number of force evaluations, sensitivity to hyperparameter choices.

## Expected outcome

OPES should converge the quantum FES 2-5× faster than WT-MetaD on the same systems, based on analogous speedups in classical MD (OPES vs. MetaD). The reduced parameter sensitivity (OPES needs only stride and optional target, vs. MetaD height/width/gamma) will make the method more reproducible.

## Risks

- OPES's kernel density estimation may be slower per step than Gaussian deposition in WT-MetaD, partially offsetting convergence gains
- The optimal CV definition for PIMD + OPES (centroid vs. bead-averaged) is unclear and may require system-specific tuning
- AIMS framework integration may require non-trivial code changes to support OPES's probability estimation logic

## Pilot results

Run 8 (300 ps, FallbackFF, PACE=500, sigma=0.15, BARRIER=60 kJ/mol, 3 seeds): OPES needed 215+ ps for first TS crossing vs WT-MetaD 150 ps. 3-seed mean barrier 2.579 ± 1.247 kcal/mol (seeds 42/123/7: 1.875/4.019/1.843), all above 1.52 ± 0.15 target. OPES 1.43× slower than WT-MetaD. 8 iterative bug-fix runs required to reach this stage (Z monotonicity, FES reweighting, KDE bandwidth, BARRIER scaling).

## Lessons learned

1. **FES reweighting sign**: OPES reweighting requires `exp(−bias/kT)` not `exp(+bias/kT)`; wrong sign upweights TS samples by exp(36) = 10¹⁵, making FES measurement nonsensical without TS crossings.
2. **FallbackFF barrier mismatch**: FallbackFF double-well produces quantum barrier ~5.9 kcal/mol at 200K/32 beads, 3.9× higher than GFN target. Never use FallbackFF for OPES vs WT-MetaD comparison — barriers are incommensurable.
3. **Z monotonicity is critical**: OPES invariant requires Z = max over all history; resetting to recent samples collapses frontier bias and stalls exploration. Must use `self._Z = max(self._Z, new_z)`.
4. **PACE=500 too slow**: With steep barriers, reduce to PACE=100 for 5× more frequent bias updates.
5. **BARRIER sizing**: Effective bias at TS = BARRIER×(γ−1)/γ must exceed the physical quantum barrier. For FallbackFF ~5.9 kcal/mol, BARRIER must be > 25 kcal/mol (> 105 kJ/mol).
