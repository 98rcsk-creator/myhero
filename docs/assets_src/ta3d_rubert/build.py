# test/ta3d.html を作る。使い方（リポジトリのいちばん上で）:
#   python3 docs/assets_src/ta3d_rubert/prep.py /tmp/art.json && python3 docs/assets_src/ta3d_rubert/build.py /tmp/art.json（Pillow が いる。★試作25 キャラのアイコンを作るため）
import json, os, sys
D=os.path.dirname(os.path.abspath(__file__))
t=open(os.path.join(D,'ta3d.src.html'),encoding='utf-8').read()
def rep(a,b):
    global t; assert t.count(a)==1,(t.count(a),a[:50]); t=t.replace(a,b)
rep('/*SPRD*/{}',json.dumps(json.load(open(os.path.join(D,'enemy_spr.json'))),separators=(',',':')))   # まもの4種類（ゲームの絵）
rep('/*CROWD*/null',json.dumps(json.load(open(os.path.join(D,'crowd.json'))),separators=(',',':')))   # 観客：コースに出ないまもの7種類＋ほかのヒーロー7人の顔
rep('/*ART*/null',json.dumps(json.load(open(sys.argv[1])),separators=(',',':')))
# ★試作22 ごほうびの剣・盾の絵は ゲーム（game/my_hero.html の ITEM_SPR）から そのまま持ってくる（同じ絵を2か所に置かない）
import re
g=open('game/my_hero.html',encoding='utf-8').read()
def grab(key):
    m=re.search(re.escape(key)+r"='(data:image/webp;base64,[A-Za-z0-9+/=]+)'",g); assert m,key; return m.group(1)
rep('/*ITEMS*/null',json.dumps({'kohaku':grab('ITEM_SPR.sword.kohaku'),'medalshield':grab('ITEM_SPR.shield.medalshield')},separators=(',',':')))
m=open('test/bgm_home.html',encoding='utf-8').read(); a=m.index('// ==== MUS:BEGIN'); b=m.index('// ==== MUS:END ====')
rep('/*MUS*/','// ゲームと同じ音楽エンジン（test/bgm_home.html の MUS:BEGIN〜MUS:END を そのまま入れている）\n'+m[a:b]+'// ==== MUS:END ====')
# ★試作25 キャラを えらぶ アイコン（キャラ選択の顔 heads_v316 を 76px に）と、ほかの7人の絵のファイル（test/ta3d_chars/<ID>.js）の 版（中身が かわったら 読みなおすように）
import hashlib, io, base64
from PIL import Image
ic={}
for cid in ['men_0','men_1','men_2','men_3','women_0','women_1','women_2','women_3']:
    im=Image.open(os.path.join(D,'..','heads_v316',cid+'.png')).convert('RGBA'); bb=im.getbbox(); im=im.crop(bb); s2=max(im.size); sq=Image.new('RGBA',(s2,s2),(0,0,0,0)); sq.paste(im,((s2-im.width)//2,(s2-im.height)//2)); sq=sq.resize((76,76),Image.LANCZOS)
    bio=io.BytesIO(); sq.save(bio,'WEBP',quality=82,method=6); ic[cid]=base64.b64encode(bio.getvalue()).decode()
rep('/*CHICON*/{}',json.dumps(ic,separators=(',',':')))
ver={}
for f in sorted(os.listdir('test/ta3d_chars')) if os.path.isdir('test/ta3d_chars') else []:
    if f.endswith('.js'): ver[f[:-3]]=hashlib.sha1(open(os.path.join('test/ta3d_chars',f),'rb').read()).hexdigest()[:8]
rep('/*CHVER*/{}',json.dumps(ver,separators=(',',':')))
open('test/ta3d.html','w',encoding='utf-8').write(t); print(len(t.encode()))
