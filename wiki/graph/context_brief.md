# Query Pack (general)

_Auto-generated compressed context. Do not edit._

## Claims (4 total)
- [supported] CV-based bias potentials can sample expanded ensembles without requiring multiple parallel replicas (conf: 0.85)
- [supported] E(3)-equivariance improves sample efficiency for molecular machine learning (conf: 0.9)
- [supported] NequIP achieves state-of-the-art accuracy on molecular dynamics benchmarks (conf: 0.9)
- [supported] The target distribution perspective unifies CV-based and tempering enhanced sampling methods (conf: 0.8)
## Open Gaps
_Auto-generated open questions. Do not edit._
- [paper/e3-equivariant-graph-neural-networks-data-efficient] Why does equivariance change the power-law exponent (slope) of the learning curve, not just the offset? Is there a theoretical explanation?
- [paper/e3-equivariant-graph-neural-networks-data-efficient] What is the theoretical many-body expansion character of message passing interatomic potentials?
- [paper/e3-equivariant-graph-neural-networks-data-efficient] What is the optimal maximum tensor rank `l` for different chemical systems?
- [paper/e3-equivariant-graph-neural-networks-data-efficient] How does NequIP scale to very large systems (thousands of atoms) in production MD?
- [paper/e3-equivariant-graph-neural-networks-data-efficient] Can equivariant models be extended to include long-range interactions without sacrificing data efficiency?
- [paper/unified-approach-enhanced-sampling] Can expanded targets be combined with well-tempered-like distributions for better scaling with higher dimensionality of CVs?
- [paper/unified-approach-enhanced-sampling] What are the optimal weighted expanded targets (different weights for different $\lambda$-states)?
- [paper/unified-approach-enhanced-sampling] Rigorous optimality criterion for target distribution selection using effective sample size
- [paper/unified-approach-enhanced-sampling] How does the velocity space difference between OPES-expand and replica exchange affect dynamical properties?
- [paper/unified-approach-enhanced-s
## Papers (2 total)
- [5] A Unified Approach to Enhanced Sampling (Computational Chemistry / ML Systems)
- [5] E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials (ML Systems)
## Recent Relationships (15 total)
  papers/e3-equivariant-graph-neural-networks-data-efficient --supports--> concepts/e3-equivariant-convolution
  papers/e3-equivariant-graph-neural-networks-data-efficient --supports--> concepts/machine-learning-interatomic-potential
  papers/e3-equivariant-graph-neural-networks-data-efficient --supports--> claims/nequip-achieves-state-art-accuracy-molecular
  papers/e3-equivariant-graph-neural-networks-data-efficient --supports--> claims/e3-equivariance-improves-sample-efficiency-molecular
  concepts/e3-equivariant-convolution --supports--> concepts/machine-learning-interatomic-potential
  papers/unified-approach-enhanced-sampling --supports--> concepts/opes-enhanced-sampling
  papers/unified-approach-enhanced-sampling --supports--> concepts/expansion-collective-variables
  papers/unified-approach-enhanced-sampling --supports--> concepts/expanded-ensemble-target-distribution
  papers/unified-approach-enhanced-sampling --supports--> claims/cv-based-bias-potential-sampling-expanded
  pa
