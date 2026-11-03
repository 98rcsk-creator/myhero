# v327 盾4種とヒーローソードの絵を、ゲームに埋め込む形に整える
#   - 透明な所に残っているゴミ（α1〜15）を消し、ふちのα16〜239を0〜255に引き伸ばす（元の最大αが250前後で全体が2%透けていた）
#   - 盾は1枚の絵から4つに切り分ける（不透明な列のかたまりごと）
#   - まるガード（ノーマル盾）は「グレーの金属（ふち・鋲）」の地図を作る（マイヒーローの「たて」の色で塗るため）
#   - 縮小して WebP に
#   使い方: python3 docs/assets_src/items_v327/prep_items.py shields.png herosword.png 出力フォルダ（できた WebP・PNG・meta.json を game/my_hero.html の ITEM_SPR に埋め込む）
import sys, os, io, json, base64
from collections import deque
import numpy as np
from PIL import Image

SH=sys.argv[1]; SW=sys.argv[2]; OUT=sys.argv[3]
os.makedirs(OUT,exist_ok=True)

def clean(arr):
    a=arr[:,:,3].astype(float)
    na=np.clip((a-16)/(240-16)*255,0,255)
    out=arr.copy(); out[:,:,3]=na.astype(np.uint8); out[na==0]=0
    return out

def crop(arr,pad=4):
    ys,xs=np.where(arr[:,:,3]>0); y0,y1=max(0,ys.min()-pad),min(arr.shape[0],ys.max()+1+pad); x0,x1=max(0,xs.min()-pad),min(arr.shape[1],xs.max()+1+pad)
    return arr[y0:y1,x0:x1],(x0,y0)

def webp(arr,path,q=88):
    im=Image.fromarray(arr,'RGBA'); im.save(path,'WEBP',quality=q,method=6); return os.path.getsize(path)

meta={}
# ── 盾 ──
Hs=np.asarray(Image.open(SH).convert('RGBA'))
a=Hs[:,:,3]; col=((a>128).sum(axis=0))>0
runs=[]; s=None
for x,v in enumerate(col):
    if v and s is None: s=x
    if not v and s is not None:
        if x-s>50: runs.append((s,x))
        s=None
if s is not None and len(col)-s>50: runs.append((s,len(col)))
assert len(runs)==4,runs
ids=['normal','star','heart','heroshield']
TARGET_H=192   # 表示はショップで最大 約150px（3倍の画面）なので少し余裕を持たせる
for i,(x0,x1) in enumerate(runs):
    sub=clean(Hs[:,max(0,x0-6):min(Hs.shape[1],x1+6)])
    sub,_=crop(sub)
    h,w=sub.shape[:2]; k=TARGET_H/h
    im=Image.fromarray(sub,'RGBA').resize((round(w*k),TARGET_H),Image.LANCZOS)
    arr=np.asarray(im).copy()
    sz=webp(arr,f'{OUT}/shield_{ids[i]}.webp')
    meta[ids[i]]={'w':arr.shape[1],'h':arr.shape[0],'webp':sz}
    if ids[i]=='normal':
        # 面（クリーム色・赤みがある）を中央から塗りつぶしで探し、残りの不透明な所＝金属（ふち・鋲）
        r,g,b,al=[arr[:,:,j].astype(int) for j in range(4)]
        warm=(r-b>=22)&(al>0)
        H2,W2=warm.shape; seen=np.zeros_like(warm); q=deque([(H2//2,W2//2)]); assert warm[H2//2,W2//2]
        seen[H2//2,W2//2]=True
        while q:
            y,x=q.popleft()
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                yy,xx=y+dy,x+dx
                if 0<=yy<H2 and 0<=xx<W2 and warm[yy,xx] and not seen[yy,xx]: seen[yy,xx]=True; q.append((yy,xx))
        # 面の中のテカリ（白っぽく赤みが少ない）は面に含める：面でない所を外側からたどって、届かない所＝面の穴
        notface=~seen; out_=np.zeros_like(notface); q=deque()
        for yy in range(H2):
            for xx in (0,W2-1):
                if notface[yy,xx] and not out_[yy,xx]: out_[yy,xx]=True; q.append((yy,xx))
        for xx in range(W2):
            for yy in (0,H2-1):
                if notface[yy,xx] and not out_[yy,xx]: out_[yy,xx]=True; q.append((yy,xx))
        while q:
            y,x=q.popleft()
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                yy,xx=y+dy,x+dx
                if 0<=yy<H2 and 0<=xx<W2 and notface[yy,xx] and not out_[yy,xx]: out_[yy,xx]=True; q.append((yy,xx))
        seen=seen|(~out_)
        metal=(al>0)&~seen
        mp=np.zeros((H2,W2,4),np.uint8); mp[metal]=(255,0,0,255)
        Image.fromarray(mp,'RGBA').save(f'{OUT}/shield_normal_map.png',optimize=True)
        L=0.3*r+0.59*g+0.11*b
        meta['normal']['mapPng']=os.path.getsize(f'{OUT}/shield_normal_map.png')
        meta['normal']['metalPx']=int(metal.sum()); meta['normal']['facePx']=int(seen.sum())
        meta['normal']['mref']=float(np.round(np.percentile(L[metal&(al>=250)],80),1))   # 金属の基準の明るさ（体の wref と同じ考え方）
# ── ヒーローソード ──
Sw=clean(np.asarray(Image.open(SW).convert('RGBA'))); Sw,(ox,oy)=crop(Sw)
h,w=Sw.shape[:2]; TH=300; k=TH/h
im=Image.fromarray(Sw,'RGBA').resize((round(w*k),TH),Image.LANCZOS); arr=np.asarray(im)
sz=webp(arr,f'{OUT}/sword_herosword.webp')
# 握る所＝青い柄の真ん中（元画像で y960〜1220 の帯の中心、x は中心）
grip_y=(1090-oy)*k
meta['herosword']={'w':arr.shape[1],'h':arr.shape[0],'webp':sz,'gripX':round(arr.shape[1]/2,1),'gripY':round(grip_y,1)}
json.dump(meta,open(f'{OUT}/meta.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(meta,ensure_ascii=False))
