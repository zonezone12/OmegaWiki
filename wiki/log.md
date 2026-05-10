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
