
## 他アカウントの公開投稿を読む（Business Discovery）— 2026-11-05
- GET /{自分のIG ID}?fields=business_discovery.username(相手){...} で、相手の鍵なしに公開投稿・いいね数・コメント数を読める（相手はプロアカウント）
- **Facebookログイン方式の鍵でしか使えない**。必要な権限：instagram_basic / instagram_manage_insights / pages_read_engagement。自分のInstagramがFacebookページに連携していること
- 今のpandaの鍵（統合ログイン＝Instagramログイン方式、EAA…でも中身は instagram_business_*）では「(#10) Application does not have permission」になる
- 仕組みは scripts/fetch_public.py と fetch-posts.yml の account=axis_public。鍵を差し替えれば動く
