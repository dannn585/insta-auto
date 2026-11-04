# AI社員スターターキット ― まずは秘書を1人雇う（無料特典・本文一式）

- 作成：プロダクト部 / 2026-11-04 / タスク T5
- 状態：本文完成・秘書レビュー済み → 11/04 Notion に非公開で移し済み（https://app.notion.com/p/40e9856d5ffc8159aa1cfc7eedda145c）→ ダン確認待ち（公開リンク作成・送信はダンの確認後）
- 一行で：**AIを毎回ゼロから使って続かない大学生・個人に、AI秘書が毎日の仕事を覚えてくれる仕組みを、無料（秘書1人分）で渡す**
- 企画書：company/products/free-gift-plan.md（ダン決定 11/04：B案／渡し方 Notion・予備 Googleドキュメント／LINE登録の後に渡す。LINEができるまではDMでリンクを直接送る）

## 目次（読む順番＝使う順番）

| ページ | ファイル | 見出し |
|---|---|---|
| 1 | pages/01-cover.md | 表紙 |
| 2 | pages/02-introduction.md | はじめに |
| 3 | pages/03-overview.md | 全体図：AI社員6人の会社 |
| 4 | pages/04-why-secretary.md | なぜ秘書から始めるのか |
| 5 | pages/05-preparation.md | 準備するもの（使い方A/B/Cを選ぶ） |
| 6 | pages/06-step1-folder.md | 手順1：フォルダを作る |
| 7 | pages/07-step2-claude-md.md | 手順2：会社のルール（CLAUDE.md）を置く |
| 8 | pages/08-step3-secretary.md | 手順3：秘書の設定を置く |
| 9 | pages/09-step4-tasks-reports.md | 手順4：タスク表と日報のひな形 |
| 10 | pages/10-first-3-days.md | 最初の3日間 |
| 11 | pages/11-first-10-prompts.md | 付録：秘書への最初の指示10個 |
| 12 | pages/12-next-steps.md | 次のステップ（完全版・導入サポートの予告） |

## 利用者がコピーするひな形（templates/）
フォルダの形のまま、利用者の my-company/ に置けばそのまま動く構成です。

| ファイル | 置く場所 | 説明しているページ |
|---|---|---|
| templates/CLAUDE.md | my-company/CLAUDE.md | 7 |
| templates/agents/secretary.md | my-company/agents/secretary.md | 8 |
| templates/tasks.md | my-company/tasks.md | 9 |
| templates/reports/report-template.md | my-company/reports/report-template.md | 9 |
| templates/knowledge/README.md | my-company/knowledge/README.md | 9 |

## 利用者の使い方の順番
1. 1〜4ページを読む（5分）
2. 5ページで使い方を選ぶ（A：デスクトップアプリ＋フォルダ／B：Claude Code／C：コピペだけ）
3. 6〜9ページの手順でフォルダとファイルを作り、3か所書き換える（30分〜1時間）
4. 10ページの「最初の3日間」を進める。指示文は11ページからコピー
5. 3日目に2人目の社員を決めて、12ページへ

## 社内向けメモ（Notionに載せない）
- 7〜9ページのコピペ枠の中身は templates/ と同じ。ひな形を直したら、ページ側の枠も同じように直す
- 12ページの【社内メモ・公開前に消す】の行は、公開前に差し替えるか消す
- 入れていないもの：ダンのアカウント名・秘密情報・料金の数字。Claude の機能は「2026年11月時点」と書き、確かめられていない画面名・ボタン名・プランごとの可否は書いていない（利用者に自分の画面で確かめてもらう書き方にした）
- 公開前にダンに試してほしいこと：使い方A（デスクトップアプリ）で、空のフォルダから6〜10ページの手順どおりに1回通す（画面の説明が実際と合っているかの確認）
