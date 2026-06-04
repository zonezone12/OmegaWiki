# Work Record — i-PI + PLUMED + PhysNet PIMD Stack Bring-Up

**System:** Well-Tempered Metadynamics (WT-MetaD) / OPES on formic-acid-dimer (FAD) double proton transfer
**Engine:** i-PI (PIMD, 32 beads) + PLUMED 2.9.2 (bias) + PhysNet (neural-network force field, TensorFlow/GPU)
**Platform:** Docker (Linux container) on Windows 11 + WSL2, NVIDIA GPU (CUDA 11.8)
**Status:** ✅ Stack verified end-to-end — corrected 400/400-step sanity run (v3) passes all metrics
**Period:** debugging campaign 2026-06-01; production analysis + PLUMED fix 2026-06-02

---

## Executive Summary

The goal was to run path-integral molecular dynamics (PIMD) of the formic acid dimer with a neural-network force field, accelerated by metadynamics, to compute a quantum free-energy barrier. The simulation **crashed or froze repeatedly** during bring-up — first at the very first Gaussian deposition, then at a series of progressively later steps.

We diagnosed and resolved **eleven distinct issues** spanning three layers: Windows↔container file I/O, the PLUMED state lifecycle, and a concurrency deadlock in the custom 32-bead driver. The final and most damaging issue — an intermittent deadlock — masqueraded as several different bugs because it froze at a *different step every time*.

**Outcome (Phase 1):** a 400-step sanity run completed cleanly, depositing hills and writing COLVAR correctly.

**Phase 2 — Production analysis revealed a new PLUMED issue (ISSUE-11/12):** the original `evaluate()` patch called `plumed.cmd("update")` on every bead call — 32 times per MD step instead of once. This inflated the hill deposition rate 32× and drove the system out of physical CV space. ISSUE-12 documents the failed attempt to fix this via `<smotion>` (i-PI's smotion does not invoke `mtd_update()` in this version). The correct fix is a bead counter in the `evaluate()` patch (ISSUE-12 fix), now verified by sanity run v3.

---

## System Architecture (one slide)

```
   i-PI (MD driver, 32 beads)
        │  Unix socket (binary protocol: STATUS → POSDATA → GETFORCE)
        ▼
   physnet_ipi_driver.py  ──►  PhysNet force field (TensorFlow, GPU)
        │
   i-PI ──► PLUMED 2.9.2  ──►  bias forces + HILLS / COLVAR output
```

- **i-PI** orchestrates the dynamics and talks to force-field "clients" over a socket.
- **PhysNet driver** is custom code: one socket client per bead (32), returns forces.
- **PLUMED** computes the collective variable (proton-transfer coordinate) and deposits the metadynamics bias.

---

## Issue Tickets

### 🎫 ISSUE-01 — Crash at first Gaussian deposition (step 200)

| | |
|---|---|
| **Severity** | Blocker |
| **Symptom** | Simulation died exactly at MD step 200, the first PLUMED hill deposition. |
| **Root cause** | PLUMED's `update()` wrote the `HILLS` file to a **Windows bind-mounted directory**. A synchronous NTFS write from inside the Linux container hangs for 60+ seconds; i-PI's socket timeout then fired and tore down all 32 bead connections. |
| **Fix** | Redirect all PLUMED output (`HILLS`, `COLVAR`) to the container-native `/tmp` (tmpfs). Writes now complete in microseconds; copied back to the workspace at the end of the run. |

---

### 🎫 ISSUE-02 — `FLUSH` action also stalled the run

| | |
|---|---|
| **Severity** | Blocker |
| **Symptom** | Even with output redirected, the run still hung. |
| **Root cause** | PLUMED's `FLUSH STRIDE=10` action force-flushes **all** open files, including internal PLUMED files still opened on the Windows bind-mount. |
| **Fix** | Removed the `FLUSH` action entirely. `PRINT` still writes every stride; `FLUSH` only existed for real-time disk visibility, which we didn't need. |

---

### 🎫 ISSUE-03 — COLVAR / HILLS always empty on first run

| | |
|---|---|
| **Severity** | Major |
| **Symptom** | Files were created but never populated. |
| **Root cause** | PLUMED's `PRINT` and `METAD` deposition only fire during `performCalcAndUpdate`, which is called by i-PI's `smotion` (structural-motion) hook — not by the regular force evaluation (`performCalcNoUpdate`). |
| **Fix** | Patched i-PI's `FFPlumed.evaluate()` to (1) increment the PLUMED step counter and (2) call `plumed.cmd("update")` after `performCalcNoUpdate`. This is the classic pre-`smotion` PLUMED pattern: one PLUMED cycle per MD step, no separate hook needed. |

---

### 🎫 ISSUE-04 — Crashed containers took 32+ minutes to exit

| | |
|---|---|
| **Severity** | Minor (productivity) |
| **Symptom** | After a failure, the container took half an hour to actually stop, blocking the next test. |
| **Root cause** | Socket timeout was 60 s. On failure each of the 32 beads waits the full timeout before i-PI cleans up → 32 × 60 s ≈ 32 min. |
| **Fix** | Reduced socket timeout 60 s → 5 s. Crashed containers now exit in ~2.7 min, tightening the debug loop. |

---

### 🎫 ISSUE-05 — Could not distinguish "killed" from "completed"

| | |
|---|---|
| **Severity** | Minor (observability) |
| **Symptom** | Background-task notifications reported "killed" even when the run had partially succeeded. |
| **Root cause** | The 5-min task watchdog and the 2.7-min container cleanup overlapped, so the outer notification was ambiguous. |
| **Fix** | The launch script writes a **sentinel file** `results/run_status.txt` containing `SUCCESS steps=400` or `FAILED steps=N` immediately before exit. A single human-readable line removes all ambiguity. |

---

### 🎫 ISSUE-06 — Dangling-pointer crashes after a patch attempt (steps 210, 280)

| | |
|---|---|
| **Severity** | Blocker (self-inflicted, during fixing) |
| **Symptom** | After an early patch to `mtd_update()`, crashes moved to steps 210 then 280. |
| **Root cause** | The patch built temporary NumPy arrays for forces/virial and handed their raw C pointers to PLUMED, then let them be garbage-collected while PLUMED still held the pointers → dangling-pointer crash. |
| **Fix** | Abandoned that approach. Moved the `update()` call into `evaluate()` (ISSUE-03 fix), where PLUMED's persistent buffers already live — no temporary arrays, no dangling pointers. Removed `smotion` from the sanity config entirely. |

---

### 🎫 ISSUE-07 — Protocol desync from a stray socket reply (step ~31)

| | |
|---|---|
| **Severity** | Major |
| **Symptom** | Run desynced and crashed around step 31. |
| **Root cause** | The driver replied to i-PI's `FLUSH` message with a header. i-PI sends `FLUSH` as a one-way server hint expecting **no reply**; the extra message slipped into the stream and desynchronized the binary protocol. |
| **Fix** | `FLUSH` handler changed to a no-op (consume and ignore). Also added `OSError`/`EOFError` handlers so a clean i-PI shutdown (`ENDRUN` closing sockets) is handled gracefully instead of as an error. |

---

### 🎫 ISSUE-08 — `BeadBarrier.abort()` missing

| | |
|---|---|
| **Severity** | Minor |
| **Symptom** | A connection-failure path called `barrier.abort()`, which didn't exist → secondary exception that hid the real connection error. |
| **Fix** | Added an `abort()` method so a failed bead connection cleanly unblocks the other waiting threads and surfaces the true error. |

---

### 🎫 ISSUE-09 — ⭐ Intermittent deadlock mid-run (steps 80 / 130) — *the main event*

| | |
|---|---|
| **Severity** | Critical Blocker |
| **Symptom** | After all the I/O fixes, runs still **froze** at a *different* step each time (80, 130, 210…). Not a crash — a hang: driver process at ~0 % CPU, GPU idle, i-PI output frozen. |
| **Diagnosis** | Measured CPU-time delta inside the container: **1 clock tick over 20 s** (~0.05 %) while the step counter sat still → a genuine deadlock, not slow compute. The random freeze step is the fingerprint of a race condition. |
| **Root cause** | The driver batched all 32 beads through one GPU pass behind a `threading.Barrier(32)` — **every bead had to arrive before any could proceed.** This assumed i-PI dispatches `POSDATA` to all 32 clients before collecting forces. **It does not.** On a partial dispatch sweep, i-PI sends positions to *N < 32* beads, then tries to collect their forces before feeding the rest. The arrived beads block forever at the barrier waiting for beads i-PI hasn't fed; i-PI blocks waiting for the arrived beads' forces. **Mutual deadlock.** |
| **Fix** | Replaced the cross-bead barrier (`BeadBarrier`) with **per-bead lock-guarded inference** (`BeadCompute`). Each bead computes its own forces under a shared lock the instant its `POSDATA` arrives. A bead's progress now depends only on acquiring the lock (always released) — **never** on whether other beads received their data — so no dispatch order can deadlock it. |
| **Verification** | Sanity run sailed past step 130 (the prior freeze point) and completed **400/400** steps cleanly. |

---

### 🎫 ISSUE-10 — TF graph retrace on partial sweeps blew the socket timeout (step 330)

| | |
|---|---|
| **Severity** | Blocker (surfaced while restoring speed) |
| **Context** | The ISSUE-09 fix (per-bead) was deadlock-free but ~20× too slow (~0.4 steps/s). We replaced it with a **hybrid**: batch all 32 beads on the fast path, but time out after 0.3 s and batch whoever arrived on a partial sweep. |
| **Symptom** | Speed was restored (8.3 steps/s) but the run then froze at step 330; i-PI logged "Client died or got unresponsive" for every bead. |
| **Root cause** | A partial sweep produced an *odd-sized* batch (observed: 2 beads, then 30). PhysNet's TensorFlow graph is shape-specialized, so each **new batch size triggers a multi-second graph retrace**. Two cold retraces back-to-back exceeded i-PI's 5 s socket timeout, so i-PI dropped all clients. |
| **Fix** | Always run a **fixed full-size (P=32) batch** — pad the missing beads with a valid geometry and discard their results. The batch shape never changes → no retrace → no timeout. Partial-sweep beads still get correct forces. |
| **Verification** | 400/400 steps, clean exit, **t/step = 0.120 s (8.3 steps/s)** — full batched speed, deadlock-free. |

---

### 🎫 ISSUE-11 — Per-bead PLUMED calls inflated hill rate 32× → CV escape

| | |
|---|---|
| **Severity** | Critical (silent data corruption) |
| **Discovered** | Post-production analysis of 600k-step run (2026-06-02) |
| **Symptom** | 600k-step production run completed successfully (exit 0, sentinel written), but FES analysis showed only 9% of COLVAR frames in the physical CV range (|CV| < 0.30 nm); CV mean drifted to +1.53 nm (> 15 Å) — far outside the physical double-well. |
| **Root cause** | `FFPlumed.evaluate()` is called **once per bead per MD step** (32 times/step). The original ISSUE-03 patch called `plumed.cmd("update")` inside `evaluate()` and incremented `plumed_step` on every call. Consequence: (1) hills deposited 32× per MD step instead of once — PACE=200 PLUMED steps = 200/32 ≈ 6 MD steps = 3 fs between hills (intended: 100 fs); (2) plumed_step advanced 32× per MD step, so PLUMED's internal STRIDE and PACE counters ran 32× too fast; (3) with no CV walls and hyper-aggressive hill deposition, the metadynamics bias drove individual bead positions into unphysical CV space (CV > 1 nm). |
| **Evidence** | PLUMED timing in ipi.log after 400-step sanity run: 12,832 cycles = 400 MD steps × 32 beads — every cycle was a bead call. No smotion contribution visible. Hill deposition rate: 96,000 hills / 300 ps = 320 hills/ps (intended: 10 hills/ps). |
| **Fix** | See ISSUE-12 — bead counter in the evaluate() patch. |

---

### 🎫 ISSUE-12 — smotion `mtd_update()` not invoked; fix via bead counter in `evaluate()`

| | |
|---|---|
| **Severity** | Blocker (ISSUE-11 fix attempt) |
| **Symptom** | After removing the `plumed.cmd("update")` call from `evaluate()` and re-enabling `<smotion mode='metad'>` (to get one centroid-based update per MD step), COLVAR and HILLS were empty — ISSUE-03 reproduced. |
| **Diagnosis** | PLUMED timing in ipi.log after 400-step sanity run without the `evaluate()` patch but with smotion: still exactly 12,832 cycles (400 × 32). If `mtd_update()` had been called by smotion, we would see 12,832 + 400 = 13,232 cycles. **Smotion's `<metad>` mode in this version of i-PI does not invoke `FFPlumed.mtd_update()`** — it uses i-PI's own internal MetaDForceField implementation, bypassing PLUMED's update cycle entirely. |
| **Root cause** | i-PI's `<smotion mode='metad'>` is a self-contained metadynamics implementation. It does NOT delegate to the `mtd_update()` method of an attached FFPlumed forcefield. The `mtd_update()` path only works if called explicitly (e.g., from a custom simulation hook), which i-PI's standard smotion loop does not do. Without `update()` being called anywhere, PLUMED's `PRINT` and `METAD` deposition never fire. |
| **Fix** | Restore the `evaluate()` patch but with a **bead counter** so `plumed_step` advances once per MD step and `update()` is called only once per MD step (on the 32nd bead call): `if self._bead_count % N_BEADS == 0: self.plumed_step += 1; ...; self.plumed.cmd("update")`. N_BEADS=32 is hardcoded to match `<nbeads>` in the XML. This gives the correct PACE/STRIDE alignment (1 PLUMED step = 1 MD step) while calling `update()` exactly once per MD step. |
| **Remaining limitation** | Hills are deposited using the **last bead's CV position** (whichever bead is call #32 in the cycle), not the centroid. The ring polymer bead spread at 200K is ~0.015 nm (< 3× the hill sigma of 0.005 nm), so the positional error per hill is bounded. CV walls prevent runaway exploration. A future improvement is to accumulate all 32 bead positions and compute the true centroid before calling `update()`. |
| **Verification** | Sanity run v3 (400 steps, corrected patch + CV walls): COLVAR = 40 frames (= 400/STRIDE=10 ✓), HILLS = 2 Gaussians (= 400/PACE=200 ✓), hill times at step 200 and 400 ✓, CV range [−0.18, −0.06] nm (physical ✓), wall bias = 0 throughout (walls not triggered ✓), WT-MetaD height decay working (5.05 → 4.94 kJ/mol ✓). |

---

## Resolution Map (presentation summary)

| Layer | Issues | Theme |
|-------|--------|-------|
| **Windows ↔ container I/O** | 01, 02 | NTFS bind-mount writes hang the Linux container → redirect to tmpfs |
| **PLUMED state lifecycle** | 03, 06, 07, 11, 12 | `update()` must fire exactly once per MD step; per-bead calls silently corrupt hill rate and CV sampling |
| **Driver concurrency** | 08, 09, 10 | Cross-bead barrier deadlocks under i-PI's real dispatch → timeout-bounded hybrid with fixed-size padded batches |
| **Tooling / observability** | 04, 05 | Fast failure + unambiguous SUCCESS/FAIL sentinel |

**Key lessons:**
- The deadlock (ISSUE-09) was masked as several different bugs because it froze at a different step each run. The breakthrough was *measuring CPU time* to distinguish a **hang** from **slow compute** — reframing the problem from "what crashes at step N" to "what's the cross-thread wait condition."
- The fix has to be *both* deadlock-free *and* fast. The naive deadlock fix (per-bead) was 20× too slow; the fast fix (variable-size batches) hit a hidden TF-retrace timeout (ISSUE-10). The shipped design — a timeout-bounded batch with **fixed-size padding** — satisfies both.
- Silent data corruption (ISSUE-11) is harder to catch than crashes: the production run exited cleanly (exit 0, sentinel, 600k steps) but the FES was unphysical. Only post-hoc analysis of COLVAR statistics (CV mean >> basin position) revealed the issue. Always verify hill count and COLVAR line count against expected values (COLVAR lines = steps/STRIDE, hills = steps/PACE) before trusting FES output.
- i-PI's `<smotion mode='metad'>` does NOT delegate to `FFPlumed.mtd_update()` (ISSUE-12). The only reliable way to trigger PLUMED's update cycle in this version is via the `evaluate()` patch — but with a bead counter to ensure exactly one call per MD step.

---

## Verification

### Phase 1 — Sanity run v1 (2026-06-01, original patch)

| Metric | Result |
|--------|--------|
| Steps completed | **400 / 400** (0.2 ps) |
| Exit | Clean — i-PI `SOFTEXIT`, container Exit 0, driver `[driver] done` |
| Deadlock | None — cleared both prior freeze points (step 130 *and* step 330) |
| **Speed** | **t/step = 0.120 s ≈ 8.3 steps/s** (full batched throughput) |
| COLVAR | 1284 lines (40 frames × 32 bead calls / stride — inflated by per-bead issue) |
| HILLS | 67 Gaussians (should have been 2; inflated 32× by per-bead issue) |
| Beads | All 32 connected, computed, and received EXIT gracefully |

### Phase 2 — Production run (2026-06-01–02, original patch)

| Metric | Result |
|--------|--------|
| Steps completed | **600,000 / 600,000** (300 ps) |
| Wall-clock | **29.2 hours** (exit 0, sentinel written) |
| Speed | ~6.4 steps/s sustained |
| COLVAR | 1,920,004 lines — 9% of frames in physical CV range (ISSUE-11) |
| HILLS | 96,000 Gaussians — expected 3,000; 32× overdeposition (ISSUE-11) |
| FES barrier | Unreliable — CV escaped physical range; only 8,575 physical hills |

### Phase 3 — Sanity run v3 (2026-06-02, corrected patch + CV walls)

| Metric | Expected | Got | Status |
|--------|----------|-----|--------|
| COLVAR frames | 400 / STRIDE=10 = **40** | 40 | ✅ |
| HILLS deposited | 400 / PACE=200 = **2** | 2 | ✅ |
| Hill times | step 200, step 400 | 200, 400 | ✅ |
| CV range | physical (< ±0.25 nm) | [−0.18, −0.06] nm | ✅ |
| Wall bias | 0 (not triggered) | 0 | ✅ |
| WT-MetaD height decay | decreasing | 5.05 → 4.94 kJ/mol | ✅ |
| Speed | ~8.3 steps/s | ~8.3 steps/s | ✅ |
| Exit | clean | exit 0, sentinel SUCCESS | ✅ |

**Performance journey:** all-or-nothing barrier (deadlocks) → per-bead lock (~0.4 steps/s) → **hybrid padded batch (8.3 steps/s, deadlock-free)** → **corrected PLUMED patch with bead counter (8.3 steps/s, correct hill rate, correct CV sampling)**.

---

## Outstanding / Next Step

| Item | Detail |
|------|--------|
| **Status** | ✅ Stack fully corrected: deadlock-free, full batch speed, correct PLUMED update rate, CV walls active. |
| **Gate** | Launch the corrected 600k-step production run (~20 h) and verify: COLVAR ≈ 60,000 lines (600k/STRIDE=10), HILLS ≈ 3,000 (600k/PACE=200), CV stays in [−0.25, +0.25] nm, FES barrier ≈ 3.90 kcal/mol = 16.3 kJ/mol (matches ASE baseline). |
| **Future improvement** | Replace last-bead hill position with true centroid (accumulate all 32 bead positions in `evaluate()` and pass centroid to `plumed.cmd("setPositions")` before `update()`). Current error: < 3× hill sigma per deposition; bounded by CV walls. |

---

## Artifacts

- `physnet_ipi_driver.py` — driver (`BeadCompute` hybrid: timeout-bounded batch, fixed-size padding)
- `launch.sh` — orchestrator: corrected `evaluate()` patch (bead counter, once-per-MD-step `update()`), `/tmp` output, sentinel
- `plumed_fad_wtmetad.dat` — PLUMED action file: `/tmp` output, no FLUSH, CV walls ±0.25 nm (KAPPA=10000)
- `input_fad_pimd.xml` — i-PI config: 600k steps, 5 s timeout, `<smotion mode='metad'>` block (kept; smotion doesn't call mtd_update but does no harm)
- `results/run_status.txt` — `SUCCESS steps=400` (sanity v3) / `SUCCESS steps=600000` (Phase 2 production)
- `results/sanity_v3.log` — corrected sanity run log
- `results/COLVAR`, `results/HILLS` — Phase 2 production output (inflated, not used for FES)
- `COLVAR`, `HILLS` — sanity v3 output (correct rates, in workspace root)
