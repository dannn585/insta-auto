# セットアップ手順（ダン用）

## 1. （完了）insta-auto に追加済み
insta-auto のいちばん上（README と同じ場所）に、次をそのまま置く：
`CLAUDE.md` / `.claude/` / `company/` / `SETUP.md`
（すでに CLAUDE.md がある場合は、リンに「まとめて」と頼む）

## 2. PCに insta-auto を置く（1回だけ）
1. VS Codeを開き、Ctrl+Shift+P →「Git: Clone」→ `https://github.com/dannn585/insta-auto` → 保存先は `ドキュメント` など
2. 拡張機能（Ctrl+Shift+X）で「Claude Code」を入れ、Claude.aiのアカウントでログイン

## 3. VS Codeで使う
- Claude Codeのパネルで `/company` と打つ → 秘書リンが状況確認と振り分けを始める
- 部署を直接呼ぶとき：「research エージェントで今週のネタを5つ出して」など
- 終わったら「pushして」と言えばGitHubに保存され、デスクトップアプリ側からも見える

## 4. デスクトップアプリで使う
- Claudeアプリの「フォルダを追加」で、2で作った insta-auto フォルダを接続する
  → VS Codeと**同じファイル**を読み書きできる
- 毎日・毎週の自動実行（予約タスク）はデスクトップアプリ側で設定する

## 同期のルール
- 作業を始める前：最新を取り込む（VS Code左下の同期ボタン or「pullして」）
- 作業が終わったら：commit & push
- 両方で同時に同じファイルを編集しない
