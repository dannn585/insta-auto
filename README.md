# insta-auto

Instagram 自動投稿（AI起業ログ）

- `drafts/YYYY-MM-DD.json` … 投稿の下書き（Claudeが作成）
- `scripts/render.py` … 下書き → `queue/YYYY-MM-DD/` に画像(1080x1350)とキャプションを生成
- `.github/workflows/publish.yml` … 毎日20:00(JST)に、その日付のフォルダを Instagram に投稿し `posted/` へ移動
- `scripts/publish.py` … Instagram公式API（Instagram Login）での投稿処理

必要な GitHub Secret: `IG_ACCESS_TOKEN`（Meta の App Dashboard で発行した長期トークン、有効期限60日）

テスト: Actions タブ → "Instagram daily post" → Run workflow（dry_run に 1 を入れると投稿せず確認だけ）

## リール
- `drafts/reels/YYYY-MM-DD.json` → `python scripts/reel.py <draft>` で `queue/YYYY-MM-DD/reel.mp4`（1080x1920, 30fps, H.264/AAC）と `cover.jpg` を生成
- `--stills` を付けると各シーンの静止画だけ出力（確認用）
- BGM は `scripts/beat.py` が毎回生成するオリジナル音源（著作権フリー）
