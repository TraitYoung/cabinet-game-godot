#!/usr/bin/env bash
# Reproducible local/CI gate. Does not start models or touch user data.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${BINA_CHECK_PYTHON:-.venv/bin/python}"
"$PYTHON" -m ruff check .
"$PYTHON" -m ruff format --check .
"$PYTHON" -m mypy
"$PYTHON" scripts/check_process_ownership.py
"$PYTHON" -m unittest discover -s test_suite -v
bash -n start.sh stop.sh scripts/dev_stack.sh scripts/setup_linux_env.sh
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
