# ほかの7人の絵（ChatGPT で ルーベルトの絵を入れかえたもの）を切り分けて、500m走が あとから読みこむ ファイルにする
#   使い方: python3 docs/assets_src/ta3d_chars/prep_char.py <キャラID> [<キャラID> ...]   → test/ta3d_chars/<キャラID>.js
#           python3 docs/assets_src/ta3d_chars/prep_char.py --check <出力フォルダ> <キャラID> ...   → 切り分けた絵の一覧（ルーベルトと並べた画像）
#           python3 docs/assets_src/ta3d_chars/prep_char.py --lite <キャラID> ...   → できた <ID>.js から ライバル用の <ID>_r.js だけ作る（★試作26）
#   元の絵（このフォルダの <キャラID>/）：
#     back2_src.png … 直立・剣を抜く（使わない）・パンチ・よーい（1段4体）
#     all4_src.png  … 白い線で 田の字に4つ：左上＝走る・走る・ジャンプ・うでをふる（使わない）／右上＝スライディング2体（右を使う）／
#                      左下＝向き8体（4列×2段：ななめうしろ・横・ななめ前・前）／右下＝顔6つ（3列×2段）
#     all4_faces_src.png … あれば 右下の顔だけ こちらを使う（メルティ：さいごの絵は 顔の髪型が かわったので 1つ前の絵の顔を使う）
#   大きさ：ルーベルト（test/ta3d.html の ART）と 同じ ポーズの「体の高さ」が そろうよう、枠ごとに 1つの倍率で縮める。
#     体の高さ＝足から「頭の いちばん広い所の半分の はばが はじまる行」まで（とがった髪・ツノ・トサカの先は 数えない。
#     そのまま高さで そろえると、ツノや とがった髪のキャラだけ 体が小さくなる）
#   切り抜き：緑っぽさ ではなく「背景の緑そのもの」からの遠さで抜く（ジルヴェスターの緑の髪・緑の服が 消えないように。prep_crowd.py と同じ考え）
import sys, io, os, json, base64, re
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
D=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.normpath(os.path.join(D,'..','..','..'))
NAMES={'men_1':'バルト','men_2':'ジルヴェスター','men_3':'ユリアン','women_0':'クララ','women_1':'エルザ','women_2':'メルティ','women_3':'ブリギッタ'}

GREEN_CHARS={'men_2'}   # 体に 明るい緑がある（ジルヴェスターの髪・服）
def keyimg(im,green=False):
    # 背景＝「ふちから つながっている 緑っぽい所」＋「どこでも 背景の緑 そのもの（かこまれた すき間）」。
    #   体の中の 明るい緑（ジルヴェスターの髪・服のテカり）は ふちと つながらないので 抜けない（前は 色だけで抜いて 穴があいた）
    #   半分すける ふち（髪の毛先）は 背景の緑を 引いて 元の色にもどす（毛先に 緑が のこらない）
    a=np.asarray(im.convert('RGB')).astype(np.float32); h,w=a.shape[:2]
    bg=np.median(np.concatenate([a[3:30,3:30].reshape(-1,3),a[3:30,w-30:w-3].reshape(-1,3),a[h-30:h-3,3:30].reshape(-1,3)]),0)
    dist=np.sqrt(((a-bg)**2).sum(2)); near=dist<125
    m=np.zeros_like(near); m[0,:]=near[0,:]; m[-1,:]=near[-1,:]; m[:,0]=near[:,0]; m[:,-1]=near[:,-1]
    while True:
        g=m.copy(); g[1:]|=m[:-1]; g[:-1]|=m[1:]; g[:,1:]|=m[:,:-1]; g[:,:-1]|=m[:,1:]; g&=near
        if (g==m).all(): break
        m=g
    if green:   # 緑のキャラ：かこまれた すき間は「背景の緑そのもの」で 31px より太い所だけ（トサカの 光った所を 抜かない）
        pure=Image.fromarray(((dist<35)*255).astype(np.uint8)).filter(ImageFilter.MinFilter(31)).filter(ImageFilter.MaxFilter(31)); B=m|(np.asarray(pure)>0)
    else:       # ほかのキャラ：体に緑は無いので、かこまれた 緑っぽい所（髪の毛の すき間・ふさの間）も ぜんぶ背景
        B=m|(dist<100)
    al=np.where(B,np.clip((dist-80)/45,0,1),1.0)
    k=al[...,None]; F=np.where(k>0.02,(a-(1-k)*bg)/np.maximum(k,0.02),a); F=np.clip(F,0,255)
    if green: F=a   # 緑のキャラは 色を もどさない（うめた穴が 赤むらさきに なる）
    if not green:   # ふちの 2〜3px に まざった 緑を とる（茶色の髪の まわりの うすい緑の線）。緑のキャラは やらない（髪・服の緑が 消える）
        rim=(np.asarray(Image.fromarray((B*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7)))>0)&(al>0)
        mx=np.maximum(F[...,0],F[...,2]); F[...,1]=np.where(rim&(F[...,1]>mx),mx,F[...,1])
        al=np.minimum(al,np.asarray(Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))).astype(np.float32)/255)   # ★2026-11-21 いちばん外の 2px を けずる（エルザの 金髪・白い服の ふちに 黄緑の線が のこった）
    return np.dstack([F,al*255]).astype(np.uint8)
def bands(v,minlen):
    out=[]; i=0; n=len(v)
    while i<n:
        if v[i]:
            j=i
            while j<n and v[j]: j+=1
            if j-i>=minlen: out.append([i,j])
            i=j
        else: i+=1
    return out
def merge_small(bs,k=0.3):   # はなれた手・髪の毛先など 細い かけらを となりの体に くっつける
    while len(bs)>1:
        w=[b[1]-b[0] for b in bs]; i=int(np.argmin(w))
        if w[i]>=k*max(w): break
        if i==0: j=1
        elif i==len(bs)-1: j=i-1
        else: j=i-1 if bs[i][0]-bs[i-1][1]<=bs[i+1][0]-bs[i][1] else i+1
        a,b=sorted([i,j]); bs[a]=[bs[a][0],bs[b][1]]; del bs[b]
    return bs
def comps(mask):   # つながっている かたまりに 分ける（4方向）。[(面積, マスク), ...]
    rest=mask.copy(); out=[]
    while rest.any():
        ys,xs=np.nonzero(rest); m=np.zeros_like(rest); m[ys[0],xs[0]]=True
        while True:
            g=m.copy(); g[1:]|=m[:-1]; g[:-1]|=m[1:]; g[:,1:]|=m[:,:-1]; g[:,:-1]|=m[:,1:]; g&=rest
            if (g==m).all(): break
            m=g
        out.append((int(m.sum()),m)); rest&=~m
    return out
def tidy(A,green):   # 1体ぶんの絵の おそうじ：はなれた 小さな かけら（髪の毛先のちぎれ）を消す・緑のキャラは 体の中の 小さな穴（トサカの光った所）を うめる
    A=A.copy(); op=A[...,3]>128; cs=comps(op); big=max(c[0] for c in cs)
    for n,m in cs:
        if n<big*0.004: A[...,3][m]=0
    if green:
        holes=~(A[...,3]>128); outside=np.zeros_like(holes); outside[0,:]=holes[0,:]; outside[-1,:]=holes[-1,:]; outside[:,0]=holes[:,0]; outside[:,-1]=holes[:,-1]
        while True:
            g=outside.copy(); g[1:]|=outside[:-1]; g[:-1]|=outside[1:]; g[:,1:]|=outside[:,:-1]; g[:,:-1]|=outside[:,1:]; g&=holes
            if (g==outside).all(): break
            outside=g
        for n,m in comps(holes&~outside):
            if n<big*0.01: A[...,3][m]=255
    ys=np.where((A[...,3]>128).sum(1)>0)[0]; xs=np.where((A[...,3]>128).sum(0)>0)[0]
    return A[ys[0]:ys[-1]+1,xs[0]:xs[-1]+1]
def split_even(prof,n):   # 等分の位置の近くで いちばん うすい所で 切る（絵が くっついていて すき間が無いとき）
    xs=np.where(prof>1)[0]; xa,xb=xs[0],xs[-1]+1; cuts=[xa]
    for k in range(1,n):
        c=xa+(xb-xa)*k/n; lo,hi=int(c-(xb-xa)*0.12),int(c+(xb-xa)*0.12); cuts.append(lo+int(np.argmin(prof[lo:hi])))
    cuts.append(xb); return [[cuts[k],cuts[k+1]] for k in range(n)]
def figures(A,rows_expect,green=False):
    op=A[...,3]>128; out=[]
    rprof=op.sum(1); rb=merge_small(bands(rprof>2,8),0.25)
    if len(rb)<len(rows_expect): rb=split_even(rprof,len(rows_expect))   # 上と下が くっついている
    assert len(rb)==len(rows_expect),('段の数',len(rb),rows_expect)
    for (y0,y1),nexp in zip(rb,rows_expect):
        prof=op[y0:y1].sum(0); cb=merge_small(bands(prof>1,3))
        if len(cb)<nexp: cb=split_even(prof,nexp)   # となりと くっついている（クララの顔の 髪どうし など）
        assert len(cb)==nexp,('列の数',len(cb),nexp)
        row=[]
        for x0,x1 in cb:
            sub=op[y0:y1,x0:x1]; ys=np.where(sub.sum(1)>1)[0]; xs=np.where(sub.sum(0)>1)[0]
            row.append(tidy(A[y0+ys[0]:y0+ys[-1]+1,x0+xs[0]:x0+xs[-1]+1],green))
        out.append(row)
    return out
def quads(im):
    a=np.asarray(im.convert('RGB')).astype(int); h,w=a.shape[:2]; white=a.min(2)>225
    rows=np.where(white.mean(1)>0.5)[0]; cols=np.where(white.mean(0)>0.5)[0]
    rows=rows[(rows>h*0.3)&(rows<h*0.7)]; cols=cols[(cols>w*0.3)&(cols<w*0.7)]
    assert len(rows) and len(cols),'白い線が見つからない'
    ry0,ry1=rows.min()-4,rows.max()+5; cx0,cx1=cols.min()-4,cols.max()+5
    return {'TL':im.crop((0,0,cx0,ry0)),'TR':im.crop((cx1,0,w,ry0)),'BL':im.crop((0,ry1,cx0,h)),'BR':im.crop((cx1,ry1,w,h))}
def efftop(op):   # 頭の いちばん広い所の 半分の はばが はじまる行（とがった髪・ツノの先を のぞく）
    h=op.shape[0]; cnt=op.sum(1); top=cnt[:max(2,int(h*0.45))]; m=top.max(); return int(np.argmax(top>=0.5*m))
def effh(A): op=A[...,3]>128; return op.shape[0]-efftop(op)
def headx(A):   # 横の基準＝頭の まん中（体の高さを はかる行から 下へ 30% の はばの まん中）
    op=A[...,3]>128; h=op.shape[0]; t=efftop(op); band=op[t:t+max(2,int((h-t)*0.3))]; xs=np.where(band.sum(0)>0)[0]; return (xs[0]+xs[-1])/2.0
def rubert():
    t=open(os.path.join(ROOT,'test','ta3d.html'),encoding='utf-8').read(); i=t.index('var ART=')+len('var ART=')
    art,_=json.JSONDecoder().raw_decode(t[i:]); P={}
    for k,p in art['poses'].items(): P[k]=np.asarray(Image.open(io.BytesIO(base64.b64decode(p['d']))).convert('RGBA'))
    F=[np.asarray(Image.open(io.BytesIO(base64.b64decode(d))).convert('RGBA')) for d in art['face']]
    return P,F
def b64(im,q=86):
    bio=io.BytesIO(); im.save(bio,'WEBP',quality=q,method=6); return base64.b64encode(bio.getvalue()).decode()
DIRS=[['bd_run0','s_run0','fd_run0','f_run0'],['bd_run1','s_run1','fd_run1','f_run1']]
def build(cid,RP,RF):
    C=os.path.join(D,cid); figs={}; groups=[]; G=cid in GREEN_CHARS
    A=keyimg(Image.open(os.path.join(C,'back2_src.png')),G); r=figures(A,[4],G)[0]
    figs.update({'b_stand':r[0],'b_punch':r[2],'b_ready':r[3]}); groups.append((['b_stand','b_punch','b_ready'],['b_stand']))
    Q=quads(Image.open(os.path.join(C,'all4_src.png')))
    r=figures(keyimg(Q['TL'],G),[4],G)[0]; figs.update({'b_run0':r[0],'b_run1':r[1],'b_jump':r[2]}); groups.append((['b_run0','b_run1','b_jump'],['b_run0','b_run1']))
    r=figures(keyimg(Q['TR'],G),[2],G)[0]; figs['b_slide']=r[1]; groups.append((['b_slide'],['b_slide']))
    rr=figures(keyimg(Q['BL'],G),[4,4],G)
    for j in range(2):
        for i in range(4): figs[DIRS[j][i]]=rr[j][i]
    dn=DIRS[0]+DIRS[1]; groups.append((dn,dn))
    fq=Q['BR'] if not os.path.exists(os.path.join(C,'all4_faces_src.png')) else quads(Image.open(os.path.join(C,'all4_faces_src.png')))['BR']
    fr=figures(keyimg(fq,G),[3,3],G); faces=fr[0]+fr[1]
    poses={}
    for names,ref in groups:
        K=np.mean([effh(RP[n]) for n in ref])/np.mean([effh(figs[n]) for n in ref])
        for n in names:
            f=figs[n]; im=Image.fromarray(f,'RGBA').resize((max(1,round(f.shape[1]*K)),max(1,round(f.shape[0]*K))),Image.LANCZOS)
            poses[n]={'im':im,'ax':round(headx(f)*K,1)}
    # 顔：ルーベルトの顔（256×256 のマス）と 同じ位置・同じ大きさに（体の高さと同じ はかり方で 6つの まん中の値）
    def bbox(a): op=a[...,3]>128; ys=np.where(op.sum(1)>0)[0]; xs=np.where(op.sum(0)>0)[0]; return xs[0],ys[0],xs[-1]+1,ys[-1]+1
    K=np.median([effh(RF[i])/effh(faces[i]) for i in range(6)]); fims=[]
    for i,f in enumerate(faces+[None]):
        if f is None:   # 7つ目：ふつうの顔＝キャラ選択の顔（heads_v316）。1つ目の顔と はば・上はし・横のまん中を そろえる（prep.py の ルーベルトと同じ）
            src=np.asarray(Image.open(os.path.join(D,'..','heads_v316',cid+'.png')).convert('RGBA')); x0,y0,x1,y1=bbox(src); f=src[y0:y1,x0:x1]
            a0=np.asarray(fims[0]); bx0,by0,bx1,by1=bbox(a0); k=(bx1-bx0)/float(f.shape[1])
            im=Image.fromarray(f,'RGBA').resize((max(1,round(f.shape[1]*k)),max(1,round(f.shape[0]*k))),Image.LANCZOS)
            cell=Image.new('RGBA',(256,256),(0,0,0,0)); cell.alpha_composite(im,(int(round((bx0+bx1)/2-im.width/2)),int(by0))); fims.append(cell); continue
        im=Image.fromarray(f,'RGBA').resize((max(1,round(f.shape[1]*K)),max(1,round(f.shape[0]*K))),Image.LANCZOS)
        ra=RF[i]; rx0,ry0,rx1,ry1=bbox(ra); rt=ry0+efftop(ra[ry0:ry1,:,3]>128); ct=efftop(np.asarray(im)[...,3]>128)
        cell=Image.new('RGBA',(256,256),(0,0,0,0)); x=int(round((rx0+rx1)/2-im.width/2)); y=int(rt-ct)
        tmp=Image.new('RGBA',(256+2*im.width,256+2*im.height),(0,0,0,0)); tmp.alpha_composite(im,(x+im.width,y+im.height)); cell=tmp.crop((im.width,im.height,im.width+256,im.height+256)); fims.append(cell)
    return poses,fims
def greenleft(im):   # 不透明なのに 背景の緑に近い 点の数（切りのこし）
    a=np.asarray(im).astype(int); op=a[...,3]>200; g=(a[...,1]>200)&(a[...,0]<90)&(a[...,2]<90); return int((op&g).sum())
LITE=['b_stand','b_ready','b_run0','b_run1','b_jump','b_slide']   # ★試作26 ライバル用（うしろ姿だけ）
def write_lite(cid):   # できた <ID>.js から ライバル用の 小さい <ID>_r.js を作る（絵は 同じ ものを そのまま）
    fn=os.path.join(ROOT,'test','ta3d_chars',cid+'.js'); t=open(fn,encoding='utf-8').read(); i=t.index(',',t.index('TA3D_CHAR('))+1
    o,_=json.JSONDecoder().raw_decode(t[i:]); lo={'poses':{k:o['poses'][k] for k in LITE}}
    out=os.path.join(ROOT,'test','ta3d_chars',cid+'_r.js')
    s2='/* MyHEROの大運動会 500m走：ライバルの '+NAMES.get(cid,cid)+'（うしろ姿だけ・'+cid+'.js から prep_char.py が作る。手で直さない） */\nTA3D_CHAR_R('+json.dumps(cid)+','+json.dumps(lo,separators=(',',':'))+');\n'
    open(out,'w',encoding='utf-8').write(s2); return out,len(s2.encode())
def write_js(cid,poses,fims):
    o={'poses':{n:{'d':b64(p['im']),'w':p['im'].width,'h':p['im'].height,'ax':p['ax']} for n,p in poses.items()},'face':[b64(f) for f in fims]}
    os.makedirs(os.path.join(ROOT,'test','ta3d_chars'),exist_ok=True); fn=os.path.join(ROOT,'test','ta3d_chars',cid+'.js')
    s='/* MyHEROの大運動会 500m走：'+NAMES.get(cid,cid)+' の絵（docs/assets_src/ta3d_chars/prep_char.py で作る。手で直さない） */\nTA3D_CHAR('+json.dumps(cid)+','+json.dumps(o,separators=(',',':'))+');\n'
    open(fn,'w',encoding='utf-8').write(s); return fn,len(s.encode())
def check(out,cid,poses,fims,RP,RF):   # ルーベルト（上の段）と このキャラ（下の段）を 同じ倍率で ならべる。白い線＝足の高さ
    order=['b_stand','b_punch','b_ready','b_run0','b_run1','b_jump','b_slide']+DIRS[0]+DIRS[1]
    R=[Image.fromarray(RP[n],'RGBA') for n in order]; Cc=[poses[n]['im'] for n in order]
    h1=max(i.height for i in R)+30; h2=max(i.height for i in Cc)+30; W=sum(max(a.width,b.width)+10 for a,b in zip(R,Cc))+10
    sheet=Image.new('RGBA',(max(W,7*132+10),h1+h2+280),(40,70,140,255)); dr=ImageDraw.Draw(sheet); x=8
    for a,b,n in zip(R,Cc,order):
        cw=max(a.width,b.width); sheet.alpha_composite(a,(x+(cw-a.width)//2,h1-a.height)); sheet.alpha_composite(b,(x+(cw-b.width)//2,h1+h2-b.height))
        dr.line((x,h1,x+cw,h1),fill=(255,255,255,140)); dr.line((x,h1+h2,x+cw,h1+h2),fill=(255,255,255,140)); dr.text((x+2,2),n,fill=(255,255,255,255)); x+=cw+10
    fx=8
    for i in range(7):
        sheet.alpha_composite(Image.fromarray(RF[i],'RGBA').resize((128,128)),(fx,h1+h2+8)); sheet.alpha_composite(fims[i].resize((128,128)),(fx,h1+h2+140)); fx+=132
    p=os.path.join(out,cid+'_check.png'); sheet.convert('RGB').save(p); return p
if __name__=='__main__':
    args=sys.argv[1:]; out=None
    if args and args[0]=='--lite':
        for cid in args[1:]: print(*write_lite(cid))
        sys.exit(0)
    if args and args[0]=='--check': out=args[1]; args=args[2:]
    RP,RF=rubert()
    for cid in args:
        print('--',cid,NAMES.get(cid)); poses,fims=build(cid,RP,RF)
        gl={n:greenleft(p['im']) for n,p in poses.items()}; gl.update({'face%d'%i:greenleft(f) for i,f in enumerate(fims)}); print('  緑の切りのこし（10点以上）:',{k:v for k,v in gl.items() if v>=10} or 'なし')
        if out: print(check(out,cid,poses,fims,RP,RF))
        else: print(*write_js(cid,poses,fims)); print(*write_lite(cid))
