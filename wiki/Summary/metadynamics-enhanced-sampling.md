---
title: "Metadynamics and Enhanced Sampling for Molecular Dynamics"
scope: "Enhanced sampling methods for overcoming energy barriers in molecular simulations; free energy calculation; collective variable design; software ecosystems"
key_topics:
  - metadynamics-enhanced-sampling
  - collective-variables
  - machine-learning-molecular-dynamics
paper_count: 0
date_updated: 2026-04-15
---

## Overview

Molecular dynamics (MD) simulations are limited by the timescale problem: rare events — conformational changes, protein folding, ligand binding — occur on timescales far beyond what unbiased MD can reach. Enhanced sampling methods address this by either biasing the simulation along chosen collective variables (CVs) or by running multiple replica simulations at different conditions.

**Metadynamics**, introduced by Laio and Parrinello (2002), is the central method of this wiki's scope. It fills the free energy landscape with Gaussian potentials deposited along CVs, gradually "flooding" energy minima and forcing the system to explore new states. Well-tempered metadynamics (Barducci et al., 2008) adds a tempering factor that ensures convergence to the true free energy surface (FES).

Key software: PLUMED (Tribello et al., 2014) is the universal plugin interfacing metadynamics with GROMACS, NAMD, LAMMPS, OpenMM, and others. PLUMED-NEST is the associated paper archive for reproducible calculations.

## Core areas

### Enhanced Sampling Landscape
The field spans multiple competing approaches:
- **Metadynamics** (and variants: well-tempered, funnel, parallel-bias, on-the-fly probability enhanced)
- **Umbrella Sampling** — harmonic restraints along a reaction coordinate; WHAM/MBAR for FES reconstruction
- **Replica Exchange MD (REMD)** — temperature ladders that enable conformational exchange
- **Adaptive Sampling** — iterative approaches (HTMD, OpenPathSampling) that use MD trajectories to adaptively seed new simulations

### Collective Variable Design
CV choice governs everything: a poor CV prevents convergence regardless of the sampling algorithm. Classical CVs include distances, angles, dihedrals, RMSD, and contact maps. Modern approaches use machine learning to learn low-dimensional representations (autoencoders, time-lagged autoencoders, VAMPnets) that automatically capture slow degrees of freedom.

### Machine Learning Integration
ML now enters the field in two ways:
1. **ML CVs** — learned collective variables that replace hand-crafted reaction coordinates
2. **ML potentials / neural network force fields** — replace expensive quantum-mechanical potentials with surrogate models (ANI, SchNet, NequIP, MACE) that run at MD speed; combined with enhanced sampling they enable both speed and accuracy

## Evolution

| Era | Milestone |
|-----|-----------|
| 2002 | Metadynamics introduced (Laio & Parrinello, PNAS) |
| 2008 | Well-tempered metadynamics — smoothly converging variant (Barducci, Bussi, Parrinello, PRL) |
| 2013 | Funnel metadynamics for binding free energies (Limongelli et al.) |
| 2014 | PLUMED 2.0 released — universal enhanced sampling plugin |
| 2016 | On-the-fly probability enhanced sampling (OPES precursor) |
| 2019 | DeepCV / machine learning collective variables emerge |
| 2020 | OPES — on-the-fly probability enhanced sampling (Invernizzi & Parrinello) |
| 2021–present | ML force fields + enhanced sampling; active learning loops |

## Current frontiers

- Automated CV discovery without supervision (deep TICs, TICA, autoencoder-based)
- Combined ML-potential + metadynamics pipelines for drug binding
- Coarse-grained enhanced sampling bridging atomistic and mesoscale
- Rare event kinetics from metadynamics (infrequent metadynamics, HTMD)

## Key references

- Laio A, Parrinello M. "Escaping free-energy minima." PNAS 2002. doi:10.1073/pnas.202427399 (seminal — not yet ingested)
- Barducci A, Bussi G, Parrinello M. "Well-Tempered Metadynamics." PRL 2008. doi:10.1103/PhysRevLett.100.020603 (not yet ingested)
- Tribello GA et al. "PLUMED 2." CPC 2014. (not yet ingested)
- [[unified-approach-enhanced-sampling]] — Invernizzi, Piaggi, Parrinello (2020)

## Related

- [[metadynamics-enhanced-sampling]]
- [[collective-variables]]
- [[machine-learning-molecular-dynamics]]
