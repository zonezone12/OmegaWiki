---
title: "OPES converges quantum-corrected free energy surfaces faster and with fewer hyperparameters than WT-MetaD in PIMD simulations"
slug: "opes-pimd-converges-quantum-fes-faster"
status: challenged
confidence: 0.2
tags: [pimd, opes, enhanced-sampling, convergence, metadynamics, nuclear-quantum-effects, free-energy]
domain: "ML Systems"
source_papers: []
evidence:
  - source: wt-metad-pimd-fad-baseline-reproduction
    type: invalidates
    strength: moderate
    detail: "v3 (exp(−bias/kT), 300 ps × 3 seeds): WT-MetaD barrier = 0.352 ± 0.021 kcal/mol with all seeds crossing TS within ~50 ps. OPES Run 9 on same FallbackFF: 3.897 ± 2.116 kcal/mol with zero TS crossings in 300 ps. WT-MetaD 11× more accurate and >6× faster for first TS crossing on FallbackFF with correct reweighting. Limited to FallbackFF (quantum barrier 0.352 kcal/mol ≠ GFN target 1.52 kcal/mol)."
  - source: opes-pimd-fad-proton-transfer-convergence
    type: invalidates
    strength: weak
    detail: "OPES needed 215+ ps for first TS crossing on FallbackFF; WT-MetaD converged in 150 ps (OPES 1.43× slower). 3-seed mean barrier 2.579 ± 1.247 kcal/mol vs WT-MetaD 1.494 kcal/mol. Evidence strength weak: FES reweighting sign bug (exp+bias instead of exp-bias) and FallbackFF barrier mismatch (~5.9 vs 1.52 kcal/mol) confound both measurements."
  - source: mlff-pimd-fad-barrier-comparison
    type: tested_by
    strength: moderate
    detail: "Prerequisite MLFF survey: PhysNet (MP2/aVTZ) 27.4 kcal/mol, MACE-OFF23 30.1 kcal/mol, ANI-2x (wB97X/6-31G*) 37.7 kcal/mol — all show zero TS crossings in 50–150 ps WT-MetaD PIMD (9 runs, 3 FFs × 3 seeds). The Fan et al. 1.52 kcal/mol target is specific to GFN2-xTB PES; no ab-initio MLFF can reproduce it. A valid OPES vs WT-MetaD FAD comparison requires GFN2-xTB-level FF, which is not yet in the toolkit. Result: INCONCLUSIVE for the claim (WT-MetaD only used, no OPES comparison possible without suitable FF)."
conditions: "PIMD enhanced sampling in AIMS framework; GFN-based MLFF; systems with conformational CVs (not ring-polymer shape CVs). Comparison is OPES_METAD vs. WT-MetaD with centroid or bead-averaged CV biasing."
date_proposed: 2026-05-08
date_updated: 2026-05-14
---

## Statement

Within path integral molecular dynamics simulations using the AIMS framework, OPES (specifically OPES_METAD variant) converges the quantum-corrected free energy surface at least 2x faster (in wall-clock time or force evaluations) than well-tempered metadynamics, while requiring fewer hyperparameter tuning iterations and producing results of comparable or higher accuracy.

## Evidence summary

**Against (weak)**: `opes-pimd-fad-proton-transfer-convergence` (Run 8, 2026-05-09) — OPES with PACE=500, sigma=0.15 was 1.43× slower than WT-MetaD on FAD proton transfer (215+ ps vs 150 ps for first TS crossing). 3-seed mean barrier 2.579 ± 1.247 kcal/mol, all failed target. Evidence is weak because: (1) FES reweighting has wrong sign (exp+bias/kT instead of exp−bias/kT), invalidating absolute barrier values for both OPES and WT-MetaD; (2) FallbackFF double-well quantum barrier ~5.9 kcal/mol is 3.9× higher than GFN target ~1.52 kcal/mol — wrong system. The comparison to the 1.52 kcal/mol target is therefore not valid for the intended GFN FF.

**Indirect prior support (unchanged)**: (1) OPES vs WT-MetaD comparisons in classical MD consistently show 2-5x convergence speedup; (2) Fan et al. 2025 demonstrates feasibility of WT-MetaD within PIMD; (3) OPES-eABF hybrid (2025) shows OPES retains advantages in hybrid sampling contexts.

**Inconclusive (2026-05-13)**: `mlff-pimd-fad-barrier-comparison` — prerequisite MLFF survey found no ab-initio MLFF can reproduce the Fan et al. GFN2-xTB barrier (1.52 kcal/mol) with standard WT-MetaD settings. Barriers 18–25× higher (PhysNet 27.4, MACE-OFF23 30.1, ANI-2x 37.7 kcal/mol) across 9 runs. Does not directly test OPES; blocks valid OPES vs WT-MetaD comparison until GFN2-xTB-level FF is available.

## Conditions and scope

- Comparison applies to CV-based enhanced sampling of conformational CVs (reaction coordinates, order parameters)
- Does not apply to ring-polymer shape biasing (path integral metadynamics, Pietrucci 2015)
- AIMS framework required for the OPES integration
- Speedup claim is for systems where WT-MetaD requires >100 ps to converge

## Counter-evidence

- OPES kernel density estimation may have higher per-step overhead than WT-MetaD Gaussian deposition
- For short simulations where WT-MetaD converges quickly, OPES overhead may dominate

## Linked ideas

- [[opes-pimd-quantum-free-energy-enhanced]]

## Open questions

- Does OPES speedup transfer from classical to quantum (PIMD) enhanced sampling?
- What is the optimal KDE kernel bandwidth for PIMD bead-averaged CV distributions?
- Which FF level of theory gives a FAD proton-transfer barrier compatible with GFN2-xTB (~1.52 kcal/mol)? Ab-initio MLFFs (MP2/aVTZ, B3LYP-D3BJ, wB97X/6-31G*) all give 27–38 kcal/mol — fundamentally different PES from GFN2-xTB.
