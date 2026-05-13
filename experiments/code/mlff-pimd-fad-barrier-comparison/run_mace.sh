#!/bin/bash
# MACE-OFF23 PIMD FAD: 50 ps x 3 seeds (B3LYP-D3BJ/def2-TZVPD, SPICE)
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$SCRIPT_DIR"
PYTHON=/c/Users/zonezone/miniforge3/envs/zong-test/python.exe
[ -f "$WIKI_ROOT/.venv/Scripts/python.exe" ] && PYTHON="$WIKI_ROOT/.venv/Scripts/python.exe"
[ -f "$WIKI_ROOT/.venv/bin/python" ] && PYTHON="$WIKI_ROOT/.venv/bin/python"
export PYTHONIOENCODING=utf-8 TORCHANI_NO_WARN_EXTENSIONS=1
mkdir -p results_mace "$WIKI_ROOT/logs"
LOG="$WIKI_ROOT/logs/mlff-mace.log"
echo "[run_mace.sh] starting: $(date)" | tee "$LOG"
for SEED in 42 123 7; do
    echo "=== Seed $SEED: $(date) ===" | tee -a "$LOG"
    $PYTHON train.py --config config_mace.yaml --ff mace --seed $SEED --out-dir results_mace 2>&1 | tee -a "$LOG"
done
echo "[run_mace.sh] done: $(date)" | tee -a "$LOG"
