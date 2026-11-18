# ChatGPT に「2枚目」として添付する、キャラごとの見本（左＝顔・右＝うしろ姿の直立）を作る
#   使い方: python3 docs/assets_src/ta3d_chars/make_cards.py 出力フォルダ
#   顔は heads_v316/<id>.png、うしろ姿は このフォルダの <id>/back2_src.png のいちばん左（直立）を切り抜いて使う。
#   背景はどちらも明るい緑（#00FF00）にそろえる。文字は入れない（AI が絵に文字を描きこまないように）。
import sys, os
import numpy as np
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__)); H=os.path.join(D,'..','heads_v316')
IDS=[('men_1','baruto'),('men_2','zilvester'),('men_3','yurian'),('women_0','klara'),('women_1','elza'),('women_2','melty'),('women_3','brigitta')]
W,HH=1536,1024; GREEN=(0,255,0)
def stand(fn):   # back2_src の 1体目（直立）を、緑のすき間で切り分けて取り出す（prep.py と同じ考え方）
    a=np.asarray(Image.open(fn).convert('RGB')).astype(np.int16)
    gn=a[...,1]-np.maximum(a[...,0],a[...,2]); op=gn<60
    cols=op.sum(0)>2; x0=int(np.argmax(cols)); x1=x0
    while x1<len(cols) and cols[x1]: x1+=1
    rows=np.where(op[:,x0:x1].sum(1)>2)[0]; y0,y1=rows[0],rows[-1]+1
    return Image.open(fn).convert('RGB').crop((x0-6,y0-6,x1+6,y1+6))
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for i,(cid,nm) in enumerate(IDS):
    c=Image.new('RGB',(W,HH),GREEN)
    f=Image.open(os.path.join(H,cid+'.png')).convert('RGBA'); f.thumbnail((700,700),Image.LANCZOS)
    c.paste(f,(40+(700-f.width)//2,(HH-f.height)//2),f)
    b=stand(os.path.join(D,cid,'back2_src.png')); k=900.0/b.height; b=b.resize((round(b.width*k),900),Image.LANCZOS)
    c.paste(b,(1140-b.width//2,(HH-900)//2))
    p=os.path.join(out,'card%d_%s.png'%(i+1,nm)); c.save(p,optimize=True); print(p,os.path.getsize(p))
