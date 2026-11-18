# test/tamaire.html（大運動会「玉入れ」の試作）を作る。使い方（リポジトリのいちばん上で）:
#   python3 docs/assets_src/tamaire/build.py
# 絵は ほかのページから そのまま持ってくる（同じ絵を2か所に置かない）：
#   主人公＝test/ta3d.html の ART（ルーベルトの仮のポーズ4つ）／まわりの子＝ta3d_rubert/crowd.json の観客のヒーロー（赤組4人・白組4人）
import json, os
D=os.path.dirname(os.path.abspath(__file__))
t=open(os.path.join(D,'tamaire.src.html'),encoding='utf-8').read()
def rep(a,b):
    global t; assert t.count(a)==1,(t.count(a),a[:50]); t=t.replace(a,b)
s=open('test/ta3d.html',encoding='utf-8').read(); i=s.index('var ART=')+len('var ART=')
art,_=json.JSONDecoder().raw_decode(s[i:])
rep('/*ART*/null',json.dumps({k:art['poses'][k] for k in ['b_stand','b_ready','b_punch','b_jump']},separators=(',',':')))
hb=json.load(open(os.path.join(D,'..','ta3d_rubert','crowd.json')))['hb']
RED=[3,5,10,0]; WHITE=[4,7,11,2]   # 赤組＝赤・オレンジの服の子／白組＝白い旗・白っぽい服の子
rep('/*CROWD*/null',json.dumps(['data:image/webp;base64,'+hb[i] for i in RED+WHITE],separators=(',',':')))
m=open('test/bgm_home.html',encoding='utf-8').read(); a=m.index('// ==== MUS:BEGIN'); b=m.index('// ==== MUS:END ====')
rep('/*MUS*/','// ゲームと同じ音楽エンジン（test/bgm_home.html の MUS:BEGIN〜MUS:END を そのまま入れている）\n'+m[a:b]+'// ==== MUS:END ====')
open('test/tamaire.html','w',encoding='utf-8').write(t); print(len(t.encode()))
