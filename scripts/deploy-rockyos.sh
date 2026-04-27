#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NPM_BIN="${NPM_BIN:-npm}"
RUN_TESTS="${RUN_TESTS:-1}"
FRONTEND_INSTALL="${FRONTEND_INSTALL:-1}"
FRONTEND_BUILD="${FRONTEND_BUILD:-1}"
SYSTEMD_RELOAD="${SYSTEMD_RELOAD:-1}"
RESTART_SERVICES="${RESTART_SERVICES:-1}"
API_SERVICE_NAME="${API_SERVICE_NAME:-monthly-fortune-api}"
WEB_SERVICE_NAME="${WEB_SERVICE_NAME:-monthly-fortune-web}"

cd "${ROOT_DIR}"

if [[ ! -d ".venv" ]]; then
  "${PYTHON_BIN}" -m venv .venv
fi

".venv/bin/pip" install --upgrade pip
".venv/bin/pip" install -r requirements.txt

if [[ "${FRONTEND_INSTALL}" == "1" ]]; then
  "${NPM_BIN}" ci
fi

if [[ "${FRONTEND_BUILD}" == "1" ]]; then
  "${NPM_BIN}" run build
fi

if [[ "${RUN_TESTS}" == "1" ]]; then
  ".venv/bin/python" -m unittest discover -s tests -v
fi

if [[ "${SYSTEMD_RELOAD}" == "1" ]] && command -v systemctl >/dev/null 2>&1; then
  sudo systemctl daemon-reload
fi

if [[ "${RESTART_SERVICES}" == "1" ]] && command -v systemctl >/dev/null 2>&1; then
  if systemctl cat "${API_SERVICE_NAME}" >/dev/null 2>&1; then
    sudo systemctl restart "${API_SERVICE_NAME}"
  else
    echo "Skipping restart: ${API_SERVICE_NAME} is not installed yet."
  fi

  if systemctl cat "${WEB_SERVICE_NAME}" >/dev/null 2>&1; then
    sudo systemctl restart "${WEB_SERVICE_NAME}"
  else
    echo "Skipping restart: ${WEB_SERVICE_NAME} is not installed yet."
  fi

  if systemctl cat nginx >/dev/null 2>&1; then
    sudo systemctl reload nginx
  else
    echo "Skipping nginx reload: nginx service is not installed yet."
  fi
fi

echo "Deployment complete."
