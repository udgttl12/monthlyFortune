#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
UVICORN_WORKERS="${UVICORN_WORKERS:-2}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Missing virtualenv interpreter at ${VENV_PYTHON}" >&2
  echo "Create it first with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

cd "${ROOT_DIR}"

exec "${VENV_PYTHON}" -m uvicorn app.main:app \
  --host "${API_HOST}" \
  --port "${API_PORT}" \
  --workers "${UVICORN_WORKERS}"
