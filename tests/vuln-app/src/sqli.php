<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>⑤ SQLインジェクション</title>
<style>
body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
h1 { color: #e94560; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #0f3460; padding: 0.4rem 0.8rem; text-align: left; }
th { background: #0f3460; }
input[type=text] { width: 400px; padding: 0.4rem; background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; }
input[type=submit] { padding: 0.4rem 1rem; background: #e94560; color: white; border: none; cursor: pointer; }
.info { color: #888; font-size: 0.85rem; }
pre { background: #0f3460; padding: 0.5rem; border-radius: 4px; }
a { color: #4fc3f7; }
</style>
</head>
<body>
<h1>⑤ SQLインジェクション（SQLite）</h1>
<p class="info">
  検索キーワードをそのままSQLに埋め込みます（プリペアドステートメントなし）。<br>
  <strong>VCDとの関連:</strong> DBダンプ後にOSコマンド実行へ移行するシナリオで使用します。
</p>

<?php
$db_path = '/tmp/users.db';

// 初回起動時にサンプルDBを作成
if (!file_exists($db_path)) {
    $db = new PDO("sqlite:$db_path");
    $db->exec("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)");
    $db->exec("INSERT INTO users VALUES (1, 'admin', 'secret123', 'admin@example.com')");
    $db->exec("INSERT INTO users VALUES (2, 'alice', 'password1', 'alice@example.com')");
    $db->exec("INSERT INTO users VALUES (3, 'bob',   'qwerty',   'bob@example.com')");
    $db->exec("INSERT INTO users VALUES (4, 'carol', 'letmein',  'carol@example.com')");
}

$db = new PDO("sqlite:$db_path");

$keyword = $_GET['q'] ?? '';
$results = [];
$error   = '';
$sql     = '';

if ($keyword !== '') {
    // 意図的にプリペアドステートメントを使わない（検証専用）
    $sql = "SELECT id, username, password, email FROM users WHERE username = '" . $keyword . "'";
    try {
        $stmt = $db->query($sql);
        $results = $stmt ? $stmt->fetchAll(PDO::FETCH_ASSOC) : [];
    } catch (Exception $e) {
        $error = $e->getMessage();
    }
}
?>

<form method="GET">
  <label>ユーザー名で検索: </label>
  <input type="text" name="q" value="<?= htmlspecialchars($keyword) ?>">
  <input type="submit" value="検索">
</form>

<h3>攻撃例:</h3>
<ul>
  <li><a href="?q=admin">?q=admin</a> — 通常検索</li>
  <li><a href="?q=' OR '1'='1">?q=' OR '1'='1</a> — 全件取得</li>
  <li><a href="?q=' OR 1=1--">?q=' OR 1=1--</a> — コメントアウト</li>
  <li><a href="?q=' UNION SELECT 1,name,sql,4 FROM sqlite_master--">UNION SELECT（テーブル定義取得）</a></li>
</ul>

<?php if ($sql): ?>
<h3>実行SQL:</h3>
<pre><?= htmlspecialchars($sql) ?></pre>
<?php endif; ?>

<?php if ($error): ?>
<p style="color:#e94560">エラー: <?= htmlspecialchars($error) ?></p>
<?php endif; ?>

<?php if (!empty($results)): ?>
<h3>検索結果 (<?= count($results) ?> 件):</h3>
<table>
  <tr><th>ID</th><th>username</th><th>password</th><th>email</th></tr>
  <?php foreach ($results as $row): ?>
  <tr>
    <td><?= htmlspecialchars($row['id']) ?></td>
    <td><?= htmlspecialchars($row['username']) ?></td>
    <td><?= htmlspecialchars($row['password']) ?></td>
    <td><?= htmlspecialchars($row['email']) ?></td>
  </tr>
  <?php endforeach; ?>
</table>
<?php elseif ($keyword !== '' && empty($error)): ?>
<p>該当なし</p>
<?php endif; ?>

<p><a href="index.php">← 戻る</a></p>
</body>
</html>
