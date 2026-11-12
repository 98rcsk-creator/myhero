# 音楽エンジンと曲（MUS）を、試聴ページから本体へ写す（v349〜）
#   正本は test/bgm_home.html の「// ==== MUS:BEGIN」〜「// ==== MUS:END ====」。曲づくりは試聴ページで行い、本体側の同じ範囲を直接直さない。
#   使い方:
#     python3 tools/sync_music.py          … 試聴ページ → game/my_hero.html に写す（index.html はリリース時に別途コピー）
#     python3 tools/sync_music.py --check  … 写さずに、2つが同じかだけ確かめる（違えば終了コード1）
import sys

SRC, DST = 'test/bgm_home.html', 'game/my_hero.html'
BEGIN, END = '// ==== MUS:BEGIN', '// ==== MUS:END ====\n'


def block(text, name):
    assert text.count(BEGIN) == 1 and text.count(END) == 1, f'{name}: MUS の目印がちょうど1つずつではない'
    i = text.index(BEGIN)
    i = text.rindex('\n', 0, i) + 1          # 目印の行の頭から
    j = text.index(END) + len(END)
    return i, j


src = open(SRC, encoding='utf-8').read()
dst = open(DST, encoding='utf-8').read()
si, sj = block(src, SRC)
di, dj = block(dst, DST)
new = src[si:sj]
same = (dst[di:dj] == new)
if '--check' in sys.argv:
    print('✅ 同じ' if same else '❌ 違う（python3 tools/sync_music.py で写す）')
    sys.exit(0 if same else 1)
if same:
    print('変化なし')
else:
    out = dst[:di] + new + dst[dj:]
    open(DST, 'w', encoding='utf-8').write(out)
    print(f'写した: {len(dst[di:dj])} → {len(new)} 文字（{DST} {len(dst.encode())} → {len(out.encode())} バイト）')
