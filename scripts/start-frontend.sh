#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_HOST="${WEB_HOST:-127.0.0.1}"
WEB_PORT="${WEB_PORT:-3000}"

cd "${ROOT_DIR}"

if [[ ! -d "${ROOT_DIR}/.next" ]]; then
  echo "Missing Next.js build output. Run npm run build first." >&2
  exit 1
fi

exec npm run start -- --hostname "${WEB_HOST}" --port "${WEB_PORT}"
