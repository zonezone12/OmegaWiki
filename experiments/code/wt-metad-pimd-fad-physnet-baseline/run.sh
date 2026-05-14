#!/usr/bin/env bash
# Run WT-MetaD PIMD on PhysNet FAD: 3 seeds x 300 ps
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_TAG="[wt-metad-pimd-fad-physnet-baseline]"
echo "$LOG_TAG Starting at $(date)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || echo "$LOG_TAG No GPU detected"

if [[ "${1:-}" == "--sanity" ]]; then
  echo "$LOG_TAG Sanity check: 10 ps seed=42"
  python train.py --config config.yaml --sanity --seed 42
  echo "$LOG_TAG Sanity PASSED"
  exit 0
fi

for SEED in 42 123 7; do
  echo "$LOG_TAG === Seed $SEED started at $(date) ==="
  python train.py --config config.yaml --seed "$SEED" --out-dir results_physnet
  echo "$LOG_TAG === Seed $SEED finished at $(date) ==="
done

echo "$LOG_TAG All 3 seeds complete at $(date)"
