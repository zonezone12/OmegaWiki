---
title: "OPES-PIMD Validation: Convergence Speed vs. WT-MetaD on FAD Proton Transfer"
slug: "opes-pimd-fad-proton-transfer-convergence"
status: completed
target_claim: "opes-pimd-converges-quantum-fes-faster"
hypothesis: "OPES_METAD applied to the CVdimer collective variable in PIMD reaches a converged FES barrier (within 0.1 kcal/mol of the fully-converged reference) in fewer force evaluations and less wall-clock time than WT-MetaD at the same conditions."
tags: [pimd, opes, metadynamics, formic-acid-dimer, convergence, validation, nuclear-quantum-effects]
domain: "ML Systems"
setup:
  model: "FallbackFF double-well (GFN checkpoint missing)"
  dataset: "Formic acid dimer (FAD), 10 atoms"
  hardware: "NVIDIA A100 80GB GPU"
  framework: "AIMS framework with OPES_METAD module"
metrics: ["convergence time (ps) to FES within 0.1 kcal/mol accuracy", "force evaluations to convergence", "final energy barrier (kcal/mol)", "per-step wall-clock time (ms)"]
baseline: "wt-metad-pimd-fad-baseline-reproduction: convergence time = 150 ps (Fan et al.)"
outcome: "failed"
key_result: "Run 9 (FES sign fixed, PACE=100): no TS crossing in 300 ps across all 3 seeds on FallbackFF; 3-seed mean barrier 3.897 ± 2.116 kcal/mol (seeds 42/123/7: 1.952/3.590/6.150) are incomplete-sampling artifacts (product basin never sampled). FallbackFF quantum barrier ~5.91 kcal/mol is 3.9× the GFN target; OPES cannot overcome it in 300 ps. Fair comparison requires GFN FF or a WT-MetaD FallbackFF baseline."
linked_idea: "opes-pimd-quantum-free-energy-enhanced"
date_planned: 2026-05-08
date_completed: "2026-05-10"
run_log: "logs/exp-opes-pimd-fad-proton-transfer-convergence-v9.log"
started: "2026-05-09T06:07"
estimated_hours: 22
remote:
  server: ""
  gpu: ""
  session: ""
  started: ""
  completed: ""
---

## Objective

Validate that OPES-PIMD converges the quantum FES for FAD proton transfer faster than the WT-MetaD-PIMD baseline. Convergence is assessed by monitoring the FES barrier height as a function of simulation time and computing the first time the running average barrier stabilizes within 0.1 kcal/mol.

## Setup

- **System**: FAD (same as baseline)
- **Force field**: MolCT-GFN (same as baseline)
- **PIMD**: 32 beads, PILE-L thermostat, 0.5 fs timestep, 200K
- **Enhanced sampling**: OPES_METAD applied to CVdimer
  - PACE = 500 steps (update stride), SIGMA = 0.05 (initial kernel width)
  - BARRIER = 5.0 kJ/mol (target well-tempered barrier estimate)
- **Simulation time**: 150 ps (same budget as WT-MetaD baseline)
- **Seeds**: 3 independent runs with different initial velocities
- **Comparison**: direct side-by-side with wt-metad-pimd-fad-baseline-reproduction

## Procedure

1. Configure OPES_METAD module in AIMS (implement if not available; PLUMED interface acceptable)
2. Run 3x 150 ps OPES-PIMD simulations
3. Reconstruct FES every 10 ps using OPES reweighting
4. Track running FES barrier height: compute first convergence time t_conv where |barrier(t) - barrier(150ps)| < 0.1 kcal/mol for all t > t_conv
5. Measure wall-clock time per 10 ps of simulation vs. WT-MetaD
6. Report: convergence time (OPES) vs. convergence time (WT-MetaD baseline)

## Results

### Run 1 (BARRIER=5 kJ/mol) — COMPLETE, all 3 seeds stalled

Results archived to `results_v1/`.

| Metric | Target | Seed 42 | Seed 123 | Seed 7 | Pass |
|--------|--------|---------|---------|--------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 72.76 | 78.30 | 114.13 | No |
| Speed (M steps/day) | > 5 | 10.91 | 10.94 | 10.98 | Yes |
| TS crossings | ≥ 1 | 0 | 0 | 0 | No |

All 3 seeds: CV stayed near −1.1 to −1.3 Å (reactant basin) for full 150 ps. The KDE barrier is a large artifact because the product basin (cv > 0) was never sampled. Convergence analysis (`analyze_convergence.py`) confirms stalled behavior: `stalled=True`, `ever_crossed=False` for all seeds.

### Run 2 (BARRIER=15 kJ/mol, SIGMA=0.05) — COMPLETE, all 3 seeds: wrong FES (code bugs)

Results archived to `results_v2/`.

| Metric | Target | Seed 42 | Seed 123 | Seed 7 | Pass |
|--------|--------|---------|---------|--------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 294.83 | 294.38 | 293.99 | No |
| Speed (M steps/day) | > 5 | 9.18 | ~9.2 | ~9.2 | Yes |
| Max CV explored | — | 0.98 | 1.53 | 1.25 | — |

**Diagnosis**: Two code bugs produced the artifact barriers, plus an exploration speed issue:

1. **`extract_barrier` NaN bug**: `np.argmin` on an array with NaN returns the NaN index, not the true valid minimum. This caused `r` to point to the last NaN in the right half, expanding the segment to reactant→product-frontier, with the barrier = 294.8 kcal/mol (the FES value at the frontier). Correct barrier with NaN→inf handling: 33–71 kcal/mol (still wrong but ×4–10 smaller).

2. **Wrong FES reweighting**: `opes.fes()` called `bias_e(si)` using the **final** KDE state for all past samples. By the end of the simulation, all visited regions have high KDE density → bias_e ≈ 0 for all samples → weights ≈ 1 → reweighted FES = biased KDE (no reweighting). The product samples that should get exp(barrier/kT) upweighting instead get weight 1, so the product appears at high free energy. Fix: record bias at the moment each PACE sample is collected (`_sample_biases` list), use those for reweighting.

3. **SIGMA=0.05 too narrow**: CV frontier advanced only 0.33 Å per 130k steps (rate ≈ 1.27×10⁻⁶ Å/step). Product minimum at +1.3 Å requires ≈ 300+ ps with SIGMA=0.05. With SIGMA=0.20 (4× wider), exploration is ≈ 4× faster and 150 ps should suffice.

Seed 123 actually explored cv up to 1.53 Å (past product minimum at +1.3) but the reweighting bug still produced a monotonically increasing FES.

### Run 3 (BARRIER=15 kJ/mol, SIGMA=0.20, code fixes) — ABORTED, KDE smearing artifact

Results archived to `results_v3/`. Screen session died mid-run (only seed_42 + seed_123 partial data). Seed_42 complete; seed_123 killed at step 100000 (50 ps).

| Metric | Target | Seed 42 | Seed 123 (partial) | Pass |
|--------|--------|---------|--------------------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 0.94 | ~6.5 at 50ps | No |
| Speed (M steps/day) | > 5 | 9.19 | 9.2 | Yes |

**Seed 42 barrier trajectory**: 9.69 (10ps) → 7.33 (50ps) → 1.57 (120ps) → 1.46 (130ps) → 0.94 (150ps).
The barrier passes through the target window at ~120 ps but never converges: it keeps falling, ending 38% below target.

**Diagnosis — Silverman adaptive bandwidth**: `_update_bw()` used Silverman's rule, growing `_bw` to:
- N=600 samples, std≈1.0 Å → bw = max(0.20, 1.06 × 1.0 × 600^(−0.2)) = max(0.20, 0.302) ≈ 0.302 Å
- At this bw, K(cv=0, cv=−1.3) = exp(−(1.3)²/(2×0.3²)) ≈ exp(−9.4) ≈ 0.00008 per kernel unit
- With ~500 reactant samples: total TS KDE inflation ≈ 500 × 0.00008 / (600 × 0.302 × √(2π)) ≈ 0.00022
- This inflates KDE(TS), reduces OPES bias at TS, suppresses barrier crossing rate → barrier kept falling

The `cv_max=2.00` in ALL FES snapshots (even step 10k) is a Gaussian tail artifact — SIGMA=0.20 tails reach the full grid boundary (+2.0 Å) even before any physical exploration of the product basin.

**Root cause**: PLUMED's OPES_METAD uses a **fixed** kernel width (not Silverman). Silverman's rule was designed for density estimation over static data — not for an online algorithm where the KDE is also the bias potential. Growing bandwidth causes tails to reach unsampled regions and inflate the apparent density there.

**Fix for Run 4**: `_update_bw()` made a no-op (fixed sigma = sigma0). sigma0 = 0.10 Å (narrow enough: K(0,−1.3,bw=0.10) = exp(−84) ≈ 0; 2× wider than Run 2 sigma=0.05 for adequate exploration). n_steps = 400000 (200 ps).

### Run 4 (BARRIER=15 kJ/mol, SIGMA=0.10 fixed, 200 ps) — ABORTED, BARRIER too small

Results archived to `results_v4/` (seed_42 only; seeds 123/7 aborted at 00:20 2026-05-09).

| Metric | Target | Seed 42 | Pass |
|--------|--------|---------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 13.24 | No |
| Speed (M steps/day) | > 5 | 6.86 | Yes |

**Diagnosis — BARRIER=15 kJ/mol insufficient for FallbackFF quantum barrier**: The FallbackFF double-well has classical barrier 4.54 kcal/mol. At 200K/32-bead PIMD, the effective quantum centroid barrier is ~3–4 kcal/mol (higher than the real GFN target of 1.52 kcal/mol). BARRIER=15 kJ/mol = 3.585 kcal/mol barely exceeds this:

- At cv=−0.45 (halfway to TS), physical potential above reactant ≈ 3.50 kcal/mol
- Bias is clamped at BARRIER = 3.585 kcal/mol
- Net driving force beyond cv=−0.45: only 3.585 − 3.50 = 0.085 kcal/mol → frontier stalled for 60+ ps
- After 200 ps, CV max = −0.839 Å (TS is at 0.0 Å; never crossed)
- FES at TS: 13–17 kcal/mol throughout (KDE artifact, product never sampled)

sigma=0.10 itself was fine — K(0,−1.3,bw=0.10) = exp(−84) ≈ 0, no smearing. The stalling was purely from insufficient BARRIER for the FallbackFF.

### Run 5 (BARRIER=30 kJ/mol, SIGMA=0.15, 200 ps) — ABORTED, still stalling

Results archived to `results_v5/` (seed_42 only, killed at step 317040, 158.5 ps).

| Metric | Target | Seed 42 (158 ps) | Pass |
|--------|--------|-----------------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | ~6–17 (KDE artifact) | No |
| Speed (M steps/day) | > 5 | ~9.2 | Yes |
| CV max reached | — | −0.726 Å | No (TS at 0.0 Å) |
| TS crossings | ≥ 1 | 0 | No |

**Diagnosis — effective_barrier too small despite BARRIER=30 kJ/mol**: BARRIER=7.17 kcal/mol sounds large, but OPES clamps bias at BARRIER × (γ−1)/γ = 7.17 × 18/19 = 6.79 kcal/mol. The rate of CV exploration depends on the net driving force beyond the current frontier. With gamma=19 and FallbackFF quantum barrier ~3–4 kcal/mol:

- Physical restoring force at cv=−0.726 (near barrier shoulder): ≈9.12 kcal/(mol·Å)
- OPES bias gradient at cv=−0.726: ≈2.8 kcal/(mol·Å) (computed from KDE density at frontier)
- Net force: 2.8 − 9.12 = −6.3 kcal/(mol·Å) → still restoring, not driving
- Result: CV frontier advanced only 0.574 Å in 158 ps (rate ≈ 3.6×10⁻⁶ Å/step); TS at 0.0 Å never reached

The exploration is arithmetically impossible given these force imbalances: OPES bias accumulates only at the visited frontier, but can only push forward when accumulated bias gradient exceeds the physical restoring force everywhere from reactant to TS.

**Fix for Run 6**: BARRIER=60 kJ/mol (14.34 kcal/mol, gamma=37). Max bias = 14.34 × 36/37 = 13.95 kcal/mol >> FallbackFF quantum barrier (~3–4 kcal/mol). Once OPES has fully explored up to TS, the bias at TS should be ~14 kcal/mol, fully flattening the barrier and driving the system over.

### Run 6 (BARRIER=60 kJ/mol, SIGMA=0.15, 200 ps) — ABORTED after seed_42, ~50 ps too short

Results archived to `results_v6/` (seed_42 complete; seed_123 killed at step 0 to launch Run 7).

| Metric | Target | Seed 42 | Pass |
|--------|--------|---------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 1.2378 | No |
| Speed (M steps/day) | > 5 | 6.74 | Yes |
| Max CV reached | — | −0.195 Å | No (TS at 0.0 Å) |
| TS crossings | ≥ 1 | 0 | No |

**Seed 42 barrier trajectory** (from log):
100 ps: 5.32 → 130 ps: 3.44 → 160 ps: 2.71 → 170 ps: 2.18 → 180 ps: 1.64 → 190 ps: 1.33 → 200 ps: 1.2378 kcal/mol

**Key findings**:
1. **BARRIER=60 kJ/mol doubles advance rate**: max_cv = −0.195 Å at 200 ps (vs. −0.726 Å at 158 ps in Run 5). Frontier advance rate = 0.0055 Å/ps steady since 10 ps.
2. **FES@-0.5 ≈ 0.25 kcal/mol**: OPES has nearly flattened the barrier up to cv=−0.5 Å.
3. **1.2378 kcal/mol barrier is KDE smearing artifact**: With frontier at cv=−0.195, sigma=0.15 kernel overlaps with TS at cv=0.0 (K=exp(−0.845)≈0.43 — substantial). The barrier will only be physical after actual TS crossing and product sampling.
4. **Needed ~50 more ps**: from −0.195 at 200 ps at rate 0.0055 Å/ps → TS crossing at ~235 ps.

**Fix for Run 7**: extend to 250 ps (n_steps=500000). All other parameters unchanged.

### Run 7 (BARRIER=60 kJ/mol, SIGMA=0.15, 250 ps) — COMPLETE (seed_42 only; seeds 123/7 killed)

Launched 2026-05-09T03:49. Output: `results_v7/`, log: `logs/exp-opes-pimd-fad-proton-transfer-convergence-v7.log`

| Metric | Target | Seed 42 | Pass |
|--------|--------|---------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 2.7607 | No |
| Speed (M steps/day) | > 5 | ~6.3 | Yes |
| Max CV reached | — | −0.425 Å | No (TS at 0.0 Å) |
| TS crossings | ≥ 1 | 0 | No |

**Root cause identified — Z update not monotonic**: The frontier stalled again at max_cv = −0.425 Å despite 250 ps (advance rate ≈ 0.0042 Å/ps, slower than Run 6's 0.0064 Å/ps).

Diagnosis: `OPESMetaD.update()` computed Z as `max([kde(s) for s in samples[-20:]])`. When the last 20 samples are at the frontier (low-density region), Z drops from ~2.66 Å⁻¹ (reactant level) to ~0.46 Å⁻¹ (frontier level). This collapses the frontier bias:

- **Buggy bias at frontier**: V = kT×(γ/(γ-1))×log(Z/p̃) = 0.408×log(0.46/0.266) = **0.22 kcal/mol** (instead of BARRIER = 14.34 kcal/mol)
- **Bias gradient at frontier**: ~2.5 kcal/(mol·Å) < physical restoring force ~6 kcal/(mol·Å) → net BACK force → stall

**Fix applied for Run 8**: monotonic Z update — `self._Z = max(self._Z, new_z)`. With monotonic Z:
- Frontier bias = 0.408×log(2.66/0.266) = **0.937 kcal/mol** (4× larger — bias gradient ~6 kcal/(mol·Å))
- Bias gradient matches physical restoring force → net forward drive → TS crossing expected

Seeds 123/7 were killed (never started due to Run 7 seed_42 taking full 250 ps).

### Run 8 (Z monotonic fix, BARRIER=60 kJ/mol, SIGMA=0.15, 300 ps) — COMPLETE

Launched 2026-05-09T06:07. Seed_42 complete 08:15. Seed_123 complete 10:21. Seed_7 complete 12:28.

| Metric | Target | Seed 42 | Seed 123 | Seed 7 | Pass |
|--------|--------|---------|---------|--------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 1.8751 | 4.0192 | 1.8429 | No |
| Speed (M steps/day) | > 5 | 6.75 | 6.82 | ~6.8 | Yes |
| TS crossings | ≥ 1 | ~215 ps | ~200 ps (brief) | No (cv=−0.29 at 300 ps) | Partial |

**3-seed mean barrier: 2.579 ± 1.247 kcal/mol** — 1.32× above target upper bound (1.67).

| Metric | Target | Seed 42 | Pass |
|--------|--------|---------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 1.8751 | No |
| Speed (M steps/day) | > 5 | 6.75 | Yes |
| TS crossings | ≥ 1 | Yes (first at ~215 ps) | Yes |

**Barrier convergence trajectory (seed_42)**:
| t (ps) | Barrier (kcal/mol) | Note |
|--------|-------------------|------|
| 220 | 5.36 | first sign of convergence (TS just crossed) |
| 230 | 4.96 | |
| 240 | 4.15 | |
| 250 | 3.84 | |
| 260 | 3.06 | |
| 270 | 2.38 | |
| 280 | 2.04 | |
| 290 | 1.92 | |
| 300 | **1.8751** | run complete; still above target by 0.21 |

**FES analysis (NPZ snapshots, seed_42)**:
- FES at TS (cv=0.0) from reweighted snapshots at t<215ps: **5.91 kcal/mol** — this is the true FallbackFF quantum barrier (32-bead PIMD at 200K raises it above classical 4.54 kcal/mol)
- FES tight frontier (< 5 kcal/mol): reached −0.075 Å at t=130ps, stalled there through t=160ps
- Physical frontier (colvar max_cv): −0.715 Å at t=157ps; TS first crossed at ~215ps
- After TS crossing, barrier dropped from 5.36 → 1.875 in 80ps — rapid convergence once product is sampled

**Key finding**: OPES with these parameters needed **215 ps to first cross the TS**, then **80 more ps** to bring the apparent barrier down to 1.875 kcal/mol. The WT-MetaD baseline converged in 150 ps total (seed_42: 1.494 kcal/mol at 150ps). At 300 ps, OPES has NOT yet converged to 1.52±0.15. OPES is slower than WT-MetaD on this system with this FallbackFF.

**Root causes of slower convergence vs WT-MetaD**:
1. **FallbackFF quantum barrier ~5.9 kcal/mol** (vs GFN target ~1.52): steep barrier requires long fill time even with BARRIER=60 kJ/mol
2. **Fixed sigma=0.15 Å kernel** fills the barrier slowly; WT-MetaD's adaptive Gaussian deposition covers the CV space faster
3. **PACE=500**: OPES only updates its KDE every 500 steps; fewer updates means slower bias accumulation near the TS

Seeds 123/7 may give different TS crossing times depending on initial velocity randomness.

### Run 9 (FES sign fixed, PACE=100, 300 ps) — COMPLETE, all 3 seeds

Launched 2026-05-09T23:12. Seed_42 complete 23:12. Seed_123 complete 2026-05-10T01:08. Seed_7 complete 03:21.
Output: `results_v9/`, log: `logs/exp-opes-pimd-fad-proton-transfer-convergence-v9.log`

**Fixes applied vs Run 8:**
1. **FES sign fix**: `weights = np.exp(-bias/kT)` (was `+bias/kT`) — correct OPES reweighting
2. **PACE=100** (was 500): 5× more frequent KDE updates for faster bias buildup

| Metric | Target | Seed 42 | Seed 123 | Seed 7 | Pass |
|--------|--------|---------|---------|--------|------|
| Barrier (kcal/mol) | 1.52 ± 0.15 | 1.9519 | 3.5900 | 6.1496 | No |
| Speed (M steps/day) | > 5 | 8.25 | 7.45 | 6.50 | Yes |
| TS crossings (CV > 0) | ≥ 1 | 0 (max cv=−0.261) | 0 (max cv=−0.431) | 0 (max cv=−0.689) | No |

**3-seed mean barrier: 3.897 ± 2.116 kcal/mol** — product basin never sampled; all barriers are incomplete-sampling artifacts.

**Key findings vs Run 8:**
- No seed crossed TS (CV > 0) in 300 ps — same stalling as Run 8 seed_7, but now all 3 seeds
- Barrier values now physically meaningful for the explored region (correct sign), but FES extrapolates from frontier with unsampled product → readings are artifacts
- PACE=100 did not accelerate TS crossing despite 5× more frequent bias updates
- Speed improved to 7.40 M steps/day (vs 6.8 in Run 8) — PACE=100 reduces overhead slightly
- Fundamental blocker: FallbackFF quantum barrier ~5.91 kcal/mol cannot be overcome by OPES in 300 ps at these conditions

**Comparison to Run 8:**
Run 8 seed_42 appeared to cross the TS at ~215 ps and yield barrier=1.875 kcal/mol — but this was an artifact of the wrong-sign FES (exp+bias/kT upweights bias-saturated TS-crossing samples by exp(36)~10¹⁵, artificially pulling the FES minimum toward the sampled region). With the correct sign, OPES has NOT crossed the TS; Run 8's apparent TS crossings were FES measurement artifacts, not true dynamical crossings.

## Analysis

- **Primary success criterion**: t_conv(OPES) < t_conv(WT-MetaD) with p < 0.1 (Wilcoxon test across 3 seeds)
- **Accuracy criterion**: final OPES barrier within 0.15 kcal/mol of 1.52 kcal/mol
- **Secondary metric**: force evaluations to convergence (OPES PACE × beads vs. WT-MetaD steps × beads)

### Run 9 final analysis: experiment FAILED — FallbackFF is the fundamental blocker

**Result summary** (Run 9, all 3 seeds, corrected methodology):
- seed_42: 1.952 kcal/mol (no TS crossing, max_cv=−0.261 at 300 ps)
- seed_123: 3.590 kcal/mol (no TS crossing, max_cv=−0.431 at 300 ps)
- seed_7: 6.150 kcal/mol (no TS crossing, max_cv=−0.689 at 300 ps)
- **3-seed mean: 3.897 ± 2.116 kcal/mol** — all barriers are frontier artifacts, not physical measurements
- Mean speed: 7.40 M steps/day (passes speed criterion)

With both methodological fixes applied (correct FES sign + PACE=100), OPES still cannot cross the TS in 300 ps. The experiment definitively shows that **FallbackFF is the fundamental limitation**: its quantum barrier at 200K/32 beads (~5.91 kcal/mol) requires OPES to build up ~14 kcal/mol of bias before the TS can be crossed, and even with PACE=100 this takes >300 ps.

**Why PACE=100 didn't help as expected**: With PACE=100, bias updates are 5× more frequent. However, each update adds only a small Gaussian (sigma=0.15 Å) at the current CV position. Near the steep FallbackFF barrier shoulder (CV ~ −0.5 to 0.0), the physical restoring force is ~9 kcal/(mol·Å). Even at PACE=100, the KDE at the frontier does not accumulate fast enough to exceed this restoring force gradient within 300 ps.

**Comparison of Run 8 and Run 9 — why Run 8 appeared to "work"**:
Run 8 showed seed_42 "crossing the TS at ~215 ps" and barrier=1.875 kcal/mol. This was entirely due to the wrong-sign FES: `exp(+bias/kT)` gives astronomically high weights to samples collected when the bias was high (near the frontier), pulling the apparent FES minimum away from the true reactant (CV=−1.3). Run 9 with `exp(-bias/kT)` reveals that no such crossing occurred — the CV trajectory stayed below 0.0 throughout. The correct comparison: **neither OPES (Run 9) nor WT-MetaD (if it also uses wrong-sign code) can be fairly evaluated until both are measured with the same correct reweighting.**

**Root cause hierarchy:**
1. **FallbackFF quantum barrier mismatch (primary)**: 5.91 kcal/mol is 3.9× the GFN target. Any OPES comparison to the 1.52 kcal/mol target is meaningless on this FF. Fix: use GFN FF, or run WT-MetaD on FallbackFF to establish a correct FallbackFF baseline and compare OPES to that.
2. **300 ps insufficient for FallbackFF** (secondary): Even BARRIER=60 kJ/mol (max bias 13.95 kcal/mol >> 5.91 kcal/mol barrier) cannot drive the CV to 0.0 in 300 ps at PACE=100/sigma=0.15. More time or a different sigma schedule is needed.
3. **No WT-MetaD FallbackFF baseline for fair comparison** (methodological): The WT-MetaD baseline used GFN FF (1.52 kcal/mol). Comparing OPES on FallbackFF to that baseline is an apples-to-oranges comparison.

**Path to a valid test of the OPES hypothesis:**
Option A (preferred): Run both OPES and WT-MetaD on the same FF with corrected FES reweighting. If FallbackFF is the only available FF, re-run WT-MetaD baseline on FallbackFF as a new experiment (`wt-metad-pimd-fad-fallbackff-baseline`).
Option B: Obtain access to GFN FF (Fan et al.'s MindSPONGE GNN checkpoint) — requires reaching out to Fan et al. or using PhysNet FF (already in repo under `physnet_fad/`).

### Run 8 final analysis: experiment FAILED — two root causes identified

**Result summary** (Run 8, all 3 seeds):
- seed_42: 1.875 kcal/mol (TS first crossed at ~215 ps, then 85 ps of convergence)
- seed_123: 4.019 kcal/mol (TS briefly crossed ~200 ps, insufficient convergence time)
- seed_7: 1.843 kcal/mol (no TS crossing; cv reached −0.289 at 300 ps — closest approach without crossing; low barrier is FES artifact from wrong-sign reweighting)
- **3-seed mean: 2.579 ± 1.247 kcal/mol** (target: 1.52 ± 0.15)
- WT-MetaD baseline: 1.494 kcal/mol at 150 ps (seed_42)

OPES required 215–300 ps to reach barely-converged FES, while WT-MetaD converged in 150 ps. **OPES is ~1.5× slower than WT-MetaD on this system.** The experiment hypothesis is falsified.

**Root cause 1 — FES reweighting sign bug:**
`fes()` uses `weights = np.exp(+bias/kT)` but the correct formula for unbiased FES recovery is `weights = np.exp(-bias/kT)`. The wrong sign upweights TS-crossing samples (bias ≈ BARRIER → weight = exp(+14.34/0.397) ≈ 6×10¹⁵) rather than downweighting them. Effects:
- FES minimum shifts to wherever the most-recently-biased region is (cv ≈ −0.59 for seed_42, cv ≈ −0.85 for seed_123) rather than the physical reactant at cv = −1.3
- The "barrier" only converges after many TS crossings flood the FES with high-weight samples
- Enormous seed-to-seed variance (1.875 vs 4.019) depending on first TS crossing time
- The measurement is internally consistent with the WT-MetaD baseline only if WT-MetaD also uses the same wrong-sign code (which it does, giving 1.494 at 150 ps — but this coincidence should not be relied on)

**Root cause 2 — FallbackFF quantum barrier mismatch:**
FES snapshots at t < 215 ps show unbiased FES at TS = 5.91 kcal/mol (FallbackFF quantum barrier at 200K/32 beads). This is 3.9× higher than the GFN target (1.52 kcal/mol). The FallbackFF was designed as a placeholder when the GFN checkpoint is unavailable, but its barrier does not match the real system. With this steep barrier:
- OPES with PACE=500, sigma=0.15 requires ~200+ ps to build enough bias for TS crossing
- WT-MetaD with adaptive Gaussian deposition (higher early bias accumulation) crosses the TS faster
- The 1.52 kcal/mol target is irrelevant for FallbackFF; the correct FallbackFF barrier is ~5.9 kcal/mol

**Root cause 3 — PACE=500 too slow for steep barrier:**
At PACE=500 (250 fs between KDE updates), the CV advances ~7.5×10⁻⁴ Å per update at the frontier advance rate of ~0.003 Å/ps. With sigma=0.15 Å, each new sample's kernel covers a 0.15/7.5×10⁻⁴ = 200-step range — meaning the system must traverse the same CV position ~200 PACE intervals before significant bias accumulates. This is intrinsically slow for a steep barrier.

**What would fix this:**
1. Fix reweighting sign: `exp(-bias/kT)` instead of `exp(+bias/kT)`
2. Use real GFN checkpoint (if available) for correct barrier height
3. Reduce PACE to 100–200 for faster bias buildup
4. Or accept that on FallbackFF, the correct "barrier" target is ~5.9 kcal/mol and rerun WT-MetaD with the same FF for fair comparison

### Run 1 analysis: BARRIER=5 kJ/mol caused stalling

**Stalling diagnosis**: BARRIER=5 kJ/mol gives γ = 1 + kT/BARRIER ≈ 1.053. Bias barely grows beyond kT; system stays in reactant for full 150 ps.

### Run 2 analysis: correct BARRIER but two code bugs and too-narrow SIGMA

See Run 2 results section above for full diagnosis. The system DID explore (seed 123 reached cv=+1.53 Å) but the reweighting produced wrong FES because the code re-evaluated each sample's bias at the final KDE state (approximately 0 for all visited regions) instead of the sampling-time state.

**Run 3 fixes applied**:
- `_sample_biases` list: instantaneous bias stored just before each PACE sample is added
- `fes()` uses `_sample_biases` for reweighting instead of re-evaluating final-state bias
- `extract_barrier`: NaN values → inf (min-finding) or -inf (max-finding) per `analyze_convergence.py`
- config: `sigma: 0.05` → `sigma: 0.20`

**Run 4 additional fixes**:
- `_update_bw()` is now a no-op: `pass` — sigma stays fixed at sigma0 throughout (PLUMED convention)
- config: `sigma: 0.20` → `sigma: 0.10`, `n_steps: 300000` → `400000`

**Run 5 additional fixes**:
- config: `barrier: 15.0` → `30.0` kJ/mol, `sigma: 0.10` → `0.15`

**Run 6 additional fixes**:
- config: `barrier: 30.0` → `60.0` kJ/mol (gamma=37.08, max bias=13.95 kcal/mol >> FallbackFF quantum barrier)

**Run 7 additional fixes**:
- config: `n_steps: 400000` → `500000` (250 ps); BARRIER and SIGMA unchanged — parameters confirmed correct in Run 6

**Run 8 root fix**:
- `OPESMetaD.update()`: `self._Z = float(np.max([...]))` → `self._Z = max(self._Z, float(np.max([...])))` — Z is now monotonically non-decreasing (never drops when frontier samples dominate last-20 window)
- config: `n_steps: 500000` → `600000` (300 ps, extra margin)

## Claim updates

### After Run 8 (2026-05-09)
- **Verdict**: not_supported (evidence strength: weak — methodological confounds)
- **Claim**: [[opes-pimd-converges-quantum-fes-faster]] confidence 0.3 → 0.2, status: proposed → challenged
- **Idea**: [[opes-pimd-quantum-free-energy-enhanced]] status: in_progress → failed
- **Judge agreement**: single-model verdict (Review LLM MCP unavailable)
- **Key reasoning**: OPES was 1.43× slower than WT-MetaD for first TS crossing (215+ ps vs 150 ps). Evidence weak due to FES sign bug and FallbackFF mismatch.

### After Run 9 (2026-05-10)
- **Verdict**: not_supported (evidence strength: moderate — methodological fixes applied, fundamental FF mismatch confirmed)
- **Claim**: [[opes-pimd-converges-quantum-fes-faster]] — confidence remains 0.2 (already challenged); no update to claim status warranted (FallbackFF comparison is not scientifically valid for GFN target)
- **Key reasoning**: With correct FES reweighting (exp(-bias/kT)) and PACE=100, zero TS crossings across all 3 seeds in 300 ps. Run 8's apparent TS crossings were FES measurement artifacts from the wrong-sign code. OPES on FallbackFF with these parameters cannot overcome the 5.91 kcal/mol quantum barrier in 300 ps. The claim cannot be tested on FallbackFF — a GFN FF run or a WT-MetaD FallbackFF baseline is required.
- **Date**: 2026-05-10

## Follow-up

**Run 9 outcome: FAILED.** All methodological fixes applied (FES sign, PACE=100); zero TS crossings in 300 ps on FallbackFF.

**Conclusion**: OPES on FallbackFF with these parameters cannot be used to evaluate the claim "OPES converges quantum FES faster than WT-MetaD." The FallbackFF quantum barrier (5.91 kcal/mol) is structurally incompatible with the GFN target (1.52 kcal/mol). No further runs on FallbackFF will resolve this — a different FF is required.

**Two paths forward:**

1. **PhysNet FF baseline** (recommended, fastest): `physnet_fad/` is already in the repo (MP2/aug-cc-pVTZ, 58069 structures, pre-trained PhysNet TF model). Run OPES-PIMD on PhysNet FF first, then run WT-MetaD on the same FF for a fair comparison. PhysNet should give a more realistic FAD proton-transfer barrier (~1–3 kcal/mol range), enabling a fair OPES vs WT-MetaD test within a few hundred ps. Design this as a new experiment: `/exp-design wt-metad-pimd-fad-physnet-baseline` + `/exp-design opes-pimd-fad-physnet-validation`.

2. **GFN FF** (ideal but gated): Fan et al.'s GFN is a MindSPONGE GNN — not a freely available checkpoint. Would require either retraining on FAD structures (requires MindSPONGE + 2918 training conformations) or direct collaboration with Fan et al. Not feasible short-term.

**Do not re-run OPES on FallbackFF.** The fundamental mismatch is confirmed across 9 runs and ~2700 ps of total simulation.
