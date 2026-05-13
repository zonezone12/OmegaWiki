---
title: "ML-PIMD for Enzyme Kinetic Isotope Effects at DFT Accuracy"
slug: "ml-pimd-enzyme-kinetic-isotope-effects"
status: failed
origin: "ideate"
origin_gaps: ["ml-pimd-aims-framework-achieves-quantum"]
tags: [pimd, machine-learning-force-fields, kinetic-isotope-effects, enzymes, nuclear-quantum-effects]
domain: "ML Systems"
priority: 2
pilot_result: ""
failure_reason: "Insufficient feasibility for near-term: enzyme systems require QM/MM treatment (quantum mechanical region + molecular mechanics environment) due to the electrostatic protein environment. Training GFN on enzyme reactive sites requires large, diverse datasets covering the conformational space of both enzyme and substrate. The published work on enzyme KIEs with ML (e.g., QM/MM + path sampling, JCTC 2022) already addresses this problem with established infrastructure. The incremental contribution of using GFN specifically is unclear without first validating GFN on smaller biomolecular systems."
linked_experiments: []
date_proposed: 2026-05-08
date_resolved: 2026-05-08
---

## Motivation

Enzyme catalysis involves quantum tunneling of protons; GFN + PIMD could enable cheap KIE predictions.

## Hypothesis

GFN-based ML-PIMD can predict enzyme KIEs at near-DFT accuracy with 1000x speedup.

## Approach sketch

Train GFN on enzyme QM/MM data; run PIMD; calculate H/D rate ratio.

## Expected outcome

KIEs in quantitative agreement with experiment.

## Risks

Enzyme systems require QM/MM; existing published solutions already available.

## Pilot results

(empty)

## Lessons learned

Enzyme KIE predictions require QM/MM treatment and large training sets. The GFN-Instanton idea (gfn-instanton-ring-polymer-tunneling-rate) addresses the tunneling rate problem more directly and at lower complexity, starting from the already-validated FAD system. Enzyme work should be deferred until GFN has been validated on larger molecular systems.
