# 表彰台の「前向きの よろこびポーズ（f_win）」を ChatGPT に たのむときの 見本を作る（★試作27）
#   使い方: /usr/bin/python3 docs/assets_src/ta3d_chars/make_fwin_ref.py 出力フォルダ
#   男の子4人・女の子4人で 1枚ずつ。それぞれ 前向きに走る絵（向き8体の「前」＝f_run0 の元の絵）を 左から ならべる。
#   背景は 明るい緑（#00FF00）。文字は入れない（AI が絵に文字を描きこまないように）。
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep_char as P
W, H, GREEN = 1536, 1024, (0, 255, 0)
GROUPS = [('men', ['men_0', 'men_1', 'men_2', 'men_3']), ('women', ['women_0', 'women_1', 'women_2', 'women_3'])]
def front(cid):   # 向き8体の 上の段 いちばん右（前・走る1）
    G = cid in P.GREEN_CHARS
    if cid == 'men_0':
        A = P.keyimg(Image.open(os.path.join(P.ROOT, 'docs', 'assets_src', 'ta3d_rubert', 'dirs_src.png')), G)
    else:
        A = P.keyimg(P.quads(Image.open(os.path.join(P.D, cid, 'all4_src.png')))['BL'], G)
    return Image.fromarray(P.figures(A, [4, 4], G)[0][3], 'RGBA')
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for gname, ids in GROUPS:
    c = Image.new('RGBA', (W, H), GREEN + (255,)); cw = W // len(ids)
    for i, cid in enumerate(ids):
        f = front(cid); k = 900.0 / f.height
        if f.width * k > cw - 40: k = (cw - 40) / f.width
        f = f.resize((round(f.width * k), round(f.height * k)), Image.LANCZOS)
        c.alpha_composite(f, (i * cw + (cw - f.width) // 2, H - 50 - f.height))
    p = os.path.join(out, 'fwin_ref_%s.png' % gname); c.convert('RGB').save(p, optimize=True); print(p, os.path.getsize(p))
