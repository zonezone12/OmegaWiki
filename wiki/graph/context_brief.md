# Query Pack (general)

_Auto-generated compressed context. Do not edit._

## Open Gaps
_Auto-generated open questions. Do not edit._
- [paper/performing-path-integral-molecular-dynamics-using] Can GFN + energy distillation maintain accuracy for free energy perturbation?
- [paper/performing-path-integral-molecular-dynamics-using] How does ML-PIMD scale to mesoscale biomolecular assemblies (enzymes, protein folding)?
- [paper/performing-path-integral-molecular-dynamics-using] Accuracy of ML-PIMD for kinetic isotope effects and quantum tunneling rates?
- [paper/performing-path-integral-molecular-dynamics-using] Extension to ring-polymer instanton rate theory?
- [paper/unified-approach-enhanced-sampling] Can expanded targets be combined with well-tempered-like distributions for better scaling with higher dimensionality of CVs?
- [paper/unified-approach-enhanced-sampling] What are the optimal weighted expanded targets (different weights for different $\lambda$-states)?
- [paper/unified-approach-enhanced-sampling] Rigorous optimality criterion for target distribution selection using effective sample size
- [paper/unified-approach-enhanced-sampling] How does the velocity space difference between OPES-expand and replica exchange affect dynamical properties?
- [paper/unified-approach-enhanced-sampling] Adaptive selection of $\lambda$-points during the simulation (beyond the initial unbiased estimate)
- [concept/expanded-ensemble-target-distribution] Rigorous optimality criterion for the expanded ensemble target (Lyubartsev metric, Riemann metric approaches)
- [concept/e
## Failed Ideas (avoid repeating)
- Equivariant GFN: Fully E(3)-Equivariant Force-Only MLFF Architecture — Similar published work exists: GNNFF (npj Computational Materials 2021) already implements a direct force prediction GNN with rotational covariance. TrajCast (Nature Machine Intelligence 2026, arXiv 2503.23794) implements equivariant autoregressive networks that bypass forces entirely. The incremental contribution of an equivariant GFN over GNNFF is insufficient to warrant a new research direction.
- GFN Energy Distillation via PIMD Bead Ensemble Training — Insufficient feasibility: the proposed distillation protocol (using PIMD bead ensembles to supervise energy prediction in GFN) lacks theoretical justification for why bead-averaged free energy estimates would improve single-configuration energy prediction. The training signal is thermodynamically averaged, not instantaneous, making it unsuitable for local energy supervision. Standard knowledge distillation from an energy-based teacher to GFN is more straightforward and does not require PIMD.
- ML-PIMD for Enzyme Kinetic Isotope Effects at DFT Accuracy — Insufficient feasibility for near-term: enzyme systems require QM/MM treatment (quantum mechanical region + molecular mechanics environment) due to the electrostatic protein environment. Training GFN on enzyme reactive sites requires large, diverse datasets covering the conformational space of both enzyme and substrate. The published work on enzyme KIEs with ML (e.g., QM/MM + path sampling, JCTC 2022) 
## Papers (2 total)
- [5] A Unified Approach to Enhanced Sampling
- [3] Performing Path Integral Molecular Dynamics Using Artificial Intelligence Enhanced Molecular Simulation Framework
## Recent Relationships (33 total)
  papers/performing-path-integral-molecular-dynamics-using --supports--> claims/ml-pimd-aims-framework-achieves-quantum
  papers/performing-path-integral-molecular-dynamics-using --supports--> concepts/opes-enhanced-sampling
  ideas/opes-pimd-quantum-free-energy-enhanced --addresses_gap--> claims/ml-pimd-aims-framework-achieves-quantum
  ideas/opes-pimd-quantum-free-energy-enhanced --addresses_gap--> claims/opes-unified-enhanced-sampling-framework
  ideas/opes-pimd-quantum-free-energy-enhanced --inspired_by--> papers/performing-path-integral-molecular-dynamics-using
  ideas/opes-pimd-quantum-free-energy-enhanced --inspired_by--> papers/unified-approach-enhanced-sampling
  ideas/gfn-instanton-ring-polymer-tunneling-rate --addresses_gap--> claims/ml-pimd-aims-framework-achieves-quantum
  ideas/gfn-instanton-ring-polymer-tunneling-rate --inspired_by--> concepts/graph-field-network
  ideas/active-learning-gfn-force-uncertainty-pimd --addresses_gap--> claims/ml-pimd-aims-framework-achieves-
