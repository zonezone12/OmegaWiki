---
title: "Active Learning Pipeline for ML Potentials with OPES Enhanced Sampling"
slug: "active-learning-pipeline-ml-potentials-opes"
status: proposed
origin: "Gap at intersection of NequIP (ML potentials) and OPES (enhanced sampling): both are now mature but no principled pipeline combines them. Training data for ML potentials is typically gathered from unbiased MD, missing rare but important configurations. OPES can drive the system to rare states — those configurations, if labeled with DFT, would make the ML potential both more accurate and more transferable."
origin_gaps:
  - machine-learning-molecular-dynamics
  - metadynamics-enhanced-sampling
tags: [active-learning, ml-potentials, enhanced-sampling, opes, nequip]
domain: ML Systems
priority: 5
pilot_result: ""
failure_reason: ""
linked_experiments: []
date_proposed: 2026-04-15
date_resolved: ""
---

## Motivation

NequIP [[e3-equivariant-graph-neural-networks-data-efficient]] achieves state-of-the-art accuracy with very few training points (~100–1000 configurations), but those training points need to cover the relevant configuration space. Standard active learning uses committee disagreement to identify uncertain configurations during unbiased MD — but unbiased MD never visits rare states (transition states, high-energy intermediates, binding/unbinding events).

OPES [[unified-approach-enhanced-sampling]] efficiently drives the simulation to rare states along chosen CVs. If the ML potential is uncertain in those rare-state regions, OPES will still visit them (as long as the potential has low uncertainty about the CV value) — or uncertainty will spike, triggering a DFT call.

The combined pipeline: OPES-driven MD with an NequIP potential + committee uncertainty → when uncertainty > threshold at rare state → call DFT → add to training set → retrain → continue. This closes the loop between enhanced sampling and ML potential quality.

## Hypothesis

An OPES-NequIP active learning loop will achieve equivalent free energy accuracy to OPES on a DFT reference potential, but at 10-100× reduced DFT cost compared to naive ab initio metadynamics.

## Approach sketch

1. Start with a small NequIP potential trained on short unbiased MD trajectory
2. Run OPES with the NequIP potential along a chosen CV (e.g., a dihedral or distance)
3. Monitor NequIP committee disagreement along the OPES trajectory
4. When disagreement > threshold at configurations along the FES: pause MD, call DFT, add to training set, retrain NequIP
5. Resume OPES; repeat until disagreement is uniformly low across the explored FES
6. Compare final FES to brute-force reference

## Expected outcome

- Converged FES with fewer DFT calls than ab initio metadynamics
- NequIP potential that is accurate in the transition region (not just in equilibrium wells)
- Generalizes to other CV choices without full retraining

## Risks

- Committee uncertainty may be poorly calibrated in NequIP (known limitation of deep ensemble uncertainty)
- OPES may drive the system to regions where the ML potential is wildly wrong before uncertainty triggers a DFT call → instability
- Retraining during a running simulation requires careful checkpoint management

## Pilot results

_Not yet run._

## Lessons learned

_Not yet filled._
