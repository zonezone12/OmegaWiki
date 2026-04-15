---
title: "Collective Variables for Enhanced Sampling"
tags: [collective-variables, reaction-coordinate, order-parameter, machine-learning]
my_involvement: main-focus
sota_updated: 2026-04-15
key_venues:
  - "Journal of Chemical Physics"
  - "Journal of Chemical Theory and Computation"
  - "Physical Review Letters"
  - "Proceedings of the National Academy of Sciences"
related_topics:
  - metadynamics-enhanced-sampling
  - machine-learning-molecular-dynamics
key_people: []
---

## Overview

A collective variable (CV) — also called an order parameter or reaction coordinate — is a low-dimensional function of atomic coordinates that captures the slow degrees of freedom relevant to a process of interest. CV choice is the single most consequential decision in any metadynamics or enhanced sampling study: a good CV leads to converged free energy surfaces, while a poor CV yields non-ergodic sampling regardless of simulation length.

Classical CVs are manually crafted from chemical intuition: distances, angles, torsions, RMSD, coordination numbers, contact maps, gyration radii. Modern machine learning approaches aim to automate CV discovery by learning low-dimensional representations of conformational data.

## Timeline

| Year | Milestone |
|------|-----------|
| 2002 | Manual CV design dominates; geometric CVs (distances, angles, dihedrals) |
| 2009 | Path CVs — progress along a reference pathway |
| 2013 | Sketch-map — dimensionality reduction for collective variables |
| 2017 | Time-lagged autoencoders (TAE) for learning slow CVs |
| 2018 | VAMPnets — variational approach to Markov state models |
| 2019 | Deep learning CVs with metadynamics (Bonati, Rizzi, Parrinello) |
| 2020 | HLDA / SPIB — improved ML CV methods |
| 2021 | DeepTICA — deep time-lagged independent component analysis |
| 2022 | Reweighted autoencoded variational Bayes for enhanced sampling (RAVE) |

## Seminal works

- Laio A, Rodriguez-Fortea A, Gervasio FL, Ceccarelli M, Parrinello M. "Assessing the accuracy of metadynamics." J Phys Chem B 2005.
- Bonati L, Rizzi V, Parrinello M. "Data-driven collective variables for enhanced sampling." J Phys Chem Lett 2020.

## SOTA tracker

| Method | Type | Key idea | Status |
|--------|------|----------|--------|
| Distance/torsion/RMSD CVs | Geometric | Expert-designed, fast | Baseline |
| Path CVs | Geometric | Progress + deviation along pathway | Stable |
| TICA | Linear ML | Time-lagged covariance | Widely used |
| Autoencoder | Deep ML | Nonlinear dim. reduction | Active |
| VAMPnet | Deep ML | Variational MSM objective | Active |
| DeepTICA | Deep ML | Deep TICA | Active |
| SPIB | Deep ML | State predictive information bottleneck | Emerging |

## Open problems

- Optimal objective function for learning CVs that capture the slowest modes
- CVs for processes with multiple, branching pathways
- Validation: how to know if a CV is "good enough" without knowing the ground truth
- CVs for rare events with no prior trajectory data (cold start problem)

## My position

ML-based CV discovery is the most important unsolved problem in the field — solving it would make enhanced sampling accessible to non-experts and dramatically reduce the time-to-answer for biological and materials simulations.

## Research gaps

- Principled framework for CV validation without ground truth reference
- Efficient on-the-fly CV refinement during metadynamics
- CVs that generalize across chemical families (transferable CVs)

## Key people

