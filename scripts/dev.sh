#!/usr/bin/env bash
# Start Redis (Docker Compose), FastAPI, and ARQ worker for local development.
#
# Usage (from repo anywhere):
#   ./scripts/dev.sh
#
# Skip bringing up Docker Redis (e.g. you use Homebrew redis):
#   SKIP_REDIS=1 ./scripts/dev.sh
#
# Environment (optional): REDIS_HOST, REDIS_PORT

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6379}"

if [[ "${SKIP_REDIS:-}" != "1" ]]; then
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$ROOT/docker-compose.yml" up -d
    echo "Redis: docker compose up -d (see docker-compose.yml)"
  else
    echo "WARN: docker not found. Start Redis yourself on ${REDIS_HOST}:${REDIS_PORT} or install Docker Desktop." >&2
    echo "      Or run: SKIP_REDIS=1 ./scripts/dev.sh" >&2
  fi
else
  echo "SKIP_REDIS=1: not starting Docker Redis."
fi

export PYTHONUNBUFFERED=1

cleanup() {
  local code=$?
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${WORKER_PID:-}" ]] && kill -0 "$WORKER_PID" 2>/dev/null; then
    kill "$WORKER_PID" 2>/dev/null || true
  fi
  exit "$code"
}

trap cleanup INT TERM

echo "Starting API (python main.py)..."
python main.py &
API_PID=$!

echo "Starting ARQ worker (arq arq_worker.WorkerSettings)..."
arq arq_worker.WorkerSettings &
WORKER_PID=$!

echo "API PID=$API_PID, worker PID=$WORKER_PID. Press Ctrl+C to stop API + worker (Redis container keeps running)."
# Wait until both exit (bash 3.2–compatible; no wait -n).
wait "$API_PID" "$WORKER_PID" || true
