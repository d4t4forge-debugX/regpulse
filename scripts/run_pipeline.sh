#!/bin/bash
set -e

cd "$(dirname "$0")/.."

VENV_PYTHON=".venv/bin/python"
LOG_FILE="logs/pipeline_$(date +%Y-%m-%d_%H-%M-%S).log"

mkdir -p logs

{
  echo "=== RegPulse pipeline run: $(date) ==="

  echo "--- Fetching new Federal Register docs ---"
  "$VENV_PYTHON" -m ingestion.fetch_federal_register

  echo "--- Running graph (retrieve, judge, memo) ---"
  "$VENV_PYTHON" -m pipeline.run_graph

  echo "=== Done: $(date) ==="
} >> "$LOG_FILE" 2>&1