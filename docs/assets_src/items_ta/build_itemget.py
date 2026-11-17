# アイテムゲット演出の試作ページ test/itemget.html を作る。使い方（リポジトリのいちばん上で）:
#   python3 docs/assets_src/items_ta/prep_items_ta.py /tmp/ita && python3 docs/assets_src/items_ta/build_itemget.py /tmp/ita
import sys, os, base64
D=os.path.dirname(os.path.abspath(__file__)); W=sys.argv[1]
t=open(os.path.join(D,'itemget.src.html'),encoding='utf-8').read()
for k,f in (('/*SWORD*/','sword_kohaku.webp'),('/*SHIELD*/','shield_medal.webp')):
    assert t.count(k)==1,k; t=t.replace(k,base64.b64encode(open(os.path.join(W,f),'rb').read()).decode())
open('test/itemget.html','w',encoding='utf-8').write(t); print(len(t.encode()))
