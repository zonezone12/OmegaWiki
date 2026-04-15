---
title: "Expansion Collective Variables"
aliases: ["expansion CVs", "expansion collective variables", "delta u lambda", "thermodynamic expansion CVs"]
tags: [collective-variables, enhanced-sampling, expanded-ensembles, free-energy, thermodynamics]
maturity: emerging
key_papers: ["unified-approach-enhanced-sampling"]
first_introduced: "2020"
date_updated: 2026-04-15
related_concepts: ["opes-enhanced-sampling", "expanded-ensemble-target-distribution"]
---

## Definition

Expansion collective variables (expansion CVs) are a class of collective variables $\Delta u_\lambda(\mathbf{x}) = u_\lambda(\mathbf{x}) - u_0(\mathbf{x})$ that encode the difference between the reduced potential at a parameter value $\lambda$ and the reference reduced potential $u_0(\mathbf{x})$. They fully characterize a non-weighted expanded ensemble target distribution, defining both the target bias potential and the free energy differences to be estimated.

The parameter $\lambda$ may represent a thermodynamic quantity (temperature, pressure) or a perturbation parameter (alchemical coupling, umbrella center).

## Intuition

In expanded ensemble enhanced sampling, we want to sample configurations relevant to a range of thermodynamic conditions (e.g., a temperature range). Rather than running separate simulations for each condition, we can combine them into a single generalized ensemble. The expansion CVs are the coordinates in this generalized space: they measure "how different" the current configuration is from the reference ensemble at each target thermodynamic state. By estimating free energies along these CVs, we can construct a bias that achieves uniform sampling across all target states.

## Formal notation

For a system with reference reduced potential $u_0(\mathbf{x})$ and target parameter range $\Delta\lambda$:

$$\Delta u_\lambda(\mathbf{x}) = u_\lambda(\mathbf{x}) - u_0(\mathbf{x})$$

The expanded ensemble target is fully characterized by:
1. The target bias: $v(\mathbf{x}) = -\log\left(\frac{1}{N_{\{\lambda\}}}\sum_\lambda e^{-\Delta u_\lambda(\mathbf{x}) + \Delta F(\lambda)}\right)$
2. The free energy differences: $\Delta F(\lambda) = -\log\langle e^{-\Delta u_\lambda}\rangle_{u_0}$

## Variants

**Linearly expanded ensembles** ($\Delta u_\lambda = \lambda \Delta u(\mathbf{x})$):
- Multicanonical: $\Delta u_\lambda(\mathbf{x}) = (\beta - \beta_0)U(\mathbf{x})$; bias is function of potential energy $U$
- Multibaric: $\Delta u_\lambda(\mathbf{x}) = \beta_0(p - p_0)V(\mathbf{x})$; bias is function of volume $V$
- Multithermal-Multibaric: $\Delta u_\lambda(\mathbf{x}) = (\beta-\beta_0)U + (\beta p - \beta_0 p_0)V$; bias on $U$ and $V$
- Thermodynamic integration: $\Delta u_\lambda = \lambda(u_1 - u_0)$; $\lambda \in [0,1]$ alchemical transformation

**Nonlinear expansion (multiumbrella)**: $\Delta u_\lambda(\mathbf{x}) = \frac{(s(\mathbf{x})-s_\lambda)^2}{2\sigma^2}$; bias is function of collective variable $s$

**Key property of linear expansion**: The bias $v(\mathbf{x})$ depends on coordinates $\mathbf{x}$ only through the thermodynamic conjugate variable (e.g., potential energy $U$ for temperature expansion, volume $V$ for pressure expansion).

## Comparison

| CV Type | Traditional CVs | Expansion CVs |
|---------|----------------|---------------|
| Purpose | Encode slow structural modes | Encode thermodynamic perturbations |
| Example | Dihedral angles, RMSD | $(β-β_0)U$, $(p-p_0)V$ |
| Target | FES along structural coordinate | Expanded ensemble coverage |
| Combined | Can be combined with expansion CVs | Can augment structural CVs |

## When to use

- When designing OPES-expand simulations for expanded ensemble sampling
- When connecting to the physical meaning of replica exchange: each replica's $\lambda$ corresponds to one expansion CV
- When performing thermodynamic integration in a single simulation
- When combining thermodynamic generalized ensembles with structural order parameter bias

## Known limitations

- The number of $\lambda$-points needed scales with the breadth and dimensionality of the expansion (e.g., multithermal × multibaric requires a grid of points)
- Effective sample size scales as $\sim 1/N_{\{\lambda\}}$
- Automatic selection of $\lambda$-points (via effective sample size from short unbiased run) is heuristic; more elaborate optimization possible

## Open problems

- Optimal distribution of $\lambda$-points to maximize effective sample size uniformity
- Weighted expanded targets with non-uniform $\lambda$ weights
- Extension to path-variable and other non-standard expanded ensemble formulations

## Key papers

- [[unified-approach-enhanced-sampling]] — introduces the concept and demonstrates applications to multicanonical, multithermal-multibaric, thermodynamic integration, and multiumbrella ensembles

## My understanding

Expansion CVs provide a rigorous formal bridge between the two traditional families of enhanced sampling. By recognizing that any expanded ensemble can be defined through these quantities, the OPES-expand method can target arbitrary combinations of thermodynamic conditions and structural order parameters in a unified framework.
