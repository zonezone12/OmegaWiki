#!/bin/bash
# Polls for completed seeds and launches next ones
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON=/c/Users/zonezone/miniforge3/envs/zong-test/python.exe
LOG_DIR=/c/Users/zonezone/Desktop/YCU_research/MetaDynamics/OmegaWiki/logs
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1

run_seed() {
    local ff=$1; local seed=$2; local cfg=$3; local outdir=$4; shift 4
    echo "[$(date +%H:%M)] $ff seed $seed starting" >> "$LOG_DIR/continuation.log"
    env "$@" $PYTHON -u train.py --config $cfg --ff $ff --seed $seed \
        --out-dir $outdir >> "$LOG_DIR/mlff-${ff}-s${seed}.log" 2>&1
    echo "[$(date +%H:%M)] $ff seed $seed done (rc=$?)" >> "$LOG_DIR/continuation.log"
}

# Wait for ANI-2x seed 42 result file (written when run completes)
echo "[$(date +%H:%M)] Waiting for ANI-2x seed 42..." >> "$LOG_DIR/continuation.log"
until [ -f "results_ani2x/seed_42.json" ] && \
      python3 -c "import json,sys; d=json.load(open('results_ani2x/seed_42.json')); sys.exit(0 if d.get('n_steps',0)>1000 else 1)" 2>/dev/null; do
    sleep 60
done
echo "[$(date +%H:%M)] ANI-2x seed 42 done, launching 123 and 7" >> "$LOG_DIR/continuation.log"

run_seed ani2x 123 config_ani2x.yaml results_ani2x TORCHANI_NO_WARN_EXTENSIONS=1
run_seed ani2x 7   config_ani2x.yaml results_ani2x TORCHANI_NO_WARN_EXTENSIONS=1

# Now run MACE (after ANI-2x frees GPU)
mkdir -p results_mace
for SEED in 42 123 7; do
    run_seed mace $SEED config_mace.yaml results_mace
done

echo "[$(date +%H:%M)] MACE done" >> "$LOG_DIR/continuation.log"
