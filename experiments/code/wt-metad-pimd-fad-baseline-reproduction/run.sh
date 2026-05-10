#!/bin/bash
# WT-MetaD PIMD FAD baseline — v3: 300 ps x 3 seeds, exp(-bias/kT) FES reweighting
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$SCRIPT_DIR"

OUT_DIR="results_v3"
LOG_DIR="$WIKI_ROOT/logs"
mkdir -p "$OUT_DIR" "$LOG_DIR"

PYTHON=python
if [ -f "$WIKI_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON="$WIKI_ROOT/.venv/Scripts/python.exe"
elif [ -f "$WIKI_ROOT/.venv/bin/python" ]; then
    PYTHON="$WIKI_ROOT/.venv/bin/python"
fi

export PYTHONIOENCODING=utf-8

SLUG=wt-metad-pimd-fad-baseline-reproduction
LOG="$LOG_DIR/exp-${SLUG}-v3.log"

echo "[run.sh] WT-MetaD v3 starting: $(date)" | tee -a "$LOG"
echo "[run.sh] Python: $PYTHON" | tee -a "$LOG"
echo "[run.sh] Output: $SCRIPT_DIR/$OUT_DIR" | tee -a "$LOG"

for SEED in 42 123 7; do
    echo "" | tee -a "$LOG"
    echo "[run.sh] === Seed $SEED starting: $(date) ===" | tee -a "$LOG"
    $PYTHON train.py --config config.yaml --seed $SEED --out-dir "$OUT_DIR" 2>&1 | tee -a "$LOG"
    echo "[run.sh] === Seed $SEED done: $(date) ===" | tee -a "$LOG"
done

echo "" | tee -a "$LOG"
echo "[run.sh] All seeds complete: $(date)" | tee -a "$LOG"
echo "[run.sh] Results in $SCRIPT_DIR/$OUT_DIR/seed_*.json" | tee -a "$LOG"
