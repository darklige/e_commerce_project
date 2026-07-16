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

ANDROID_STUDIO_JBR="/Applications/Android Studio.app/Contents/jbr/Contents/Home"

if [ -x "$ROOT_DIR/apps/android/gradlew" ] && { java -version >/dev/null 2>&1 || [ -x "$ANDROID_STUDIO_JBR/bin/java" ]; }; then
  echo "== Android build =="
  export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
  if ! java -version >/dev/null 2>&1 && [ -x "$ANDROID_STUDIO_JBR/bin/java" ]; then
    export JAVA_HOME="$ANDROID_STUDIO_JBR"
  fi
  (
    cd "$ROOT_DIR/apps/android"
    ./gradlew lint test assembleDebug
  )
else
  echo "Android build skipped: Gradle Wrapper and Java Runtime are not available"
fi
