---
title: "On-the-fly CV Validation and Refinement During Metadynamics"
slug: "fly-cv-validation-refinement-during-metadynamics"
status: proposed
origin: "Core gap from collective-variables topic: there is no principled, automated way to know whether a CV is 'good enough' during or after a metadynamics run without knowing the ground truth FES. Poor CVs cause non-ergodic sampling that looks deceptively converged."
origin_gaps:
  - collective-variables
tags: [collective-variables, metadynamics, convergence, validation]
domain: ML Systems
priority: 4
pilot_result: ""
failure_reason: ""
linked_experiments: []
date_proposed: 2026-04-15
date_resolved: ""
---

## Motivation

In metadynamics and OPES [[unified-approach-enhanced-sampling]], the choice of collective variables (CVs) determines everything — a CV that does not capture the slowest degrees of freedom produces a bias that fills the wrong energy wells and gives a non-converged FES. Currently, diagnosing CV quality requires either:
1. Running the simulation to apparent convergence and looking for inconsistencies (expensive, circular)
2. Comparing to a reference (which usually doesn't exist)
3. Expert intuition (not scalable)

## Hypothesis

The **effective sample size (ESS)** of the reweighted ensemble (available from OPES natively) is a proxy for CV quality: a CV that captures all slow modes will yield a high ESS across the simulation, while a CV that misses a slow mode will show a low ESS in the directions it ignores. ESS can be monitored online and used to trigger CV refinement.

## Approach sketch

1. Run OPES with an initial CV (e.g., a distance or torsion)
2. Monitor ESS online; when ESS drops or fluctuates periodically, flag a possible missing slow mode
3. Cluster the trajectory using time-lagged independent component analysis (TICA) on the full Cartesian coordinates
4. If TICA reveals a slow mode not captured by the current CV, augment the CV set with the leading TICA component
5. Restart or continue OPES with the augmented CV

## Expected outcome

- A diagnostic that identifies poor CVs during rather than after the simulation
- Automatic CV augmentation that recovers missed slow modes at low cost
- Reduced expert burden for users who don't know which CVs to choose

## Risks

- ESS fluctuations have many causes beyond poor CV quality (statistical noise, rare transitions)
- TICA on the fly requires streaming implementations (expensive)
- Adding a CV mid-simulation requires careful handling of the accumulated bias

## Pilot results

_Not yet run._

## Lessons learned

_Not yet filled._
