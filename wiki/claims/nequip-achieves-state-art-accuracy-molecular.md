---
title: "NequIP achieves state-of-the-art accuracy on molecular dynamics benchmarks"
slug: nequip-achieves-state-art-accuracy-molecular
status: supported
confidence: 0.9
tags: [equivariance, NequIP, molecular-dynamics, benchmark, force-fields]
domain: "ML Systems"
source_papers: [e3-equivariant-graph-neural-networks-data-efficient]
evidence:
  - source: e3-equivariant-graph-neural-networks-data-efficient
    type: supports
    strength: strong
    detail: "NequIP (l=3) achieves lowest energy and force MAE on original and revised MD-17 benchmarks across 7-10 molecules, outperforming SchNet, DimeNet, sGDML, FCHL19, GAP, ACE, PaiNN, GemNet, SpookyNet, NewtonNet, and UNiTE with 1000 training points."
conditions: "Benchmarked on MD-17 (original and revised), CCSD/CCSD(T) small molecules, liquid water/ice, and LiPS superionic conductor. Results are for moderate-size training sets (1000 structures). Comparisons are against published results at the time of paper release (2021-2022)."
date_proposed: 2026-04-15
date_updated: 2026-04-15
---

## Statement

NequIP, an E(3)-equivariant graph neural network interatomic potential, achieves state-of-the-art accuracy on a diverse set of molecular dynamics benchmarks including small organic molecules (MD-17), quantum-chemical accuracy data (CCSD/CCSD(T)), liquid water and ice, and periodic solid-state systems, using standard training set sizes of 1000 reference structures.

## Evidence summary

Strong evidence from the NequIP paper: systematic comparison against 10+ published ML-IP methods across 7 organic molecules (MD-17), high-accuracy CCSD(T) data, and multiple periodic systems. Improvements are consistent across systems and particularly large for force prediction. The revised MD-17 benchmark (with higher numerical accuracy) shows even stronger performance gains.

## Conditions and scope

- Results hold for moderate training set sizes (950-1000 structures per molecule)
- Performance advantage is most pronounced for equivariant features (l≥1) vs invariant (l=0)
- For very large training sets, the relative advantage may diminish as invariant methods saturate
- Computational cost is higher than invariant GNNs due to tensor product operations

## Counter-evidence

None identified at time of ingest. Subsequent work (MACE, Allegro) has further improved accuracy, but NequIP remains highly competitive and was the first to establish this performance level.

## Linked ideas

## Open questions

- How does accuracy scale to very large systems (10,000+ atoms) where NequIP has not been benchmarked?
- Are there chemical systems where invariant methods match equivariant ones (e.g., highly symmetric crystals)?
