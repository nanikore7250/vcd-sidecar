#!/usr/bin/env bash
# VCDアラートを手動送信するスクリプト
# Falco + Falcosidekick なしで vcd-sidecar の動作を検証できます
#
# 使い方:
#   ./tests/trigger_alert.sh [シナリオ番号]
#
# シナリオ:
#   1 - Shell spawned (bash起動) ← デフォルト
#   2 - Outbound connection (リバースシェル)
#   3 - File written (Webshell設置)
#   4 - Privilege escalation (setuid)

set -euo pipefail

SIDECAR_URL="${VCD_SIDECAR_URL:-http://localhost:8888}"
SCENARIO="${1:-1}"

# vuln-appのコンテナIDを取得
CONTAINER_ID=$(docker inspect --format '{{.Id}}' vcd-test-vuln-app 2>/dev/null || echo "")
CONTAINER_NAME="vcd-test-vuln-app"

if [[ -z "$CONTAINER_ID" ]]; then
  echo "ERROR: コンテナ vcd-test-vuln-app が見つかりません"
  echo "先に起動してください: docker compose -f docker-compose.test.yml up -d"
  exit 1
fi

# コンテナのPID1を取得（フォレンジック用）
PID=$(docker inspect --format '{{.State.Pid}}' vcd-test-vuln-app)

echo "=== VCD アラート手動送信 ==="
echo "対象コンテナ: ${CONTAINER_NAME}"
echo "コンテナID:   ${CONTAINER_ID:0:12}"
echo "PID:          ${PID}"
echo ""

case "$SCENARIO" in
  1)
    RULE="VCD - Shell spawned in container"
    PRIORITY="WARNING"
    PROC_NAME="bash"
    echo "シナリオ: ① Shell spawned (bash起動)"
    ;;
  2)
    RULE="VCD - Outbound connection in container"
    PRIORITY="WARNING"
    PROC_NAME="php"
    echo "シナリオ: ② Outbound connection (外向き接続)"
    ;;
  3)
    RULE="VCD - Unexpected file written in container"
    PRIORITY="WARNING"
    PROC_NAME="php"
    echo "シナリオ: ③ File written (ファイル書き込み)"
    ;;
  4)
    RULE="VCD - Privilege escalation attempt"
    PRIORITY="CRITICAL"
    PROC_NAME="php"
    echo "シナリオ: ④ Privilege escalation (特権昇格)"
    ;;
  *)
    echo "ERROR: 不明なシナリオ番号: $SCENARIO (1-4 を指定してください)"
    exit 1
    ;;
esac

PAYLOAD=$(cat <<EOF
{
  "rule": "${RULE}",
  "priority": "${PRIORITY}",
  "output": "[VCD TEST] ${RULE} (container=${CONTAINER_NAME} pid=${PID})",
  "output_fields": {
    "container.id": "${CONTAINER_ID}",
    "container.name": "${CONTAINER_NAME}",
    "proc.name": "${PROC_NAME}",
    "proc.pid": "${PID}"
  },
  "time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
)

echo ""
echo "送信先: ${SIDECAR_URL}/webhook"
echo "ペイロード:"
echo "$PAYLOAD" | python3 -m json.tool 2>/dev/null || echo "$PAYLOAD"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST "${SIDECAR_URL}/webhook" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:")

echo "レスポンス: HTTP ${HTTP_STATUS}"
echo "$BODY"
echo ""

if [[ "$HTTP_STATUS" == "200" ]]; then
  echo "✓ アラート送信成功"
  echo ""
  echo "VCDフローが開始されました。以下で確認してください:"
  echo "  - コンテナ状態: docker ps -a | grep vuln-app"
  echo "  - 証拠ファイル: ls -la ./forensics/"
  echo "  - サイドカーログ: docker logs vcd-test-sidecar -f"
else
  echo "✗ アラート送信失敗 (HTTP ${HTTP_STATUS})"
  exit 1
fi
