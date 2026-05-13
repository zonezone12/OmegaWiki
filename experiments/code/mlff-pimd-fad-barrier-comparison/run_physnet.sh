#!/bin/bash
# PhysNet PIMD FAD: 300 ps x 3 seeds (MP2/aug-cc-pVTZ)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$SCRIPT_DIR"
PYTHON=/c/Users/zonezone/miniforge3/envs/zong-test/python.exe
[ -f "$WIKI_ROOT/.venv/Scripts/python.exe" ] && PYTHON="$WIKI_ROOT/.venv/Scripts/python.exe"
[ -f "$WIKI_ROOT/.venv/bin/python" ] && PYTHON="$WIKI_ROOT/.venv/bin/python"
export PYTHONIOENCODING=utf-8 TF_CPP_MIN_LOG_LEVEL=3 TF_ENABLE_ONEDNN_OPTS=0
mkdir -p results_physnet "$WIKI_ROOT/logs"
LOG="$WIKI_ROOT/logs/mlff-physnet.log"
echo "[run_physnet.sh] starting: $(date)" | tee "$LOG"
for SEED in 42 123 7; do
    echo "=== Seed $SEED: $(date) ===" | tee -a "$LOG"
    $PYTHON train.py --config config_physnet.yaml --ff physnet --seed $SEED --out-dir results_physnet 2>&1 | tee -a "$LOG"
done
echo "[run_physnet.sh] done: $(date)" | tee -a "$LOG"
