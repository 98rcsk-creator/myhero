# 玉入れのポーズを ChatGPT に伝えるための「棒人間の見本」（絵として使うものではない）
#   使い方: python3 docs/assets_src/tamaire/make_pose_guide.py 出力.png
#   横3列×たて2段。どれも うしろ姿（キャラの右手＝画面の右）。うすい灰色の線は地面の高さの目安。
import sys
from PIL import Image, ImageDraw
C=512; W,H=C*3,C*2; GND=470
im=Image.new('RGB',(W,H),(255,255,255)); d=ImageDraw.Draw(im)
BODY=(150,150,150); HAIR=(105,105,105); RED=(220,30,40); ARW=(60,120,230)
def limb(ox,oy,pts,w=26):
    pts=[(ox+x,oy+y) for x,y in pts]
    d.line(pts,fill=BODY,width=w,joint='curve')
    for x,y in pts: d.ellipse((x-w/2,y-w/2,x+w/2,y+w/2),fill=BODY)
def fig(cx,cy,head,torso,arms,legs,ball=None,arrow=None,hand_open=None):
    ox,oy=cx*C,cy*C
    d.line((ox+30,oy+GND,ox+C-30,oy+GND),fill=(215,215,215),width=4)
    for l in legs: limb(ox,oy,l)
    (tx0,ty0,tx1,ty1)=torso; d.rounded_rectangle((ox+tx0,oy+ty0,ox+tx1,oy+ty1),radius=30,fill=BODY)
    for a in arms: limb(ox,oy,a,22)
    hx,hy,r=head; d.ellipse((ox+hx-r,oy+hy-r,ox+hx+r,oy+hy+r),fill=HAIR)
    if ball: bx,by=ball; d.ellipse((ox+bx-20,oy+by-20,ox+bx+20,oy+by+20),fill=RED)
    if hand_open:
        hx2,hy2=hand_open
        for dx in (-14,-5,4,13): d.line((ox+hx2,oy+hy2,ox+hx2+dx,oy+hy2-22),fill=BODY,width=7)
    if arrow:
        (ax0,ay0),(ax1,ay1)=arrow; d.line((ox+ax0,oy+ay0,ox+ax1,oy+ay1),fill=ARW,width=8)
        import math; a=math.atan2(ay1-ay0,ax1-ax0)
        for s in (2.6,-2.6): d.line((ox+ax1,oy+ay1,ox+ax1+28*math.cos(a+s),oy+ay1+28*math.sin(a+s)),fill=ARW,width=8)
# 1 かまえる：足を少し開いて立つ・右手の玉を右の腰の横にさげる
fig(0,0,(256,150,78),(212,228,300,335),
    [[(222,250),(200,295),(192,335)],[(290,250),(316,295),(322,335)]],
    [[(236,330),(226,400),(218,462)],[(276,330),(286,400),(294,462)]],ball=(326,352))
# 2 ためる：ひざを曲げてしずむ・右手（玉）を右うしろへ大きく引く
fig(1,0,(256,195,78),(212,272,300,370),
    [[(222,292),(196,325),(190,360)],[(290,292),(338,340),(362,392)]],
    [[(236,365),(200,410),(212,462)],[(276,365),(312,410),(300,462)]],ball=(368,410),arrow=((400,430),(420,470)))
# 3 投げる：つま先立ちでのびる・右手を頭より高く 奥へ ふり上げる（玉は もう はなしている）
fig(2,0,(250,140,78),(206,216,294,318),
    [[(216,238),(194,282),(188,320)],[(286,232),(318,170),(334,100)]],
    [[(232,314),(228,390),(232,450)],[(270,314),(276,390),(272,450)]],arrow=((350,80),(395,10)),hand_open=(336,92))
# 4 ひろう：かがんで右手で足元の玉をつかむ
fig(0,1,(240,250,78),(200,310,292,388),
    [[(212,330),(196,370),(196,405)],[(284,328),(318,392),(332,448)]],
    [[(220,382),(184,420),(204,462)],[(272,382),(308,420),(292,462)]],ball=(340,452))
# 5 かった：両手を高く上げてジャンプ（バンザイ）
fig(1,1,(256,120,78),(212,198,300,300),
    [[(222,218),(184,150),(168,86)],[(290,218),(328,150),(344,86)]],
    [[(236,296),(222,360),(214,415)],[(276,296),(290,360),(298,415)]])
# 6 まけた：肩を落として うつむく・両手はだらんと下
fig(2,1,(256,178,74),(214,252,298,345),
    [[(222,272),(212,325),(210,372)],[(290,272),(300,325),(302,372)]],
    [[(238,342),(236,400),(234,462)],[(274,342),(276,400),(278,462)]])
for x in (C,2*C): d.line((x,0,x,H),fill=(200,200,200),width=3)
d.line((0,C,W,C),fill=(200,200,200),width=3)
im.save(sys.argv[1],optimize=True)
