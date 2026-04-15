---
title: "Free Energy"
slug: "free-energy"
domain: "general"
status: mainstream
aliases: ["Helmholtz free energy", "Gibbs free energy", "free energy surface", "FES", "potential of mean force", "PMF"]
first_introduced: "1882"
date_updated: 2026-04-15
source_url: "https://en.wikipedia.org/wiki/Helmholtz_free_energy"
---

## Definition

In thermodynamics, the **Helmholtz free energy** $F$ measures the useful work obtainable from a closed thermodynamic system at constant temperature:

$$F = U - TS$$

where $U$ is internal energy, $T$ is temperature, and $S$ is entropy. The change in $F$ during a process equals the maximum work the system can perform isothermally. At constant temperature, $F$ is minimized at equilibrium. *(Wikipedia)*

In molecular simulation, the more commonly used quantity is the **free energy surface (FES)** or **potential of mean force (PMF)** along a set of collective variables $\mathbf{s}$:

$$F(\mathbf{s}) = -k_\mathrm{B} T \ln \int \delta(\mathbf{s}(\mathbf{x}) - \mathbf{s})\, e^{-U(\mathbf{x})/k_\mathrm{B}T}\, d\mathbf{x}$$

This is the central quantity that metadynamics, umbrella sampling, and OPES seek to compute.

## Intuition

Free energy combines energy and entropy into a single landscape that governs which states are thermodynamically stable. A deep free energy minimum is stable not just because it is low in energy, but because many microstates map to it (high entropy). Barriers on the FES determine kinetics — the higher the barrier, the slower the transition.

The **free energy difference** $\Delta F$ between two states (e.g., bound vs. unbound ligand) is what determines binding affinity: $\Delta F = -k_\mathrm{B} T \ln K_\mathrm{eq}$.

## Formal notation

Gibbs free energy (at constant T, P):
$$G = H - TS = F + PV$$

Free energy difference via thermodynamic integration:
$$\Delta F_{A \to B} = \int_0^1 \left\langle \frac{\partial U(\lambda)}{\partial \lambda} \right\rangle_\lambda d\lambda$$

Free energy from histogram reweighting (WHAM/MBAR):
$$F(\mathbf{s}) = -k_\mathrm{B} T \ln P(\mathbf{s}) + \text{const}$$

## Key variants

- **Potential of mean force (PMF)**: FES along a 1D reaction coordinate; most common output of 1D metadynamics
- **Free energy perturbation (FEP)**: compute $\Delta F$ by alchemical transformation; gold standard for drug binding
- **Thermodynamic integration (TI)**: integrate $\langle \partial U/\partial \lambda \rangle$ along an alchemical path
- **Umbrella sampling + WHAM/MBAR**: harmonic biases along a CV; unbiased by multi-state reweighting

## Known limitations

- FES is only meaningful along the chosen CVs; if CVs miss a slow mode, the FES is converged but wrong
- Absolute binding free energies require careful treatment of standard state volume and sampling of unbound states
- Convergence assessment is non-trivial for high-dimensional systems

## Open problems

(LLM analysis) Automating CV selection so the FES is always computed along the truly slow degrees of freedom; reliable convergence diagnostics for high-dimensional systems; combining ML potentials with FEP/TI at near-QM accuracy.

## Relevance to active research

(LLM analysis) The FES is the primary output of metadynamics and OPES. All claims in this wiki about enhanced sampling methods ultimately concern whether the computed FES is converged, accurate, and computationally efficient to obtain. Binding free energy calculations using metadynamics are a major application.
