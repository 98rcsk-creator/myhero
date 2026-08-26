#!/bin/sh
# 実機確認リンクを渡す前に必ず実行する（CLAUDE.md §9-10）。
# 記憶に頼らず、この1本で「渡してよい状態か」を機械判定する。
# 使い方: sh tools/relink.sh
set -u
FAIL=0
say(){ printf '%s\n' "$*"; }

git fetch origin main -q 2>/dev/null

say "=== ① 未マージのコミット（空であること） ==="
LEFT=$(git log --oneline origin/main..HEAD)
if [ -n "$LEFT" ]; then
  say "$LEFT"
  say "❌ mainに届いていないコミットがある → PRを立て直すこと（説明文の更新では防げない）"
  FAIL=1
else
  say "✅ 空。取りこぼしなし"
fi

say ""
say "=== ② 公開ページ = main = 手元 のバイト照合 ==="
TMP=$(mktemp)
curl -s "https://98rcsk-creator.github.io/myhero/index.html?cb=$$" -o "$TMP"
L=$(wc -c < "$TMP"); M=$(git show origin/main:index.html | wc -c); W=$(wc -c < game/my_hero.html)
say "公開 $L / main $M / 手元 $W"
if [ "$L" = "$M" ] && [ "$M" = "$W" ]; then
  say "✅ 3つとも一致"
else
  say "❌ 不一致。デプロイ待ちか、index.html の同期漏れ（cp game/my_hero.html index.html）"
  FAIL=1
fi
rm -f "$TMP"

say ""
if [ "$FAIL" = "0" ]; then
  say "🟢 渡してよい。地の文でこのURLを貼ること（コードブロックに入れない＝§9-9）:"
  say ""
  say "https://98rcsk-creator.github.io/myhero/index.html?test=1&t=$(date +%m%d%H%M)"
else
  say "🔴 まだ渡すな。上の❌を直してから再実行する"
fi
exit $FAIL
