---
title: "Boltzmann Distribution"
slug: "boltzmann-distribution"
domain: "general"
status: mainstream
aliases: ["canonical distribution", "Gibbs distribution", "Boltzmann factor"]
first_introduced: "1868"
date_updated: 2026-04-15
source_url: "https://en.wikipedia.org/wiki/Boltzmann_distribution"
---

## Definition

In statistical mechanics, a Boltzmann distribution is a probability distribution that gives the probability that a system will be in a certain state as a function of that state's energy and the temperature of the system:

$$p_i \propto \exp\!\left(-\frac{\varepsilon_i}{k_\mathrm{B} T}\right)$$

where $p_i$ is the probability of state $i$, $\varepsilon_i$ is its energy, $k_\mathrm{B}$ is the Boltzmann constant, and $T$ is absolute temperature. *(Wikipedia)*

## Intuition

High-energy states are exponentially less probable than low-energy states at equilibrium. The factor $\exp(-\varepsilon / k_\mathrm{B} T)$ is the **Boltzmann factor** — it encodes how strongly thermal fluctuations can excite the system above its lowest energy. At low $T$, only the lowest-energy states are visited; at high $T$, the distribution broadens and high-energy states become accessible.

For a continuous system (like a molecule), the probability density over configuration space $\mathbf{x}$ is:
$$\mu(\mathbf{x}) \propto \exp\!\left(-\frac{U(\mathbf{x})}{k_\mathrm{B} T}\right)$$

This is the **canonical (NVT) distribution** — the target that standard MD samples, and the reference against which enhanced sampling methods must correctly reweight.

## Formal notation

Partition function (normalization):
$$Z = \sum_i \exp\!\left(-\frac{\varepsilon_i}{k_\mathrm{B} T}\right) \quad \text{(discrete)} \qquad Z = \int \exp\!\left(-\frac{U(\mathbf{x})}{k_\mathrm{B} T}\right) d\mathbf{x} \quad \text{(continuous)}$$

Free energy:
$$F = -k_\mathrm{B} T \ln Z$$

## Key variants

- **Canonical (NVT)**: fixed N, V, T — most common for MD
- **Grand canonical (µVT)**: fixed chemical potential µ, V, T — allows particle exchange
- **Isothermal-isobaric (NPT)**: Gibbs distribution (additional barostat factor)

## Known limitations

- Assumes thermal equilibrium; out-of-equilibrium processes require non-equilibrium frameworks
- Direct sampling from the Boltzmann distribution is intractable for high-barrier systems — requires enhanced sampling

## Open problems

(LLM analysis) Accurate free energy differences from the ratio of partition functions; reweighting enhanced-sampling trajectories back to the Boltzmann distribution (crucial for OPES, metadynamics post-processing).

## Relevance to active research

(LLM analysis) The Boltzmann distribution is the target distribution for all enhanced sampling methods. Metadynamics and OPES both ultimately aim to sample it (in the well-tempered limit / with reweighting). Any ML-based CV or force field must produce a simulation whose long-time statistics recover the correct Boltzmann distribution.
