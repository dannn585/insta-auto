# タスク一覧
状態：未着手 / 進行中 / レビュー待ち / 確認待ち（ダン） / 完了
| ID | タスク | 担当 | 期限 | 状態 | メモ |
|---|---|---|---|---|---|
| T1 | 会社の仕組み（このファイル一式）を insta-auto に追加 | secretary | 11/04 | 完了 | 11/04 push済み |
| T2 | 毎日のリサーチを予約タスク化（vidIQで伸びているリールを調べる） | research | 11/05 | 未着手 | デスクトップアプリ側で設定 |
| T3 | @panda の初投稿（11/03）の数字を確認 | research | 11/05 | 完了 | 11/04 着手。GitHubからの数字取得はダンの権限が必要（下のT9）。11/04 17:30 vidIQ公開データ：フォロワー0、DAY0 31回・DAY1 5回再生（いいね0）。保存・シェア・視聴時間はvidIQにInstagram未接続のため取れず。詳細 knowledge/research-log.md |
| T4 | AXISの鍵の発行 | secretary | 未定 | 確認待ち（ダン） | 代表の了解・ログインが必要 |
| T5 | 「AI」とコメント→DMで渡す無料特典の企画 | product | 11/08 | 完了 | 11/04 着手。企画案 company/products/free-gift-plan.md（B案おすすめ）。11/04 ダン決定：B案・Notion（予備Googleドキュメント）・LINE登録後に渡す（LINE開設まではDMでリンク直送）。11/04 本文全12ページ＋ひな形5点完成 → company/products/starter-kit/（目次・使い方は README.md）。1〜5ページの下書きも見直し済み（無料プランで使えるとは書かない、自動で読むのは Claude Code だけと明記）。次：秘書レビュー → ダンが使い方A（デスクトップアプリ）で1回通して確認 → Notionへ移す（公開・リンク作成はダンの確認後）。12ページの【社内メモ】行は公開前に消す。11/04 ダン決定（B案・Notion・LINE登録後に渡す）。本文12ページ＋ひな形5点 company/products/starter-kit/ 完成・秘書レビュー済み。Notionへの移し替えは T13 |
| T6 | プロフィールから販売までの導線の設計案 | marketing | 11/08 | 完了 | 11/04 案を作成 company/marketing/funnel-v1.md（特典はT5のB案に合わせた）。ダンの判断2点：①プロフィール案A/B（推奨B）と固定投稿の差し替え ②DMは手動＋公式機能、特典はLINE登録後に渡す（LINE開設）でよいか。狙う数字と判断日：「AI」コメント率0.3%→11/18判断／週30件超が2週続けば外部ツール検討→11/30判断。11/04 ダン決定：プロフィール案B・固定投稿差し替え・LINE登録後に特典。実施は T14・T15 |
| T7 | @panda 11/06〜11/08 の投稿下書き（予約が11/05で切れるため） | creative | 11/05 | 完了 | 11/04 下書き完成：drafts/reels/2026-11-06.json（DAY3 リール・AI社員6人）、drafts/reels/2026-11-07.json（DAY4 リール・自動化5選）、drafts/2026-11-08.json（DAY5 カルーセル・会社の決めごと）。形式チェックOK。画像・動画化（render.py / reel.py）はこのPCに PIL・playwright が無く未実施 → queue/ には未生成 |
| T8 | 自動投稿の時間ずれ（20:00予定が実際は深夜3〜6時）の対策 | secretary | 11/06 | 完了 | GitHubの予約実行が5〜7時間遅れている。11/04 対策済み：予約を0分から外して5回に分け、19:30〜23:59 JST の回だけ投稿（AXISは20:30〜）。11/05 の投稿で効果を確認 |
| T9 | 「Fetch past posts」をダンが手動実行（数字の取得） | ダン | 11/05 | 完了 | Claude側からは権限不足で実行できない。11/04 実行済み（ログインが dannn585 に切り替わり、秘書から実行）。フォロワー0・いいね0・コメント0 |
| T10 | 11/06〜08 の下書きを画像・動画にして queue/ へ（11/06 20:00 までに必須） | secretary | 11/05 | 完了 | このPCに部品（pillow・playwright）が無い。PCに入れるか、デスクトップアプリ側で作るか。11/04 部品を入れて生成→queue/ に入れて push。声は GitHub で自動付与済み |
| T11 | vidIQ に Instagram をつなぐ（保存・シェア・視聴時間を取るため） | ダン | 11/07 | 確認待ち（ダン） | アカウント設定の変更なのでダンが実施 |
| T12 | リン・カンパニーをプラグイン（lin-company）1つにまとめ、どのフォルダでも使えるようにする | secretary | 11/04 | 完了 | 11/04 完了。.claude/ と ~/.claude の重複は削除（ダン了承済み）。呼び方 /lin-company:company。直し方は lin-company-plugin/README.md |
| T13 | スターターキットを Notion に移す（手順は starter-kit/README.md）→ 公開リンクはダンが確認して作る | ダン | 11/08 | 確認待ち（ダン） | 11/04 夜 秘書が Notion に非公開の下書きで移した（表紙＋2〜12ページの子ページ、12ページの社内メモ行は削除済み）。URL：https://app.notion.com/p/40e9856d5ffc8159aa1cfc7eedda145c 。残り：ダンが中身を確認→使い方Aで1回通す→Notionの「共有→Webで公開」でリンク作成 |
| T14 | プロフィールを案Bに変更（特典リンクができてから） | ダン | 11/08 | 確認待ち（ダン） | 文面は marketing/funnel-v1.md「案B」。先に変えると渡せない申し込みが来るため、T13の後 |
| T15 | LINE公式アカウント（無料プラン）を開設 | ダン | 11/10 | 確認待ち（ダン） | できるまでは DM で Notion のリンクを直接送る |
| T16 | 固定投稿②「AI秘書の作り方キット、中身を全部見せます」カルーセル制作 | creative | 11/09 | 未着手 | T13 の後。固定①は 11/06 DAY3 リールを使う |
| T17 | 11/05 の投稿が 19:30〜23:59 に出たか確認 | secretary | 11/06 | 未着手 | T8 の効果確認 |
| T18 | VS Code 側の Chrome で Instagram（@panda.7475341）にログインする | ダン | 11/08 | 確認待ち（ダン） | 11/04 ブラウザ接続は確認済み。ただしこの Chrome では Instagram 未ログイン。ログインは本人のみ。T14（プロフィール変更）の前に必要 |
| T19 | AXISの公開投稿を panda の鍵で取り込む（Business Discovery） | secretary | 11/08 | 確認待ち（ダン） | 11/05 実行 → Meta「(#10) アプリに権限がない」。今の鍵は Instagramログイン方式で、Business Discovery は Facebookログイン方式（instagram_basic・instagram_manage_insights・pages_read_engagement、pandaをFacebookページに連携）が必要。仕組み（scripts/fetch_public.py・fetch-posts.yml の axis_public）は完成済み。鍵を追加発行すれば即動く |
| T20 | AXISのCanvaテンプレに合わせて投稿デザインを作り直す | secretary | 11/06 | 完了 | 11/05 テンプレ（DAG8ijGL2Fc「AXIS１ 勉強会やってます」5枚）を読み取り、axis/templates/slide.html と axis/scripts/reel.py を作り直し。11/04カルーセル（6枚）・11/06リールを再生成。残り：活動写真を axis/assets/bg.jpg に置くと背景がテンプレと同じ「写真を白く薄めた」見た目になる（今は色だけで代用）。Canvaでの直接複製は権限で止められた |
