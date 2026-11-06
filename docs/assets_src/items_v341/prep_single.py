# v343 雷の盾・闇の盾の単品の絵（ユーザーが ChatGPT で描き直した 1254x1254）を、ゲームに埋め込む形に整える
#   使い方: python3 docs/assets_src/items_v341/prep_single.py shield_thunder_single.png shield_dark_single.png 出力フォルダ
#   - 背景は透明でなく、市松模様（灰色233〜237と白254の2段・マス22〜26px）が描き込まれている
#   - マス目の周期とずれを左上の行・列から測り、各画素に「その場所にあるはずの背景の色」を出す。
#     無彩色でその色に近い所（マス目の境目の近くはどちらの段でもよい）を、ふちからつながる分だけ背景として消す
#     （闇の盾の銀のトゲは明るい灰色だが、その場所の市松の色とたまたま一致する所はわずかで、ふちからつながらない）
#   - 絵のふちの1pxは背景と混ざっているので削る（高さ192pxに縮めると1px未満になり、ふちは自然にぼける）
#   - 高さ192px（今の盾と同じ）の WebP。v342 の1枚絵からの切り出し（闇の盾はトゲがとなりとくっついていた）の代わり
import sys, os, json
import numpy as np
from PIL import Image

def grid(line):
    # 背景だけの行（列）でマスの切り替わりを全部拾い、番号と位置を直線で当てはめる（周期の小数まで出す。四捨五入すると端で数pxずれる）
    d = line < 245; t = np.array([i for i in range(1, len(d)) if d[i] != d[i - 1]], float)
    n = np.round((t - t[0]) / np.median(np.diff(t)))
    P, o = np.polyfit(n, t, 1)
    return float(P), float(o % P)

def cut_loose(path):
    # 雷の盾用：ふちに無彩色の明るい色が無いので、「無彩色で明るい（200以上）所」をふちからつながる分だけ全部消す
    #   （盾の下にうすい影があり、マス目の色と合わずに残った＝マス目方式では消し切れなかった）
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    v = a.min(axis=2); sat = a.max(axis=2) - v
    cand = (sat <= 10) & (v >= 200)
    bg = np.zeros(cand.shape, bool); bg[0, :] = cand[0, :]; bg[-1, :] = cand[-1, :]; bg[:, 0] = cand[:, 0]; bg[:, -1] = cand[:, -1]
    while True:
        nb = bg.copy(); nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]
        nb &= cand
        if (nb == bg).all(): break
        bg = nb
    nb = bg.copy(); nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]; bg = nb
    out = np.dstack([a, np.where(bg, 0, 255)]).astype(np.uint8); out[bg] = 0
    return out, 'loose'

def cut_checker(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    v = a.min(axis=2); sat = a.max(axis=2) - v
    Px, ox = grid(v[6, :]); Py, oy = grid(v[:, 6])   # いちばん上の行・左の列は全部背景
    H, W = v.shape; yy, xx = np.mgrid[0:H, 0:W]
    k = (np.floor((xx - ox) / Px) + np.floor((yy - oy) / Py)).astype(int) & 1
    # k=0 / k=1 のマスの色（左上の行で測る）
    k0 = np.median(v[0:200, 0:200][k[0:200, 0:200] == 0]); k1 = np.median(v[0:200, 0:200][k[0:200, 0:200] == 1])
    exp = np.where(k == 0, k0, k1)
    dx = np.minimum((xx - ox) % Px, Px - (xx - ox) % Px); dy = np.minimum((yy - oy) % Py, Py - (yy - oy) % Py)
    edge = (dx < 1.6) | (dy < 1.6)
    lo, hi = min(k0, k1), max(k0, k1)
    cand = (sat <= 8) & ((np.abs(v - exp) <= 10) | (edge & (v >= lo - 10)))
    bg = np.zeros(cand.shape, bool); bg[0, :] = cand[0, :]; bg[-1, :] = cand[-1, :]; bg[:, 0] = cand[:, 0]; bg[:, -1] = cand[:, -1]
    while True:
        nb = bg.copy(); nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]
        nb &= cand
        if (nb == bg).all(): break
        bg = nb
    nb = bg.copy(); nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]; bg = nb   # 絵のふちの混ざった1px
    out = np.dstack([a, np.where(bg, 0, 255)]).astype(np.uint8); out[bg] = 0
    return out, (round(Px, 3), round(ox, 2), round(Py, 3), round(oy, 2), float(k0), float(k1))

def crop(arr, pad=4):
    ys, xs = np.where(arr[:, :, 3] > 0)
    return arr[max(0, ys.min() - pad):ys.max() + 1 + pad, max(0, xs.min() - pad):xs.max() + 1 + pad]

OUT = sys.argv[3]; os.makedirs(OUT, exist_ok=True); meta = {}
for path, name in ((sys.argv[1], 'star'), (sys.argv[2], 'heart')):
    arr, lv = (cut_loose if name == 'star' else cut_checker)(path); c = crop(arr); h, w = c.shape[:2]
    im = Image.fromarray(c, 'RGBA').resize((round(w * 192 / h), 192), Image.LANCZOS)
    im.save(f'{OUT}/shield_{name}.webp', 'WEBP', quality=88, method=6)
    meta[name] = {'checker': lv, 'crop': [w, h], 'size': list(im.size), 'webp': os.path.getsize(f'{OUT}/shield_{name}.webp')}
print(json.dumps(meta, ensure_ascii=False))
