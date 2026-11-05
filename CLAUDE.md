# Instagram 事業（リポジトリ insta-auto）

会社のルール・タスク・日報は **本社 `../CLAUDE.md` と `../company/`**（リポジトリ claude-company）にある。
このフォルダは Instagram の投稿データと自動投稿の仕組みだけを置く。

- @panda.7475341：`drafts/`（下書き）→ `queue/`（投稿待ち）→ `posted/`（投稿済み）
- AXIS（@axis_doshisha）運用代行：`axis/`
- 自動投稿：`.github/workflows/`（GitHub Actions。PCがオフでも動く）。トークンは GitHub Secrets だけに置く
- 道具：`scripts/`（画像・動画の生成など）、`templates/`、`assets/`
- Instagram の運用方針：`../company/knowledge/instagram-strategy.md`

ここを触ったら、このフォルダで commit & push（insta-auto）。会社の記録を触ったら本社でも commit & push。
