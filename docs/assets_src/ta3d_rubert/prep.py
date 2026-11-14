# うしろ姿4ポーズ・顔6つの元絵（緑バック）を切り抜いて、test/ta3d.html に入れる形（WebP の base64）にする
#   使い方: python3 docs/assets_src/ta3d_rubert/prep.py 出力.json [プレビュー.png]
import sys, io, json, base64, os
import numpy as np
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__))
def key(fn):
    a=np.asarray(Image.open(os.path.join(D,fn)).convert('RGB')).astype(np.float32)
    r,g,b=a[...,0],a[...,1],a[...,2]; gn=g-np.maximum(r,b)                 # 緑っぽさ
    al=np.clip(1-(gn-30)/70,0,1)                                            # 30 までは不透明・100 で透明
    g2=np.where(gn>0,np.maximum(r,b),g)                                     # ふちの緑かぶりを取る
    return np.dstack([r,g2,b,al*255]).astype(np.uint8)
def b64(im,q=88):
    bio=io.BytesIO(); im.save(bio,'WEBP',quality=q,method=6); return base64.b64encode(bio.getvalue()).decode()
out={'pose':[], 'face':[]}; prev=[]
# ---- うしろ姿：たての すき間で4つに分ける ----
A=key('back_src.png'); op=A[...,3]>128; col=op.sum(0)>2; segs=[]; x=0; W=A.shape[1]
while x<W:
    if col[x]:
        x0=x
        while x<W and col[x]: x+=1
        if x-x0>60: segs.append((x0,x))
    else: x+=1
assert len(segs)==4, segs
K=300/690.0                                                                  # 走るポーズの高さ 690px → 300px
for i,(x0,x1) in enumerate(segs):
    rows=np.where(op[:,x0:x1].sum(1)>2)[0]; y0,y1=rows[0],rows[-1]+1
    c=A[y0:y1,x0:x1]; h,w=c.shape[:2]
    top=c[:int(h*0.35),:,3]>128; xs=np.where(top.sum(0)>0)[0]; ax=(xs[0]+xs[-1])/2.0   # 頭のまん中＝横の基準
    im=Image.fromarray(c,'RGBA').resize((round(w*K),round(h*K)),Image.LANCZOS)
    out['pose'].append({'d':b64(im),'w':im.width,'h':im.height,'ax':round(ax*K,1)}); prev.append(im)
    print('pose',i,(x0,y0,x1,y1),im.size,'ax',round(ax*K,1))
# ---- 顔：3×2 のマスをそのまま（位置をそろえたまま）半分の大きさに ----
Fc=key('faces_src.png'); H,W=Fc.shape[:2]; cw,ch=W//3,H//2
for j in range(2):
    for i in range(3):
        im=Image.fromarray(Fc[j*ch:(j+1)*ch,i*cw:(i+1)*cw],'RGBA').resize((256,256),Image.LANCZOS)
        out['face'].append(b64(im)); prev.append(im)
json.dump(out,open(sys.argv[1],'w'))
print('bytes',sum(len(p['d']) for p in out['pose']),sum(len(f) for f in out['face']))
if len(sys.argv)>2:
    o=Image.new('RGBA',(sum(p.width for p in prev)+10*len(prev),320),(90,120,200,255)); x=5
    for p in prev: o.alpha_composite(p,(x,5)); x+=p.width+10
    o.save(sys.argv[2])
