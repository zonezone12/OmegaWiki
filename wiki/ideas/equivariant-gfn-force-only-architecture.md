---
title: "Equivariant GFN: Fully E(3)-Equivariant Force-Only MLFF Architecture"
slug: "equivariant-gfn-force-only-architecture"
status: failed
origin: "ideate"
origin_gaps: ["ml-pimd-aims-framework-achieves-quantum"]
tags: [machine-learning-force-fields, graph-field-network, equivariance, graph-neural-networks]
domain: "ML Systems"
priority: 2
pilot_result: ""
failure_reason: "Similar published work exists: GNNFF (npj Computational Materials 2021) already implements a direct force prediction GNN with rotational covariance. TrajCast (Nature Machine Intelligence 2026, arXiv 2503.23794) implements equivariant autoregressive networks that bypass forces entirely. The incremental contribution of an equivariant GFN over GNNFF is insufficient to warrant a new research direction."
linked_experiments: []
date_proposed: 2026-05-08
date_resolved: 2026-05-08
---

## Motivation

Improve GFN accuracy for hydrogen-bonded systems via E(3)-equivariant force readout.

## Hypothesis

E(3)-equivariant force readout will improve GFN accuracy over the current invariant MolCT-GFN.

## Approach sketch

Replace MolCT backbone with equivariant architecture (NequIP-style); implement equivariant force readout.

## Expected outcome

Lower force RMSE and improved accuracy for water O-H bonds and hydrogen transfer reactions.

## Risks

GNNFF and related work already cover this ground.

## Pilot results

(empty)

## Lessons learned

GNNFF (2021) predicts forces directly with rotational covariance. The incremental novelty of a new equivariant force-only architecture is insufficient given existing published work. Future work should extend GNNFF or MACE to PIMD rather than re-derive the equivariant architecture.
