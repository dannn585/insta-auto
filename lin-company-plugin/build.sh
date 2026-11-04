#!/usr/bin/env bash
# リン・カンパニーの元ファイル（insta-auto/.claude/）から
#   1. 全体用の場所（~/.claude/agents, ~/.claude/commands）
#   2. プラグイン（lin-company-plugin/plugins/lin-company/）
# を作り直すスクリプト。元ファイルを直したら、これを実行する。
#   bash lin-company-plugin/build.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_WIN='C:\Users\ssrdn\OneDrive\デスクトップ\claude作業場\insta-auto'
PLUGIN="$ROOT/lin-company-plugin/plugins/lin-company"
NOTE="> **会社の本拠地**：\`$HOME_WIN\`
> この文中の \`CLAUDE.md\`・\`company/\` などは、すべて本拠地の中の場所。今いるフォルダが別でも、記録の読み書きと git pull / commit / push は本拠地で行う。"

convert() { # $1=元ファイル $2=出力先
  mkdir -p "$(dirname "$2")"
  NOTE="$NOTE" awk 'BEGIN { note = ENVIRON["NOTE"] }
    { print }
    /^---$/ { n++; if (n==2) { print ""; print note } }
  ' "$1" > "$2"
}

for dest in "$HOME/.claude" "$PLUGIN"; do
  for f in "$ROOT"/.claude/agents/*.md;   do convert "$f" "$dest/agents/$(basename "$f")"; done
  for f in "$ROOT"/.claude/commands/*.md; do convert "$f" "$dest/commands/$(basename "$f")"; done
done
echo "作り直しました：$HOME/.claude と $PLUGIN"
