---
title: "Langevin Dynamics"
slug: "langevin-dynamics"
domain: "general"
status: mainstream
aliases: ["Langevin thermostat", "stochastic dynamics", "Brownian dynamics"]
first_introduced: "1908"
date_updated: 2026-04-15
source_url: "https://en.wikipedia.org/wiki/Langevin_dynamics"
---

## Definition

Langevin dynamics is an approach to the mathematical modeling of the dynamics of molecular systems using the Langevin equation. It was originally developed by French physicist Paul Langevin. The approach is characterized by the use of simplified models while accounting for omitted degrees of freedom by the use of stochastic differential equations. *(Wikipedia)*

The Langevin equation extends Newton's equations of motion by adding a friction term and a stochastic noise term to model the effect of a heat bath:

$$m\ddot{\mathbf{r}} = -\nabla U(\mathbf{r}) - \gamma m \dot{\mathbf{r}} + \sqrt{2\gamma m k_\mathrm{B} T}\, \boldsymbol{\xi}(t)$$

where $\gamma$ is the friction coefficient and $\boldsymbol{\xi}(t)$ is Gaussian white noise with $\langle \xi_i(t)\xi_j(t') \rangle = \delta_{ij}\delta(t-t')$.

## Intuition

Standard Newtonian MD conserves total energy (NVE ensemble), but experiments happen at constant temperature. Langevin dynamics acts as a thermostat by coupling the system to an implicit solvent or heat bath through friction and random kicks. The friction damps velocities (cooling); the noise term adds random energy (heating). When balanced (fluctuation-dissipation theorem), the system samples the canonical (NVT) ensemble.

The overdamped limit ($m \to 0$, or equivalently $\gamma \to \infty$) gives **Brownian dynamics**, widely used for polymer models and coarse-grained simulations.

## Formal notation

Langevin equation:
$$d\mathbf{r} = \mathbf{v}\, dt, \qquad m\, d\mathbf{v} = \left[-\nabla U(\mathbf{r}) - \gamma m \mathbf{v}\right] dt + \sqrt{2\gamma m k_\mathrm{B}T}\, d\mathbf{W}$$

where $d\mathbf{W}$ is a Wiener process increment.

Fluctuation-dissipation relation (ensures correct NVT sampling):
$$\langle F_\text{rand}(t) F_\text{rand}(t') \rangle = 2\gamma m k_\mathrm{B} T \delta(t - t')$$

## Key variants

- **Underdamped Langevin (full)**: retains inertia; used in most MD codes (GROMACS, NAMD, OpenMM)
- **Overdamped Langevin / Brownian dynamics**: position-only SDE; used for coarse-grained models
- **Nosé-Hoover thermostat**: deterministic thermostat; NVT sampling without stochastic forces
- **BAOAB / OBABO integrators**: splitting schemes for underdamped Langevin with excellent sampling properties

## Known limitations

- Friction coefficient $\gamma$ is a free parameter; too high dampens dynamics and slows rare events; too low gives poor thermostatting
- Modifies kinetics (passage times) in ways that can complicate direct comparison to experiment
- Brownian dynamics neglects inertia and is inappropriate for fast processes

## Open problems

(LLM analysis) Optimal $\gamma$ selection for enhanced sampling with metadynamics; BAOAB vs. OBABO integrator accuracy at large $\gamma$; Langevin dynamics with ML force fields (stochastic + learned PES).

## Relevance to active research

(LLM analysis) Langevin dynamics is the default thermostat in production MD runs with GROMACS + PLUMED for metadynamics. Understanding friction effects is important for infrequent metadynamics (which recovers Kramers rates), because too high $\gamma$ violates the infrequent deposition condition.
