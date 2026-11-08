#!/usr/bin/env bash
# Local Hindsight, API and frontend. Only stop groups owned by this launcher.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="$ROOT/.devstack"
LOG_DIR="$STATE_DIR/logs"
mkdir -p "$LOG_DIR"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ ! -s "$NVM_DIR/nvm.sh" ] || . "$NVM_DIR/nvm.sh"
PYTHON="$ROOT/.venv/bin/python"
[ -x "$PYTHON" ] || PYTHON=python3
export AX_PROJECT_ROOT="$ROOT"
if [ -z "${AX_DB_PATH:-}" ]; then
  AX_DB_PATH="$("$PYTHON" -c 'from dotenv import dotenv_values; import sys; print(dotenv_values(sys.argv[1]).get("AX_DB_PATH") or "")' "$ROOT/.env")"
fi
export AX_DB_PATH="${AX_DB_PATH:-$HOME/.axiodrasil/axiodrasil_core.db}"
export PYTHONIOENCODING=utf-8

port_listen() {
  ss -ltn "sport = :$1" 2>/dev/null | grep -q ":$1"
}
wait_port() {
  local i
  for ((i=0; i<${2:-60}; i++)); do
    if port_listen "$1"; then return 0; fi
    sleep 1
  done
  return 1
}
docker_compose() {
  if docker info >/dev/null 2>&1; then
    docker compose -f "$ROOT/docker-compose.yml" "$@"
  else
    sudo docker compose -f "$ROOT/docker-compose.yml" "$@"
  fi
}
start_service() {
  local name="$1" port="$2"
  shift 2
  if port_listen "$port"; then
    if "$PYTHON" "$ROOT/scripts/stack_process.py" status "$STATE_DIR/$name.json"; then
      echo "[$name] already running"
      return 0
    fi
    echo "[$name] port $port occupied; leaving existing process untouched" >&2
    return 1
  fi
  "$PYTHON" "$ROOT/scripts/stack_process.py" start "$STATE_DIR/$name.json" -- "$@"
  if ! wait_port "$port" 90; then
    echo "[$name] failed; see $LOG_DIR/$name.log" >&2
    return 1
  fi
}
case "${1:-status}" in
  start)
    mkdir -p "$(dirname "$AX_DB_PATH")"
    if ! port_listen 8888; then docker_compose up -d hindsight; fi
    wait_port 8888 180
    start_service backend 8000 "$PYTHON" -m uvicorn main:app --host 127.0.0.1 --port 8000
    start_service frontend 3000 bash -lc "cd '$ROOT/frontend' && npm run dev"
    echo "Ready: http://127.0.0.1:3000/solo"
    ;;
  stop)
    "$PYTHON" "$ROOT/scripts/stack_process.py" stop "$STATE_DIR/frontend.json"
    "$PYTHON" "$ROOT/scripts/stack_process.py" stop "$STATE_DIR/backend.json"
    docker_compose stop hindsight
    ;;
  restart)
    bash "$0" stop
    bash "$0" start
    ;;
  status)
    for item in hindsight:8888 backend:8000 frontend:3000; do
      if port_listen "${item##*:}"; then echo "$item RUNNING"; else echo "$item STOPPED"; fi
    done
    ;;
  *) echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2 ;;
esac
