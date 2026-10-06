"""Mô tả cảnh: Scene (một câu thoại) gồm nền, các Actor (nhân vật/đồ vật/chữ), hiệu ứng và camera.

Toạ độ thế giới luôn là 1920x1080 (dù xuất video độ phân giải nào).
"""
import math
from dataclasses import dataclass, field

WORLD_W, WORLD_H = 1920, 1080


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp(x)
    return x ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, k=1.9):
    x = clamp(x)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def ease_out_bounce(x):
    x = clamp(x)
    n, d = 7.5625, 2.75
    if x < 1 / d:
        return n * x * x
    if x < 2 / d:
        x -= 1.5 / d
        return n * x * x + .75
    if x < 2.5 / d:
        x -= 2.25 / d
        return n * x * x + .9375
    x -= 2.625 / d
    return n * x * x + .984375


# ---------------------------------------------------------------- models
@dataclass
class Actor:
    """Một vật trên cảnh.

    what  : tên hình vẽ sẵn ("giao_su", "trai_dat"...), "img:ten" (ảnh trong thư mục images/ của tập),
            hoặc đường dẫn .png.
    x, y  : vị trí tâm (khung 1920x1080).
    enter : cách xuất hiện  pop | slide_left | slide_right | drop | rise | fade | spin_in | grow | None
    exit  : cách biến mất    pop | slide_left | slide_right | fall | rise | fade | spin_out | None
    idle  : chuyển động liên tục, chuỗi cách nhau bằng dấu cách:
            bob float sway wiggle breathe pulse hop shake jelly
    path  : [(giây, x, y), ...] di chuyển mượt qua các điểm.
    move  : (vx, vy) px/giây, gravity: px/giây² (dùng cho đồ bay văng).
    spin  : độ/giây.   talk: nhân vật nhép miệng theo giọng.   kw: tham số riêng của hình vẽ.
    """
    what: str
    x: float = WORLD_W / 2
    y: float = WORLD_H / 2
    scale: float = 1.0
    rot: float = 0.0
    flip: bool = False
    enter: str | None = "pop"
    enter_at: float = 0.0
    enter_dur: float = 0.5
    exit: str | None = None
    exit_at: float | None = None      # âm = tính từ cuối cảnh
    exit_dur: float = 0.4
    idle: str = ""
    path: list = field(default_factory=list)
    move: tuple = (0.0, 0.0)
    gravity: float = 0.0
    spin: float = 0.0
    talk: bool = False
    width: float | None = None        # chỉ cho ảnh: rộng mong muốn (px)
    boil: bool = True                 # rung nét kiểu vẽ tay
    sound: str | None = "auto"        # tiếng khi xuất hiện: auto | pop | whoosh | ding | boom | None
    kw: dict = field(default_factory=dict)


@dataclass
class Cam:
    """Camera: zoom từ zoom[0] -> zoom[1], lia từ pan[0] -> pan[1] (lệch so với tâm, px).
    punch: [giây, ...] giật zoom nhanh vào nhịp nhấn.  shake: [(giây, thời_lượng, biên_độ), ...]
    focus: (x, y) tâm zoom (mặc định giữa màn hình)."""
    zoom: tuple = (1.0, 1.06)
    pan: tuple = ((0, 0), (0, 0))
    punch: list = field(default_factory=list)
    shake: list = field(default_factory=list)
    focus: tuple | None = None


@dataclass
class Scene:
    """Một cảnh = một câu thoại.

    say  : chữ phụ đề; bọc *từ khoá* để tô vàng.
    read : (tuỳ chọn) lời cho máy đọc nếu khác phụ đề (vd đọc số thành chữ).
    bg   : "vu_tru" | "giay" | "troi" | (r,g,b) | "img:ten" | đường dẫn ảnh.
    fx   : ["twinkle", "speed", "confetti", "sparkle", ("rays", {...}), ("flash", {"t": 1.2})]
    dur  : thời lượng tối thiểu (giây). Mặc định = độ dài giọng + đệm.
    transition: hiệu ứng chuyển VÀO cảnh này: fade | whip | zoom | cut
    """
    say: str
    actors: list = field(default_factory=list)
    bg: object = "vu_tru"
    fx: list = field(default_factory=list)
    cam: Cam = field(default_factory=Cam)
    read: str | None = None
    dur: float = 0.0
    pad_before: float = 0.25
    pad_after: float = 0.45
    transition: str = "whip"
    captions: bool = True
    sfx: list = field(default_factory=list)   # [(giây, "pop"|"whoosh"|"ding"|"boom"), ...]


# ---------------------------------------------------------------- actor animation
def _offscreen(kind, a):
    return {
        "slide_left": (-a.x - 400, 0), "slide_right": (WORLD_W - a.x + 400, 0),
        "drop": (0, -a.y - 400), "rise": (0, WORLD_H - a.y + 400),
        "fall": (0, WORLD_H - a.y + 500),
    }.get(kind, (0, 0))


def _path_pos(path, t):
    if t <= path[0][0]:
        return path[0][1], path[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(path, path[1:]):
        if t <= t1:
            e = ease_in_out((t - t0) / max(1e-6, t1 - t0))
            return x0 + (x1 - x0) * e, y0 + (y1 - y0) * e
    return path[-1][1], path[-1][2]


def actor_state(a, t, scene_dur, phase=0.0, talk=0.0):
    """Trả về dict x, y, scale, sx, sy, rot, alpha hoặc None nếu chưa/không hiện."""
    x, y = (_path_pos(a.path, t) if a.path else (a.x, a.y))
    sc, sx, sy, rot, alpha = a.scale, 1.0, 1.0, a.rot, 1.0
    if a.enter:
        if t < a.enter_at:
            return None
        e = (t - a.enter_at) / a.enter_dur
        if e < 1:
            k = a.enter
            if k == "pop":
                sc *= max(0.01, ease_out_back(e))
                sy *= 1 + .18 * math.sin(e * math.pi) * (1 - e)
                sx *= 1 - .10 * math.sin(e * math.pi) * (1 - e)
            elif k == "grow":
                sc *= max(0.01, ease_out_cubic(e))
            elif k == "fade":
                alpha = ease_out_cubic(e)
            elif k == "spin_in":
                sc *= max(0.01, ease_out_back(e, 1.2))
                rot += 360 * (1 - ease_out_cubic(e))
            elif k in ("slide_left", "slide_right", "drop", "rise"):
                ox, oy = _offscreen(k, a)
                ee = ease_out_bounce(e) if k == "drop" else ease_out_back(e, 1.1)
                x += ox * (1 - ee)
                y += oy * (1 - ee)
                if k in ("slide_left", "slide_right"):
                    rot += (8 if k == "slide_left" else -8) * math.sin(e * math.pi)
    if a.exit:
        ex = a.exit_at if a.exit_at is not None else -a.exit_dur
        if ex < 0:
            ex = scene_dur + ex
        if t >= ex:
            e = (t - ex) / a.exit_dur
            if e >= 1:
                return None
            k = a.exit
            if k == "pop":
                sc *= max(0.01, 1 - ease_in_cubic(e) + .15 * math.sin(e * math.pi))
            elif k == "fade":
                alpha *= 1 - e
            elif k == "spin_out":
                sc *= max(0.01, 1 - ease_in_cubic(e))
                rot -= 360 * ease_in_cubic(e)
            elif k in ("slide_left", "slide_right", "rise", "fall"):
                ox, oy = {"slide_left": (-a.x - 500, 0), "slide_right": (WORLD_W - a.x + 500, 0),
                          "rise": (0, -a.y - 500), "fall": (0, WORLD_H - a.y + 500)}[k]
                ee = ease_in_cubic(e)
                x += ox * ee
                y += oy * ee
    # chuyển động tự do
    t0 = max(0.0, t - (a.enter_at if a.enter else 0.0))
    x += a.move[0] * t0
    y += a.move[1] * t0 + .5 * a.gravity * t0 * t0
    rot += a.spin * t0
    for k in a.idle.split():
        if k == "bob":
            y += 10 * math.sin(2.4 * t + phase)
        elif k == "float":
            y += 20 * math.sin(1.4 * t + phase)
            rot += 2 * math.sin(1.1 * t + phase)
        elif k == "sway":
            rot += 4 * math.sin(1.9 * t + phase)
        elif k == "wiggle":
            rot += 6 * math.sin(10 * t + phase)
        elif k == "breathe":
            sy *= 1 + .025 * math.sin(3 * t + phase)
            sx *= 1 - .012 * math.sin(3 * t + phase)
        elif k == "pulse":
            sc *= 1 + .06 * math.sin(6 * t + phase)
        elif k == "hop":
            h = abs(math.sin(3.2 * t + phase))
            y -= 28 * h
            sy *= 1 + .06 * (h - .5)
        elif k == "shake":
            x += 6 * math.sin(41 * t + phase)
            y += 4 * math.sin(37 * t + phase * 2)
        elif k == "jelly":
            sx *= 1 + .05 * math.sin(7 * t + phase)
            sy *= 1 - .05 * math.sin(7 * t + phase)
    if a.talk and talk > 0:
        y -= 5 * talk
        sy *= 1 + .015 * talk
    return dict(x=x, y=y, scale=sc, sx=sx, sy=sy, rot=rot, alpha=alpha)
