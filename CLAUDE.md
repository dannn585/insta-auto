# Instagram 事業（リポジトリ insta-auto）

会社のルール・タスク・日報は **本社 `../CLAUDE.md` と `../company/`**（リポジトリ claude-company）にある。
このフォルダは Instagram の投稿データと自動投稿の仕組みだけを置く。

## panda（@dan_aishain、旧 @panda.7475341）
- 目的：**収益化**。リール → プロフィール → 固定投稿 →「AI」とコメント → DM → LINE → 商品（キット）。設計は `../company/marketing/funnel-v1.md`
- 誰に：Claude・AI で仕事や作業を楽にしたい人。「Claudeの〇〇N選」「Claudeで会社を作った記録（DAYn）」が2本柱
- 口調・見た目：結論から短く。リールはスタイル v3（11/13〜：生成りの明るい1色の背景・墨の極太文字・黄色は文字の下の帯だけ・最初の1秒で画面が動く。`scripts/reel_v3.py`）。カルーセルは v2 のまま（当面止めている）。詳細は `../company/knowledge/instagram-strategy.md`
- 置き場所：`drafts/`（下書き）→ `queue/`（投稿待ち。毎日20:00）→ `posted/`（投稿済み）。差し替えた古い予約は `spare/`

## AXIS（@axis_doshisha）
- **目的・口調・ルールは本社の `../axis/CLAUDE.md`**（panda と目的が違う：集客が目的）。担当は `lin-company:axis`
- 投稿データは `axis/`（自動投稿がこの場所を使うので、本社へは移さない）

## 共通
- 自動投稿：`.github/workflows/`（GitHub Actions。PCがオフでも動く）。トークンは GitHub Secrets だけに置く
- 道具：`scripts/`（画像・動画の生成など）、`templates/`、`assets/`
- Instagram の運用方針：`../company/knowledge/instagram-strategy.md`

ここを触ったら、このフォルダで commit & push（insta-auto）。会社の記録を触ったら本社でも commit & push。
