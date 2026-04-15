---
title: "On-the-fly Probability Enhanced Sampling (OPES)"
aliases: ["OPES", "on-the-fly probability enhanced sampling", "OPES metadynamics", "OPES-metad", "OPES-expand"]
tags: [enhanced-sampling, metadynamics, collective-variables, bias-potential, free-energy, molecular-dynamics]
maturity: active
key_papers: ["unified-approach-enhanced-sampling"]
first_introduced: "2020"
date_updated: 2026-04-15
related_concepts: ["expansion-collective-variables", "expanded-ensemble-target-distribution"]
---

## Definition

OPES (On-the-fly Probability Enhanced Sampling) is a collective-variable-based enhanced sampling method that constructs a bias potential by iteratively estimating the probability distribution of the system on-the-fly. The bias is designed to steer the simulation toward a user-specified target probability distribution $p^{tg}(\mathbf{s})$ by applying:

$$V(\mathbf{s}) = -\frac{1}{\beta}\log\frac{p^{tg}(\mathbf{s})}{P(\mathbf{s})}$$

where $P(\mathbf{s})$ is the unbiased probability distribution estimated from the running simulation.

## Intuition

Unlike metadynamics, which builds up bias by depositing Gaussians at visited configurations, OPES directly targets a specified probability distribution. The key insight is that if you know (or can estimate) the unbiased distribution $P(\mathbf{s})$, you can immediately compute the bias needed to reach any target $p^{tg}(\mathbf{s})$. Since $P(\mathbf{s})$ is not known a priori, OPES estimates it iteratively using kernel density estimation (for well-tempered targets) or free energy reweighting (for expanded ensemble targets), updating the bias at fixed strides.

OPES converges faster than metadynamics in most practical cases and has fewer free parameters: the main inputs are the target distribution specification and the update stride.

## Formal notation

**OPES-metad (well-tempered/uniform targets):**
- Target: $p^{WT}(\mathbf{s}) \propto [P(\mathbf{s})]^{1/\gamma}$ where $\gamma > 1$ is the bias factor
- Bias estimation via weighted kernel density estimation of $P_n(\mathbf{s})$

**OPES-expand (expanded ensemble targets):**
- Target: $p_{\{\lambda\}}(\mathbf{x}) = \frac{1}{N_{\{\lambda\}}}\sum_\lambda P_\lambda(\mathbf{x})$
- Bias: $v(\mathbf{x}) = -\log\left(\frac{1}{N_{\{\lambda\}}}\sum_\lambda e^{-\Delta u_\lambda(\mathbf{x}) + \Delta F(\lambda)}\right)$
- Free energy estimate iteratively updated: $\Delta F_n(\lambda) = -\log\left(\frac{\sum_k e^{-\Delta u_\lambda^{(k)} + v_{k-1}^{(k)}}}{\sum_k e^{v_{k-1}^{(k)}}}\right)$

## Variants

- **OPES-metad**: original formulation for metadynamics-like (well-tempered or uniform) sampling along CVs; uses kernel density estimation to estimate $P(\mathbf{s})$
- **OPES-expand**: expanded ensemble variant (introduced in unified-approach-enhanced-sampling); uses free energy reweighting instead of kernel density estimation; targets sums of Boltzmann distributions at different thermodynamic conditions

## Comparison

| Aspect | OPES | Metadynamics | Replica Exchange |
|--------|------|--------------|-----------------|
| Target specification | Explicit | Implicit (uniform/well-tempered) | Implicit (temperature ladder) |
| Parameters | Few (stride, target) | Multiple (height, width, $\gamma$) | Many (replicas, temperatures) |
| Parallel replicas | Optional | Optional | Required |
| Convergence | Generally faster | Slower | Depends on overlap |
| Expanded ensembles | Yes (OPES-expand) | No (without hybrid) | Yes |

## When to use

- When you want a principled, converging alternative to metadynamics with fewer parameters
- When sampling expanded ensembles (multicanonical, multithermal-multibaric) without requiring multiple replicas
- When combining thermodynamic expanded ensembles with CV-based FES reconstruction
- Implemented in PLUMED as the `OPES_METAD` and `OPES_EXPAND` modules

## Known limitations

- Requires specification of the target distribution (or target range for expanded ensembles)
- For expanded ensembles: efficiency scales as $\sim 1/N_{\{\lambda\}}$ with the number of $\lambda$-points
- OPES-metad requires kernel density estimation which can be expensive in high-dimensional CV spaces
- The velocity space sampled differs from replica exchange (configuration space identical)

## Open problems

- Optimal target distribution selection for maximum effective sample size
- Combination of expanded and well-tempered targets
- Extension to path collective variables and other non-standard CV types
- Weighted expanded targets for selective thermodynamic state sampling

## Key papers

- [[unified-approach-enhanced-sampling]] — introduces OPES-expand for unified enhanced sampling via expanded ensembles

## My understanding

OPES represents a principled generalization of metadynamics where the target distribution is made explicit. The unified framework (OPES-expand) is particularly powerful because it shows that replica exchange and CV-bias methods are two instances of the same target-distribution framework, enabling combinations of both within a single simulation.
