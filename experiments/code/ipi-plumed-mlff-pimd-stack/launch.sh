#!/bin/bash
# In-container launch script for i-PI + PhysNet WT-MetaD PIMD on FAD.
# Run from /workspace inside the container (i.e. after: docker run ... ipi-plumed-mlff:latest bash)
# Usage: bash launch.sh [--n-beads 32] [--steps 600000] [--sanity]

set -uo pipefail   # fail on unbound vars and pipe errors, but NOT on non-zero i-PI exit

N_BEADS=32
STEPS=600000
SANITY=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --n-beads) N_BEADS="$2"; shift 2 ;;
    --steps)   STEPS="$2";   shift 2 ;;
    --sanity)  SANITY=1;     shift   ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

mkdir -p results
# Remove stale i-PI output files (HILLS/COLVAR now written to /tmp — not here)
# and the previous run's status sentinel, so a fresh run can't be misread as done.
rm -f ipi_out.md ipi_out.pos_*.xyz HILLS COLVAR results/run_status.txt /tmp/HILLS /tmp/COLVAR

XML=input_fad_pimd.xml
if [[ $SANITY -eq 1 ]]; then
  echo "[launch] SANITY run: 400 steps (0.2 ps), smotion ON (centroid CV), PLUMED output → /tmp"
  sed \
    -e "s|<total_steps>600000</total_steps>|<total_steps>400</total_steps>|g" \
    input_fad_pimd.xml > /tmp/input_sanity.xml
  XML=/tmp/input_sanity.xml
fi

# Patch i-PI's FFPlumed.evaluate() — corrected centroid-rate fix:
#   plumed_step advances once per MD step (every N_BEADS=32 bead calls)
#   update() called once per MD step (last bead call) → correct PACE/STRIDE
#   smotion is kept for centroid force distribution; plumed.cmd("update") is the
#   authoritative trigger for HILLS deposition and COLVAR output.
N_BEADS=32
python3 - << PYEOF
N_BEADS = $N_BEADS
filepath = '/usr/local/lib/python3.10/dist-packages/ipi/engine/forcefields.py'
with open(filepath, 'r') as fh:
    src = fh.read()

# Advance plumed_step once per MD step (every N_BEADS bead calls), not every call.
old_step = ('        self.plumed.cmd("setStep", self.plumed_step)\n'
            '        self.plumed.cmd("setCharges", self.charges)')
new_step = (f'        if not hasattr(self, "_bead_count"): self._bead_count = 0\n'
            f'        self._bead_count += 1\n'
            f'        if self._bead_count % {N_BEADS} == 0:\n'
            f'            self.plumed_step += 1  # one PLUMED step = one MD step\n'
            f'        self.plumed.cmd("setStep", self.plumed_step)\n'
            f'        self.plumed.cmd("setCharges", self.charges)')

# Call update() only on the last bead call of each MD step.
old_upd = ('        self.plumed.cmd("prepareCalc")\n'
           '        self.plumed.cmd("performCalcNoUpdate")\n'
           '\n'
           '        bias = np.zeros(1, float)')
new_upd = ('        self.plumed.cmd("prepareCalc")\n'
           '        self.plumed.cmd("performCalcNoUpdate")\n'
           f'        if self._bead_count % {N_BEADS} == 0:\n'
           f'            self.plumed.cmd("update")  # deposit hills + PRINT; once per MD step\n'
           '\n'
           '        bias = np.zeros(1, float)')

patched = 0
if old_step in src:
    src = src.replace(old_step, new_step); patched += 1
if old_upd in src:
    src = src.replace(old_upd, new_upd); patched += 1

if patched == 2:
    with open(filepath, 'w') as fh:
        fh.write(src)
    import os, glob
    for pyc in glob.glob('/usr/local/lib/python3.10/dist-packages/ipi/engine/__pycache__/forcefields*.pyc'):
        os.remove(pyc)
    print(f'[patch] evaluate(): bead counter + plumed_step-per-MD-step + update()-per-MD-step (N={N_BEADS})')
else:
    print(f'[patch] WARNING: only {patched}/2 targets found — check forcefields.py')
PYEOF

echo "[launch] Starting i-PI (background) ..."
i-pi "$XML" &> results/ipi.log &
IPI_PID=$!
echo "[launch] i-PI PID=$IPI_PID"

echo "[launch] Waiting 5s for i-PI to open socket ..."
sleep 5

echo "[launch] Starting PhysNet driver (n_beads=$N_BEADS) ..."
python3 physnet_ipi_driver.py \
  --n-beads "$N_BEADS" \
  --socket /tmp/ipi_physnet \
  --physnet-base /repo/experiments/code/opes-pimd-fad-proton-transfer-convergence \
  &> results/driver.log &
DRIVER_PID=$!
echo "[launch] Driver PID=$DRIVER_PID"

echo "[launch] Running. Monitor with: tail -f results/ipi.log results/driver.log"
echo "[launch] COLVAR: results/run.COLVAR (written by PLUMED)"
echo "         HILLS:  HILLS (written by PLUMED, in cwd)"
echo "[launch] Stop with: kill $IPI_PID $DRIVER_PID"

# Wait for i-PI to finish; driver exits automatically when i-PI disconnects
wait $IPI_PID
echo "[launch] i-PI finished."
wait $DRIVER_PID 2>/dev/null || true
echo "[launch] Driver finished."

# Copy PLUMED output from container-native /tmp back to /workspace
cp /tmp/HILLS /tmp/COLVAR /workspace/ 2>/dev/null && echo "[launch] Copied HILLS and COLVAR from /tmp to /workspace." || echo "[launch] Warning: HILLS/COLVAR not found in /tmp."

# Check if simulation completed all planned steps (sentinel for success detection)
LAST_STEP=$(tail -1 /workspace/ipi_out.md 2>/dev/null | awk '{print $1}' | python3 -c "import sys; v=sys.stdin.read().strip(); print(int(float(v))) if v else print(0)" 2>/dev/null || echo 0)
echo "[launch] Last step completed: $LAST_STEP"
if [[ "$LAST_STEP" -ge "$STEPS" ]] 2>/dev/null || [[ $SANITY -eq 1 && "$LAST_STEP" -ge 400 ]]; then
  echo "SUCCESS steps=$LAST_STEP" > /workspace/results/run_status.txt
  echo "[launch] SUCCESS — all steps completed."
else
  echo "FAILED steps=$LAST_STEP" > /workspace/results/run_status.txt
  echo "[launch] FAILED — simulation did not complete (last step: $LAST_STEP)."
fi
echo "[launch] Results in results/"
