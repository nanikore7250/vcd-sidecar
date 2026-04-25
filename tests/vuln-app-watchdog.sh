#!/bin/sh
# Watchdog: vcd-test-vuln-app の destroy イベントを監視し、docker run で再生成する
# docker compose ではなく docker run を使うことで、プロジェクト名の不一致問題を回避する

set -eu

IMAGE="vcd-test-vuln-app:latest"
CONTAINER="vcd-test-vuln-app"
NETWORK="vcd-test-net"
PORT="8080:80"

echo "[watchdog] starting. monitoring '${CONTAINER}' for destroy events..."

docker events \
    --filter "container=${CONTAINER}" \
    --filter "event=destroy" \
    --format "{{.Time}}" \
| while read ts; do
    echo "[watchdog] destroy detected at ${ts}"
    echo "[watchdog] waiting for name release..."
    sleep 2

    # 万が一残骸が残っていれば除去
    docker rm -f "${CONTAINER}" 2>/dev/null || true

    echo "[watchdog] recreating ${CONTAINER} from ${IMAGE}..."
    docker run -d \
        --name "${CONTAINER}" \
        --restart no \
        --network "${NETWORK}" \
        -p "${PORT}" \
        "${IMAGE}"

    echo "[watchdog] ${CONTAINER} recreated (clean state from image)"
done
