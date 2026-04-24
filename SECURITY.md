# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | Yes       |

## Reporting a Vulnerability

Please report vulnerabilities via
[GitHub Security Advisories](https://github.com/nanikore7250/vcd-sidecar/security/advisories/new).
Do not use GitHub Issues for vulnerability reports.

---

## ⚠️ 重要な警告 / Important Warnings

このコンテナは以下の強い権限を必要とします。

### 必要な権限

| 権限 | 理由 |
|------|------|
| `/var/run/docker.sock` のマウント | 他のコンテナを停止・強制終了するため |
| `NET_ADMIN` capability | iptablesによるネットワーク断を実行するため |

### 使用前に必ず理解してください

- **コンテナが強制終了されます**
  攻撃検知時に対象コンテナを `docker stop` / `docker kill` します。
  本番環境への適用前に、再起動ポリシー（`restart: always`）を必ず設定してください。

- **`restart: always` が必須です**
  自動再起動機構がない場合、自壊後にサービスが停止したままになります。
  VCDはサービスの自動回復を前提とした設計です。

- **誤検知のリスクがあります**
  Falcoのデフォルトルールは広範です。`falco/vcd_rules.yaml` を本番環境に合わせてチューニングし、
  十分なステージング検証を経てから適用してください。

- **`docker.sock` のマウントはリスクを伴います**
  `/var/run/docker.sock` をマウントしたコンテナは、ホスト上の全Dockerコンテナを操作できます。
  信頼できる分離されたネットワーク環境でのみ使用してください。

- **SIGTERMハンドリングへの依存**
  `graceful` モードおよび `timeout` モードでの残存通信完了待機は、
  対象コンテナのアプリケーションが SIGTERM を正しくハンドリングしている場合のみ機能します。
  ハンドリングしていない場合はタイムアウト後に SIGKILL で強制終了されます。
  これはアプリケーション実装に依存する制約です。

### 推奨する運用環境

- Kubernetes / Docker Compose の管理下にある隔離されたクラスタ
- Falco + Falcosidekick が適切に設定されていること
- 証拠保存先ボリュームへのアクセス制御が行われていること
- vcd-sidecar 自体のコンテナへのアクセスが制限されていること（port 8888 は内部ネットワークのみ公開）
