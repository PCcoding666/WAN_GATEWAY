#!/usr/bin/env bash
# Deploy / update Wan Gateway on any Docker host from the image CI publishes to GHCR.
#
#   ./production/deploy.sh                 # latest image
#   ./production/deploy.sh <tag|sha>       # a specific build (rollback)
#
# Reads the runtime settings from a .env file next to this script or in the
# current directory (DASHSCOPE_API_KEY is required; see ../.env.example).
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/pccoding666/wan_gateway}"
TAG="${1:-latest}"
NAME="${CONTAINER_NAME:-wan-gateway}"
PORT="${PORT:-7860}"
DATA_DIR="${DATA_DIR:-$HOME/wan-gateway/data}"

here="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${ENV_FILE:-}"
for candidate in "$ENV_FILE" "$PWD/.env" "$here/.env" "$here/../.env"; do
  if [ -n "$candidate" ] && [ -f "$candidate" ]; then ENV_FILE="$candidate"; break; fi
done
[ -f "${ENV_FILE:-/nonexistent}" ] || { echo "No .env found (copy .env.example and set DASHSCOPE_API_KEY)"; exit 1; }
grep -q '^DASHSCOPE_API_KEY=.\+' "$ENV_FILE" || { echo "DASHSCOPE_API_KEY missing in $ENV_FILE"; exit 1; }

command -v docker >/dev/null || { echo "docker is not installed"; exit 1; }

echo "▶ pulling $IMAGE:$TAG"
docker pull "$IMAGE:$TAG"

echo "▶ restarting container $NAME on port $PORT"
docker rm -f "$NAME" >/dev/null 2>&1 || true
mkdir -p "$DATA_DIR"
docker run -d --name "$NAME" --restart unless-stopped \
  -p "$PORT:7860" \
  -v "$DATA_DIR:/app/data" \
  --env-file "$ENV_FILE" \
  "$IMAGE:$TAG" >/dev/null

echo "▶ waiting for http://127.0.0.1:$PORT/"
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null "http://127.0.0.1:$PORT/"; then
    echo "✅ Wan Gateway is up: http://127.0.0.1:$PORT/"
    docker ps --filter "name=$NAME" --format '   {{.Names}}  {{.Status}}  {{.Image}}'
    exit 0
  fi
  sleep 2
done
echo "❌ container did not answer; last logs:"
docker logs --tail 50 "$NAME"
exit 1
