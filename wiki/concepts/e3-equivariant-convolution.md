---
title: "E(3)-Equivariant Convolution"
aliases: ["equivariant convolution", "equivariant neural network convolution", "tensor field network convolution", "E3 equivariant", "NequIP convolution", "SO3 equivariant convolution"]
tags: [equivariance, convolution, geometric-deep-learning, symmetry, spherical-harmonics, tensor-products]
maturity: active
key_papers: [e3-equivariant-graph-neural-networks-data-efficient]
first_introduced: "2018"
date_updated: 2026-04-15
related_concepts: [machine-learning-interatomic-potential]
---

## Definition

A convolutional operation on geometric data (e.g., sets of atoms in 3D space) that is equivariant with respect to the E(3) symmetry group — rotations, reflections, and translations. Formally, a function f: X → Y is equivariant w.r.t. group G if D_Y[g] f(x) = f(D_X[g] x) for all g ∈ G. In practice, this means that if the input (e.g., atomic positions) is rotated, the output features rotate accordingly via the same group representation.

## Intuition

Standard GNN convolutions for molecular systems use invariant features (scalars like distances, angles), discarding all directional information. Equivariant convolutions instead maintain features as geometric tensors — scalars (l=0), vectors (l=1), matrices (l=2), etc. — and ensure that applying a rotation to the input causes the features to transform predictably. This allows the network to directly reason about directionality (e.g., forces, dipoles, stress tensors) rather than reconstructing it from invariant intermediates.

## Formal notation

Features are irreducible representations of O(3): V_{acm}^{(l,p)}, indexed by rotation order l, parity p ∈ {+1, -1}, atom a, channel c, and representation index m ∈ [-l, l].

Convolutional filter:
```
F(r_ij) = R(r_ij) Y_m^(l)(r̂_ij)
```
where R(r_ij) is a learnable radial MLP and Y_m^(l) is a spherical harmonic.

Full convolution combining input feature (l_i, p_i) with filter (l_f, p_f) to output (l_o, p_o):
```
L_{acm_o}^(l_o,p_o) = Σ_{m_f,m_i} C_{(l_i,m_i)(l_f,m_f)}^{(l_o,m_o)} Σ_{b∈S} R_c^(l_f,l_i)(r_ab) Y_{m_f}^(l_f)(r̂_ab) V_{bcm_i}^(l_i,p_i)
```
Parity selection rule: p_o = p_i × p_f. C are Clebsch-Gordan coefficients.

## Variants

- **TFN (Tensor Field Networks)**: original equivariant convolution for 3D point clouds (Thomas et al. 2018)
- **NequIP**: applied to interatomic potentials; uses Bessel basis + polynomial envelope for radial functions; ResNet-style interaction blocks
- **l=1 only (PaiNN, NewtonNet)**: restricts to vector features, cheaper but less expressive
- **MACE**: multi-ACE framework extending NequIP with higher-body-order features
- **Allegro**: strictly local equivariant potential using parallel tensor contractions

## Comparison

| Method | Features | Symmetry | Notes |
|--------|----------|----------|-------|
| SchNet / DimeNet | Scalars only | Invariant | Fast but limited angular info |
| PaiNN | l=0 + l=1 | Equivariant | Lightweight, l=1 max |
| NequIP | l=0..l_max | Equivariant | Full tensor hierarchy |
| MACE | l=0..l_max | Equivariant | Higher body order |

## When to use

- When the property of interest is a tensor (forces, dipole moments, polarizability, stress)
- When data is scarce (equivariance dramatically improves sample efficiency)
- When angular geometric information is critical (bond angles, torsions, crystal symmetry)
- When energy conservation and rotation-equivariant forces are required

## Known limitations

- Tensor product operations are expensive: cost grows roughly as O(l_max^3) per interaction
- Implementation complexity is high (Clebsch-Gordan coefficients, irrep bookkeeping)
- Memory requirements scale with number of irreps and channels
- Currently limited to short-range (cutoff-based local) interactions

## Open problems

- Theoretical explanation for why equivariance changes the learning curve exponent (not just offset)
- Efficient implementations for very high l (l > 4)
- Extension to include long-range electrostatic interactions within equivariant framework
- Optimal tensor rank l for different chemical systems and properties

## Key papers

- [[e3-equivariant-graph-neural-networks-data-efficient]] — NequIP: introduced E(3)-equivariant convolutions for interatomic potentials with remarkable data efficiency

## My understanding

This is the core technical innovation enabling a new generation of highly data-efficient ML force fields. The key insight is that physical symmetries are not just a regularizer but fundamentally change learning dynamics. The Clebsch-Gordan tensor product is the mathematical heart of equivariant convolution: it decomposes the product of two irreps into a sum of irreps, preserving transformation properties throughout the network.
