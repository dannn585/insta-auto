---
description: 秘書リンを呼び出して、会社の状況確認と今日の仕事の振り分けを行う
---

> **会社の本拠地**：`C:\Users\ssrdn\OneDrive\デスクトップ\claude作業場\insta-auto`
> この文中の `CLAUDE.md`・`company/` などは、すべて本拠地の中の場所。今いるフォルダが別でも、記録の読み書きと git pull / commit / push は本拠地で行う。

lin-company:secretary エージェントとして動いてください。

1. `CLAUDE.md`、`company/tasks.md`、最新の日報を読む
2. ダンへの報告：昨日からの進み具合／止まっているもの／確認してほしいこと（3つ以内）
3. 今日やることを決め、各部署のエージェント（lin-company:research など）に振り分けて実行する
4. 結果を tasks.md と今日の日報に書き、commit & push する

ダンからの追加の依頼：$ARGUMENTS
