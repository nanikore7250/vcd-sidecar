<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>④ ローカルファイルインクルード</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
h1 { color: #e94560; }
pre { background: #0f3460; padding: 1rem; border-radius: 4px; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
input[type=text] { width: 400px; padding: 0.4rem; background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; }
input[type=submit] { padding: 0.4rem 1rem; background: #e94560; color: white; border: none; cursor: pointer; }
.info { color: #888; font-size: 0.85rem; }
a { color: #4fc3f7; }
</style>
</head>
<body>
<h1>④ ローカルファイルインクルード（LFI）</h1>
<p class="info">
  <code>?file=</code> パラメータをサニタイズせずに <code>file_get_contents()</code> に渡します。<br>
  <strong>VCDトリガー:</strong> <code>/etc/passwd</code>, <code>/etc/shadow</code> へのアクセスを Falco が検知します。
</p>

<form method="GET">
  <label>ファイルパス: </label>
  <input type="text" name="file" value="<?= htmlspecialchars($_GET['file'] ?? '/etc/hostname') ?>">
  <input type="submit" value="読み取り">
</form>

<h3>攻撃例:</h3>
<ul>
  <li><a href="?file=/etc/hostname">?file=/etc/hostname</a> — コンテナ名確認</li>
  <li><a href="?file=/etc/passwd">?file=/etc/passwd</a> — ユーザー一覧（VCDトリガー）</li>
  <li><a href="?file=/etc/shadow">?file=/etc/shadow</a> — パスワードハッシュ（VCDトリガー）</li>
  <li><a href="?file=/proc/self/environ">?file=/proc/self/environ</a> — 環境変数（認証情報漏洩）</li>
  <li><a href="?file=/proc/self/cmdline">?file=/proc/self/cmdline</a> — コマンドライン</li>
  <li><a href="?file=../../../../../../etc/passwd">パストラバーサル</a></li>
</ul>

<?php
if (isset($_GET['file']) && $_GET['file'] !== '') {
    $path = $_GET['file'];
    echo "<h3>ファイル: <code>" . htmlspecialchars($path) . "</code></h3>";
    echo "<pre>";
    // 意図的にパス検証なし（検証専用）
    $content = @file_get_contents($path);
    if ($content === false) {
        echo "読み取り失敗（権限不足またはファイルが存在しない）";
    } else {
        // null-byteを改行に変換（/proc/*/environ等）
        echo htmlspecialchars(str_replace("\0", "\n", $content));
    }
    echo "</pre>";
}
?>

<p><a href="index.php">← 戻る</a></p>
</body>
</html>
