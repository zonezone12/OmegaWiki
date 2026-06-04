#!/bin/bash
# In-container launch script for i-PI + PhysNet OPES_METAD PIMD on FAD.
# Usage: bash launch_opes.sh [--n-beads 32] [--steps 600000] [--sanity]

set -uo pipefail

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
rm -f ipi_opes.md ipi_opes.pos_*.xyz

XML=input_fad_opes.xml
if [[ $SANITY -eq 1 ]]; then
  echo "[launch_opes] SANITY run: 400 steps (0.2 ps)"
  sed "s|<total_steps>600000</total_steps>|<total_steps>400</total_steps>|g" \
    input_fad_opes.xml > /tmp/input_opes_sanity.xml
  XML=/tmp/input_opes_sanity.xml
fi

# Apply i-PI FFPlumed patch (required for PLUMED hill deposition / OPES kernel updates)
python3 - << 'PYEOF'
filepath = '/usr/local/lib/python3.10/dist-packages/ipi/engine/forcefields.py'
with open(filepath, 'r') as fh:
    src = fh.read()
old = ('        # sets the step and does the actual update\n'
       '        self.plumed.cmd("setStep", self.plumed_step)\n'
       '        self.plumed.cmd("update")')
new = ('        # sets the step and does the actual update\n'
       '        self.plumed.cmd("setStep", self.plumed_step)\n'
       '        self.plumed.cmd("prepareCalc")\n'
       '        self.plumed.cmd("performCalcNoUpdate")\n'
       '        self.plumed.cmd("update")')
if old in src:
    with open(filepath, 'w') as fh:
        fh.write(src.replace(old, new))
    import os, glob
    for pyc in glob.glob('/usr/local/lib/python3.10/dist-packages/ipi/engine/__pycache__/forcefields*.pyc'):
        os.remove(pyc)
    print('[patch] FFPlumed mtd_update patched')
else:
    print('[patch] already patched or not found')
PYEOF

echo "[launch_opes] Starting i-PI (OPES) ..."
i-pi "$XML" &> results/ipi_opes.log &
IPI_PID=$!
echo "[launch_opes] i-PI PID=$IPI_PID"

sleep 5

echo "[launch_opes] Starting PhysNet driver (n_beads=$N_BEADS) ..."
python3 physnet_ipi_driver.py \
  --n-beads "$N_BEADS" \
  --socket /tmp/ipi_physnet \
  --physnet-base /workspace \
  --verbose \
  &> results/driver_opes.log &
DRIVER_PID=$!
echo "[launch_opes] Driver PID=$DRIVER_PID"

echo "[launch_opes] Running. Monitor: tail -f results/ipi_opes.log results/driver_opes.log"
echo "              COLVAR: /tmp/COLVAR  KERNELS: /tmp/KERNELS"

wait $IPI_PID
echo "[launch_opes] i-PI finished."
wait $DRIVER_PID 2>/dev/null || true

cp /dev/shm/COLVAR /workspace/COLVAR_opes 2>/dev/null && echo "[launch_opes] Copied COLVAR_opes" || echo "[launch_opes] Warning: COLVAR not found in /dev/shm"
cp /dev/shm/KERNELS /workspace/KERNELS_opes 2>/dev/null || true
echo "[launch_opes] Done. Results in results/"
