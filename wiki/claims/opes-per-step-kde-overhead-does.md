---
title: "OPES kernel density estimation overhead does not eliminate convergence speed gains in PIMD"
slug: "opes-per-step-kde-overhead-does"
status: proposed
confidence: 0.3
tags: [pimd, opes, computational-efficiency, kernel-density-estimation, enhanced-sampling]
domain: "ML Systems"
source_papers: []
evidence:
  - source: opes-pimd-fad-proton-transfer-convergence
    type: supports
    strength: weak
    detail: "Run 9 (PACE=100, FallbackFF): OPES speed = 7.40 M steps/day vs WT-MetaD v3 = 9.26 M steps/day — ~20% per-step overhead on FallbackFF. On GFN (7.2 M steps/day, slower FF), the absolute overhead is similar → overhead fraction comparable. The net-benefit condition cannot be evaluated: OPES failed to converge (zero TS crossings), so there is no convergence speedup to offset the overhead cost. Inconclusive on whether KDE overhead is ultimately negligible."
  - source: opes-pimd-fad-physnet-validation
    type: contradicts
    strength: moderate
    detail: "OPES (PACE=100, sigma=0.10 Å) on PhysNet: 0.84 M/day vs WT-MetaD 0.97 M/day — 13% overhead. Exceeds the <10% threshold for claim to hold. With PhysNet batch inference (0.97 M/day), 13% is non-negligible overhead. KDE cost scales with kernel count: at 300 ps with PACE=100, N_kernels=3000 — this is where O(N) KDE cost becomes measurable."
conditions: "PIMD with P=32 beads, GFN force field; OPES KDE updates at stride 100-500 steps. Overhead measured as fraction of total simulation time spent on OPES KDE update vs. GFN force evaluation."
date_proposed: 2026-05-08
date_updated: 2026-05-14
---

## Statement

The computational overhead of OPES kernel density estimation (KDE) updates per stride accounts for less than 10% of total PIMD simulation time when using GFN force fields, such that the net wall-clock time reduction from faster FES convergence exceeds the per-step overhead cost.

## Evidence summary

No direct evidence. Reasoning: GFN achieves 7.2M steps/day (extremely fast), so the KDE overhead at stride 100-500 steps is amortized. OPES KDE update cost scales with the number of kernels (O(N_kernels)), but in practice OPES is efficient.

## Conditions and scope

- Only applies when using GFN (fast) as the MLFF; if DFT is used, force evaluation dominates and overhead is negligible regardless
- For very long PIMD runs where N_kernels accumulates, KDE overhead may grow

## Counter-evidence

- For first-principles PIMD (0.006M steps/day), overhead is always negligible — this claim only matters for ML-PIMD
- OPES PLUMED implementation uses adaptive kernel pruning to limit N_kernels growth

## Linked ideas

- [[opes-pimd-quantum-free-energy-enhanced]]

## Open questions

- At what kernel count does OPES KDE overhead become significant relative to GFN force evaluation?
