# リン・カンパニー プラグイン

秘書リンと5部署のエージェント、`/company` コマンドを、どのフォルダからでも使えるようにするためのもの。

## 3つの置き場所
| 場所 | 役割 |
|---|---|
| `insta-auto/.claude/` | **元のファイル**。直すときはここだけ直す |
| `~/.claude/agents`, `~/.claude/commands` | 全体用（どのフォルダでも `secretary` などで呼べる） |
| `lin-company-plugin/plugins/lin-company/` | プラグイン（`lin-company:secretary` などで呼べる） |

全体用とプラグインのファイルには「会社の本拠地＝insta-auto」の一文が入っている。別のフォルダで呼んでも、記録（company/）の読み書きと git pull / push は insta-auto で行う。

## 元のファイルを直したら
```
bash lin-company-plugin/build.sh
claude plugin update lin-company@lin-company
```

## 別のPCで入れるとき
```
claude plugin marketplace add <insta-auto の場所>/lin-company-plugin
claude plugin install lin-company@lin-company --scope user
```
