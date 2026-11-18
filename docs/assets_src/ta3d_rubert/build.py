# test/ta3d.html を作る。使い方（リポジトリのいちばん上で）:
#   python3 docs/assets_src/ta3d_rubert/prep.py /tmp/art.json && python3 docs/assets_src/ta3d_rubert/build.py /tmp/art.json
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
open('test/ta3d.html','w',encoding='utf-8').write(t); print(len(t.encode()))
