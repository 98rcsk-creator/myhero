# 体のポーズ（向きごと）・顔の元絵（緑バック）を切り抜いて、test/ta3d.html に入れる形（WebP の base64）にする
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
out={'poses':{}, 'face':[]}; prev=[]
# ---- 体の絵：1枚の元絵に たて×よこ にならんだポーズを、すき間で切り分けて 名前をつける ----
#   名前：向き＋ポーズ。向き b＝うしろ bd＝ななめうしろ s＝横 fd＝ななめ前 f＝前（どれも「画面の右を向く」絵。左へ行くときはゲームが反転する）
#   None＝使わない絵。元絵がまだ無いものは とばす（ゲームは うしろ姿で代わりにする）
SHEETS=[('back_src.png',  [['b_run0','b_run1','b_jump',None]]),                 # 4つ目は剣をふる絵（剣をやめたので使わない）
        ('back2_src.png', [['b_stand',None,'b_punch','b_ready']]),            # 直立・（剣を抜く＝使わない）・右手をふりぬく＝パンチに使う・よーい
        ('dirs_src.png',  [['bd_run0','s_run0','fd_run0','f_run0'],              # 上の段：走る1（右足が前）
                           ['bd_run1','s_run1','fd_run1','f_run1']])]            # 下の段：走る2（左足が前）
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
def headw(c):   # 頭のはば：絵の上 28% で いちばん広い行（頭は大きい丸なので、向きが変わっても ほぼ同じ）
    m=c[:int(c.shape[0]*0.28),:,3]>128; return max(int(r.sum()) for r in m)
HEAD=None   # 基準：うしろ姿の走る1枚目の頭のはば × 300/690（＝試作3 からの大きさ）
for fn,names in SHEETS:
    if not os.path.exists(os.path.join(D,fn)): print('skip',fn); continue
    A=key(fn); op=A[...,3]>128; figs=[]
    rows=bands(op,1)
    assert len(rows)==len(names),(fn,'段の数',len(rows),len(names))
    for (ry0,ry1),nm in zip(rows,names):
        cols=bands(op[ry0:ry1],0); assert len(cols)==len(nm),(fn,'列の数',len(cols),len(nm))
        for (x0,x1),n in zip(cols,nm):
            sub=op[ry0:ry1,x0:x1]; yy=np.where(sub.sum(1)>2)[0]; y0,y1=ry0+yy[0],ry0+yy[-1]+1
            figs.append((n,A[y0:y1,x0:x1]))
    hw=sorted(headw(c) for n,c in figs)[len(figs)//2]   # この元絵の頭のはば（まん中の値）
    if HEAD is None: HEAD=hw*300/690.0
    K=HEAD/hw
    for n,c in figs:
        if n is None: continue
        h,w=c.shape[:2]; top=c[:int(h*0.28),:,3]>128; xs=np.where(top.sum(0)>0)[0]; ax=(xs[0]+xs[-1])/2.0   # 頭のまん中＝横の基準
        im=Image.fromarray(c,'RGBA').resize((round(w*K),round(h*K)),Image.LANCZOS)
        out['poses'][n]={'d':b64(im),'w':im.width,'h':im.height,'ax':round(ax*K,1)}; prev.append(im)
        print(fn,n,im.size,'ax',round(ax*K,1))
# ---- 顔：3×2 のマスをそのまま（位置をそろえたまま）半分の大きさに ----
Fc=key('faces_src.png'); H,W=Fc.shape[:2]; cw,ch=W//3,H//2
for j in range(2):
    for i in range(3):
        im=Image.fromarray(Fc[j*ch:(j+1)*ch,i*cw:(i+1)*cw],'RGBA').resize((256,256),Image.LANCZOS)
        out['face'].append(b64(im)); prev.append(im)
# 7つ目：ふつうの顔（キャラ選択の元絵 face_calm_src.png・背景は透明）。顔1の頭（首をのぞく上75%）と 幅・上はし・横のまん中 を合わせる
c0=Fc[0:ch,0:cw]; m=c0[:int(ch*0.75),:,3]>128; xs=np.where(m.sum(0)>0)[0]; ys=np.where(m.sum(1)>0)[0]
src=Image.open(os.path.join(D,'face_calm_src.png')).convert('RGBA'); sa=np.asarray(src)[...,3]>128; sx=np.where(sa.sum(0)>0)[0]; sy=np.where(sa.sum(1)>0)[0]
k=(xs[-1]-xs[0])/float(sx[-1]-sx[0]); im=src.resize((round(src.width*k),round(src.height*k)),Image.LANCZOS)
cell=Image.new('RGBA',(cw,ch),(0,0,0,0)); cell.alpha_composite(im,(int(round((xs[0]+xs[-1])/2-(sx[0]+sx[-1])/2*k)),int(round(ys[0]-sy[0]*k))))
im=cell.resize((256,256),Image.LANCZOS); out['face'].append(b64(im)); prev.append(im)
json.dump(out,open(sys.argv[1],'w'))
print('bytes',sum(len(v['d']) for v in out['poses'].values()),sum(len(f) for f in out['face']))
if len(sys.argv)>2:
    o=Image.new('RGBA',(sum(p.width for p in prev)+10*len(prev),320),(90,120,200,255)); x=5
    for p in prev: o.alpha_composite(p,(x,5)); x+=p.width+10
    o.save(sys.argv[2])
