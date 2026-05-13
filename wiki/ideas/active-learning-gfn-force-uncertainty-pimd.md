---
title: "Active-Learning GFN: Force-Uncertainty Committee for On-the-Fly MLFF Expansion During PIMD"
slug: "active-learning-gfn-force-uncertainty-pimd"
status: proposed
origin: "ideate"
origin_gaps: ["ml-pimd-aims-framework-achieves-quantum"]
tags: [pimd, machine-learning-force-fields, graph-field-network, active-learning, uncertainty-quantification]
domain: "ML Systems"
priority: 4
pilot_result: ""
failure_reason: ""
linked_experiments: []
date_proposed: 2026-05-08
date_resolved: ""
---

## Motivation

Fan et al. (2025) trained GFN force fields statically before PIMD, relying on a fixed training dataset (2918 FAD conformations, 1204 water configurations). PIMD explores ring polymer configurations that may differ from standard MD configurations, potentially causing out-of-distribution failures. Active learning approaches (UDD-AL, FALCON, Solovykh et al. 2025) have shown that on-the-fly dataset expansion during MD/PIMD dramatically improves transferability for energy-based MLFFs. However, active learning for force-only MLFFs is unexplored — the absence of energy prediction changes uncertainty calibration.

## Hypothesis

A committee of 3-5 GFN models trained from different random initializations can provide reliable force uncertainty estimates (via variance across committee predictions). Using this uncertainty to trigger DFT calculations on high-uncertainty PIMD configurations, then retraining, will reduce force RMSE on PIMD-relevant configurations by 50%+ compared to static training, at a total computational cost that remains much lower than FPMD.

## Approach sketch

1. **Committee training**: Train 3-5 independent GFN models on the same dataset with different random seeds. Uncertainty = std(F_1, F_2, ..., F_N) over committee predictions for each atom.

2. **Active learning loop**:
   - Start PIMD simulation with initial GFN committee
   - At each step, compute uncertainty for all bead configurations
   - If max(uncertainty) > threshold: flag configuration as candidate
   - Every K steps: evaluate DFT forces on flagged configurations; add to training set; retrain committee
   - Continue PIMD with updated committee

3. **PIMD-specific challenge**: Bead configurations sample paths in ring polymer space, not just equilibrium configurations. The active learning loop should preferentially collect bead configurations near transition states (high CV values) where PIMD accuracy matters most.

4. **Benchmark**: FAD proton transfer system from Fan et al. Compare:
   - Static GFN (Fan et al. baseline): 0.48 kcal/(mol*A) force RMSE
   - Active-learning GFN: force RMSE after 3 active learning cycles
   - Cost: total DFT evaluations in active learning vs. full static training set (2918)

5. **Force-only calibration analysis**: Check if force-only committee uncertainty is well-calibrated (uncertainty correlates with actual force error). This is a methodological contribution independent of the PIMD application.

## Expected outcome

Active-learning GFN should achieve lower force RMSE on PIMD configurations (especially near transition states) than static GFN, with fewer total DFT evaluations. Force-only committee uncertainty will be better calibrated for forces than energy-based committee uncertainty for forces (since GFN is directly trained on forces).

## Risks

- Force-only committee uncertainty may not be well-calibrated: without energy prediction, the committee models may all converge to locally consistent force fields that disagree only in unimportant high-frequency modes
- PIMD active learning cycle may not converge: if bead configurations keep triggering retraining indefinitely, the approach becomes expensive
- Committee inference overhead: 3-5x GFN evaluations per step; may eliminate the 1200x speedup advantage vs FP-PIMD

## Pilot results

(empty)

## Lessons learned

(empty)
