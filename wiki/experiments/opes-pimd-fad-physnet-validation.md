---
title: "OPES-PIMD PhysNet Validation: Convergence Speed vs. WT-MetaD on FAD Proton Transfer"
slug: "opes-pimd-fad-physnet-validation"
status: planned
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "OPES_METAD with PACE=100, sigma_fixed=0.10 Å, and BARRIER = 3.5 × PhysNet_quantum_barrier converges the PhysNet FAD proton-transfer FES in fewer force evaluations and less wall-clock time than the WT-MetaD baseline established in wt-metad-pimd-fad-physnet-baseline."
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
baseline: "wt-metad-pimd-fad-physnet-baseline: first TS crossing time and converged barrier (set after Stage 1)"
outcome: ""
key_result: ""
linked_idea: ""
date_planned: 2026-05-14
date_completed: ""
run_log: ""
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
  - BARRIER: **3.5 × baseline_barrier_kcal × 4.184 kJ/mol** (set after baseline completes)
    - Example: if baseline = 3.0 kcal/mol → BARRIER = 43.9 kJ/mol
    - Example: if baseline = 1.5 kcal/mol → BARRIER = 21.9 kJ/mol
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

(to be filled after /exp-run)

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

(to be filled after /exp-eval)

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
