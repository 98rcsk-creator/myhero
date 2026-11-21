# ChatGPT に「1枚目」として添付する、ルーベルトの4枚（①走る・ジャンプ ②スライディング ③向き8つ ④ワイプの顔）を 田の字に並べた1枚の絵を作る
#   使い方: python3 docs/assets_src/ta3d_chars/make_ref4.py 出力.png
#   2026-11-19 ユーザー：1回に4枚ぶん まとめて頼むと ちゃんと できる（ユリアン）。1枚ずつだと何日もかかる。
#   ユリアンで いちばん きれいに できたのは「白い線で 田の字に分かれた1枚」だったので、その形の見本を ルーベルトで作って渡す（同じ形で 返ってくるので 切り分けやすい）
import sys, os
import numpy as np
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__)); R=os.path.join(D,'..','ta3d_rubert')
W,H,L=2048,1024,8; GREEN=(0,255,0); out=Image.new('RGB',(W,H),(255,255,255))
qw,qh=(W-L)//2,(H-L)//2
for k,fn in enumerate(['back_src.png','slide_src.png','dirs_src.png','faces_src.png']):   # 左上・右上・左下・右下
    x0=(k%2)*(qw+L); y0=(k//2)*(qh+L); q=Image.new('RGB',(qw,qh),GREEN)
    im=Image.open(os.path.join(R,fn)).convert('RGB'); a=np.asarray(im).astype(int); fg=(a[...,1]-np.maximum(a[...,0],a[...,2]))<60   # 緑の よけいな ふちを 切って、絵を 大きく入れる
    ys=np.where(fg.sum(1)>2)[0]; xs=np.where(fg.sum(0)>2)[0]; m=24; im=im.crop((max(0,xs[0]-m),max(0,ys[0]-m),min(im.width,xs[-1]+m),min(im.height,ys[-1]+m))); s=min(qw/im.width,qh/im.height); im=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
    q.paste(im,((qw-im.width)//2,(qh-im.height)//2)); out.paste(q,(x0,y0))
out.save(sys.argv[1],optimize=True); print(sys.argv[1],out.size,os.path.getsize(sys.argv[1]))
