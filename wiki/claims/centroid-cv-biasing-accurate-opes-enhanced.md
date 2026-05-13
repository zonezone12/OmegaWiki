---
title: "Centroid CV biasing is an accurate strategy for OPES-enhanced PIMD free energy calculations"
slug: "centroid-cv-biasing-accurate-opes-enhanced"
status: proposed
confidence: 0.4
tags: [pimd, opes, collective-variables, centroid, free-energy, nuclear-quantum-effects]
domain: "ML Systems"
source_papers: []
evidence: []
conditions: "Centroid CV = mean position of ring polymer beads. Accuracy comparison against full path-integral reweighting (bead-averaged FES). Systems: FAD proton transfer, water-ice phase transition."
date_proposed: 2026-05-08
date_updated: 2026-05-08
---

## Statement

Applying OPES bias to the centroid (mean bead position) collective variable in PIMD produces free energy surfaces that agree with the reference bead-averaged path-integral reweighting to within 0.2 kcal/mol, while requiring significantly less overhead per simulation step.

## Evidence summary

No direct evidence. Theoretical basis: centroid MD (Voth group) shows the centroid captures dominant quantum fluctuation contributions for moderate-temperature systems. For systems dominated by tunneling (cryogenic), centroid approximation may be insufficient.

## Conditions and scope

- Most reliable for T > 200 K systems where zero-point energy (not deep tunneling) dominates
- Less accurate near quantum tunneling-dominated transition states
- CV must be a linear function of atom positions (distance differences, coordination numbers) for centroid averaging to preserve CV meaning

## Counter-evidence

- Centroid approximation is quasi-classical, not exact quantum; for proton transfer with large tunneling contribution, bead-averaged reweighting is needed
- Pietrucci (2015) path integral metadynamics uses ring polymer shape CV specifically to avoid this issue

## Linked ideas

- [[opes-pimd-quantum-free-energy-enhanced]]

## Open questions

- At what temperature does the centroid CV approximation break down for hydrogen transfer?
- Does the centroid approximation error depend on the OPES convergence (or cancels out)?
