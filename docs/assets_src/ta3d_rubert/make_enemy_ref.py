# AI に「まものと仲良く応援するヒーロー」を頼むときに添付する見本（enemy_ref.jpg）を作る。ゲームの絵には使わない
#   コースに出る4体（enemy_spr.json）＋ 観客のまもの7体（crowd.json の e）を、白い背景に 4列×3段で 大きく並べる
#   使い方: python3 docs/assets_src/ta3d_rubert/make_enemy_ref.py
import os, io, json, base64
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__))
spr=json.load(open(os.path.join(D,'enemy_spr.json'))); cr=json.load(open(os.path.join(D,'crowd.json')))['e']
ims=[Image.open(io.BytesIO(base64.b64decode(v))).convert('RGBA') for v in list(spr.values())+list(cr.values())]
CW,CH,H=420,380,300
sheet=Image.new('RGB',(CW*4,CH*3),(255,255,255))
for i,im in enumerate(ims):
    k=H/im.height; im=im.resize((max(1,round(im.width*k)),H),Image.LANCZOS)
    if im.width>CW-40: k=(CW-40)/im.width; im=im.resize((CW-40,round(im.height*k)),Image.LANCZOS)
    x=(i%4)*CW+(CW-im.width)//2; y=(i//4)*CH+(CH-im.height)//2; sheet.paste(im,(x,y),im)
sheet.save(os.path.join(D,'enemy_ref.jpg'),quality=90); print(len(ims), sheet.size)
