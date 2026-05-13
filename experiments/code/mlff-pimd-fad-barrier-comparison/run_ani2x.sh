#!/bin/bash
# ANI-2x PIMD FAD: 150 ps x 3 seeds (wB97X/6-31G*)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$SCRIPT_DIR"
PYTHON=/c/Users/zonezone/miniforge3/envs/zong-test/python.exe
[ -f "$WIKI_ROOT/.venv/Scripts/python.exe" ] && PYTHON="$WIKI_ROOT/.venv/Scripts/python.exe"
[ -f "$WIKI_ROOT/.venv/bin/python" ] && PYTHON="$WIKI_ROOT/.venv/bin/python"
export PYTHONIOENCODING=utf-8 TORCHANI_NO_WARN_EXTENSIONS=1
mkdir -p results_ani2x "$WIKI_ROOT/logs"
LOG="$WIKI_ROOT/logs/mlff-ani2x.log"
echo "[run_ani2x.sh] starting: $(date)" | tee "$LOG"
for SEED in 42 123 7; do
    echo "=== Seed $SEED: $(date) ===" | tee -a "$LOG"
    $PYTHON train.py --config config_ani2x.yaml --ff ani2x --seed $SEED --out-dir results_ani2x 2>&1 | tee -a "$LOG"
done
echo "[run_ani2x.sh] done: $(date)" | tee -a "$LOG"
