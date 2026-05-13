---
title: "OPES hyperparameter sensitivity is lower than WT-MetaD in PIMD enhanced sampling"
slug: "opes-hyperparameter-sensitivity-lower-than-wt"
status: proposed
confidence: 0.5
tags: [pimd, opes, metadynamics, hyperparameter-sensitivity, enhanced-sampling, reproducibility]
domain: "ML Systems"
source_papers: ["unified-approach-enhanced-sampling"]
evidence:
  - source: "unified-approach-enhanced-sampling"
    type: supports
    strength: weak
    detail: "OPES shown to have fewer parameters than metadynamics in classical MD; robustness to BIASFACTOR in well-tempered target is better than metadynamics height/sigma sensitivity"
conditions: "Hyperparameter sensitivity measured as variance of converged FES barrier height across a grid of hyperparameter values. OPES parameters: stride (100-1000 steps), optional BIASFACTOR. WT-MetaD parameters: height (0.1-2.0 kJ/mol), sigma (0.01-0.1), BIASFACTOR."
date_proposed: 2026-05-08
date_updated: 2026-05-08
---

## Statement

In PIMD enhanced sampling, the variance of the converged free energy barrier height across a grid of hyperparameter values is at least 2x smaller for OPES than for WT-MetaD, demonstrating greater practical robustness to parameter choice.

## Evidence summary

Weak indirect evidence: Invernizzi et al. (2020, unified-approach-enhanced-sampling) discuss OPES's robustness to parameter choices in classical MD. No evidence in PIMD context.

## Conditions and scope

- Comparison on same system (FAD proton transfer) with same MLFF (GFN) and same number of total simulation steps
- Sensitivity measured by CV of FES barrier across 3x3 hyperparameter grid

## Counter-evidence

None direct. PIMD introduces additional stochasticity (bead thermal noise) that may wash out OPES vs. MetaD differences.

## Linked ideas

- [[opes-pimd-quantum-free-energy-enhanced]]

## Open questions

- Does the PIMD ring polymer noise increase sensitivity to enhanced sampling hyperparameters relative to classical MD?
