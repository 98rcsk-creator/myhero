# 応援するヒーロー（crowd_src.png・緑バック）を切り抜いて crowd.json の hb に入れる
#   ★試作20 ユーザーの追加の2枚も同じやり方で後ろに足す：crowd2_src.png（7人の別のポーズ）・crowd_pair_src.png（まものと仲良しの7組）
#   大きさ：ヒーローの背の高さが 210px になるよう 1枚ごとに縮める。crowd_src・crowd2 は7体の高さのまん中の値＝ヒーローの背。
#   仲良しの絵は ヒーローが小さめに描かれていて、肩車の組は上にまものが乗っている → 何も乗っていない3組（ジルヴェスター・ユリアン・エルザ）の高さのまん中＝353px をヒーローの背とする。
#   ゲームは「絵の高さ÷210」倍で描く（肩車の組は背が高く、横にならぶ組は はばが広くなる。ヒーローの大きさは そろう）
#   緑の髪・緑の服のキャラがいるので、「緑っぽさ」ではなく「背景の緑そのもの（ほぼ 0,255,0）」だけを抜く
#   使い方: python3 docs/assets_src/ta3d_rubert/prep_crowd.py [プレビュー.png]
import sys, io, json, base64, os
import numpy as np
from PIL import Image, ImageFilter
D=os.path.dirname(os.path.abspath(__file__))
def key(fn):
    a=np.asarray(Image.open(os.path.join(D,fn)).convert('RGB')).astype(np.float32)
    r,g,b=a[...,0],a[...,1],a[...,2]
    dist=np.sqrt(r*r+(255-g)**2+b*b)                                   # 背景の緑からの遠さ
    al=np.clip((dist-60)/70,0,1)                                       # 60 までは透明・130 から不透明
    edge=(al>0)&(np.asarray(Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)))<255)   # ふちの2px
    g2=np.where(edge & (g>np.maximum(r,b)),np.maximum(r,b),g)          # ふちだけ 緑かぶりを取る（服の緑は そのまま）
    A=np.dstack([r,g2,b,al*255]).astype(np.uint8); op=A[...,3]>128
    return A,op
def bands(mask,axis,minlen=60):
    v=mask.sum(axis)>2; out=[]; i=0; n=len(v)
    while i<n:
        if v[i]:
            j=i
            while j<n and v[j]: j+=1
            if j-i>minlen: out.append((i,j))
            i=j
        else: i+=1
    return out
out=[]; prev=[]
for fn,ref in (('crowd_src.png',None),('crowd2_src.png',None),('crowd_pair_src.png',353.0)):
    A,op=key(fn); figs=[]
    for ry0,ry1 in bands(op,1):
        for x0,x1 in bands(op[ry0:ry1],0):
            yy=np.where(op[ry0:ry1,x0:x1].sum(1)>2)[0]; figs.append(A[ry0+yy[0]:ry0+yy[-1]+1,x0:x1])
    assert len(figs)==7,(fn,len(figs))
    K=210.0/(ref or np.median([f.shape[0] for f in figs]))
    for f in figs:
        im=Image.fromarray(f,'RGBA').resize((round(f.shape[1]*K),round(f.shape[0]*K)),Image.LANCZOS)
        bio=io.BytesIO(); im.save(bio,'WEBP',quality=86,method=6); out.append(base64.b64encode(bio.getvalue()).decode()); prev.append(im)
c=json.load(open(os.path.join(D,'crowd.json'))); c['hb']=out; json.dump(c,open(os.path.join(D,'crowd.json'),'w'))
print(len(out),'体',[p.size for p in prev],'bytes',sum(len(o) for o in out))
if len(sys.argv)>1:
    o=Image.new('RGBA',(sum(p.width for p in prev)+10*len(prev),max(p.height for p in prev)+10),(90,120,200,255)); x=5
    for p in prev: o.alpha_composite(p,(x,5)); x+=p.width+10
    o.save(sys.argv[1])
