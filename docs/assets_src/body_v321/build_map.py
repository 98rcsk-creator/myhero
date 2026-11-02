# 新しい体の塗り分けの地図（BODY_SPR.map）を元画像 body.png から作る。★v325
#   1=上着 2=ズボン 3=ブーツ 4=肌。出力は BODY_SPR.map と同じ形式（357x360・R=領域x50・A=255）。
#   使い方: python3 docs/assets_src/body_v321/build_map.py 出力.png
#   体の縮小画像（BODY_SPR.base）は game/my_hero.html から読み、不透明な画素にだけ領域を入れる。
# v321 の作り方からの変更点（v321 は手の甲のテカリが服の色・袖口のふちが肌色・ブーツの上にズボンの色になっていた）：
#   - 肌を「赤み r-b>=28」で判定するのをやめ、袖口と手・首と襟の境目の線（元画像を拡大して目盛りで読んだ座標）で決める。
#     この1枚の素材専用の座標なので、素材を差し替えたら測り直す。
#   - ズボンとブーツの境目は斜めの曲線で、v321 の帯（y1016〜1046）からはみ出す列があった。
#     目盛りで読んだ大まかな線の ±7px で一番暗いしわを探し、なめらかにする。
#   - 上着とズボンの境目（y752〜812 の一番暗いしわ）も列ごとのガタつきをなめらかにする。
import sys, io, base64, re, os
import numpy as np
from PIL import Image, ImageDraw

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))
OUT=sys.argv[1] if len(sys.argv)>1 else 'map_new.png'
B=np.asarray(Image.open(os.path.join(ROOT,'docs/assets_src/body_v321/body.png')).convert('RGBA')).astype(float)
H,W=B.shape[:2]
r,g,b,a=B[:,:,0],B[:,:,1],B[:,:,2],B[:,:,3]
L=0.3*r+0.59*g+0.11*b
op=a>0

def smooth(v,w1=21,w2=9):
    out=np.array([np.median(v[max(0,i-w1//2):i+w1//2+1]) for i in range(len(v))])
    return np.array([np.mean(out[max(0,i-w2//2):i+w2//2+1]) for i in range(len(v))])

def poly_mask(pts):
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon(pts,fill=255); return np.asarray(m)>0

# ── 肌：袖口と手の境目のしわ／首と襟の境目より、手・首の側の不透明な画素 ──
HAND_POLY=[
 [(130,660),(190,653),(210,655),(230,661.7),(250,671.7),(270,685),(287.5,697),(295,708),(299,720),(302,728),(315,732),(315,845),(130,845)],
 [(1125,660),(1062,653),(1050,654),(1035,656.7),(1015,666.7),(995,678),(975,691.7),(965,700),(957.5,712.5),(952.5,725),(951,728),(938,732),(938,845),(1125,845)],
]
NECK_POLY=[(530,200),(725,200),(725,284),(713,290),(690,300),(660,306),(625,308),(590,305),(560,298),(540,290),(530,284)]
skin=np.zeros((H,W),bool)
for pts in HAND_POLY+[NECK_POLY]: skin|=poly_mask(pts)&op

# ── 上着とズボンの境目：列ごとに y752〜812 で一番暗いしわ（帯に不透明な画素が無い列は 772）→ なめらかに ──
hem=np.full(W,772.0)
for x in range(W):
    col=a[752:813,x]>=128
    if col.any(): hem[x]=752+int(np.where(col,L[752:813,x],1e9).argmin())
hem=smooth(hem)

# ── ズボンとブーツの境目：目盛りで読んだ大まかな線 → 各列でその ±7px の一番暗いしわ → なめらかに ──
BOOT_LINE=[[(347,1020),(370,1014),(390,1012),(420,1013),(440,1017),(465,1023),(490,1030),(515,1039),(540,1046),(565,1050),(588,1051)],
           [(665,1046),(675,1047),(715,1045),(750,1035),(790,1022),(830,1015),(865,1012),(900,1017),(910,1022)]]
boot=np.full(W,1031.0)
for n_,pts in enumerate(BOOT_LINE):
    px=np.array([p[0] for p in pts],float); py=np.array([p[1] for p in pts],float)
    xs=np.arange(int(px[0]),int(px[-1])+1); rough=np.interp(xs,px,py); ref=rough.copy()
    for k,x in enumerate(xs):
        y0=int(round(rough[k]))-7; col=a[y0:y0+15,x]>=128
        if col.any(): ref[k]=y0+int(np.where(col,L[y0:y0+15,x],1e9).argmin())
    sm=smooth(ref,15,7); boot[xs]=sm
    if n_==0: boot[:xs[0]]=sm[0]
    else: boot[xs[-1]+1:]=sm[-1]
gap=np.arange(589,665); boot[gap]=np.interp(gap,[588,665],[boot[588],boot[665]])   # 2本の脚のあいだ

yy=np.arange(H)[:,None]
lab=np.zeros((H,W),np.uint8)
cloth=np.where(yy<hem[None,:],1,np.where(yy<boot[None,:],2,3))
lab[op]=cloth[op]; lab[skin]=4

# ── 縮小：v321 と同じ切り抜き・同じ「縮小後の画素の中心にあたる元の画素」──
X0,Y0,CW,CH=134,215,986,993; OH=360; s=OH/CH; OW=round(CW*s)
src=open(os.path.join(ROOT,'game/my_hero.html'),encoding='utf-8').read(); seg=src[src.find('var BODY_SPR={'):][:300000]
base=np.asarray(Image.open(io.BytesIO(base64.b64decode(re.search(r"base:'data:image/webp;base64,([A-Za-z0-9+/=]+)'",seg).group(1)))).convert('RGBA'))
assert base.shape[:2]==(OH,OW),base.shape
md=np.zeros((OH,OW,4),np.uint8); cnt=[0]*5
for y in range(OH):
    for x in range(OW):
        if base[y,x,3]==0: continue
        sx=min(W-1,round(X0+(x+0.5)/s)); sy=min(H-1,round(Y0+(y+0.5)/s)); rg=int(lab[sy,sx])
        rr=1
        while rg==0 and rr<=4:   # 縁：近くの領域を探す（v321 と同じ）
            for dx,dy in ((rr,0),(-rr,0),(0,rr),(0,-rr)):
                q=int(lab[min(H-1,max(0,sy+dy)),min(W-1,max(0,sx+dx))])
                if q: rg=q; break
            rr+=1
        if rg==0: rg=1
        cnt[rg]+=1; md[y,x]=(rg*50,0,0,255)
Image.fromarray(md,'RGBA').save(OUT,optimize=True)
print('地図',OW,'x',OH,'→',OUT,os.path.getsize(OUT),'B ／ 画素数[-,上着,ズボン,ブーツ,肌]',cnt)
