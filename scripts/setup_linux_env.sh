#!/usr/bin/env bash
# 在 Debian / Ubuntu / WSL 内配置 Axiodrasil 开发依赖
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[setup] project root: $ROOT"

echo "[setup] apt packages..."
# 无密码 sudo 时：在 Windows 侧执行  wsl -u root -- apt-get install -y ...
if [ "$(id -u)" -eq 0 ]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-pip python3-venv python3-dev \
    build-essential curl ca-certificates nodejs npm
elif sudo -n true 2>/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential curl ca-certificates nodejs npm
else
  echo "[setup] skip apt (need password). Install Python 3.13, Node.js >=20.9 and Docker Compose."
fi

python3 -c 'import sys; assert sys.version_info >= (3, 13), "Python 3.13 or later is required"'

echo "[setup] python venv..."
if [ ! -d "$ROOT/.venv" ]; then
  python3 -m venv "$ROOT/.venv"
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
python -m pip install -U pip wheel
python -m pip install -r "$ROOT/requirements.lock.txt"
# launcher GUI 在 Linux 可选；不强制装 customtkinter

echo "[setup] node..."
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck disable=SC1091
[ ! -s "$NVM_DIR/nvm.sh" ] || . "$NVM_DIR/nvm.sh"
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (major < 20 || (major === 20 && minor < 9)) { console.error("Node.js >=20.9 is required"); process.exit(1); }'
node -v
npm -v

echo "[setup] frontend npm ci..."
cd "$ROOT/frontend"
npm ci

echo "[setup] data dir..."
mkdir -p "$HOME/.axiodrasil/logs"
mkdir -p "$ROOT/data"
mkdir -p "$ROOT/.devstack/logs"

ENV_FILE="$ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
  cp "$ROOT/.env.example" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "[setup] created .env from .env.example — fill API keys"
fi

# 确保 Linux 本地库路径提示写入（不覆盖已有密钥）
if ! grep -q '^AX_DB_PATH=' "$ENV_FILE" 2>/dev/null; then
  {
    echo ""
    echo "# Linux / WSL local DB (avoid Windows UNC)"
    echo "AX_DB_PATH=$HOME/.axiodrasil/axiodrasil_core.db"
  } >> "$ENV_FILE"
  echo "[setup] appended AX_DB_PATH to .env"
fi

if [ ! -f "$ROOT/frontend/.env.local" ]; then
  printf 'BACKEND_URL=http://127.0.0.1:8000\n' > "$ROOT/frontend/.env.local"
fi

if ! docker compose version >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "[setup] Hindsight still needs a running Docker engine with Compose."
  echo "  Debian: sudo apt-get install docker.io docker-compose"
  echo "  WSL Docker Desktop: enable integration for this distribution."
fi

echo "[setup] done."
echo "  Activate venv:  source $ROOT/.venv/bin/activate"
echo "  Start stack:    $ROOT/start.sh"
echo "  Stop stack:     $ROOT/stop.sh"
