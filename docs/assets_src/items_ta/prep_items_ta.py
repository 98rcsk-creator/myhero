# 番外編のごほうび（紅白の剣・金メダルの盾）の元の絵を、ゲームに埋め込む形に整える
#   使い方: python3 docs/assets_src/items_ta/prep_items_ta.py 出力フォルダ
#   やり方は items_v341/prep_v341.py と同じ（背景＝ふちからつながる明るい無彩色を消す・白と混ざったふち2pxは白を引いて色を戻す）
#   - 剣: 元の絵の刃は全体の63%で、今の剣（刃を1.45倍に伸ばしたあと 約64%）と同じくらい → 伸ばさない
#         高さ 372px（今の剣 370〜380px）。握る所・刃の下のはしは prep_v341.py と同じ決め方
#   - 盾: 高さ 192px（今の盾と同じ）
import sys, os, json
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)

def cut_bg(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    mx = a.max(axis=2); mn = a.min(axis=2)
    cand = (mn >= 236) & (mx - mn <= 14)
    bg = np.zeros(cand.shape, bool); bg[0, :] = cand[0, :]; bg[-1, :] = cand[-1, :]; bg[:, 0] = cand[:, 0]; bg[:, -1] = cand[:, -1]
    while True:
        nb = bg.copy(); nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]
        nb &= cand
        if (nb == bg).all(): break
        bg = nb
    fg = ~bg; near = bg.copy()
    for _ in range(2):
        n2 = near.copy(); n2[1:] |= near[:-1]; n2[:-1] |= near[1:]; n2[:, 1:] |= near[:, :-1]; n2[:, :-1] |= near[:, 1:]; near = n2
    edge = fg & near
    alpha = np.where(fg, 1.0, 0.0); w = np.clip((mn - 200) / 50, 0, 1); alpha[edge] = 1 - w[edge]
    rgb = a.copy(); al = np.maximum(alpha, 1e-3)[..., None]
    rgb[edge] = np.clip((a[edge] - (1 - alpha[edge])[:, None] * 255) / al[edge], 0, 255)
    out = np.dstack([rgb, alpha * 255]).round().astype(np.uint8); out[alpha <= 0.02] = 0
    return out

def crop(arr, pad=4):
    ys, xs = np.where(arr[:, :, 3] > 0)
    return arr[max(0, ys.min() - pad):ys.max() + 1 + pad, max(0, xs.min() - pad):xs.max() + 1 + pad]

def grip(a, ymin=0):   # prep_v341.py と同じ
    w = (a > 128).sum(axis=1); ys = np.where(w > 0)[0]; y0, y1 = ys.min(), ys.max(); mw = w.max()
    narrow = (w > 0) & (w < 0.4 * mw); narrow[:max(ymin, y0 + int((y1 - y0) * 0.4))] = False
    best = (0, 0, 0); s = None
    for y in range(len(w) + 1):
        v = narrow[y] if y < len(w) else False
        if v and s is None: s = y
        if not v and s is not None:
            if y - s > best[0]: best = (y - s, s, y)
            s = None
    _, r0, r1 = best; m = np.median(w[r0:r0 + (r1 - r0) // 2])
    g0 = r0
    while g0 < r1 and w[g0] > m * 1.1: g0 += 1
    g1 = g0
    while g1 < r1 and w[g1] <= m * 1.1: g1 += 1
    xs = np.where((a[g0:g1] > 128).any(axis=0))[0]
    return (xs.min() + xs.max() + 1) / 2, (g0 + g1) / 2

def blade_bottom(al):   # prep_v341.py の stretch_blade と同じ決め方（下55%でいちばん幅の広い行＝鍔から上へ、幅が55%を切るまで）
    w = (al > 128).sum(axis=1); ys = np.where(w > 0)[0]; top, bot = ys.min(), ys.max()
    lo = top + int((bot - top) * 0.45); g = lo + int(np.argmax(w[lo:])); bb = g
    while bb > top and w[bb - 1] > 0.55 * w[g]: bb -= 1
    return int(top), int(bb)

def save(arr, path, TH):
    h, w = arr.shape[:2]; im = Image.fromarray(arr, 'RGBA').resize((round(w * TH / h), TH), Image.LANCZOS)
    im.save(path, 'WEBP', quality=88, method=6); return np.asarray(im)

meta = {}
a = save(crop(cut_bg(os.path.join(D, 'sword_kohaku_src.png'))), f'{OUT}/sword_kohaku.webp', 372)
top, bb = blade_bottom(a[:, :, 3]); gx, gy = grip(a[:, :, 3], bb)
meta['sword'] = {'w': int(a.shape[1]), 'h': 372, 'gripX': round(gx, 1), 'gripY': round(gy, 1), 'top': top, 'blade': bb, 'webp': os.path.getsize(f'{OUT}/sword_kohaku.webp')}
s = save(crop(cut_bg(os.path.join(D, 'shield_medal_src.png'))), f'{OUT}/shield_medal.webp', 192)
meta['shield'] = {'w': int(s.shape[1]), 'h': 192, 'webp': os.path.getsize(f'{OUT}/shield_medal.webp')}
json.dump(meta, open(f'{OUT}/meta.json', 'w'), indent=1); print(json.dumps(meta))
