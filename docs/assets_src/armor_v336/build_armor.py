# v336 鎧4種（黄金の鎧・漆黒の鎧・王者のローブ・ヒーロースーツ）の絵を、ゲームに埋め込む形に整える
#   元の絵: armor4_src.png（ユーザーが ChatGPT で作った 1254x1254・透明背景・2x2 に4体）
#   使い方: python3 docs/assets_src/armor_v336/build_armor.py docs/assets_src/armor_v336/armor4_src.png 出力フォルダ
#   出力: <id>.webp（体の絵と同じ 357x360 にそろえた絵）、<id>_tmap.png（ラインの色を変える所の重み 0〜255）、armor.json（基準の明るさ・切り分け線・手の位置）
#
#   そろえ方: 首の上端→y=2、足の裏→y=355.6、首の真ん中→x=178.5（白い体 BODY_SPR と同じ所）。縦横同じ倍率（形を変えない）
#   ラインの色（ユーザー指定 2026-11-03）:「胸・肩・腰の白いライン」を1色でまとめて変える。ローブだけは白い毛皮を全部
#     白さ＝彩度が低く明るい所（ふちはなめらかに重みを落とす）。首（肌）とクリーム色（ローブの真ん中の布）は入れない
#   切り分け線（ゲーム中に腕と脚を回すため）: 白い体（v334 の NB_RIG）と同じ考え方で、絵ごとにすき間を測って引く
#     腕＝拳と胴のすき間の真ん中、脚＝左右の脚が分かれる所から下。ローブは裾が両脚をまたぐので、脚は裾の下（靴）だけ
#     出力の前に「腕と脚の重なり0・取りこぼし0・腰より下が胴に残らない」を全画素で確かめる（だめなら止まる）
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
BW, BH, NECK_TOP, SOLE, CX = 357, 360, 2, 355.6, 178.5
IDS = {'gold': (0, 600, 0, 627), 'darkarmor': (0, 600, 627, 1254), 'royal': (600, 1254, 0, 627), 'herosuit': (600, 1254, 627, 1254)}
ALL_WHITE = {'royal'}   # 白を全部変える（毛皮のふちが途中で色が切り替わらないように）
# 胸・肩・腰（腕・脚・ブーツは外す）。拳がなくなる y205 から下は腰のふちまで横に広げる。下は y248（漆黒の膝の銀の輪 y256〜 を入れない）
ZONE = [(0, 0), (357, 0), (357, 135), (268, 135), (268, 205), (287, 205), (287, 248), (70, 248), (70, 205), (89, 205), (89, 135), (0, 135)]

def clean(arr):
    # 透明な所の色のゴミ（α1〜15）を消し、ふちのα16〜239を0〜255に引き伸ばす（v327・v328 と同じ）
    a = arr[:, :, 3].astype(float); na = np.clip((a - 16) / (240 - 16) * 255, 0, 255)
    out = arr.copy(); out[:, :, 3] = na.astype(np.uint8); out[na == 0] = 0; return out

def whiteness(a):
    r, g, b, al = [a[:, :, i].astype(float) for i in range(4)]
    mx = np.maximum(np.maximum(r, g), b) / 255; mn = np.minimum(np.minimum(r, g), b) / 255
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # 白い毛皮・ラインは彩度0.07前後、ローブの真ん中のクリーム色の布は0.14 → 0.09までを白、0.12からは入れない
    return np.clip((0.12 - s) / 0.03, 0, 1) * np.clip((mx - 0.62) / 0.12, 0, 1) * (al / 255)

def big_only(w, minpx=60):
    # 金属のつや（白く光る小さな点）は外す：白いかたまりのうち minpx 画素より小さいものを消す。ふちのなめらかさは残す
    B = w > 0.5; H, W_ = B.shape; lab = np.zeros(B.shape, np.int32); keep = np.zeros(B.shape, bool); n = 0
    for y in range(H):
        for x in range(W_):
            if B[y, x] and not lab[y, x]:
                n += 1; st = [(y, x)]; lab[y, x] = n; pts = []
                while st:
                    cy, cx = st.pop(); pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W_ and B[ny, nx] and not lab[ny, nx]: lab[ny, nx] = n; st.append((ny, nx))
                if len(pts) >= minpx:
                    for cy, cx in pts: keep[cy, cx] = True
    k = keep.copy()
    for _ in range(3):   # 3px ふくらませて、残したかたまりのふち（重み0.5未満）も残す
        k = k | np.roll(k, 1, 0) | np.roll(k, -1, 0) | np.roll(k, 1, 1) | np.roll(k, -1, 1)
    return w * k

def segs(row):
    r = np.nonzero(row)[0]
    if not len(r): return []
    out = []; st = r[0]; pv = r[0]
    for x in r[1:]:
        if x != pv + 1: out.append((int(st), int(pv))); st = x
        pv = x
    out.append((int(st), int(pv))); return out

def mask(polys):
    im = Image.new('L', (BW, BH), 0); d = ImageDraw.Draw(im)
    for pts in polys: d.polygon([tuple(p) for p in pts], fill=255)
    return np.array(im) > 0

def rig_for(A, robe):
    # 腕：胴から離れている行（左右とも別のかたまり）でのすき間の真ん中
    arm = {}
    for y in range(100, 240):
        sg = [s for s in segs(A[y]) if s[1] - s[0] >= 2]
        if len(sg) >= 3 and sg[0][1] < 120 and sg[-1][0] > 237:
            arm[y] = ((sg[0][1] + sg[1][0]) / 2, (sg[-2][1] + sg[-1][0]) / 2)
    # すき間がつづく一番長い区間を使う（肩のトゲなどで一瞬だけ3つに分かれる行は外す）
    best = (0, 0, 0); st = None
    for y in range(100, 241):
        if y in arm and st is None: st = y
        if y not in arm and st is not None:
            if y - st > best[0]: best = (y - st, st, y - 1)
            st = None
    _, y0, y1 = best
    assert y1 - y0 > 40, '腕のすき間が短すぎる'
    top = y0 - 10; bot = y1 + 6
    grid = list(range(y0, y1, 4)) + [y1]   # すき間の真ん中を4行ごとに取って折れ線にする（腕と胴を抜く所が同じ線をたどる）
    def bx(y, i):  # 折れ線の上の x（すき間より上は、すき間の一番上より4px外＝肩のふくらみ）
        if y < y0: return arm[y0][i] + (4 if i == 0 else -4)
        if y >= y1: return arm[y1][i]
        for a_, b_ in zip(grid, grid[1:]):
            if a_ <= y <= b_: return arm[a_][i] + (arm[b_][i] - arm[a_][i]) * (y - a_) / (b_ - a_)
    def side(yfrom, i, edge):  # 腕の多角形：上は yfrom、折れ線に沿って拳の下まで（上へ戻る点を入れない＝形がねじれない）
        pts = [(edge, yfrom), (bx(yfrom, i), yfrom)] + [(bx(y, i), y) for y in grid if y > yfrom] + [(bx(y1, i), bot), (edge, bot)]
        return [[round(x, 2), y] for x, y in pts]
    def left(yfrom): return side(yfrom, 0, 0)
    def right(yfrom): return side(yfrom, 1, BW)
    # 脚：左右の脚が分かれる最初の行（真ん中付近に2つのかたまり）
    sep = None
    for y in range(bot, 352):
        sg = [s for s in segs(A[y]) if s[1] - s[0] >= 20 and s[0] > 40 and s[1] < 317]
        if len(sg) == 2 and sg[0][1] < CX + 12 and sg[1][0] > CX - 12: sep = y; break
    assert sep, '脚が分かれる所が見つからない'
    sg = [s for s in segs(A[sep + 2]) if s[1] - s[0] >= 20 and s[0] > 40 and s[1] < 317]
    mid = (sg[0][1] + sg[1][0]) / 2
    legTop = sep - 10
    xl = max(arm[y1][0], 30) if legTop <= bot else 30   # 腕の多角形と重ならない左端
    xr = min(arm[y1][1], 327) if legTop <= bot else 327
    def legL(yfrom):
        if yfrom < bot: return [[xl, yfrom], [mid, yfrom], [mid, BH], [30, BH], [30, bot], [xl, bot]]
        return [[30, yfrom], [mid, yfrom], [mid, BH], [30, BH]]
    def legR(yfrom):
        if yfrom < bot: return [[mid, yfrom], [xr, yfrom], [xr, bot], [327, bot], [327, BH], [mid, BH]]
        return [[mid, yfrom], [327, yfrom], [327, BH], [mid, BH]]
    rig = {'armL': left(top), 'armR': right(top), 'cutArmL': left(y0 + 6), 'cutArmR': right(y0 + 6),
           'legL': legL(legTop), 'legR': legR(legTop), 'cutLeg': None,
           'piv': {'al': [100, 112], 'ar': [257, 112], 'll': [round((sg[0][0] + sg[0][1]) / 2), legTop], 'lr': [round((sg[1][0] + sg[1][1]) / 2), legTop]},
           'legK': 0.6 if robe else 1}
    cl = legL(legTop + 10); cr = legR(legTop + 10)
    rig['cutLeg'] = [cl, cr]
    # 手（拳）の真ん中：腕の多角形の中の、拳の下端から40px上まで
    mL = mask([rig['armL']]) & A; mR = mask([rig['armR']]) & A
    yy = np.arange(BH)[:, None] * np.ones((1, BW)); xx = np.ones((BH, 1)) * np.arange(BW)[None, :]
    for nm, m in (('handL', mL), ('handR', mR)):
        f = m & (yy >= y1 - 40)
        rig[nm] = [round(float(xx[f].mean()), 1), round(float(yy[f].mean()), 1)]
    rig['_meta'] = {'armGap': [y0, y1], 'legSep': sep}
    return rig

def check(A, rig):
    armL, armR, legL, legR = [mask([rig[k]]) for k in ('armL', 'armR', 'legL', 'legR')]
    cut = mask([rig['cutArmL'], rig['cutArmR']] + rig['cutLeg']); torso = A & ~cut
    cover = (torso | (armL & A) | (armR & A) | (legL & A) | (legR & A))
    yy = np.arange(BH)[:, None]
    hip = rig['piv']['ll'][1] + 10
    return {'取りこぼし': int((A & ~cover).sum()), '腕と脚の重なり': int(((armL | armR) & (legL | legR) & A).sum()),
            '左右の腕の重なり': int((armL & armR & A).sum()), '胴の腰より下': int((torso & (yy >= hip) & ~(yy < 0)).sum())}

src = clean(np.array(Image.open(SRC).convert('RGBA')))
meta = {}
for k, (y0, y1, x0, x1) in IDS.items():
    sub = src[y0:y1, x0:x1]; ys, xs = np.nonzero(sub[:, :, 3] > 40)
    fig = sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; al = fig[:, :, 3] > 40
    yy, xx = np.nonzero(al); top = yy.min(); sole = yy.max() + 0.5
    r = np.nonzero(al[top + 2])[0]; ncx = (r.min() + r.max()) / 2
    s = (SOLE - NECK_TOP) / (sole - top)
    W = round(fig.shape[1] * s); H = round(fig.shape[0] * s); ox = round(CX - ncx * s); oy = round(NECK_TOP - top * s)
    im = Image.fromarray(fig, 'RGBA').resize((W, H), Image.LANCZOS)
    cv = Image.new('RGBA', (BW, BH), (0, 0, 0, 0)); cv.paste(im, (ox, oy), im)
    # ラインの重み：大きい絵で白さを測ってから同じ倍率で縮める
    wm = Image.fromarray((whiteness(fig) * 255).astype(np.uint8), 'L').resize((W, H), Image.LANCZOS)
    wc = Image.new('L', (BW, BH), 0); wc.paste(wm, (ox, oy))
    w = np.array(wc).astype(float) / 255
    A = np.array(cv)[:, :, 3] > 40
    neck = 0
    while neck < BH and (not A[neck].any() or np.ptp(np.nonzero(A[neck])[0]) < 75): neck += 1
    w[:neck + 2] = 0   # 首（肌）は入れない
    if k not in ALL_WHITE: w *= mask([ZONE])
    w = big_only(w)
    a = np.array(cv).astype(float); L = 0.3 * a[:, :, 0] + 0.59 * a[:, :, 1] + 0.11 * a[:, :, 2]
    ref = float(np.percentile(L[w > 0.9], 70))
    cv.save(os.path.join(OUT, k + '.webp'), 'WEBP', quality=82, method=6)
    Image.fromarray((np.round(w * 15) * 17).astype(np.uint8), 'L').save(os.path.join(OUT, k + '_tmap.png'), optimize=True)   # 16段（ファイルが半分。ふちの段差は見えない）
    cv.save(os.path.join(OUT, k + '_aligned.png'))
    rig = rig_for(A, k == 'royal'); chk = check(A, rig)
    print(k, '倍率', round(s, 4), '首', neck, '基準の明るさ', round(ref, 1), 'ラインの画素', int((w > 0.5).sum()), rig['_meta'], '手', rig['handL'], rig['handR'], chk)
    assert chk['取りこぼし'] == 0 and chk['腕と脚の重なり'] == 0 and chk['左右の腕の重なり'] == 0 and chk['胴の腰より下'] == 0, k + ' の切り分けに問題'
    del rig['_meta']
    meta[k] = {'ref': round(ref, 1), 'rig': rig}
json.dump(meta, open(os.path.join(OUT, 'armor.json'), 'w'), ensure_ascii=False)
print('ok')
