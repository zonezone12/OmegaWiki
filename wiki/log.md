# Wiki Log

> Append-only chronological log. Entry format: `## [YYYY-MM-DD] action | details`
## [2026-04-15] ingest | claims for unified-approach-enhanced-sampling: 0 matched existing, 2 new
## [2026-04-15] ingest | concepts for unified-approach-enhanced-sampling: 0 matched existing, 3 new, 0 foundation-refs
## [2026-04-15] ingest | added papers/unified-approach-enhanced-sampling | updated: concepts/opes-enhanced-sampling, concepts/expansion-collective-variables, concepts/expanded-ensemble-target-distribution, claims/cv-based-bias-potential-sampling-expanded, claims/opes-unified-enhanced-sampling-framework, people/michele-parrinello, people/michele-invernizzi
## [2026-05-08] ingest | added papers/performing-path-integral-molecular-dynamics-using | updated: concepts/graph-field-network (new), claims/ml-pimd-aims-framework-achieves-quantum (new), concepts/opes-enhanced-sampling (edge added)
## [2026-05-08] ingest | claims for performing-path-integral-molecular-dynamics-using: 0 matched existing, 1 new
## [2026-05-08] ingest | concepts for performing-path-integral-molecular-dynamics-using: 1 matched existing (opes-enhanced-sampling, edge only), 1 new (graph-field-network), 0 foundation-refs
## [2026-05-08] ideate | 3 ideas proposed, 4 ideas filtered out | direction: ML-PIMD + OPES + GFN (cold-start mode)
## [2026-05-08] exp-design | 6 experiments designed for idea opes-pimd-quantum-free-energy-enhanced | claims: opes-pimd-converges-quantum-fes-faster (new), centroid-cv-biasing-accurate-opes-enhanced (new), opes-hyperparameter-sensitivity-lower-than-wt (new), opes-per-step-kde-overhead-does (new)
## [2026-05-08] exp-run | deployed wt-metad-pimd-fad-baseline-reproduction | env: local | pid: 1739 | log: logs/exp-wt-metad-pimd-fad-baseline-reproduction.log | eta: 1h | NOTE: using fallback Morse FF (GFN checkpoint not present)
## [2026-05-08] exp-run | completed wt-metad-pimd-fad-baseline-reproduction | outcome: failed | barrier=-0.69 kcal/mol (target 1.52, fallback FF); speed=8.35 M/day (PASS). Fix: download GFN-MolCT checkpoint.
## [2026-05-08] exp-run | deployed opes-pimd-fad-proton-transfer-convergence | env: local | PID: 1965 | seeds: [42,123,7] | fallback double-well FF | eta: 3h
## [2026-05-08] exp-run | completed wt-metad-pimd-fad-baseline-reproduction v2 | outcome: succeeded | barrier=1.494 kcal/mol (target 1.52+/-0.15 PASS) | speed=10.40 M steps/day (PASS) | extract_barrier fixed: midpoint-split replaces buggy mask-based approach
## [2026-05-08] exp-run | opes-pimd-fad-proton-transfer-convergence Run 1 COMPLETE (3/3 stalled, BARRIER=5 kJ/mol); Run 2 launched (BARRIER=15 kJ/mol, GPU, PID 901)
## [2026-05-08] exp-run | opes-pimd-fad-proton-transfer-convergence Run 1 COMPLETE (3/3 stalled, BARRIER=5 kJ/mol, barriers 73-114 kcal/mol); Run 2 launched (BARRIER=15 kJ/mol, GPU RTX 4060, PID 901)
## [2026-05-08] exp-run | Run 2 COMPLETE (all 3 seeds) | outcome: code bugs -- extract_barrier NaN bug + wrong reweighting + SIGMA too narrow | Run 3 launched 2026-05-08T21:42 with fixes: NaN handling, sampling-time reweighting, SIGMA=0.20
## [2026-05-08] exp-run | Run 4 launched | slug: opes-pimd-fad-proton-transfer-convergence | sigma=0.10 fixed, n_steps=400000 | PID=1959 | eta: 4h
## [2026-05-08] exp-run | Run 4 launched | slug: opes-pimd-fad-proton-transfer-convergence | sigma=0.10 fixed bw, n_steps=400000 (200ps) | PID=1959 | log: logs/exp-opes-pimd-fad-proton-transfer-convergence-v4.log | eta: ~03:00 2026-05-09
## [2026-05-08] exp-run | Run 4 check at 65ps | seed_42 CV frontier at -1.14 Ang, bias=0.33 kcal/mol, FES profile physical (1.51 at cv=-1.0) | on track for TS crossing ~100-120ps
## [2026-05-08] exp-run | Run 4 aborted (seed_42 only) | barrier=13.24 (stalled, BARRIER=15kJ/mol < FallbackFF quantum barrier ~3-4 kcal/mol) | Run 5 launched PID=1060 | sigma=0.15 BARRIER=30kJ/mol | eta ~04:30 2026-05-09
## [2026-05-08] exp-run | Run 7 complete (seed_42 only): barrier=2.7607 kcal/mol, max_cv=-0.425Ang, 0 TS crossings; Z update bug diagnosed; Run 8 launched with monotonic Z fix (300 ps, PID 5428)
## [2026-05-09] exp-eval | opes-pimd-fad-proton-transfer-convergence → opes-pimd-converges-quantum-fes-faster | verdict: not_supported (weak evidence) | confidence: 0.3→0.2 | status: proposed→challenged | idea: opes-pimd-quantum-free-energy-enhanced → failed
## [2026-05-09] exp-run | completed opes-pimd-fad-proton-transfer-convergence Run 9 | outcome: failed | seeds 42/123/7: 1.952/3.590/6.150 kcal/mol (mean 3.897±2.116) | zero TS crossings in 300 ps | FES sign fixed + PACE=100 | FallbackFF barrier mismatch confirmed as fundamental blocker
## [2026-05-10] exp-run | wt-metad-pimd-fad-baseline-reproduction v3 | 300ps x3seeds | FallbackFF quantum barrier = 0.352±0.021 kcal/mol (exp(-bias/kT)); OPES Run9 = 3.897±2.116 (11x too high, zero TS crossings → OPES under-convergence confirmed)
## [2026-05-13] exp-eval | mlff-pimd-fad-barrier-comparison → opes-pimd-converges-quantum-fes-faster | verdict: inconclusive | confidence: 0.2→0.2 | finding: GFN2-xTB PES fundamentally softer than ab-initio MLFFs for FAD; no FF gives <3 kcal/mol barrier
## [2026-05-14] daily-arxiv | 0 ingested, 5 relevant (score>=2) / 1995 total (CS+chem-ph+comp-ph+mtrl-sci)

### High Priority (ingested)
_None — no score-3 papers found today. No direct advances in OPES+PIMD combination or nuclear-quantum FES methods._

### Worth Watching (relevance = 2)
- **Diagnosing Spectral Ceilings in Equivariant Neural Force Fields** — https://arxiv.org/abs/2605.08286 — Spectral-injection diagnostic shows which angular frequencies equivariant backbones (NequIP/MACE family) preserve; identifies accuracy bottleneck. Directly addresses open GFN architecture question.
- **Benchmarking Compositional Generalisation for ML Interatomic Potentials** — https://arxiv.org/abs/2605.08988 — MLIP generalisation to out-of-distribution compositions; relevant to GFN robustness for diverse molecular chemistry.
- **Dual-LAO for fast and robust relative binding free energies** — https://arxiv.org/abs/2512.17624 — RBFE at reduced cost via dual lambda-dynamics; directly in the enhanced-sampling/free-energy space.
- **Coarse-grained graph architectures for all-atom force predictions** — https://arxiv.org/abs/2505.01058 — CGAA-FF: equivariant GNN with CG message-passing for all-atom forces; relevant to GFN architecture and PIMD efficiency.
- **Tangent-Plane Evidential Uncertainty in Active Learning for Interatomic Potentials** — https://arxiv.org/abs/2605.12353 — Uncertainty quantification for magnetic MLIPs; methodology relevant to active-learning-gfn-force-uncertainty-pimd idea.

### Weakly Relevant (3 papers)
- MDGYM: Benchmarking AI Agents on Molecular Simulations — https://arxiv.org/abs/2605.08941 — RL/LLM agents for MD workflow automation
- Teaching Molecular Dynamics to a Non-Autoregressive Ionic Transport Predictor — https://arxiv.org/abs/2605.09311 — fast ionic-transport prediction from static structures
- Toward Autonomous Computational Catalysis via Agentic Systems — https://arxiv.org/abs/2601.13508 — agentic AI for catalysis

### Notes
- DeepXiv token expired — trending section omitted; scoring used raw RSS abstracts only.
- Physics categories fetched: physics.chem-ph (17), physics.comp-ph (25), cond-mat.mtrl-sci (54) in addition to default CS/AI (1910).
## [2026-05-14] exp-eval | wt-metad-pimd-fad-baseline-reproduction -> opes-pimd-converges-quantum-fes-faster | verdict: not_supported (moderate) | confidence: 0.2->0.2 | Claude self-review only
## [2026-05-14] exp-design | 2 experiments designed for PhysNet OPES vs WT-MetaD comparison | claims: opes-pimd-converges-quantum-fes-faster (tested_by x2), opes-per-step-kde-overhead-does (tested_by x1)
## [2026-05-14] exp-run | deployed wt-metad-pimd-fad-physnet-baseline | env: local | PID: 11416 | seeds: [42,123,7] | PhysNet FF | h=3 kJ/mol gamma=50 PACE=200 300ps | speed=0.47M/day | log: logs/exp-wt-metad-pimd-fad-physnet-baseline.log | eta: ~92h (~2026-05-18)
## [2026-05-14] exp-run | confirmed wt-metad-pimd-fad-physnet-baseline | Python PID: 15196 | cmd PID: 8772 | PhysNet loaded OK | CV0=-1.4833 | n_steps=600000 (300ps) | seed_42 running
## [2026-05-24] daily-arxiv | 0 ingested, 0 relevant / 0 RSS + 20 DeepXiv trending (all CS/AI, none domain-relevant) | weekend run

### daily-arxiv digest 2026-05-24

**Sources**: arXiv RSS: 0 papers (weekend — no new submissions on Sundays) | DeepXiv trending: 20 papers fetched

**Note**: DeepXiv brief API unavailable (expired token). arXiv rate-limited during batch fetch. All 20 trending papers retrieved individually via arXiv abstract pages.

### High Priority (ingested)
_None._

### Worth Watching (relevance = 2)
_None — all 20 trending papers were CS/AI/NLP (LLM agents, diffusion models, embedding methods, retrieval systems). Zero domain overlap with metadynamics, enhanced sampling, PIMD, or ML force fields._

### Trending This Week (from DeepXiv, top 5 by social impact)
- Normalizing Trajectory Models — 2605.08078 — 85,908 views (cs.CV/cs.LG — generative models)
- Code as Agent Harness — 2605.18747 — 20,749 views (cs.CL/cs.AI — agent survey)
- SEGA (diffusion transformer resolution extrapolation) — 2605.22668 — 21,569 views (cs.CV)
- Compiling Agentic Workflows into LLM Weights — 2605.22502 — 5,788 views (cs.AI)
- Life-Harness (runtime harness adaptation) — 2605.22166 — 7,228 views (cs.AI)

### SOTA Updates
_None._

<details>
<summary>Not Relevant (20 papers scanned)</summary>

All 20 DeepXiv trending papers this week (2605.08078 through 2605.17989) are in cs.AI/cs.CL/cs.CV/cs.IR/cs.DB — no physics.chem-ph, cond-mat, or ML-for-molecules content in the trending list.

</details>
## [2026-05-24] exp-run | resumed wt-metad-pimd-fad-physnet-baseline | seed42 RESUME (325 hills warm-start, 31.3ps done, 268.7ps remaining) | seeds 123+7 fresh after seed42 | PID: 20992
## [2026-05-28] daily-arxiv | 0 ingested, 2 relevant / 1140 total (21 after keyword filter)

### High Priority (ingested)
_None today._

### Worth Watching (relevance = 2)
- **STFlow: Data-Coupled Flow Matching for Geometric Trajectory Simulation** — https://arxiv.org/abs/2505.18647 — Flow matching generative model for geometric MD trajectories; may be relevant as a surrogate/accelerated sampling approach
- **Consistent Projection of Langevin Dynamics: Preserving Thermodynamics and Kinetics in Coarse-Grained Models** — https://arxiv.org/abs/2512.03706 — Zwanzig projection-based CG Langevin dynamics preserving both thermodynamics and kinetics; directly relevant to coarse-grained MD and free energy methods

### Trending This Week (from DeepXiv)
_DeepXiv trending returned papers with empty titles (API issue); skipped._

### SOTA Updates
_None._

<details>
<summary>Weakly Relevant (4 papers)</summary>

- How the Optimizer Shapes Learned Solutions in Equivariant Neural Networks — https://arxiv.org/abs/2605.27662
- On the Equivariant Learning of the Q-tensor Order Parameter — https://arxiv.org/abs/2605.27679
- Excited Pfaffians: Generalized Neural Wave Functions Across Structure and State — https://arxiv.org/abs/2603.14515
- The conditional-mean barrier: From deterministic regression to conditional distribution learning — https://arxiv.org/abs/2605.28076

</details>
## [2026-05-29] exp-run | wt-metad-pimd-fad-physnet-baseline Phase 1 complete | 0/3 TS crossings at gamma=50 h=3 kJ/mol | cv_max: seed42=-1.33A seed123=-0.62A seed7=-0.66A | barrier ~10-20 kcal/mol (PhysNet artifact) | escalating to gamma=100 h=5 kJ/mol seed1
## [2026-05-29] ideate | proposed idea: ipi-plumed-mlff-pimd-stack | i-PI + PLUMED + ML force server in Docker for 5-20x PIMD throughput improvement | priority=4
## [2026-05-30] exp-run | wt-metad-pimd-fad-physnet-baseline Phase 2 complete | seed 1 gamma=100 h=5 kJ/mol | barrier=3.90 kcal/mol | first TS crossing=163.1ps | converged=True at 150ps | speed=0.97M/day | experiment status -> completed
## [2026-05-30] exp-eval | wt-metad-pimd-fad-physnet-baseline -> opes-pimd-converges-quantum-fes-faster | verdict: inconclusive [single-model, Review LLM unavailable] | baseline established: 3.90 kcal/mol, 163.1 ps | confidence: 0.2->0.2 | next: opes-pimd-fad-physnet-validation BARRIER=81.6 kJ/mol
## [2026-05-30] exp-run | opes-pimd-fad-physnet-validation ready | code: experiments/code/opes-pimd-fad-physnet-validation/ | BARRIER=81.6 kJ/mol PACE=100 sigma=0.10 gamma=50.1 | sanity PASSED (PhysNet GPU:0, CV0=-1.483) | run: run_gpu.bat <seed> for seeds 42 123 7
## [2026-05-31] exp-eval | opes-pimd-fad-physnet-validation -> opes-pimd-converges-quantum-fes-faster | verdict: not_supported [single-model] | confidence: 0.2->0.1 | root cause: KDE bias at frontier ~0.28 kcal/mol (kT=0.40), insufficient density contrast with sigma=0.10A | opes-per-step-kde-overhead-does: 0.5->0.3 (13% overhead measured)
## [2026-05-31] ideate | ipi-plumed-mlff-pimd-stack -> in_progress | direction: PLUMED OPES_METAD via i-PI + Docker + PhysNet TCP force server | triggered by opes-pimd-fad-physnet-validation NOT_SUPPORTED verdict (custom KDE bias ~kT, insufficient)
## [2026-05-31] exp-run | ipi-plumed-physnet-opes-fad | code ready: physnet_server.py (batched TCP, P=32 threads + barrier), plumed.dat (OPES_METAD sigma=0.05A PACE=500), input.xml (32-bead PILE-L 200K), Dockerfile (Ubuntu+i-PI+PLUMED 2.9), docker-compose.yml | next: docker build + test server
## [2026-06-01] exp-run | ipi-plumed-mlff-pimd-stack production3 | 32-bead OPES run | crash at initialization (stale RESTART files) | diagnosis: i-PI socket handshaking crashed partway through 32-bead connection sequence | fix: clean workspace (#RESTART#, bck.*, COLVAR_opes)
## [2026-06-01] exp-run | ipi-plumed-mlff-pimd-stack production4 | 16-bead diagnostic run (50 ps, 100k steps) | ran to step 90 then deadlock (both i-PI+driver hung) | fixed: force_fields.py, physnet-base path, physnet_fad checkpoint | decision: pivot to proven sanity config for full production
## [2026-06-01] exp-run | ipi-plumed-mlff-pimd-stack production5 LAUNCHED | 32-bead full production (600k steps = 300 ps) | using sanity-test configuration (proven to work) | eta: ~24h (PhysNet 0.97M/day)
