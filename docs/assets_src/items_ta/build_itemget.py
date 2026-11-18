# アイテムゲット演出の試作ページ test/itemget.html を作る。使い方（リポジトリのいちばん上で）:
#   python3 docs/assets_src/items_ta/build_itemget.py
#   絵は ゲーム（game/my_hero.html の ITEM_SPR.sword.kohaku・ITEM_SPR.shield.medalshield）から そのまま持ってくる
import os, re
D=os.path.dirname(os.path.abspath(__file__))
t=open(os.path.join(D,'itemget.src.html'),encoding='utf-8').read(); g=open('game/my_hero.html',encoding='utf-8').read()
def grab(key):
    m=re.search(re.escape(key)+r"='data:image/webp;base64,([A-Za-z0-9+/=]+)'",g); assert m,key; return m.group(1)
for k,key in (('/*SWORD*/','ITEM_SPR.sword.kohaku'),('/*SHIELD*/','ITEM_SPR.shield.medalshield')):
    assert t.count(k)==1,k; t=t.replace(k,grab(key))
open('test/itemget.html','w',encoding='utf-8').write(t); print(len(t.encode()))
