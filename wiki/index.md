# Wiki Index

papers:
papers:
  - slug: unified-approach-enhanced-sampling
    title: "On-the-fly Probability Enhanced Sampling (OPES): A Unified Framework"
    tags: [enhanced-sampling, opes, collective-variables, free-energy, metadynamics]
    importance: 4
  - slug: performing-path-integral-molecular-dynamics-using
    title: "Performing Path Integral Molecular Dynamics Using Artificial Intelligence Enhanced Molecular Simulation Framework"
    tags: [pimd, machine-learning-force-fields, nuclear-quantum-effects, enhanced-sampling, metadynamics, molecular-dynamics, graph-neural-networks]
    importance: 3

concepts:
  - slug: expanded-ensemble-target-distribution
    tags: [enhanced-sampling, expanded-ensembles, free-energy]
    maturity: active
  - slug: expansion-collective-variables
    tags: [enhanced-sampling, collective-variables, opes]
    maturity: active
  - slug: opes-enhanced-sampling
    tags: [enhanced-sampling, metadynamics, collective-variables, bias-potential, free-energy, molecular-dynamics]
    maturity: active
  - slug: graph-field-network
    tags: [machine-learning-force-fields, graph-neural-networks, molecular-dynamics, direct-force-prediction]
    maturity: emerging

concepts:

topics:

people:

ideas:

methods:

experiments:

Summary:

foundations:
ideas:
  - slug: opes-pimd-quantum-free-energy-enhanced
    status: proposed
    domain: ML Systems
    priority: 5
  - slug: gfn-instanton-ring-polymer-tunneling-rate
    status: proposed
    domain: ML Systems
    priority: 4
  - slug: active-learning-gfn-force-uncertainty-pimd
    status: proposed
    domain: ML Systems
    priority: 4
  - slug: equivariant-gfn-force-only-architecture
    status: failed
    domain: ML Systems
    priority: 2
  - slug: gfn-energy-distillation-pimd-bead-ensemble
    status: failed
    domain: ML Systems
    priority: 2
  - slug: ml-pimd-enzyme-kinetic-isotope-effects
    status: failed
    domain: ML Systems
    priority: 2
  - slug: opes-bead-count-adaptive-convergence-pimd
    status: failed
    domain: ML Systems
    priority: 2

experiments:
  - slug: wt-metad-pimd-fad-baseline-reproduction
    status: completed
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems
  - slug: opes-pimd-fad-proton-transfer-convergence
    status: completed
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems
  - slug: mlff-pimd-fad-barrier-comparison
    status: completed
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems
  - slug: wt-metad-pimd-fad-physnet-baseline
    status: planned
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems
  - slug: opes-pimd-fad-physnet-validation
    status: planned
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems
  - slug: opes-pimd-water-ice-phase-transition
    status: planned
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems
  - slug: opes-pimd-centroid-vs-bead-averaged
    status: planned
    target_claim: centroid-cv-biasing-accurate-opes-enhanced
    domain: ML Systems
  - slug: opes-vs-wt-metad-hyperparameter-sensitivity
    status: planned
    target_claim: opes-hyperparameter-sensitivity-lower-than-wt
    domain: ML Systems
  - slug: opes-pimd-temperature-robustness-water-melting
    status: planned
    target_claim: opes-pimd-converges-quantum-fes-faster
    domain: ML Systems

claims:
  - slug: cv-based-bias-potential-sampling-expanded
    status: supported
    confidence: 0.85
    domain: "Computational Chemistry / ML Systems"
  - slug: opes-unified-enhanced-sampling-framework
    status: weakly_supported
    confidence: 0.7
    domain: "Computational Chemistry / ML Systems"
  - slug: ml-pimd-aims-framework-achieves-quantum
    status: weakly_supported
    confidence: 0.65
    domain: "ML Systems"
  - slug: opes-pimd-converges-quantum-fes-faster
    status: proposed
    confidence: 0.3
    domain: "ML Systems"
  - slug: centroid-cv-biasing-accurate-opes-enhanced
    status: proposed
    confidence: 0.4
    domain: "ML Systems"
  - slug: opes-hyperparameter-sensitivity-lower-than-wt
    status: proposed
    confidence: 0.5
    domain: "ML Systems"
  - slug: opes-per-step-kde-overhead-does
    status: proposed
    confidence: 0.5
    domain: "ML Systems"

people:
  - slug: michele-invernizzi
    affiliation: ""
  - slug: michele-parrinello
    affiliation: ""

claims:
  - slug: cv-based-bias-potential-sampling-expanded
    status: supported
    confidence: 0.85
    domain: "Computational Chemistry / ML Systems"
  - slug: opes-unified-enhanced-sampling-framework
    status: weakly_supported
    confidence: 0.7
    domain: "Computational Chemistry / ML Systems"
  - slug: ml-pimd-aims-framework-achieves-quantum
    status: weakly_supported
    confidence: 0.65
    domain: "ML Systems"
