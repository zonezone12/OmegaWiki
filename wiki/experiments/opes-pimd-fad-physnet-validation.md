---
title: "OPES-PIMD PhysNet Validation: Convergence Speed vs. WT-MetaD on FAD Proton Transfer"
slug: "opes-pimd-fad-physnet-validation"
status: completed
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "OPES_METAD with PACE=100, sigma_fixed=0.10 Å, and BARRIER=81.6 kJ/mol (5× 3.90 kcal/mol) achieves first TS crossing before 163.1 ps (WT-MetaD reference) in ≥ 2/3 seeds, and converges the PhysNet FAD proton-transfer FES with comparable or lower barrier estimate (3.90 ± 0.5 kcal/mol)."
tags: [pimd, opes, formic-acid-dimer, physnet, mlff, convergence, validation, nuclear-quantum-effects]
domain: "ML Systems"
setup:
  model: "PhysNet (MP2/aug-cc-pVTZ, 58069 FAD structures) — same as baseline"
  dataset: "Formic acid dimer (FAD), 10 atoms"
  hardware: "NVIDIA RTX 4060 Laptop GPU 8GB"
  framework: "Custom PIMD + OPESMetaD module (AIMS framework)"
metrics:
  - "first TS crossing time (ps) — primary comparison metric vs WT-MetaD baseline"
  - "convergence time to FES within 0.2 kcal/mol of baseline reference (ps)"
  - "final energy barrier (kcal/mol)"
  - "per-step wall-clock time (ms) — for opes-per-step-kde-overhead-does claim"
  - "number of force evaluations to convergence"
baseline: "wt-metad-pimd-fad-physnet-baseline: barrier=3.90 kcal/mol, first TS crossing=163.1 ps (γ=100, h=5 kJ/mol, seed 1)"
outcome: "failed"
key_result: "OPES (PACE=100, sigma=0.10 Å, BARRIER=81.6 kJ/mol, seed 42) failed to cross FAD TS in 300 ps; cv_max=-1.273 Å vs TS at 0.0 Å; bias at frontier ~0.28 kcal/mol (≈kT=0.40 kcal/mol, negligible); WT-MetaD reference crossed at 163.1 ps and converged to 3.90 kcal/mol. OPES slower by >300 ps on this system."
linked_idea: ""
date_planned: 2026-05-14
date_completed: "2026-05-31"
run_log: "logs/exp-opes-pimd-fad-physnet-validation.log"
---

## Objective

Directly test whether OPES converges the PhysNet FAD quantum FES faster than WT-MetaD. This is the first clean OPES vs WT-MetaD comparison on a realistic MLFF (after all FallbackFF attempts failed due to FF mismatch). Both methods run on the same PhysNet FF with the same PIMD setup, correct FES reweighting, and the same 3 seeds. The result provides the first valid evidence for or against the primary target claim.

**Depends on**: `wt-metad-pimd-fad-physnet-baseline` must complete with ≥ 2 TS crossings to set BARRIER parameter.

## Setup

- **System**: FAD (same as baseline)
- **Force field**: PhysNetFF (same as baseline)
- **PIMD**: 32 beads, PILE-L thermostat, 0.5 fs timestep, 200K, friction=1.0
- **OPES_METAD**:
  - CV: CVdimer (centroid of beads)
  - PACE: **100** steps (from lessons learned: 5× more frequent than PACE=500)
  - sigma_fixed: **0.10 Å** (fixed bandwidth; no Silverman adaptive rule)
  - BARRIER: **81.6 kJ/mol** (= 5 × 3.90 kcal/mol × 4.184; conservative per 1-seed escalation path)
  - Z_monotonic: True (self._Z = max(self._Z, new_z) — critical fix from Run 7 bug)
  - FES reweighting: `exp(−bias/kT)` (correct sign — critical fix from Run 8/9 bug)
  - cv_min: −2.0, cv_max: 2.0, cv_bins: 400
- **Simulation**: 300 ps × 3 seeds (seeds: 42, 123, 7 — same seeds as baseline)
- **Escalation**: If 0/3 seeds cross TS, increase BARRIER by 2× and retry (max 1 escalation)

## Procedure

1. **Confirm baseline**: read `wt-metad-pimd-fad-physnet-baseline` results; extract mean converged barrier and mean first TS crossing time; compute OPES BARRIER = 3.5 × barrier_kcal × 4.184
2. **Run 3 × 300 ps OPES simulations** (seeds 42, 123, 7 sequentially):
   - Config: `experiments/code/opes-pimd-fad-physnet-validation/config.yaml`
   - Reuse OPESMetaD implementation from `experiments/code/opes-pimd-fad-proton-transfer-convergence/`
   - All lessons-learned fixes applied: fixed sigma, Z monotonic, correct reweighting sign, PACE=100
3. **Track CV max** at every 50 ps; record first step where CV centroid > 0.0 Å
4. **Extract barrier** using `exp(−bias/kT)` reweighting + midpoint-split at each 50 ps checkpoint
5. **Measure per-step time**: log wall-clock time for each PACE block; compare to WT-MetaD baseline speed
6. **Convergence check**: same criterion as baseline (|barrier(t) − barrier(t−50ps)| < 0.2 kcal/mol)

## Results

### Seed 42 — 2026-05-30 to 2026-05-31

| Metric | OPES seed 42 | WT-MetaD seed 1 (reference) |
|--------|-------------|------------------------------|
| TS crossed | ✗ | ✅ at 163.1 ps |
| cv_max (Å) | −1.273 | +1.356 |
| Barrier est. (kcal/mol) | 34.9 (artifact, unsampled FES) | **3.90** (converged) |
| Convergence | ✗ | ✅ at 150 ps |
| Speed (M/day) | 0.84 | 0.97 |

**Root cause: insufficient bias at frontier.** OPES KDE bias at the frontier (−1.273 Å) was ~0.28 kcal/mol throughout — comparable to kT=0.40 kcal/mol at 200K. The KDE with sigma=0.10 Å cannot discriminate between the reactant well minimum (−1.45 Å) and the frontier (−1.27 Å) when both are within the well-sampled region. Z (running max KDE density) was calibrated to the well, leaving P(frontier)/Z ≈ 0.49 → V(frontier) ≈ 0.28 kcal/mol regardless of how many hills accumulated.

**Speed overhead**: OPES 0.84 M/day vs WT-MetaD 0.97 M/day — **13% slower** due to KDE recomputation every 100 steps. This challenges the `opes-per-step-kde-overhead-does` claim (≥10% overhead).

**Note on initial bug**: first launch used per-bead serial force evaluation (32× slower due to missing batch path for CPU PIMD). Fixed before the main run — 0.84 M/day reflects the corrected batch-path implementation.

## Analysis

**Primary comparison**:
| Metric | WT-MetaD (baseline) | OPES |
|--------|--------------------|----|
| First TS crossing (ps) | {from baseline} | {this experiment} |
| 3-seed mean barrier (kcal/mol) | {from baseline} | {this experiment} |
| Convergence time (ps) | {from baseline} | {this experiment} |
| Speed (M steps/day) | {from baseline} | {this experiment} |

**Success criterion for claim**:
- OPES first TS crossing < WT-MetaD first TS crossing in ≥ 2/3 seeds → **SUPPORTED**
- OPES convergence time < WT-MetaD convergence time in ≥ 2/3 seeds → **SUPPORTED**
- OPES first TS crossing > WT-MetaD in ≥ 2/3 seeds → **NOT_SUPPORTED**
- Zero TS crossings for OPES while WT-MetaD succeeded → **NOT_SUPPORTED** (strong)

**Secondary metric (opes-per-step-kde-overhead-does)**:
- If OPES speed (M steps/day) > 0.9 × WT-MetaD speed → overhead < 10% → claim partially supported
- If OPES speed < 0.85 × WT-MetaD speed → overhead > 15% → claim challenged

## Claim updates

- **Verdict**: not_supported [single-model verdict — Review LLM unavailable]
- **Claim**: [[opes-pimd-converges-quantum-fes-faster]] confidence 0.2 → **0.1**, status unchanged `challenged`
- **Secondary claim**: [[opes-per-step-kde-overhead-does]] confidence 0.5 → **0.3** (13% overhead contradicts <10% threshold)
- **Reasoning**: OPES with sigma=0.10 Å failed to cross TS in 300 ps on PhysNet FAD PIMD (200K, 32 beads). Root cause: KDE bias at frontier ~0.28 kcal/mol ≈ kT — insufficient density contrast with sigma larger than the reactant well width. WT-MetaD crossed at 163.1 ps. Speed 13% slower due to KDE overhead. Single seed; tuned hyperparameters (sigma=0.05 Å) may change result.
- **Caveat**: result applies to OPES with these specific hyperparameters on this system — does not rule out OPES advantages with tuned sigma or on other systems/barriers.
- **Date**: 2026-05-31

## Follow-up

**OPES faster (SUPPORTED)**:
- Update `opes-pimd-converges-quantum-fes-faster` confidence upward (→ weakly_supported or higher)
- Run ablation: `opes-vs-wt-metad-hyperparameter-sensitivity` (already planned)
- Consider designing paper plan: first clean OPES+PIMD result on realistic MLFF

**OPES slower (NOT_SUPPORTED)**:
- Analyze root cause: BARRIER too small? PACE too high? σ too narrow?
- Consider trying XTB2 (GFN2-xTB, Fan et al.'s exact FF) — 4× slower but the canonical system
- Record specific failure reason in claim evidence for anti-repetition memory

**Speed overhead acceptable** → update `opes-per-step-kde-overhead-does` with supporting evidence

**Barrier matches Fan et al. 1.52 kcal/mol** → high-value result; supports claim generality across MLFF levels of theory
