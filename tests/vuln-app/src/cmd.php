<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>① OSコマンドインジェクション</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
h1 { color: #e94560; }
pre { background: #0f3460; padding: 1rem; border-radius: 4px; white-space: pre-wrap; }
input[type=text] { width: 400px; padding: 0.4rem; background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; }
input[type=submit] { padding: 0.4rem 1rem; background: #e94560; color: white; border: none; cursor: pointer; }
.info { color: #888; font-size: 0.85rem; }
a { color: #4fc3f7; }
</style>
</head>
<body>
<h1>① OSコマンドインジェクション</h1>
<p class="info">
  入力値をそのまま <code>shell_exec()</code> に渡します。<br>
  <strong>VCDトリガー:</strong> <code>bash</code> や <code>sh</code> を起動すると Falco が検知します。
</p>

<form method="GET">
  <label>コマンド: </label>
  <input type="text" name="cmd" value="<?= htmlspecialchars($_GET['cmd'] ?? 'id') ?>">
  <input type="submit" value="実行">
</form>

<h3>攻撃例:</h3>
<ul>
  <li><a href="?cmd=id">id</a> — ユーザー確認</li>
  <li><a href="?cmd=whoami">whoami</a></li>
  <li><a href="?cmd=cat+/etc/passwd">cat /etc/passwd</a> — 機密ファイル読み取り</li>
  <li><a href="?cmd=bash+-c+'id'">bash -c 'id'</a> — シェル起動（VCDトリガー）</li>
  <li><a href="?cmd=ls+-la+/var/vcd/forensics">ls /var/vcd/forensics</a> — 証拠ファイル確認</li>
</ul>

<?php
if (isset($_GET['cmd']) && $_GET['cmd'] !== '') {
    $cmd = $_GET['cmd'];
    echo "<h3>実行: <code>" . htmlspecialchars($cmd) . "</code></h3>";
    echo "<pre>";
    // 意図的に危険な実行（検証専用）
    $output = shell_exec($cmd . ' 2>&1');
    echo htmlspecialchars($output ?? '(出力なし)');
    echo "</pre>";
    echo "<p class='info'>PID: " . getmypid() . "</p>";
}
?>

<p><a href="index.php">← 戻る</a></p>
</body>
</html>
