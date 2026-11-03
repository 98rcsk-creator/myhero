# v328 ふつうの剣4本（銀・炎・雷・闇）の絵を、ゲームに埋め込む形に整える（ヒーローソードの握る所も同じ決め方で測り直す）
#   使い方: python3 docs/assets_src/items_v328/prep_swords.py swords.png ../items_v327/herosword.png 出力フォルダ
#   - 透明な所の色のゴミ（α1〜15）を消し、ふちのα16〜239を0〜255に引き伸ばす（v327 の盾と同じ）
#   - 1枚に並んだ4本を、不透明な列のかたまりで切り分ける
#   - 高さ300px の WebP（q88）。握る所＝柄の真ん中（鍔の下で幅がほぼ一定の帯）を絵の画素で出す
import sys, os, json
import numpy as np
from PIL import Image

SW, HERO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

def clean(arr):
    a=arr[:,:,3].astype(float); na=np.clip((a-16)/(240-16)*255,0,255)
    out=arr.copy(); out[:,:,3]=na.astype(np.uint8); out[na==0]=0; return out

def crop(arr,pad=4):
    ys,xs=np.where(arr[:,:,3]>0); y0,y1=max(0,ys.min()-pad),min(arr.shape[0],ys.max()+1+pad); x0,x1=max(0,xs.min()-pad),min(arr.shape[1],xs.max()+1+pad)
    return arr[y0:y1,x0:x1]

def grip(a):
    # 下の6割で「いちばん広い所（鍔）の4割より細い行」がつづく所＝柄＋柄頭。その中で幅がほぼ一定の最初のかたまり＝柄
    w=(a>128).sum(axis=1); ys=np.where(w>0)[0]; y0,y1=ys.min(),ys.max(); mw=w.max()
    narrow=(w>0)&(w<0.4*mw); narrow[:y0+int((y1-y0)*0.4)]=False
    best=(0,0,0); s=None
    for y in range(len(w)+1):
        v=narrow[y] if y<len(w) else False
        if v and s is None: s=y
        if not v and s is not None:
            if y-s>best[0]: best=(y-s,s,y)
            s=None
    _,r0,r1=best; m=np.median(w[r0:r0+(r1-r0)//2])
    g0=r0
    while g0<r1 and w[g0]>m*1.1: g0+=1
    g1=g0
    while g1<r1 and w[g1]<=m*1.1: g1+=1
    xs=np.where((a[g0:g1]>128).any(axis=0))[0]
    return (xs.min()+xs.max()+1)/2, (g0+g1)/2

def save(arr,name,TH=300):
    h,w=arr.shape[:2]; k=TH/h
    im=Image.fromarray(arr,'RGBA').resize((round(w*k),TH),Image.LANCZOS); a2=np.asarray(im)
    gx,gy=grip(a2[:,:,3])
    path=f'{OUT}/sword_{name}.webp'; im.save(path,'WEBP',quality=88,method=6)
    return {'w':a2.shape[1],'h':a2.shape[0],'webp':os.path.getsize(path),'gripX':round(gx,1),'gripY':round(gy,1)}

meta={}
S=np.asarray(Image.open(SW).convert('RGBA')); a=S[:,:,3]
col=(a>128).sum(axis=0)>0; runs=[]; s=None
for x,v in enumerate(col):
    if v and s is None: s=x
    if not v and s is not None:
        if x-s>30: runs.append((s,x))
        s=None
if s is not None and len(col)-s>30: runs.append((s,len(col)))
assert len(runs)==4,runs
for name,(x0,x1) in zip(['silver','flame','thunder','dark'],runs):
    meta[name]=save(crop(clean(S[:,max(0,x0-6):min(S.shape[1],x1+6)])),name)
meta['herosword']=save(crop(clean(np.asarray(Image.open(HERO).convert('RGBA')))),'herosword')
json.dump(meta,open(f'{OUT}/meta.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(meta,ensure_ascii=False))
