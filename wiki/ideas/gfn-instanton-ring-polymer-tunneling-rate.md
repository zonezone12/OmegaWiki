---
title: "GFN-Instanton: Two-Stage Ring Polymer Instanton Rate Calculations Using Force-Only GFN"
slug: "gfn-instanton-ring-polymer-tunneling-rate"
status: proposed
origin: "ideate"
origin_gaps: ["ml-pimd-aims-framework-achieves-quantum"]
tags: [pimd, machine-learning-force-fields, graph-field-network, instanton, quantum-tunneling, kinetic-isotope-effects]
domain: "ML Systems"
priority: 4
pilot_result: ""
failure_reason: ""
linked_experiments: []
date_proposed: 2026-05-08
date_resolved: ""
---

## Motivation

Fan et al. (2025) introduced GFN as a force-only MLFF achieving 1200x speedup over first-principles PIMD. Ring-polymer instanton theory computes quantum tunneling rate constants (including kinetic isotope effects) via saddle-point optimization in imaginary time. Instanton path geometry optimization requires only forces (gradients of the Euclidean action), while the final rate calculation requires energy values. This creates a natural two-stage workflow where GFN handles the expensive many-bead optimization step cheaply, while only a small number of high-accuracy energy evaluations are needed for the final rate.

## Hypothesis

A two-stage protocol using GFN forces for ring-polymer instanton path optimization (many force evaluations at GFN cost) followed by high-level energy evaluation along the optimized instanton path (few DFT or energy-based MLFF evaluations) will compute quantum tunneling rates and kinetic isotope effects at near-CCSD(T) accuracy with significantly fewer expensive DFT calculations than conventional instanton methods.

## Approach sketch

1. **Stage 1 — Instanton path optimization with GFN**:
   - Initialize P-bead ring polymer between reactant and product wells
   - Minimize Euclidean action S_E = sum_k [harmonic spring] + [V(x_k)/P]
   - Gradient w.r.t. bead k: spring_term + (1/P) * F_k (GFN provides F_k)
   - Iterate until instanton path converges (typically 100-500 force evaluations per bead)
   - Cost: GFN is 1200x faster than DFT, so P*100 bead evaluations are cheap

2. **Stage 2 — Rate calculation with high-level energies**:
   - Evaluate energy V(x_k) at P instanton bead positions using DFT/energy-MLFF
   - Compute action S_E = sum_k [spring + V(x_k)/P]
   - Compute tunneling splitting or thermal rate using instanton rate formula
   - Cost: only P high-level energy evaluations (P ~= 32-64 beads)

3. **Benchmark**: Formic acid dimer (FAD) proton transfer — already validated system from Fan et al.
   - Compare: two-stage GFN-instanton vs. full DFT instanton, vs. Δ-ML instanton (JACS 2023)
   - Measure: KIE (H/D substitution), tunneling splitting, computational cost

4. **KIE calculation**: Replace H with D in FAD, rerun instanton with GFN-D (or mass-rescaled GFN), compare rate ratio

## Expected outcome

GFN reduces Stage 1 cost by ~1000x vs DFT (same speedup as ML-PIMD). Stage 2 requires only P ~32-64 DFT energy evaluations (vs. P*100-500 in full DFT instanton). Net: 10-100x reduction in total computational cost for KIE calculation at near-DFT accuracy.

## Risks

- GFN force accuracy on instanton path configurations (which are off-equilibrium) may be lower than on MD configurations; out-of-distribution error could cause incorrect instanton geometries
- Energy-force inconsistency: using GFN forces (from one model) with DFT energies (from another) may introduce discontinuities in the potential surface around the instanton path
- Perturbative correction versions of instanton (RPI+PC) require Hessians, which GFN cannot provide; method limited to standard instanton theory

## Pilot results

(empty)

## Lessons learned

(empty)
