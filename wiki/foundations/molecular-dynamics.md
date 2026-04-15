---
title: "Molecular Dynamics Simulation"
slug: "molecular-dynamics"
domain: "general"
status: mainstream
aliases: ["MD simulation", "classical MD", "atomistic MD"]
first_introduced: "1957"
date_updated: 2026-04-15
source_url: "https://en.wikipedia.org/wiki/Molecular_dynamics"
---

## Definition

Molecular dynamics (MD) is a computer simulation method for analyzing the physical movements of atoms and molecules. The atoms and molecules are allowed to interact for a fixed period of time, giving a view of the dynamic "evolution" of the system. In the most common version, the trajectories of atoms and molecules are determined by numerically solving Newton's equations of motion for a system of interacting particles, where forces between the particles and their potential energies are often calculated using interatomic potentials or molecular mechanical force fields. MD simulations are widely applied in chemical physics, materials science, and biophysics.

*(Wikipedia)*

## Intuition

Imagine placing atoms in a box, assigning each a position and velocity, and then stepping forward in time by integrating F = ma at each step. Forces come from a **force field** — a parameterized model of bond stretching, angle bending, torsions, and non-bonded (electrostatic + van der Waals) interactions. The result is a time series of atomic coordinates (a **trajectory**) from which thermodynamic and kinetic properties are computed by statistical averaging.

The fundamental limitation is **timescale**: the integration timestep is ~1–2 fs (femtoseconds), but biologically important events (folding, binding, conformational change) happen on microseconds to seconds. This gap of 9–15 orders of magnitude is the central problem that enhanced sampling methods address.

## Formal notation

Equations of motion:
$$m_i \ddot{\mathbf{r}}_i = \mathbf{F}_i = -\nabla_{\mathbf{r}_i} U(\mathbf{r}_1, \ldots, \mathbf{r}_N)$$

where $U$ is the potential energy function (force field), $m_i$ and $\mathbf{r}_i$ are the mass and position of atom $i$.

Velocity Verlet integrator (standard):
$$\mathbf{r}(t + \Delta t) = \mathbf{r}(t) + \mathbf{v}(t)\Delta t + \frac{\mathbf{F}(t)}{2m}\Delta t^2$$
$$\mathbf{v}(t + \Delta t) = \mathbf{v}(t) + \frac{\mathbf{F}(t) + \mathbf{F}(t+\Delta t)}{2m}\Delta t$$

## Key variants

- **NVT (canonical ensemble)**: constant number of particles N, volume V, temperature T — uses a thermostat (Nosé-Hoover, Langevin)
- **NPT (isothermal-isobaric)**: constant N, pressure P, T — uses a barostat (Parrinello-Rahman) in addition to thermostat
- **NVE (microcanonical)**: constant N, V, energy E — conservative; no thermostat
- **Coarse-grained MD**: groups of atoms represented as single beads; enables longer timescales at the cost of atomic detail (MARTINI force field)
- **QM/MM**: quantum mechanical treatment of a reactive core region embedded in a classical MM environment
- **Replica Exchange MD (REMD)**: multiple copies at different temperatures exchange configurations; overcomes barriers

## Known limitations

- Timescale gap: ~1 fs timestep vs. µs–s events of interest
- Force field accuracy: approximations in the potential energy model; no bond breaking in standard classical FF
- Finite-size effects: periodic boundary conditions required; system size artifacts
- Initial condition sensitivity: short equilibration can leave memory of starting structure

## Open problems

(LLM analysis) Integration of ML potentials (NequIP, MACE) as drop-in replacements for classical force fields with near-QM accuracy; automated generation of reliable training sets; seamless combination with enhanced sampling.

## Relevance to active research

(LLM analysis) Classical MD provides the underlying propagation engine for all enhanced sampling methods (metadynamics, OPES, replica exchange). Improving timescale coverage (via enhanced sampling) and potential accuracy (via ML force fields) are the two main research vectors in the field. The combination — ML-potential-driven OPES — is an active frontier.
