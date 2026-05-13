#!/usr/bin/env bash
# OPES-PIMD FAD proton transfer convergence -- Stage 9 (FES sign fix, PACE=100, sigma=0.15, BARRIER=60 kJ/mol, 300 ps)
# Runs 3 independent seeds (42, 123, 7) sequentially.
# Usage: bash run.sh
# Output: results_v8/seed_{N}.json + results_v8/fes_snapshots/seed_{N}/fes_step*.npz

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$SCRIPT_DIR"

OUT_DIR="results_v9"
LOG_DIR="$WIKI_ROOT/logs"
mkdir -p "$OUT_DIR" "$LOG_DIR"

PYTHON=python
if [ -f "$WIKI_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON="$WIKI_ROOT/.venv/Scripts/python.exe"
elif [ -f "$WIKI_ROOT/.venv/bin/python" ]; then
    PYTHON="$WIKI_ROOT/.venv/bin/python"
fi

echo "[run.sh] OPES-PIMD Stage 8 starting: $(date)"
echo "[run.sh] Python: $PYTHON"
echo "[run.sh] Output: $SCRIPT_DIR/$OUT_DIR"

for SEED in 42 123 7; do
    echo ""
    echo "[run.sh] === Seed $SEED starting: $(date) ==="
    $PYTHON train.py --config config.yaml --seed $SEED --out-dir "$OUT_DIR"
    echo "[run.sh] === Seed $SEED done: $(date) ==="
done

echo ""
echo "[run.sh] All seeds complete: $(date)"
echo "[run.sh] Results in $SCRIPT_DIR/$OUT_DIR/seed_*.json"
echo "[run.sh] FES snapshots in $SCRIPT_DIR/results_v8/fes_snapshots/"
