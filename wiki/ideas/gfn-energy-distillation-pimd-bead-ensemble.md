---
title: "GFN Energy Distillation via PIMD Bead Ensemble Training"
slug: "gfn-energy-distillation-pimd-bead-ensemble"
status: failed
origin: "ideate"
origin_gaps: ["ml-pimd-aims-framework-achieves-quantum"]
tags: [machine-learning-force-fields, graph-field-network, energy-distillation, pimd]
domain: "ML Systems"
priority: 2
pilot_result: ""
failure_reason: "Insufficient feasibility: the proposed distillation protocol (using PIMD bead ensembles to supervise energy prediction in GFN) lacks theoretical justification for why bead-averaged free energy estimates would improve single-configuration energy prediction. The training signal is thermodynamically averaged, not instantaneous, making it unsuitable for local energy supervision. Standard knowledge distillation from an energy-based teacher to GFN is more straightforward and does not require PIMD."
linked_experiments: []
date_proposed: 2026-05-08
date_resolved: 2026-05-08
---

## Motivation

GFN lacks energy prediction, limiting applicability to FEP/TI calculations.

## Hypothesis

PIMD bead configurations provide a natural ensemble for distilling energy prediction into GFN.

## Approach sketch

Train energy-based teacher; run PIMD; distill bead-averaged free energy to GFN student.

## Expected outcome

GFN gains energy prediction capability while retaining force-only speedup.

## Risks

Training signal mismatch between bead-averaged free energy and instantaneous energy prediction.

## Pilot results

(empty)

## Lessons learned

The thermodynamic averaging in PIMD makes the bead ensemble a poor teacher signal for instantaneous energy prediction. Simpler approach: standard knowledge distillation from energy-based MolCT to GFN using the same training dataset. The PIMD bead ensemble angle adds complexity without clear advantage.
