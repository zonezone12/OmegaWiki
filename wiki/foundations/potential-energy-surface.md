---
title: "Potential Energy Surface"
slug: "potential-energy-surface"
domain: "general"
status: mainstream
aliases: ["PES", "energy landscape", "potential energy landscape", "energy hypersurface"]
first_introduced: "1931"
date_updated: 2026-04-15
source_url: "https://en.wikipedia.org/wiki/Potential_energy_surface"
---

## Definition

A potential energy surface (PES) or energy landscape describes the energy of a system, especially a collection of atoms, in terms of certain parameters, normally the positions of the atoms. The surface might define the energy as a function of one or more coordinates; if there is only one coordinate, the surface is called a potential energy curve or energy profile. *(Wikipedia)*

For an $N$-atom system, the PES is a $(3N-6)$-dimensional hypersurface:
$$U: \mathbb{R}^{3N} \to \mathbb{R}, \qquad U = U(\mathbf{r}_1, \ldots, \mathbf{r}_N)$$

## Intuition

(LLM analysis) The PES is the multidimensional "terrain" that governs chemical structure and reactivity. Atoms settle into energy minima (stable configurations), and chemical reactions or conformational changes correspond to trajectories that climb over saddle points (transition states) connecting those minima.

The Born-Oppenheimer approximation underpins the PES concept: electrons move so much faster than nuclei that we can compute an electronic energy for each fixed nuclear configuration, giving an effective potential for nuclear motion. In classical MD, this PES is approximated by a force field; in ML-MD, it is learned by a neural network.

## Formal notation

Critical points:
- **Minimum**: $\nabla U = 0$, Hessian $H = \nabla^2 U$ is positive definite
- **First-order saddle point (transition state)**: $\nabla U = 0$, $H$ has exactly one negative eigenvalue
- **Minimum energy path (MEP)**: the steepest descent path from saddle to minima (intrinsic reaction coordinate, IRC)

Harmonic approximation at a minimum $\mathbf{r}^*$:
$$U(\mathbf{r}) \approx U(\mathbf{r}^*) + \frac{1}{2}(\mathbf{r} - \mathbf{r}^*)^T H (\mathbf{r} - \mathbf{r}^*)$$

## Key variants

- **Classical force field PES**: parameterized analytical functions (AMBER, CHARMM, OPLS); fast but approximate
- **Ab initio PES**: DFT or coupled cluster; accurate but expensive (scales as $O(N^3)$ to $O(N^7)$)
- **ML potential PES**: neural network trained on ab initio data; near-DFT accuracy at classical MD speed
- **Coarse-grained PES**: effective potential over reduced degrees of freedom (MARTINI, CGMD)

## Known limitations

- Classical force fields lack bond-breaking; cannot model chemical reactions
- True PES is $3N$-dimensional; visualization and analysis require dimensionality reduction
- Saddle point searches scale poorly with system size; finding all transition states is NP-hard

## Open problems

(LLM analysis) Construction of accurate PES for large reactive systems using ML; uncertainty quantification for ML PES (when is the potential reliable?); discovering unknown stable minima (crystal structure prediction, protein structure prediction).

## Relevance to active research

(LLM analysis) The PES is the object that ML potentials (NequIP, MACE) learn to approximate. Enhanced sampling methods navigate the PES efficiently to find all relevant minima and the barriers between them. The free energy surface along chosen CVs is the thermal average over the full PES — integrating out all degrees of freedom not captured by the CV.
