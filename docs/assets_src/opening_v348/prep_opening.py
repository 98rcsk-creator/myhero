# v348 オープニングの絵（ユーザーが作った 941x1672 の1枚絵）を、ゲームに埋め込む WebP にする
#   使い方: python3 docs/assets_src/opening_v348/prep_opening.py docs/assets_src/opening_v348/opening_src.png 出力.webp
#   品質78：70=249KB／78=292KB／84=361KB／90=467KB を比べて決めた（画面には 1170px 幅＝約1.24倍に広げて出る）
#   動きは絵に入れない。本体の OPN_R（キャラごとの領域とゆれ）で、絵を網目にして少しずつ伸び縮みさせる
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); assert im.size == (941, 1672), im.size
im.save(sys.argv[2], 'WEBP', quality=78, method=6)
