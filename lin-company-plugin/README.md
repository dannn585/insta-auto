# リン・カンパニー プラグイン

秘書リンと5部署のエージェント、`/company` コマンドを、どのフォルダからでも使えるようにするプラグイン。
**リン・カンパニーの元のファイルは、ここ1か所だけ。**

## 呼び方
- 入口：`/lin-company:company`
- エージェント：`lin-company:secretary`、`lin-company:research` など

どのフォルダで呼んでも、記録（company/）の読み書きと git pull / push は本拠地の insta-auto で行う（各ファイルの冒頭に書いてある）。

## 中身
```
lin-company-plugin/
├─ .claude-plugin/marketplace.json   プラグインの置き場の情報
└─ plugins/lin-company/
   ├─ .claude-plugin/plugin.json     プラグインの名前・版
   ├─ agents/                        秘書と5部署
   └─ commands/company.md            /lin-company:company
```

## 直したら（反映させる手順）
インストールしたプラグインはコピーされて使われるので、直しただけでは反映されない。
1. `plugins/lin-company/.claude-plugin/plugin.json` の `version` を1つ上げる（例 1.1.0 → 1.2.0）
2. 次を実行して、新しい画面を開く
```
claude plugin marketplace update lin-company
claude plugin update lin-company@lin-company
```

## 別のPCで入れるとき
```
claude plugin marketplace add <insta-auto の場所>/lin-company-plugin
claude plugin install lin-company@lin-company --scope user
```
