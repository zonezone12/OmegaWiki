#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON=/c/Users/zonezone/miniforge3/envs/zong-test/python.exe
LOG_DIR=/c/Users/zonezone/Desktop/YCU_research/MetaDynamics/OmegaWiki/logs
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 TF_CPP_MIN_LOG_LEVEL=3 TF_ENABLE_ONEDNN_OPTS=0

echo "[$(date +%H:%M)] Waiting for PhysNet seed 42..." >> "$LOG_DIR/continuation.log"
until [ -f "results_physnet/seed_42.json" ] && \
      python3 -c "import json,sys; d=json.load(open('results_physnet/seed_42.json')); sys.exit(0 if d.get('n_steps',0)>1000 else 1)" 2>/dev/null; do
    sleep 60
done
echo "[$(date +%H:%M)] PhysNet seed 42 done, launching 123 and 7" >> "$LOG_DIR/continuation.log"

for SEED in 123 7; do
    echo "[$(date +%H:%M)] PhysNet seed $SEED starting" >> "$LOG_DIR/continuation.log"
    $PYTHON -u train.py --config config_physnet.yaml --ff physnet --seed $SEED \
        --out-dir results_physnet >> "$LOG_DIR/mlff-physnet-s${SEED}.log" 2>&1
    echo "[$(date +%H:%M)] PhysNet seed $SEED done" >> "$LOG_DIR/continuation.log"
done
echo "[$(date +%H:%M)] PhysNet ALL done" >> "$LOG_DIR/continuation.log"
