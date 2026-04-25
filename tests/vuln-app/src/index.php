<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>VCD 動作検証サイト</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
h1 { color: #e94560; }
h2 { color: #0f3460; background: #16213e; padding: 0.5rem; border-left: 4px solid #e94560; }
.card { background: #16213e; border: 1px solid #0f3460; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
.card a { color: #4fc3f7; text-decoration: none; font-size: 1.1rem; }
.card a:hover { color: #e94560; }
.tag { font-size: 0.75rem; background: #e94560; color: white; padding: 2px 6px; border-radius: 3px; margin-left: 0.5rem; }
.falco-rule { font-size: 0.8rem; color: #888; margin-top: 0.3rem; }
</style>
</head>
<body>
<h1>⚠ VCD 動作検証サイト</h1>
<p>このサイトは <strong>vcd-sidecar の動作検証専用</strong> です。本番環境では絶対に使用しないでください。</p>

<h2>検証シナリオ</h2>

<div class="card">
  <a href="cmd.php">① OSコマンドインジェクション</a>
  <span class="tag">HIGH</span>
  <p class="falco-rule">→ Falcoルール: VCD - Shell spawned in container</p>
</div>

<div class="card">
  <a href="upload.php">② ファイルアップロード（Webshell設置）</a>
  <span class="tag">HIGH</span>
  <p class="falco-rule">→ Falcoルール: VCD - Unexpected file written in container</p>
</div>

<div class="card">
  <a href="rshell.php">③ リバースシェル</a>
  <span class="tag">CRITICAL</span>
  <p class="falco-rule">→ Falcoルール: VCD - Outbound connection in container</p>
</div>

<div class="card">
  <a href="lfi.php">④ ローカルファイルインクルード（LFI）</a>
  <span class="tag">MEDIUM</span>
  <p class="falco-rule">→ Falcoルール: VCD - Sensitive file read in container</p>
</div>

<div class="card">
  <a href="sqli.php">⑤ SQLインジェクション</a>
  <span class="tag">MEDIUM</span>
  <p class="falco-rule">→ 直接のFalcoルールなし（検証用）</p>
</div>

<hr>
<p style="color:#888; font-size: 0.85rem;">
  vcd-sidecar webhook: <code>http://vcd-sidecar:8888/webhook</code><br>
  アラートを手動送信する場合は <code>tests/trigger_alert.sh</code> を参照してください。
</p>
</body>
</html>
