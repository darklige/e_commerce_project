#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== API tests =="
uv sync --project "$ROOT_DIR/apps/api" --group dev
(
  cd "$ROOT_DIR/apps/api"
  uv run ruff check .
  uv run pytest
)

if command -v npm >/dev/null 2>&1; then
  echo "== Web checks =="
  cd "$ROOT_DIR/apps/web"
  if [ ! -d node_modules ]; then
    npm install
  fi
  npm run lint
  npm run typecheck
  npm run build
else
  echo "npm is not installed; skipping web checks"
fi

if command -v gradle >/dev/null 2>&1 && command -v java >/dev/null 2>&1; then
  echo "== Android build =="
  gradle -p "$ROOT_DIR/apps/android" :app:assembleDebug
else
  echo "Android build skipped: Gradle and/or Java Runtime is not installed"
fi
