#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="$ROOT_DIR/output/playwright/m5"
WEB_PORT="${WEB_PORT:-3007}"
WEB_URL="http://127.0.0.1:${WEB_PORT}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"

mkdir -p "$ARTIFACT_DIR"

echo "== M5 baseline verification =="
"$ROOT_DIR/scripts/verify-m0.sh"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "== Docker Compose config =="
  docker compose -f "$ROOT_DIR/infra/docker/docker-compose.yml" config >/dev/null

  if [ "${RUN_DOCKER_SMOKE:-0}" = "1" ]; then
    echo "== Docker Compose smoke =="
    docker compose -f "$ROOT_DIR/infra/docker/docker-compose.yml" up --build -d
    docker_compose_cleanup() {
      docker compose -f "$ROOT_DIR/infra/docker/docker-compose.yml" down >/dev/null 2>&1 || true
    }
    trap docker_compose_cleanup EXIT
    for _ in $(seq 1 90); do
      if curl -fsS http://127.0.0.1:8000/api/v1/health/live >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    curl -fsS http://127.0.0.1:8000/api/v1/health/live >/dev/null
    curl -fsS http://127.0.0.1:8000/api/v1/health/ready >/dev/null
    docker_compose_cleanup
    trap - EXIT
  fi
else
  echo "Docker Compose is not available; skipping compose checks"
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is not installed; cannot run required Playwright CLI smoke checks" >&2
  exit 1
fi

if [ ! -f "$PWCLI" ]; then
  echo "Playwright CLI wrapper not found at $PWCLI; cannot run required browser smoke checks" >&2
  exit 1
fi

echo "== M5 browser smoke =="
(
  cd "$ROOT_DIR/apps/web"
  npm run dev -- --hostname 127.0.0.1 --port "$WEB_PORT" \
    >"$ARTIFACT_DIR/web-dev.log" 2>&1 &
  echo "$!" >"$ARTIFACT_DIR/web-dev.pid"
)

WEB_PID="$(cat "$ARTIFACT_DIR/web-dev.pid")"
cleanup() {
  if kill -0 "$WEB_PID" >/dev/null 2>&1; then
    kill "$WEB_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  if curl -fsS "$WEB_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "$WEB_URL" >/dev/null 2>&1; then
  echo "web server did not become ready; see $ARTIFACT_DIR/web-dev.log" >&2
  exit 1
fi

check_page() {
  local path="$1"
  local expected="$2"
  local label="$3"
  local output_file="$ARTIFACT_DIR/${label}.snapshot.txt"

  (
    cd "$ARTIFACT_DIR"
    bash "$PWCLI" open "$WEB_URL$path" >/dev/null
    bash "$PWCLI" snapshot >"$output_file"
  )

  if ! grep -q "$expected" "$output_file"; then
    echo "Expected '$expected' in $path snapshot; see $output_file" >&2
    exit 1
  fi
  echo "checked $path"
}

check_page "/" "M5 Hardening" "home"
check_page "/products" "精选商品" "products"
check_page "/cart" "购物车" "cart"
check_page "/checkout" "确认订单" "checkout"
check_page "/orders/order-20260716001" "申请售后" "order-detail"
check_page "/after-sales" "售后进度" "after-sales"
check_page "/after-sales/as-20260716001" "申请客服介入" "after-sales-detail"
check_page "/merchant/after-sales" "售后处理队列" "merchant-after-sales"
check_page "/admin/work-orders" "证据链" "admin-work-orders"

echo "M5 browser smoke completed; artifacts in $ARTIFACT_DIR"
