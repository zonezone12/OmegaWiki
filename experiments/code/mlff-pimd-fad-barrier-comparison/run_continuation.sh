#!/bin/bash
# Continuation script: runs remaining seeds for ANI-2x, PhysNet, and MACE
# Call after seed-42 processes (PIDs passed as args) finish
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PYTHON=/c/Users/zonezone/miniforge3/envs/zong-test/python.exe
LOG_DIR=/c/Users/zonezone/Desktop/YCU_research/MetaDynamics/OmegaWiki/logs
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1

echo "[continuation] starting at $(date)" | tee -a "$LOG_DIR/continuation.log"

# Wait for ANI-2x seed 42 (PID $1) if provided
if [ -n "$1" ]; then
    echo "Waiting for ANI-2x PID $1..." | tee -a "$LOG_DIR/continuation.log"
    wait $1 2>/dev/null || true
fi

# Run ANI-2x seeds 123 and 7
mkdir -p results_ani2x
for SEED in 123 7; do
    echo "=== ANI-2x seed $SEED: $(date) ===" | tee -a "$LOG_DIR/mlff-ani2x-s${SEED}.log"
    TORCHANI_NO_WARN_EXTENSIONS=1 $PYTHON -u train.py \
      --config config_ani2x.yaml --ff ani2x --seed $SEED --out-dir results_ani2x \
      2>&1 | tee -a "$LOG_DIR/mlff-ani2x-s${SEED}.log"
done
echo "[continuation] ANI-2x all seeds done: $(date)" | tee -a "$LOG_DIR/continuation.log"

# Wait for PhysNet seed 42 (PID $2) if provided
if [ -n "$2" ]; then
    echo "Waiting for PhysNet PID $2..." | tee -a "$LOG_DIR/continuation.log"
    wait $2 2>/dev/null || true
fi

# Run PhysNet seeds 123 and 7
mkdir -p results_physnet
for SEED in 123 7; do
    echo "=== PhysNet seed $SEED: $(date) ===" | tee -a "$LOG_DIR/mlff-physnet-s${SEED}.log"
    TF_CPP_MIN_LOG_LEVEL=3 TF_ENABLE_ONEDNN_OPTS=0 $PYTHON -u train.py \
      --config config_physnet.yaml --ff physnet --seed $SEED --out-dir results_physnet \
      2>&1 | tee -a "$LOG_DIR/mlff-physnet-s${SEED}.log"
done
echo "[continuation] PhysNet all seeds done: $(date)" | tee -a "$LOG_DIR/continuation.log"

# Run MACE all 3 seeds (after ANI-2x frees GPU)
mkdir -p results_mace
for SEED in 42 123 7; do
    echo "=== MACE seed $SEED: $(date) ===" | tee -a "$LOG_DIR/mlff-mace-s${SEED}.log"
    $PYTHON -u train.py \
      --config config_mace.yaml --ff mace --seed $SEED --out-dir results_mace \
      2>&1 | tee -a "$LOG_DIR/mlff-mace-s${SEED}.log"
done
echo "[continuation] MACE all seeds done: $(date)" | tee -a "$LOG_DIR/continuation.log"
echo "[continuation] ALL DONE: $(date)" | tee -a "$LOG_DIR/continuation.log"
