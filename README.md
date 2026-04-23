# vcd-sidecar

**Volatile Cyber Defense (VCD) Phase 4** — 言語非依存のSidecarコンテナ型自壊・証拠保全システム

Falcoが検知した攻撃アラートを受け取り、**ネットワーク断 → 証拠保全 → コンテナ自壊**を実行するSidecarコンテナです。
アプリケーションのコードを一切変更せず、既存のFalco環境に追加するだけでVCDが機能します。

---

## アーキテクチャ

```
[Falco DaemonSet]
  syscallを監視（シェル起動・リバースシェル・特権昇格 etc.）
  ↓ アラート
[Falcosidekick]
  アラートをwebhookに転送
  ↓ HTTP POST
[vcd-sidecar]
  ① ネットワーク断（iptables）
  ② 証拠保全（/proc情報収集）
  ③ メモリダンプ（gcore・オプション）
  ④ コンテナ自壊（docker stop / kill）
  ↓ ボリューム経由
[forensicsストレージ]
  証拠ファイルを永続化
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

詳細は [docker-compose.example.yml](docker-compose.example.yml) を参照してください。

### 2. Falcosidekick の転送先を設定する

```yaml
webhook:
  address: http://vcd-sidecar:8888/webhook
```

### 3. Falco カスタムルールを追加する（オプション）

```bash
cp falco/vcd_rules.yaml /etc/falco/rules.d/
```

---

## 環境変数

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VCD_WEBHOOK_PORT` | `8888` | webhook受信ポート |
| `VCD_FORENSICS_DIR` | `/var/vcd/forensics` | 証拠ファイルの保存先 |
| `VCD_MEMORY_DUMP` | `false` | gcoreによるメモリダンプの有効化 |
| `VCD_TERMINATE_MODE` | `graceful` | 自壊モード（`graceful` / `strict` / `timeout`） |
| `VCD_TERMINATE_TIMEOUT` | `30` | `timeout`モード時の待機秒数 |
| `VCD_TARGET_CONTAINER` | （空） | 監視対象コンテナ名（省略するとアラートから自動取得） |

### 自壊モード

| モード | 動作 | 用途 |
|--------|------|------|
| `graceful` | `docker stop`（SIGTERM → 10秒後SIGKILL） | デフォルト。可用性とセキュリティのバランス |
| `strict` | `docker kill`（即時SIGKILL） | 高セキュリティ要件。残存通信を待たない |
| `timeout` | `docker stop -t N`（N秒後SIGKILL） | `VCD_TERMINATE_TIMEOUT`でリスク許容度を調整 |

---

## VCDフロー

Falcosidekickから `/webhook` にPOSTが届くと以下の順序で実行されます：

```
① ネットワーク断（iptables で外向き/内向き通信を遮断）
② 軽量フォレンジック収集（/proc/{pid}/environ, cmdline, net/tcp, fd/）
③ メモリダンプ（VCD_MEMORY_DUMP=true の場合のみ）
④ コンテナ自壊（VCD_TERMINATE_MODE に従う）
```

ネットワーク断を先に行うことで、証拠収集・メモリダンプ中の外部通信を防ぎます。

---

## エンドポイント

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/webhook` | POST | Falcosidekickからのアラート受信 |
| `/healthz` | GET | ヘルスチェック |

---

## 証拠ファイル

```
/var/vcd/forensics/
└── 20240423T123456Z_abc123def456.json
```

```json
{
  "timestamp": "20240423T123456Z",
  "container_id": "abc123...",
  "falco_alert": { "rule": "...", "priority": "WARNING", ... },
  "proc": {
    "pid": "1234",
    "cmdline": "bash",
    "environ": "PATH=/usr/bin\n...",
    "net_tcp": "...",
    "open_files": ["0 -> /dev/pts/0", ...]
  }
}
```

---

## セキュリティ上の注意

詳細は [SECURITY.md](SECURITY.md) を参照してください。

- `docker.sock` のマウントにより、ホスト上の全コンテナを操作できる権限を持ちます
- `NET_ADMIN` が必要です
- `restart: always` を設定しないとサービスが自壊後に停止します
- Falcoルールのチューニングを必ず行い、誤検知を最小化してください

---

## 関連リソース

- VCD概念実証: https://github.com/nanikore7250/VolatileCyberDefense
- vcd-python（アプリ組み込み型）: https://github.com/nanikore7250/vcd-python
- 論文（Zenodo）: https://zenodo.org/records/19648507
- Falco: https://falco.org
- Falcosidekick: https://github.com/falcosecurity/falcosidekick

---

## ライセンス

MIT
