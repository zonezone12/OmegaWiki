# Wiki Index

papers:
  - slug: e3-equivariant-graph-neural-networks-data-efficient
    title: "E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials"
    tags: [equivariance, graph-neural-networks, interatomic-potentials, molecular-dynamics, data-efficiency, machine-learning]
    importance: 5
    domain: ML Systems
  - slug: unified-approach-enhanced-sampling
    title: "A Unified Approach to Enhanced Sampling"
    tags: [enhanced-sampling, metadynamics, opes, expanded-ensembles, collective-variables, free-energy, molecular-dynamics]
    importance: 5
    domain: Computational Chemistry / ML Systems

concepts:
  - slug: e3-equivariant-convolution
    title: "E(3)-Equivariant Convolution"
    tags: [equivariance, convolution, geometric-deep-learning, symmetry, spherical-harmonics, tensor-products]
    maturity: active
  - slug: expanded-ensemble-target-distribution
    title: "Expanded Ensemble Target Distribution"
    tags: [enhanced-sampling, statistical-mechanics, free-energy, replica-exchange, thermodynamics, molecular-dynamics]
    maturity: active
  - slug: expansion-collective-variables
    title: "Expansion Collective Variables"
    tags: [collective-variables, enhanced-sampling, expanded-ensembles, free-energy, thermodynamics]
    maturity: emerging
  - slug: machine-learning-interatomic-potential
    title: "Machine Learning Interatomic Potential"
    tags: [molecular-dynamics, force-fields, interatomic-potentials, machine-learning, computational-chemistry]
    maturity: active
  - slug: opes-enhanced-sampling
    title: "On-the-fly Probability Enhanced Sampling (OPES)"
    tags: [enhanced-sampling, metadynamics, collective-variables, bias-potential, free-energy, molecular-dynamics]
    maturity: active

topics:
  - slug: collective-variables
    title: "Collective Variables for Enhanced Sampling"
    tags: [collective-variables, reaction-coordinate, order-parameter, machine-learning]
  - slug: machine-learning-molecular-dynamics
    title: "Machine Learning for Molecular Dynamics"
    tags: [machine-learning, neural-network-potentials, force-fields, molecular-dynamics]
  - slug: metadynamics-enhanced-sampling
    title: "Metadynamics and Enhanced Sampling Methods"
    tags: [metadynamics, enhanced-sampling, free-energy, molecular-dynamics]

people:
  - slug: albert-musaelian
    tags: [machine-learning-force-fields, equivariant-neural-networks, molecular-dynamics]
    affiliation: "Harvard University (SEAS)"
  - slug: boris-kozinsky
    tags: [molecular-dynamics, machine-learning-force-fields, computational-materials-science, equivariant-neural-networks]
    affiliation: "Harvard University (SEAS) / Robert Bosch Research and Technology Center"
  - slug: michele-invernizzi
    tags: [enhanced-sampling, opes, metadynamics, collective-variables, molecular-dynamics]
    affiliation: "Department of Physics, ETH Zurich / Università della Svizzera italiana, Lugano"
  - slug: michele-parrinello
    tags: [enhanced-sampling, metadynamics, molecular-dynamics, free-energy, collective-variables]
    affiliation: "ETH Zurich / Università della Svizzera italiana, Lugano; Italian Institute of Technology"
  - slug: simon-batzner
    tags: [machine-learning-force-fields, equivariant-neural-networks, molecular-dynamics, graph-neural-networks]
    affiliation: "Harvard University (SEAS)"
  - slug: tess-smidt
    tags: [equivariant-neural-networks, geometric-deep-learning, computational-physics, e3nn]
    affiliation: "MIT (EECS) / Lawrence Berkeley National Laboratory"

ideas:
  - slug: active-learning-pipeline-ml-potentials-opes
    title: "Active Learning Pipeline for ML Potentials with OPES Enhanced Sampling"
    tags: [active-learning, ml-potentials, enhanced-sampling, opes, nequip]
    status: proposed
    domain: ML Systems
    priority: 5
  - slug: fly-cv-validation-refinement-during-metadynamics
    title: "On-the-fly CV Validation and Refinement During Metadynamics"
    tags: [collective-variables, metadynamics, convergence, validation]
    status: proposed
    domain: ML Systems
    priority: 4

experiments:

claims:
  - slug: cv-based-bias-potential-sampling-expanded
    title: "CV-based bias potentials can sample expanded ensembles without requiring multiple parallel replicas"
    tags: [enhanced-sampling, opes, replica-exchange, collective-variables, expanded-ensembles]
    status: supported
    confidence: 0.85
    domain: Computational Chemistry / ML Systems
  - slug: e3-equivariance-improves-sample-efficiency-molecular
    title: "E(3)-equivariance improves sample efficiency for molecular machine learning"
    tags: [equivariance, sample-efficiency, data-efficiency, molecular-dynamics, learning-curves]
    status: supported
    confidence: 0.9
    domain: ML Systems
  - slug: nequip-achieves-state-art-accuracy-molecular
    title: "NequIP achieves state-of-the-art accuracy on molecular dynamics benchmarks"
    tags: [equivariance, NequIP, molecular-dynamics, benchmark, force-fields]
    status: supported
    confidence: 0.9
    domain: ML Systems
  - slug: opes-unified-enhanced-sampling-framework
    title: "The target distribution perspective unifies CV-based and tempering enhanced sampling methods"
    tags: [enhanced-sampling, metadynamics, replica-exchange, unified-framework, target-distribution, collective-variables]
    status: supported
    confidence: 0.8
    domain: Computational Chemistry / ML Systems

Summary:
  - slug: metadynamics-enhanced-sampling
    title: "Metadynamics and Enhanced Sampling for Molecular Dynamics"

foundations:
