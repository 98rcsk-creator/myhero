#!/bin/sh
# 実機確認リンクを渡す前に必ず実行する（CLAUDE.md §9-10）。
# 記憶に頼らず、この1本で「渡してよい状態か」を機械判定する。
#
# 使い方:
#   sh tools/relink.sh                      … 本番（index.html）を検査
#   sh tools/relink.sh test/mh_v304.html    … テスト用の別ページを検査
#
# ★v304b テスト用URLを渡す運用を足したので、引数で対象を切り替えられるようにした。
#   以前は本番URLしか見ていなかったため、テスト用URLを渡したときに
#   「デプロイがまだ404」を素通りさせてユーザーに404を踏ませた。
set -u
PAGE=${1:-index.html}
FAIL=0
say(){ printf '%s\n' "$*"; }

git fetch origin main -q 2>/dev/null

say "=== 対象: $PAGE ==="
say ""
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
say "=== ② 公開ページが実際に生きているか（HTTP）==="
URL="https://98rcsk-creator.github.io/myhero/$PAGE"
CODE=$(curl -s -o /dev/null -w '%{http_code}' "$URL?cb=$$")
say "HTTP $CODE  $URL"
if [ "$CODE" != "200" ]; then
  say "❌ 200以外。GitHub Pages のデプロイがまだ終わっていない可能性が高い（少し待って再実行）"
  FAIL=1
else
  say "✅ 200"
fi

say ""
say "=== ③ 公開ページ = main = 手元 のバイト照合 ==="
TMP=$(mktemp)
curl -s "$URL?cb=$$" -o "$TMP"
L=$(wc -c < "$TMP")
M=$(git show "origin/main:$PAGE" 2>/dev/null | wc -c)
W=$(wc -c < "$PAGE" 2>/dev/null || echo 0)
say "公開 $L / main $M / 手元 $W"
if [ "$CODE" = "200" ] && [ "$L" = "$M" ] && [ "$M" = "$W" ]; then
  say "✅ 3つとも一致"
else
  say "❌ 不一致。デプロイ待ちか、同期漏れ（本番なら cp game/my_hero.html index.html）"
  FAIL=1
fi
rm -f "$TMP"

say ""
if [ "$FAIL" = "0" ]; then
  say "🟢 渡してよい。地の文でこのURLを貼ること（コードブロックに入れない＝§9-9）:"
  say ""
  say "$URL?test=1&t=$(date +%m%d%H%M)"
else
  say "🔴 まだ渡すな。上の❌を直してから再実行する"
fi
exit $FAIL
