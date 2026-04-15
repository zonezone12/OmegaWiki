---
title: "Machine Learning for Molecular Dynamics"
tags: [machine-learning, neural-network-potentials, force-fields, molecular-dynamics]
my_involvement: reading
sota_updated: 2026-04-15
key_venues:
  - "Nature Chemistry"
  - "Nature Communications"
  - "Journal of Chemical Theory and Computation"
  - "Physical Review Letters"
  - "NeurIPS"
  - "ICML"
related_topics:
  - metadynamics-enhanced-sampling
  - collective-variables
key_people: []
---

## Overview

Machine learning is transforming molecular dynamics in two complementary ways:

1. **ML potentials / neural network force fields (NNFFs)**: Replace expensive quantum-mechanical energy evaluations (DFT, coupled cluster) with fast surrogate models trained on ab initio data. Enables near-QM accuracy at classical MD speeds for systems up to millions of atoms. Key architectures: ANI, SchNet, DimeNet, NequIP, MACE, PaiNN.

2. **ML collective variables**: Use deep learning to discover optimal reaction coordinates from unbiased MD trajectory data, removing the main bottleneck of expert CV selection for enhanced sampling (see [[collective-variables]]).

## Timeline

| Year | Milestone |
|------|-----------|
| 2007 | Behler-Parrinello neural network potentials — first practical NNFF |
| 2012 | ANI-1 potential for organic molecules |
| 2017 | SchNet — continuous-filter convolutional network for molecules |
| 2018 | Deep Potential MD (DeePMD) for large-scale MD |
| 2020 | NequIP — equivariant graph NN potentials; MACE |
| 2020 | ML CVs integrated with metadynamics |
| 2022 | Universal potentials (MACE-MP-0) trained on Materials Project |
| 2023–24 | Foundation models for molecular simulation (ESM, etc.) |

## Seminal works

- Behler J, Parrinello M. "Generalized Neural-Network Representation of High-Dimensional Potential-Energy Surfaces." PRL 2007.
- Schütt KT et al. "SchNet: A continuous-filter convolutional neural network for modeling quantum interactions." NeurIPS 2017.
- Batzner S et al. "E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials." Nature Comm 2022.

## SOTA tracker

| Model | Key feature | Scale |
|-------|-------------|-------|
| Behler-Parrinello NN | Atomic fingerprints | Small-medium molecules |
| ANI | Transferable organic potential | Drug-like molecules |
| SchNet | Message-passing NN | General |
| DeePMD | Large-scale, production ready | Bulk materials |
| NequIP | E(3)-equivariant; data-efficient | General |
| MACE | Higher-order equivariant; universal | Universal (MACE-MP-0) |

## Open problems

- Sample efficiency: large ab initio training datasets remain expensive
- Handling reactive chemistry (bond breaking/forming)
- Uncertainty quantification for reliable MD production runs
- Combining ML potentials with enhanced sampling (workflow integration)

## My position

MACE and NequIP represent the current frontier for ML potentials. The integration of ML potentials with enhanced sampling (e.g., OPES + MACE) is the next major workflow that will enable accurate binding free energies without manual CV selection.

## Research gaps

- Active learning loops that efficiently grow ML potential training sets using enhanced sampling
- Robustness of ML CVs to changes in force field

## Key people

