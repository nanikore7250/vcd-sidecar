# vcd-sidecar

**Volatile Cyber Defense (VCD) Phase 4** — Language-agnostic sidecar container for automated isolation, forensics, and self-destruction

Receives attack alerts via **webhook** and executes: network isolation → evidence collection → container self-destruction.  
No application code changes required — deploy alongside any existing container.

---

## Architecture

```
[Alert source]              (Falco + Falcosidekick, SIEM, custom script, etc.)
  ↓ HTTP POST /webhook
[vcd-sidecar]
  ① Network isolation      (iptables DROP on all inbound/outbound traffic)
  ② Evidence collection    (/proc — environ, cmdline, net/tcp, open files)
  ③ Memory dump            (gcore, optional)
  ④ Container destruction  (docker stop / kill + remove)
  ↓
[vuln-app-watchdog]         (docker:cli — recreates a clean container from image)
```

---

## Quick Start

### 1. Add to your docker-compose

```yaml
services:
  app:
    image: myapp:latest
    restart: always   # required: auto-restart after self-destruction

  vcd-sidecar:
    image: nanikore7250/vcd-sidecar:latest
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./forensics:/var/vcd/forensics
    ports:
      - "8888:8888"
    cap_add:
      - NET_ADMIN
```

### 2. Send an alert to trigger VCD

```bash
# Manual trigger (for testing)
./tests/trigger_alert.sh 1          # scenario: shell spawned
./tests/trigger_alert.sh 2          # scenario: outbound connection
./tests/trigger_alert.sh 3          # scenario: suspicious file write
./tests/trigger_alert.sh 4          # scenario: privilege escalation

# Or send directly via curl
curl -X POST http://localhost:8888/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "rule": "VCD - Shell spawned in container",
    "priority": "WARNING",
    "output_fields": {
      "container.id": "<container_id>",
      "container.name": "my-app",
      "proc.pid": "1234"
    }
  }'
```

### 3. Observe the VCD flow

```bash
docker logs vcd-test-sidecar        # isolation → forensics → destroy logs
docker ps -a | grep app             # container removed and recreated
ls ./forensics/                     # evidence files
```

---

## Test Environment

Spin up a complete demo environment (vulnerable PHP app + vcd-sidecar + watchdog):

```bash
docker compose -f docker-compose.test.yml up --build -d
./tests/trigger_alert.sh 1
```

The watchdog automatically recreates the container from a clean image after destruction.

### Integrating with Falco

To connect a real Falco + Falcosidekick pipeline, point Falcosidekick at the webhook:

```yaml
# falcosidekick environment
WEBHOOK_ADDRESS: http://vcd-sidecar:8888/webhook
WEBHOOK_MINIMUMPRIORITY: warning
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VCD_WEBHOOK_PORT` | `8888` | Webhook listening port |
| `VCD_FORENSICS_DIR` | `/var/vcd/forensics` | Evidence file output directory |
| `VCD_MEMORY_DUMP` | `false` | Enable gcore memory dump |
| `VCD_TERMINATE_MODE` | `graceful` | `graceful` / `strict` / `timeout` |
| `VCD_TERMINATE_TIMEOUT` | `30` | Seconds to wait in `timeout` mode |
| `VCD_TARGET_CONTAINER` | (empty) | Target container (auto-detected from alert if unset) |

### Termination Modes

| Mode | Behavior | Use case |
|------|----------|----------|
| `graceful` | `docker stop` (SIGTERM → SIGKILL after 10 s) | Default |
| `strict` | `docker kill` (immediate SIGKILL) | High-security |
| `timeout` | `docker stop -t N` | Configurable risk tolerance |

---

## VCD Flow Detail

```
POST /webhook
  ↓
① iptables isolation   — DROP all FORWARD traffic for the container IP
② Forensics collection — /proc/{pid}/{environ,cmdline,net/tcp,fd/}
③ Memory dump          — gcore (only when VCD_MEMORY_DUMP=true)
④ docker stop/kill     — according to VCD_TERMINATE_MODE
⑤ docker rm            — remove writable layer so restart recreates from image
⑥ iptables cleanup     — remove isolation rules for the recreated container
```

---

## Evidence File Format

```
forensics/
└── 20240423T123456Z_abc123def456.json
```

```json
{
  "timestamp": "20240423T123456Z",
  "container_id": "abc123...",
  "alert": { "rule": "...", "priority": "WARNING" },
  "proc": {
    "pid": "1234",
    "cmdline": "bash -i",
    "environ": "PATH=/usr/bin\n...",
    "net_tcp": "...",
    "open_files": ["0 -> /dev/pts/0", "..."]
  }
}
```

---

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | Receive alert and trigger VCD flow |
| `/healthz` | GET | Health check |

---

## Security Notes

- Mounting `docker.sock` grants the ability to manage all containers on the host — restrict access accordingly
- `NET_ADMIN` capability is required for iptables isolation
- Set `restart: always` on the target container, or use a watchdog to ensure clean recreation

---

## References

- VCD proof-of-concept: https://github.com/nanikore7250/VolatileCyberDefense
- vcd-python (app-embedded variant): https://github.com/nanikore7250/vcd-python
- Paper (Zenodo): https://zenodo.org/records/19648507

---

## License

MIT

---
---

# vcd-sidecar

**Volatile Cyber Defense (VCD) Phase 4** — 言語非依存のSidecarコンテナ型自壊・証拠保全システム

**webhook** で攻撃アラートを受け取り、ネットワーク断 → 証拠保全 → コンテナ自壊を実行します。  
アプリケーションのコードを一切変更せず、既存コンテナに追加するだけで動作します。

---

## アーキテクチャ

```
[アラート送信元]             （Falco + Falcosidekick、SIEM、カスタムスクリプト等）
  ↓ HTTP POST /webhook
[vcd-sidecar]
  ① ネットワーク断           （iptables で全外向き/内向き通信を遮断）
  ② 証拠保全                 （/proc — environ, cmdline, net/tcp, open files）
  ③ メモリダンプ             （gcore・オプション）
  ④ コンテナ自壊             （docker stop / kill + remove）
  ↓
[vuln-app-watchdog]          （docker:cli — イメージからクリーンな状態で再生成）
```

---

## クイックスタート

### 1. docker-compose に追加する

```yaml
services:
  app:
    image: myapp:latest
    restart: always   # ← 必須：自壊後に自動再起動

  vcd-sidecar:
    image: nanikore7250/vcd-sidecar:latest
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./forensics:/var/vcd/forensics
    ports:
      - "8888:8888"
    cap_add:
      - NET_ADMIN
```

### 2. アラートを送信して VCD を起動する

```bash
# 手動トリガー（動作確認用）
./tests/trigger_alert.sh 1          # シナリオ: シェル起動（コマンドインジェクション）
./tests/trigger_alert.sh 2          # シナリオ: 外向き接続（リバースシェル）
./tests/trigger_alert.sh 3          # シナリオ: ファイル書き込み（Webshell設置）
./tests/trigger_alert.sh 4          # シナリオ: 特権昇格

# curl で直接送信する場合
curl -X POST http://localhost:8888/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "rule": "VCD - Shell spawned in container",
    "priority": "WARNING",
    "output_fields": {
      "container.id": "<container_id>",
      "container.name": "my-app",
      "proc.pid": "1234"
    }
  }'
```

### 3. VCD フローを確認する

```bash
docker logs vcd-test-sidecar        # 隔離 → 証拠保全 → 自壊のログ
docker ps -a | grep app             # コンテナが削除・再生成されているか確認
ls ./forensics/                     # 証拠ファイルの保存を確認
```

---

## テスト環境

脆弱なPHPアプリ + vcd-sidecar + watchdog を一括起動するデモ環境：

```bash
docker compose -f docker-compose.test.yml up --build -d
./tests/trigger_alert.sh 1
```

Watchdog がコンテナ自壊後、クリーンなイメージから自動再生成します。

### Falco との連携

Falco + Falcosidekick を使用する場合は、Falcosidekick の転送先を設定します：

```yaml
# Falcosidekick の環境変数
WEBHOOK_ADDRESS: http://vcd-sidecar:8888/webhook
WEBHOOK_MINIMUMPRIORITY: warning
```

---

## 環境変数

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VCD_WEBHOOK_PORT` | `8888` | webhook受信ポート |
| `VCD_FORENSICS_DIR` | `/var/vcd/forensics` | 証拠ファイルの保存先 |
| `VCD_MEMORY_DUMP` | `false` | gcoreによるメモリダンプの有効化 |
| `VCD_TERMINATE_MODE` | `graceful` | `graceful` / `strict` / `timeout` |
| `VCD_TERMINATE_TIMEOUT` | `30` | `timeout`モード時の待機秒数 |
| `VCD_TARGET_CONTAINER` | （空） | 対象コンテナ名（省略するとアラートから自動取得） |

### 自壊モード

| モード | 動作 | 用途 |
|--------|------|------|
| `graceful` | `docker stop`（SIGTERM → 10秒後SIGKILL） | デフォルト |
| `strict` | `docker kill`（即時SIGKILL） | 高セキュリティ要件 |
| `timeout` | `docker stop -t N`（N秒後SIGKILL） | リスク許容度を調整 |

---

## VCDフロー詳細

```
POST /webhook
  ↓
① iptables 隔離    — コンテナIPへの全 FORWARD トラフィックを DROP
② フォレンジック   — /proc/{pid}/{environ,cmdline,net/tcp,fd/} を収集
③ メモリダンプ     — gcore（VCD_MEMORY_DUMP=true の場合のみ）
④ docker stop/kill — VCD_TERMINATE_MODE に従い停止
⑤ docker rm        — 書き込み可能レイヤーを削除（再起動時にイメージから再生成）
⑥ iptables クリア  — 再生成されたコンテナ用に隔離ルールを削除
```

---

## 証拠ファイル形式

```
forensics/
└── 20240423T123456Z_abc123def456.json
```

```json
{
  "timestamp": "20240423T123456Z",
  "container_id": "abc123...",
  "alert": { "rule": "...", "priority": "WARNING" },
  "proc": {
    "pid": "1234",
    "cmdline": "bash -i",
    "environ": "PATH=/usr/bin\n...",
    "net_tcp": "...",
    "open_files": ["0 -> /dev/pts/0", "..."]
  }
}
```

---

## エンドポイント

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/webhook` | POST | アラート受信・VCDフロー起動 |
| `/healthz` | GET | ヘルスチェック |

---

## セキュリティ上の注意

- `docker.sock` のマウントはホスト上の全コンテナ管理権限を持つため、アクセス制限を必ず設定してください
- iptables 隔離に `NET_ADMIN` が必要です
- 対象コンテナに `restart: always` を設定するか、watchdog で再生成を担保してください

---

## 関連リソース

- VCD概念実証: https://github.com/nanikore7250/VolatileCyberDefense
- vcd-python（アプリ組み込み型）: https://github.com/nanikore7250/vcd-python
- 論文（Zenodo）: https://zenodo.org/records/19648507

---

## ライセンス

MIT
