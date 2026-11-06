# v341・v342 剣5本（刃を長くした描き直し）と盾3つ（炎・雷・闇）の絵を、ゲームに埋め込む形に整える
#   元の絵: swords5.png（2172x724）・shields5.jpg（1170x542。左から 銀・炎・雷・闇・ヒーロー の5つ。銀とヒーローは今の絵のまま使う）
#   使い方: python3 docs/assets_src/items_v341/prep_v341.py swords5.png shields5.jpg 出力フォルダ
#   - どちらも背景が透明ではなく、白にうっすら市松模様（247〜255）。ふちから「明るい無彩色」がつながっている所を背景として消す
#     （絵の中の白い所はふちとつながっていないので消えない）
#   - 絵のふち2pxは白と混ざっているので、白を引いて色を戻し（アンブレンド）、白さに応じて透けさせる＝白いフチが残らない
#   - 剣: 高さ300px（今と同じ）の WebP。握る所は prep_swords.py と同じ決め方（鍔の下で幅がほぼ一定の帯の真ん中）
#   - 盾: 高さ192px（今の盾と同じ）の WebP
import sys, os, json
import numpy as np
from PIL import Image

SW, SH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

def cut_bg(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    mx = a.max(axis=2); mn = a.min(axis=2)
    cand = (mn >= 236) & (mx - mn <= 14)                      # 背景らしい色（明るい無彩色）
    bg = np.zeros(cand.shape, bool); bg[0, :] = cand[0, :]; bg[-1, :] = cand[-1, :]; bg[:, 0] = cand[:, 0]; bg[:, -1] = cand[:, -1]
    while True:                                                # ふちからつながっている所だけ広げる
        nb = bg.copy(); nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]
        nb &= cand
        if (nb == bg).all(): break
        bg = nb
    fg = ~bg
    near = bg.copy()                                           # 背景から2px以内の絵＝白と混ざったふち
    for _ in range(2):
        n2 = near.copy(); n2[1:] |= near[:-1]; n2[:-1] |= near[1:]; n2[:, 1:] |= near[:, :-1]; n2[:, :-1] |= near[:, 1:]; near = n2
    edge = fg & near
    alpha = np.where(fg, 1.0, 0.0)
    w = np.clip((mn - 200) / 50, 0, 1)                         # 白さ（200以下は絵、250で背景）
    alpha[edge] = 1 - w[edge]
    rgb = a.copy()
    al = np.maximum(alpha, 1e-3)[..., None]
    rgb[edge] = np.clip((a[edge] - (1 - alpha[edge])[:, None] * 255) / al[edge], 0, 255)   # 白を引いて元の色へ
    out = np.dstack([rgb, alpha * 255]).round().astype(np.uint8); out[alpha <= 0.02] = 0
    return out

def runs(arr, minw):
    col = (arr[:, :, 3] > 128).sum(axis=0) > 0; r = []; s = None
    for x, v in enumerate(list(col) + [False]):
        if v and s is None: s = x
        if not v and s is not None:
            if x - s > minw: r.append((s, x))
            s = None
    return r

def main_only(arr):
    # いちばん大きいかたまりだけ残す（切った列の向こう側の、となりの盾のふちが細く残るのを消す）
    m = arr[:, :, 3] > 20; H_, W_ = m.shape; lab = np.zeros(m.shape, np.int32); best = (0, 0); n = 0
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]: continue
        n += 1; st = [(y0, x0)]; lab[y0, x0] = n; k = 0
        while st:
            y, x = st.pop(); k += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H_ and 0 <= xx < W_ and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = n; st.append((yy, xx))
        if k > best[0]: best = (k, n)
    keep = lab == best[1]
    for _ in range(2):   # ふちのうすい所（α20以下）も残すため2pxふくらませる
        keep = keep | np.roll(keep, 1, 0) | np.roll(keep, -1, 0) | np.roll(keep, 1, 1) | np.roll(keep, -1, 1)
    o = arr.copy(); o[~keep] = 0; return o

def crop(arr, pad=4):
    ys, xs = np.where(arr[:, :, 3] > 0)
    return arr[max(0, ys.min() - pad):ys.max() + 1 + pad, max(0, xs.min() - pad):xs.max() + 1 + pad]

def grip(a):   # prep_swords.py と同じ
    w = (a > 128).sum(axis=1); ys = np.where(w > 0)[0]; y0, y1 = ys.min(), ys.max(); mw = w.max()
    narrow = (w > 0) & (w < 0.4 * mw); narrow[:y0 + int((y1 - y0) * 0.4)] = False
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

def save(arr, path, TH):
    h, w = arr.shape[:2]; im = Image.fromarray(arr, 'RGBA').resize((round(w * TH / h), TH), Image.LANCZOS)
    im.save(path, 'WEBP', quality=88, method=6); return np.asarray(im)

meta = {'sword': {}, 'shield': {}}
S = cut_bg(SW); r = runs(S, 30); assert len(r) == 5, r
for name, (x0, x1) in zip(['silver', 'flame', 'thunder', 'dark', 'herosword'], r):
    a2 = save(crop(main_only(S[:, max(0, x0 - 6):x1 + 6])), f'{OUT}/sword_{name}.webp', 300)
    gx, gy = grip(a2[:, :, 3]); ys = np.where((a2[:, :, 3] > 40).any(axis=1))[0]
    meta['sword'][name] = {'w': int(a2.shape[1]), 'h': 300, 'gripX': round(gx, 1), 'gripY': round(gy, 1), 'top': int(ys.min()), 'webp': os.path.getsize(f'{OUT}/sword_{name}.webp')}
H = cut_bg(SH); r = runs(H, 50); print('盾のかたまり', r)
# 雷と闇、闇とヒーローは、闇のトゲの先が y217〜261 で数pxくっついている → くっついた列の中で絵がいちばん少ない列で切る
cnt = (H[:, :, 3] > 128).sum(axis=0); rr = []
for x0, x1 in r:
    if x1 - x0 < 320: rr.append((x0, x1)); continue
    cuts = []; xs = x0
    while x1 - xs > 320:
        lo, hi = xs + 180, xs + 260
        c = lo + int(np.argmin(cnt[lo:hi])); cuts.append(c); rr.append((xs, c)); xs = c + 1
    rr.append((xs, x1)); print('  切った列', cuts)
r = rr
assert len(r) == 5, r
def only(arr, x0, x1):   # 切った列より外の絵（となりの盾）を消す
    o = arr.copy(); o[:, :x0] = 0; o[:, x1:] = 0; return o
for name, (x0, x1) in zip(['_silver', 'fireshield', 'star', 'heart', '_hero'], r):
    if name.startswith('_'): continue   # 銀・ヒーローは今の絵のまま
    c = crop(main_only(only(H, x0, x1)[:, max(0, x0 - 6):x1 + 6]))
    if name == 'heart':   # 闇の盾は金色を使っていない。左右のふち12pxに残った金色＝となりの雷・ヒーローのふち（トゲとくっついていた所）を消す
        r_, g_, b_ = [c[:, :, i].astype(int) for i in range(3)]
        gold = (r_ > 140) & (g_ > 100) & (b_ < 120) & (r_ - b_ > 60); side = np.zeros(gold.shape, bool); side[:, :12] = True; side[:, -12:] = True
        c = c.copy(); c[gold & side] = 0; print('  闇の盾のふちから消した金色', int((gold & side).sum()), 'px')
    save(c, f'{OUT}/shield_{name}.webp', 192)
    meta['shield'][name] = {'webp': os.path.getsize(f'{OUT}/shield_{name}.webp')}
json.dump(meta, open(f'{OUT}/meta.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False))
