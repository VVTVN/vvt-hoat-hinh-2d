"""Thư viện hình vẽ sẵn (không cần API ảnh). Mỗi hình vẽ quanh gốc (0,0) = tâm.

Thêm hình mới:
    @doodle(rong, cao)
    def ten_hinh(p, st, **kw): ...      # p: Pen, st: trạng thái (t, talk, blink...)
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .draw import INK, RED, WHITE, YELLOW, Pen, arc_pts, font

DOODLES = {}


def doodle(w, h):
    def deco(fn):
        DOODLES[fn.__name__] = (fn, w, h)
        return fn
    return deco


# ---------------------------------------------------------------- nhân vật chính
# Góc tay (rad, 0 = sang phải, pi/2 = chúi xuống) cho tay phải màn hình; tay trái lấy đối xứng.
POSES = {
    #          phải: (cánh tay, cẳng tay)   trái: (cánh tay, cẳng tay)
    "idle":   ((1.25, 1.55), (1.25, 1.55)),
    "point":  ((-0.30, -0.45), (1.25, 1.55)),
    "wave":   ((-0.85, -1.70), (1.25, 1.55)),
    "shock":  ((0.55, -2.05), (0.55, -2.05)),
    "shrug":  ((0.45, -0.55), (0.45, -0.55)),
    "fly":    ((-1.05, -1.35), (-1.05, -1.35)),
    "cheer":  ((-0.95, -1.25), (-0.95, -1.25)),
    "think":  ((1.25, 1.55), (0.75, -1.95)),
}


def _arm(p, side, upper, fore, coat=True):
    sx, sy = 44 * side, -78
    a1 = upper if side > 0 else math.pi - upper
    a2 = fore if side > 0 else math.pi - fore
    ex, ey = sx + 72 * math.cos(a1), sy + 72 * math.sin(a1)
    hx, hy = ex + 64 * math.cos(a2), ey + 64 * math.sin(a2)
    pts = [(sx, sy), (ex, ey), (hx, hy)]
    if coat:
        p.d.line([p.P(*q) for q in pts], fill=INK, width=p.W(25), joint="curve")
        p.d.line([p.P(*q) for q in pts], fill=WHITE, width=p.W(16), joint="curve")
    else:
        p.line(pts, INK, 7)
    p.circle(hx, hy, 15, fill=WHITE, w=4)
    return hx, hy


def _coat_poly(side):
    return [(30 * side, -112), (70 * side, -92), (86 * side, 92), (22 * side, 100)]


@doodle(600, 620)
def giao_su(p, st, pose="idle", face="smile", coat=(245, 245, 240), shirt=(120, 150, 190), **_):
    """Ông giáo sư người que áo blouse. pose: idle/point/wave/shock/shrug/fly/cheer/think."""
    t = st["t"]
    talk = st.get("talk", 0.0)
    # chân
    kick = math.sin(t * 14) * 0.5 if pose == "fly" else 0
    for side in (-1, 1):
        a = math.pi / 2 - side * (0.25 + (kick * side if pose == "fly" else 0))
        fx, fy = 12 * side + 125 * math.cos(a), 110 + 125 * math.sin(a)
        p.line([(12 * side, 110), (fx, fy)], INK, 7)
        p.circle(fx + 14 * side, fy + 4, 20, fill=INK, w=0, ry=10)
    # áo sơ mi caro
    shirt_poly = [(-38, -112), (38, -112), (34, 112), (-34, 112)]
    p.poly(shirt_poly, fill=shirt, outline=None)
    for i in range(-3, 4):
        p.d.line([p.P(i * 11, -110), p.P(i * 11, 110)], fill=tuple(int(c * .7) for c in shirt), width=p.W(3))
    for k in range(16):
        y = -100 + k * 14
        p.d.line([p.P(-36, y), p.P(36, y)], fill=(160, 80, 80), width=p.W(2))
    # tà áo blouse
    for side in (-1, 1):
        flap = _coat_poly(side)
        p.poly(flap, fill=coat, outline=None)
        p.hatch((min(x for x, _ in flap), -112, max(x for x, _ in flap), 100), (205, 210, 220),
                n=18, angle=1.2, length=18, w=2, mask=flap)
        p.line(flap, INK, 5, closed=True)
    # tay
    (ru, rf), (lu, lf) = POSES.get(pose, POSES["idle"])
    if pose == "wave":
        rf += math.sin(t * 9) * 0.55
    elif pose in ("cheer", "fly"):
        rf += math.sin(t * 10) * .3
        lf += math.sin(t * 10 + 1.5) * .3
    elif pose == "point":
        ru += math.sin(t * 4) * .05
    elif pose == "shock":
        ru += math.sin(t * 22) * .05
        lu += math.sin(t * 22 + 1) * .05
    _arm(p, 1, ru, rf)
    _arm(p, -1, lu, lf)
    # đầu
    hx, hy = 0, -172
    p.circle(hx, hy, 62, fill=WHITE, w=6)
    blink = st.get("blink", False)
    if face == "shock":
        for ex in (-22, 22):
            p.circle(ex, hy - 10, 13, fill=WHITE, w=4)
            p.dot(ex + math.sin(t * 20) * 2, hy - 10, 5)
        p.circle(0, hy + 28, 12 + 4 * talk, fill=INK, w=3, ry=17 + 6 * talk)
        p.line([(70, hy - 72), (78, hy - 44)], (120, 190, 255), 5)
        p.dot(80, hy - 36, 8, (120, 190, 255))
    else:
        for ex in (-19, 19):
            if blink:
                p.line([(ex - 8, hy - 6), (ex + 8, hy - 6)], INK, 4, amp=.3)
            else:
                p.dot(ex, hy - 8, 7)
        if talk > 0.08:
            h = 6 + 20 * talk
            p.circle(0, hy + 20, 14 + 3 * talk, fill=(120, 40, 50), w=4, ry=h / 2)
        elif face == "sad":
            p.line(arc_pts(0, hy + 36, 18, math.pi * 1.15, math.pi * 1.85), INK, 5, amp=.4)
        else:
            p.line(arc_pts(0, hy + 10, 24, .35, math.pi - .35), INK, 5, amp=.4)
        p.dot(-36, hy + 10, 9, (255, 170, 170))
        p.dot(36, hy + 10, 9, (255, 170, 170))


@doodle(130, 200)
def nguoi_nho(p, st, color=(240, 120, 90), **_):
    """Người que nhỏ (dân thường)."""
    t = st["t"]
    sw = math.sin(t * 8) * .3
    p.line([(0, -10), (0, 45)], INK, 6)
    p.line([(0, 45), (-22, 90)], INK, 6)
    p.line([(0, 45), (22, 90)], INK, 6)
    p.line([(0, 5), (-35, 35 + 20 * sw)], INK, 6)
    p.line([(0, 5), (35, 35 - 20 * sw)], INK, 6)
    p.poly([(-16, -5), (16, -5), (14, 45), (-14, 45)], fill=color, w=4)
    p.circle(0, -45, 32, fill=WHITE, w=5)
    p.dot(-10, -50, 4)
    p.dot(10, -50, 4)
    p.line(arc_pts(0, -45, 12, .4, math.pi - .4), INK, 3, amp=.2)


# ---------------------------------------------------------------- vũ trụ
_CONT = []
_r = random.Random(3)
for _k in range(6):
    _cx, _cy = _k * 1.05 + _r.uniform(-.2, .2), _r.uniform(-.55, .5)
    _CONT.append([(_cx + _r.uniform(.18, .32) * math.cos(2 * math.pi * i / 14) * 1.2,
                   _cy + _r.uniform(.18, .32) * math.sin(2 * math.pi * i / 14)) for i in range(14)])
_PERIOD = 6.3


def _earth_box(kw):
    r = kw.get("r", 250)
    return 2 * r + 60, 2 * r + 60


@doodle(_earth_box, None)
def trai_dat(p, st, r=250, spin=0.9, stop_at=None, face=None, **_):
    """Trái Đất tự quay. spin: tốc độ; stop_at: giây thì phanh gấp; face: None/'happy'/'scared'."""
    t = st["t"]
    if stop_at is not None and t > stop_at:
        rot = stop_at * spin + spin * 0.12 * (1 - math.exp(-(t - stop_at) * 8))
    else:
        rot = t * spin
    rot += st.get("seed_rot", 0)
    R = int(r * p.s)
    size = 2 * R + 8
    lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    q = Pen(lay, p.rng, p.s)
    q.circle(0, 0, r, fill=(60, 130, 210), w=0)
    q.hatch((-r, -r, r, r), (40, 95, 175), n=int(150), angle=.7, length=30, w=3)
    for pts in _CONT:
        P = [(((u - rot) % _PERIOD) - _PERIOD / 2, v) for u, v in pts]
        if max(x for x, _ in P) - min(x for x, _ in P) > 2:
            continue
        Q = [(r * math.sin(max(-1.5, min(1.5, x * .95))) * math.cos(y * .9), r * math.sin(y * 1.05)) for x, y in P]
        q.poly(Q, fill=(95, 175, 85), outline=(40, 90, 40), w=3, amp=1)
    shade = Image.new("L", lay.size, 0)
    sd = ImageDraw.Draw(shade)
    c = size / 2
    sd.ellipse([c - R, c - R, c + R, c + R], fill=95)
    sd.ellipse([c - R * 1.25, c - R * 1.2, c + R * .75, c + R * .8], fill=0)
    shade = shade.filter(ImageFilter.GaussianBlur(max(1, R * .12)))
    dark = Image.new("RGBA", lay.size, (10, 20, 60, 0))
    dark.putalpha(shade)
    lay = Image.alpha_composite(lay, dark)
    mask = Image.new("L", lay.size, 0)
    ImageDraw.Draw(mask).ellipse([c - R, c - R, c + R, c + R], fill=255)
    a = lay.getchannel("A")
    lay.putalpha(Image.fromarray(np.minimum(np.asarray(a), np.asarray(mask))))
    p.img.alpha_composite(lay, (int(p.cx - c), int(p.cy - c)))
    p.circle(0, 0, r, w=6)
    if face:
        k = r / 250
        if face == "scared":
            for ex in (-60, 60):
                p.circle(ex * k, -40 * k, 30 * k, fill=WHITE, w=4)
                p.dot(ex * k + math.sin(t * 25) * 3, -40 * k, 11 * k)
            p.circle(0, 55 * k, 26 * k, fill=INK, w=3, ry=34 * k)
        else:
            for ex in (-60, 60):
                if st.get("blink"):
                    p.line([(ex * k - 15 * k, -40 * k), (ex * k + 15 * k, -40 * k)], INK, 5)
                else:
                    p.dot(ex * k, -40 * k, 14 * k)
            p.line(arc_pts(0, 20 * k, 50 * k, .4, math.pi - .4), INK, 6, amp=.5)
            p.dot(-95 * k, 15 * k, 16 * k, (255, 150, 160))
            p.dot(95 * k, 15 * k, 16 * k, (255, 150, 160))


@doodle(260, 160)
def hanh_tinh(p, st, color=(170, 120, 200), ring=(240, 200, 120), **_):
    p.circle(0, 0, 50, fill=color, w=5)
    p.hatch((-50, -50, 50, 50), tuple(int(c * .8) for c in color), n=20, angle=-.5, length=20, w=3,
            mask=p.circle_pts(0, 0, 46, n=20, extra=0))
    p.line(arc_pts(0, 6, 100, -.15, math.pi + .15, ry=24), ring, 7, amp=.6)


@doodle(300, 300)
def mat_troi(p, st, **_):
    t = st["t"]
    for i in range(12):
        a = i * math.pi / 6 + t * .6
        r0, r1 = 92, 130 + 10 * math.sin(t * 6 + i)
        p.line([(r0 * math.cos(a), r0 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a))], (255, 190, 60), 9)
    p.circle(0, 0, 80, fill=(255, 210, 70), w=6)
    p.dot(-25, -10, 7)
    p.dot(25, -10, 7)
    p.line(arc_pts(0, 8, 28, .4, math.pi - .4), INK, 5, amp=.3)


@doodle(60, 60)
def sao(p, st, r=22, **_):
    k = 1 + .25 * math.sin(st["t"] * 5 + r)
    p.star4(0, 0, r * k)


# ---------------------------------------------------------------- đồ vật
@doodle(160, 160)
def nha(p, st, wall=(240, 210, 150), roof=RED, **_):
    p.poly([(-50, -5), (50, -5), (50, 60), (-50, 60)], fill=wall, w=4)
    p.poly([(-62, -5), (0, -60), (62, -5)], fill=roof, w=4)
    p.poly([(-12, 25), (12, 25), (12, 60), (-12, 60)], fill=(120, 80, 50), w=3)
    p.poly([(22, 10), (40, 10), (40, 28), (22, 28)], fill=(170, 220, 255), w=3)


@doodle(130, 190)
def cay(p, st, **_):
    p.line([(0, 0), (0, 80)], (110, 70, 40), 14)
    p.circle(0, -20, 48, fill=(80, 165, 80), w=5)
    p.circle(-28, 5, 30, fill=(80, 165, 80), w=4)
    p.circle(28, 5, 30, fill=(80, 165, 80), w=4)


@doodle(190, 120)
def o_to(p, st, color=(250, 200, 60), **_):
    body = [(-75, 20), (75, 20), (75, -12), (35, -15), (15, -48), (-40, -48), (-58, -15), (-75, -12)]
    p.poly(body, fill=color, w=4)
    p.poly([(-30, -40), (8, -40), (24, -16), (-46, -16)], fill=(170, 220, 255), w=3)
    for wx in (-40, 40):
        p.circle(wx, 22, 18, fill=INK, w=3)
        p.dot(wx, 22, 6, (200, 200, 200))


@doodle(200, 150)
def con_bo(p, st, **_):
    t = st["t"]
    p.circle(0, 0, 62, fill=WHITE, w=4, ry=38)
    p.dot(-20, -10, 15)
    p.dot(25, 8, 12)
    for lx in (-35, 35):
        a = math.sin(t * 12 + lx) * 8
        p.line([(lx, 32), (lx + a, 70)], INK, 6)
    p.circle(-70, -22, 26, fill=(255, 205, 205), w=4)
    p.dot(-78, -30, 4)
    p.line([(-62, -48), (-55, -62)], INK, 4)


@doodle(340, 160)
def may_bay(p, st, **_):
    body = [(-140, 0), (-100, -28), (110, -28), (150, 0), (110, 22), (-100, 22)]
    p.poly(body, fill=WHITE, w=5)
    p.poly([(-20, 0), (40, 0), (-10, 70), (-40, 70)], fill=(200, 210, 230), w=4)
    p.poly([(-120, -20), (-95, -20), (-130, -70), (-150, -70)], fill=(200, 210, 230), w=4)
    for i in range(6):
        p.circle(-50 + i * 28, -8, 8, fill=(170, 220, 255), w=2)
    p.line([(-160, -10), (-260, -10)], (230, 230, 255), 4, amp=1)
    p.line([(-160, 12), (-240, 12)], (230, 230, 255), 4, amp=1)


@doodle(240, 240)
def bien_stop(p, st, **_):
    r = 100
    pts = [(r * math.cos(math.pi / 8 + i * math.pi / 4), r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
    p.poly(pts, fill=RED, w=7)
    p.line([(.82 * x, .82 * y) for x, y in pts], WHITE, 4, closed=True, amp=.5)
    p.text(0, 4, "STOP", 64)


@doodle(420, 140)
def nut_dang_ky(p, st, **_):
    p.poly([(-180, -50), (180, -50), (180, 50), (-180, 50)], fill=(230, 40, 40), w=6)
    p.text(0, 0, "ĐĂNG KÝ", 62)


@doodle(700, 300)
def mui_ten_cong(p, st, color=YELLOW, **_):
    """Mũi tên vòng cung (chỉ chiều quay)."""
    pts = arc_pts(0, 120, 320, math.pi * 1.18, math.pi * 1.82, ry=200)
    p.line(pts, color, 9)
    (x1, y1), (x0, y0) = pts[-1], pts[-3]
    a = math.atan2(y1 - y0, x1 - x0)
    for da in (2.6, -2.6):
        p.line([(x1 + 40 * math.cos(a + da), y1 + 40 * math.sin(a + da)), (x1, y1)], color, 9)


@doodle(420, 120)
def mui_ten(p, st, color=YELLOW, **_):
    p.line([(-190, 0), (180, 0)], color, 9)
    p.line([(140, -35), (185, 0), (140, 35)], color, 9)


def _text_box(kw):
    f = font(kw.get("size", 90))
    lines = kw.get("text", "").split("\n")
    w = max(f.getlength(ln) for ln in lines)
    return w + kw.get("size", 90) * .6, kw.get("size", 90) * (1.25 * len(lines) + .4)


@doodle(_text_box, None)
def chu(p, st, text="", size=90, color=WHITE, stroke=INK, **_):
    """Chữ viết tay to (dùng cho số liệu, tiêu đề)."""
    lines = text.split("\n")
    lh = size * 1.25
    for i, ln in enumerate(lines):
        p.text(0, (i - (len(lines) - 1) / 2) * lh, ln, size, color, stroke, sw=max(3, size / 11))


@doodle(240, 240)
def dau_hoi(p, st, **_):
    p.circle(0, 0, 90, fill=WHITE, w=6)
    p.line([(-40, 85), (-70, 115), (-15, 92)], INK, 6)
    p.text(0, 4, "?", 130, (240, 90, 70))


@doodle(400, 280)
def vu_no(p, st, color=(255, 210, 80), **_):
    """Vụ nổ / tia sáng kiểu truyện tranh."""
    n = 14
    pts = []
    for i in range(2 * n):
        a = i * math.pi / n
        r = 180 if i % 2 == 0 else 105
        pts.append((r * math.cos(a), r * .7 * math.sin(a)))
    p.poly(pts, fill=color, w=6)


@doodle(300, 200)
def may(p, st, **_):
    for x, y, r in [(-60, 15, 55), (0, -15, 70), (65, 15, 55)]:
        p.circle(x, y, r, fill=WHITE, w=0)
    p.line(arc_pts(-60, 15, 55, math.pi * .55, math.pi * 1.45), INK, 5)
    p.line(arc_pts(0, -15, 70, math.pi * 1.1, math.pi * 1.9), INK, 5)
    p.line(arc_pts(65, 15, 55, -math.pi * .45, math.pi * .45), INK, 5)
    p.line([(-80, 68), (85, 68)], INK, 5)
