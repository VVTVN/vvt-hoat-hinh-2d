"""Dựng từng khung hình: nền -> hiệu ứng -> nhân vật -> camera -> chuyển cảnh -> phụ đề."""
import bisect
import math
import os
import random
import re

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .doodles import DOODLES
from .draw import INK, YELLOW, Pen, font
from .scene import WORLD_H, WORLD_W, actor_state, ease_in_out, ease_out_back, ease_out_cubic

TRANSITION = 0.35


# ---------------------------------------------------------------- nền
def _bg_vu_tru(seed=7):
    rng = random.Random(seed)
    img = Image.new("RGB", (WORLD_W, WORLD_H), (14, 22, 48))
    p = Pen(img, rng, 1, 0, 0)
    p.hatch((0, 0, WORLD_W, WORLD_H), (22, 34, 70), n=2200, angle=-.6, length=44, w=2)
    for _ in range(340):
        x, y, r = rng.uniform(0, WORLD_W), rng.uniform(0, WORLD_H), rng.choice([1, 1, 1.5, 2, 2.5])
        p.dot(x, y, r, (235, 235, 255))
    for _ in range(10):
        p.star4(rng.uniform(40, WORLD_W - 40), rng.uniform(40, WORLD_H - 240), rng.uniform(11, 20))
    return img


def _bg_giay(seed=7):
    rng = random.Random(seed)
    img = Image.new("RGB", (WORLD_W, WORLD_H), (247, 240, 224))
    p = Pen(img, rng, 1, 0, 0)
    p.hatch((0, 0, WORLD_W, WORLD_H), (236, 226, 205), n=1600, angle=-.6, length=44, w=2)
    return img


def _bg_troi(seed=7):
    rng = random.Random(seed)
    a = np.linspace(0, 1, WORLD_H)[:, None, None]
    top, bot = np.array([120, 190, 240]), np.array([205, 233, 250])
    arr = (top * (1 - a) + bot * a) * np.ones((1, WORLD_W, 1))
    img = Image.fromarray(arr.astype(np.uint8))
    p = Pen(img, rng, 1, 0, 0)
    p.hatch((0, 0, WORLD_W, 800), (150, 205, 240), n=900, angle=-.6, length=44, w=2)
    ground = [(-20, 860), (500, 830), (1100, 870), (1940, 840), (1940, 1100), (-20, 1100)]
    p.poly(ground, fill=(120, 190, 100), w=6)
    p.hatch((0, 840, WORLD_W, WORLD_H), (95, 160, 80), n=500, angle=-1.1, length=30, w=3, mask=ground)
    return img


def _bg_hoang_hon(seed=7):
    rng = random.Random(seed)
    a = np.linspace(0, 1, WORLD_H)[:, None]
    stops = [(0, (70, 55, 130)), (.45, (230, 110, 100)), (.75, (255, 170, 90)), (1, (255, 200, 120))]
    arr = np.zeros((WORLD_H, 3))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = ((a >= p0) & (a <= p1))[:, 0]
        k = ((a[m] - p0) / (p1 - p0))
        arr[m] = np.array(c0) * (1 - k) + np.array(c1) * k
    img = Image.fromarray((arr[:, None, :] * np.ones((1, WORLD_W, 1))).astype(np.uint8))
    p = Pen(img, rng, 1, 0, 0)
    p.hatch((0, 0, WORLD_W, 820), (255, 255, 255), n=300, angle=-.6, length=44, w=1)
    hills = [(-20, 900), (300, 820), (700, 880), (1150, 800), (1600, 870), (1940, 830), (1940, 1100), (-20, 1100)]
    p.poly(hills, fill=(70, 45, 80), w=6)
    return img


BACKGROUNDS = {"vu_tru": _bg_vu_tru, "giay": _bg_giay, "troi": _bg_troi, "hoang_hon": _bg_hoang_hon}


def _cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * s + .5), int(img.height * s + .5)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


# ---------------------------------------------------------------- hiệu ứng
def _fx_list(scene):
    out = []
    for f in scene.fx:
        out.append((f, {}) if isinstance(f, str) else (f[0], dict(f[1])))
    return out


def fx_behind(img, name, kw, t, rng):
    p = Pen(img, rng, 1, 0, 0)
    R = random.Random(kw.get("seed", 11))
    if name == "twinkle":
        for _ in range(kw.get("n", 28)):
            x, y, ph, w = R.uniform(0, WORLD_W), R.uniform(0, WORLD_H - 150), R.uniform(0, 6.3), R.uniform(2, 5)
            k = .5 + .5 * math.sin(t * w + ph)
            if k > .25:
                p.star4(x, y, 5 + 15 * k)
    elif name == "speed":
        d = -1 if kw.get("dir", "right") == "left" else 1
        col = kw.get("color", (225, 232, 255))
        for _ in range(kw.get("n", 34)):
            y, L, v, x0 = R.uniform(0, WORLD_H), R.uniform(160, 480), R.uniform(1800, 3200), R.uniform(0, 3000)
            x = (x0 + v * t) % (WORLD_W + 900) - 450
            if d < 0:
                x = WORLD_W - x
            p.d.line([(x, y), (x - d * L, y)], fill=col, width=R.choice([3, 4, 5]))
    elif name == "rays":
        cx, cy = kw.get("x", WORLD_W / 2), kw.get("y", WORLD_H / 2)
        col = kw.get("color", (36, 52, 96))
        n = kw.get("n", 14)
        for i in range(n):
            a0 = 2 * math.pi * i / n + t * kw.get("speed", .25)
            a1 = a0 + math.pi / n
            p.d.polygon([(cx, cy), (cx + 2600 * math.cos(a0), cy + 2600 * math.sin(a0)),
                         (cx + 2600 * math.cos(a1), cy + 2600 * math.sin(a1))], fill=col)


def fx_front(img, name, kw, t, rng):
    p = Pen(img, rng, 1, 0, 0)
    R = random.Random(kw.get("seed", 23))
    if name == "confetti":
        cols = [(255, 90, 80), (255, 210, 70), (90, 190, 255), (120, 220, 120), (230, 130, 255)]
        for _ in range(kw.get("n", 90)):
            x0, v, ph, c = R.uniform(0, WORLD_W), R.uniform(250, 520), R.uniform(0, 6.3), R.choice(cols)
            y = (R.uniform(-1200, 0) + v * t) % (WORLD_H + 200) - 100
            x = x0 + 40 * math.sin(t * 2 + ph)
            a = t * 5 + ph
            w, h = 16 * abs(math.cos(t * 4 + ph)) + 3, 10
            pts = [(x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a))
                   for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
            p.d.polygon(pts, fill=c)
    elif name == "sparkle":
        for _ in range(kw.get("n", 16)):
            x, y = R.uniform(kw.get("x0", 0), kw.get("x1", WORLD_W)), R.uniform(kw.get("y0", 0), kw.get("y1", WORLD_H))
            ph, per = R.uniform(0, 2), R.uniform(.8, 1.6)
            k = ((t + ph) % per) / per
            if k < .5:
                p.star4(x, y, 26 * math.sin(k * 2 * math.pi), (255, 255, 220))


# ---------------------------------------------------------------- phụ đề
def parse_words(say):
    words = []
    for i, part in enumerate(re.split(r"\*", say)):
        for k, w in enumerate(part.split()):
            # dấu câu đứng ngay sau *từ khoá* thì dính vào từ trước, không cách
            if k == 0 and words and not part[:1].isspace() and re.fullmatch(r"[,.!?…:;]+", w):
                words[-1] = (words[-1][0] + "\x00" + w, words[-1][1])
            else:
                words.append((w, i % 2 == 1))
    return words


def chunk_words(words, max_words=7):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if (len(cur) >= 4 and re.search(r"[,.!?…:;]$", w[0])) or len(cur) >= max_words:
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) <= 2 and len(chunks[-1]) + len(cur) <= max_words + 2:
            chunks[-1] += cur
        else:
            chunks.append(cur)
    return chunks


def draw_caption(img, words, age, size, y, maxw=None):
    k = .8 + .2 * ease_out_back(age / .18)
    words = [tuple(w.split("\x00")) + ((hl,) if "\x00" in w else ("", hl)) for w, hl in words]
    maxw = maxw or img.width * .92
    size *= k
    while True:
        f = font(size)
        space = f.getlength(" ")
        widths = [f.getlength(w + tail) for w, tail, _ in words]
        total = sum(widths) + space * (len(words) - 1)
        if total <= maxw or size < 20:
            break
        size *= .93
    d = ImageDraw.Draw(img)
    x = (img.width - total) / 2
    sw = max(2, int(size / 9))
    for (w, tail, hl), wd in zip(words, widths):
        d.text((x, y), w, font=f, fill=YELLOW if hl else (255, 255, 255), stroke_width=sw, stroke_fill=INK, anchor="ls")
        if tail:
            d.text((x + f.getlength(w), y), tail, font=f, fill=(255, 255, 255), stroke_width=sw, stroke_fill=INK,
                   anchor="ls")
        x += wd + space


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, ep_dir, scenes, timing, talk, captions, W=1920, H=1080, fps=30, short=False, title=""):
        self.ep_dir, self.scenes, self.timing = ep_dir, scenes, timing
        self.talk, self.captions = talk, captions
        self.W, self.H, self.fps = W, H, fps
        self.short, self.title = short, title
        if short:   # khung dọc: tiêu đề trên, khung phim giữa, phụ đề dưới
            u = W / 1080
            self.PW, self.PH = W, int(1000 * u)
            self.panel_y = int(430 * u)
            self.short_x = [self._short_focus(sc) for sc in scenes]
        else:
            self.PW, self.PH = W, H
        self.starts = [s for s, _ in timing]
        self.total = timing[-1][0] + timing[-1][1]
        self._bg, self._img = {}, {}
        rng = np.random.default_rng(1)
        g = rng.normal(0, 1, (H // 2, W // 2))
        grain = Image.fromarray(np.uint8(np.clip(244 + g * 6, 0, 255))).resize((W, H), Image.BILINEAR)
        self.grain = Image.merge("RGB", [grain] * 3)

    @staticmethod
    def _short_focus(sc):
        """Tâm khung dọc: short_x của cảnh, không thì giữa các vật nằm trong màn hình."""
        if sc.short_x is not None:
            return sc.short_x
        xs = [a.path[-1][1] if a.path else a.x for a in sc.actors]
        xs = [x for x in xs if 0 <= x <= WORLD_W]
        return (min(xs) + max(xs)) / 2 if xs else WORLD_W / 2

    # -- tài nguyên
    def _path(self, what):
        if what.startswith("img:"):
            return os.path.join(self.ep_dir, "images", what[4:] + ".png")
        return what if os.path.isabs(what) else os.path.join(self.ep_dir, what)

    def image(self, what):
        if what not in self._img:
            self._img[what] = Image.open(self._path(what)).convert("RGBA")
        return self._img[what]

    def background(self, bg):
        key = repr(bg)
        if key not in self._bg:
            if isinstance(bg, tuple):
                img = Image.new("RGB", (WORLD_W, WORLD_H), bg)
            elif bg in BACKGROUNDS:
                img = BACKGROUNDS[bg]()
            else:
                img = _cover(Image.open(self._path(bg)).convert("RGB"), WORLD_W, WORLD_H)
            self._bg[key] = img
        return self._bg[key]

    # -- nhân vật
    def sprite(self, a, st, sc, rng):
        if a.what in DOODLES:
            fn, w, h = DOODLES[a.what]
            if callable(w):
                w, h = w(a.kw)
            lay = Image.new("RGBA", (max(2, int(w * sc)), max(2, int(h * sc))), (0, 0, 0, 0))
            fn(Pen(lay, rng, sc), st, **a.kw)
            return lay
        src = self.image(a.what)
        base = (a.width / src.width) if a.width else 1.0
        s = base * sc
        return src.resize((max(2, int(src.width * s)), max(2, int(src.height * s))), Image.BICUBIC)

    def draw_actor(self, world, a, idx, si, t, dur, frame, talk):
        phase = idx * 1.37 + si * .71
        s = actor_state(a, t, dur, phase, talk if a.talk else 0)
        if s is None:
            return
        boil = (frame // 4) % 3
        rng = random.Random(si * 1000 + idx * 10 + boil)
        st = dict(t=t, age=t - (a.enter_at if a.enter else 0.0), talk=talk if a.talk else 0.0,
                  blink=((t + phase * 1.7) % 3.4) < .12)
        lay = self.sprite(a, st, s["scale"], rng)
        rot = s["rot"]
        if a.boil and a.what not in DOODLES:
            rot += rng.uniform(-.6, .6)
        if a.flip:
            lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
        if abs(s["sx"] - 1) > .003 or abs(s["sy"] - 1) > .003:
            lay = lay.resize((max(2, int(lay.width * s["sx"])), max(2, int(lay.height * s["sy"]))), Image.BILINEAR)
        if abs(rot) > .05:
            lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
        if s["alpha"] < .999:
            al = lay.getchannel("A").point(lambda v, k=s["alpha"]: int(v * k))
            lay.putalpha(al)
        world.paste(lay, (int(s["x"] - lay.width / 2), int(s["y"] - lay.height / 2)), lay)

    # -- một cảnh tại thời điểm t (giây trong cảnh) -> ảnh đầu ra W x H
    def scene_frame(self, si, t, frame):
        sc = self.scenes[si]
        start, dur = self.timing[si]
        world = self.background(sc.bg).copy()
        rng = random.Random(frame // 4 % 3)
        fxs = _fx_list(sc)
        for name, kw in fxs:
            fx_behind(world, name, kw, t, rng)
        gi = int((start + t) * self.fps)
        talk = float(self.talk[gi]) if 0 <= gi < len(self.talk) else 0.0
        for idx, a in enumerate(sc.actors):
            self.draw_actor(world, a, idx, si, t, dur, frame, talk)
        for name, kw in fxs:
            fx_front(world, name, kw, t, rng)
        # camera
        cam = sc.cam
        p = ease_in_out(t / max(dur, .01))
        z = cam.zoom[0] + (cam.zoom[1] - cam.zoom[0]) * p
        for tp in cam.punch:
            dt = t - tp
            if 0 <= dt < .5:
                z *= 1 + .12 * ease_out_cubic(dt / .08) * (1 - dt / .5) ** 2
        fx_, fy_ = cam.focus or (WORLD_W / 2, WORLD_H / 2)
        if self.short:
            fx_ = self.short_x[si]
        (px0, py0), (px1, py1) = cam.pan
        cx = fx_ + px0 + (px1 - px0) * p
        cy = fy_ + py0 + (py1 - py0) * p
        ch = WORLD_H / z
        cw = min(WORLD_W, ch * self.PW / self.PH) if self.short else WORLD_W / z
        for ts, sd, amp in cam.shake:
            dt = t - ts
            if 0 <= dt < sd:
                k = amp * (1 - dt / sd)
                cx += k * math.sin(dt * 53)
                cy += k * math.sin(dt * 47 + 1)
        cx = min(max(cx, cw / 2), WORLD_W - cw / 2) if (z >= 1 or self.short) else WORLD_W / 2
        cy = min(max(cy, ch / 2), WORLD_H - ch / 2) if z >= 1 else WORLD_H / 2
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        out = world.resize((self.PW, self.PH), Image.BICUBIC, box=box)
        if not self.short:
            out = ImageChops.multiply(out, self.grain)
        for name, kw in fxs:
            if name == "flash":
                dt = t - kw.get("t", 0)
                if 0 <= dt < .45:
                    out = Image.blend(out, Image.new("RGB", out.size, (255, 255, 255)), .85 * (1 - dt / .45))
        return out

    def frame(self, i):
        T = i / self.fps
        si = max(0, bisect.bisect_right(self.starts, T) - 1)
        start, dur = self.timing[si]
        lt = T - start
        img = self.scene_frame(si, lt, i)
        kind = self.scenes[si].transition
        if si > 0 and lt < TRANSITION and kind != "cut":
            prev = self.scene_frame(si - 1, self.timing[si - 1][1] + lt, i)
            p = ease_in_out(lt / TRANSITION)
            if kind == "fade":
                img = Image.blend(prev, img, p)
            elif kind == "zoom":
                z = 1 + .6 * p
                w, h = self.PW / z, self.PH / z
                prev = prev.resize((self.PW, self.PH), Image.BILINEAR,
                                   box=((self.PW - w) / 2, (self.PH - h) / 2, (self.PW + w) / 2, (self.PH + h) / 2))
                img = Image.blend(prev, img, p)
            else:  # whip
                both = Image.new("RGB", (self.PW * 2, self.PH))
                both.paste(prev, (0, 0))
                both.paste(img, (self.PW, 0))
                off = int(p * self.PW)
                arr = np.asarray(both.crop((off, 0, off + self.PW, self.PH)), np.float32)
                blur = int(70 * math.sin(p * math.pi))
                if blur > 2:
                    acc = np.zeros_like(arr)
                    ks = range(-blur, blur + 1, max(1, blur // 6))
                    for k in ks:
                        acc += np.roll(arr, k, axis=1)
                    arr = acc / len(ks)
                img = Image.fromarray(arr.astype(np.uint8))
        if self.short:
            img = self.compose_short(img, T)
            cap_size, cap_y = 84 * self.W / 1080, self.panel_y + self.PH + 200 * self.W / 1080
        else:
            cap_size, cap_y = 66 * self.H / 1080, self.H - 95 * self.H / 1080
        for c0, c1, words in self.captions:
            if c0 <= T < c1:
                draw_caption(img, words, T - c0, cap_size, cap_y)
                break
        return img.tobytes()

    def compose_short(self, panel, T):
        W, H, u = self.W, self.H, self.W / 1080
        back = _cover(panel.resize((self.PW // 6, self.PH // 6)), 180, 320).filter(ImageFilter.GaussianBlur(8))
        back = back.resize((W, H), Image.BILINEAR).point(lambda v: int(v * .45))
        back.paste(panel, (0, self.panel_y))
        d = ImageDraw.Draw(back)
        d.rectangle([-2, self.panel_y - int(6 * u), W + 2, self.panel_y + self.PH + int(6 * u)],
                    outline=(250, 250, 246), width=int(8 * u))
        # tiêu đề
        if self.title:
            size = 96 * u
            f = font(size)
            words, lines, cur = self.title.split(), [], ""
            for w in words:
                trial = (cur + " " + w).strip()
                if f.getlength(trial) > W * .88 and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = trial
            lines.append(cur)
            lh = size * 1.18
            y = self.panel_y / 2 - lh * (len(lines) - 1) / 2 + 8 * u * math.sin(T * 2.2)
            for k, ln in enumerate(lines):
                d.text((W / 2, y + k * lh), ln, font=f, fill=YELLOW, stroke_width=int(size / 10), stroke_fill=INK,
                       anchor="mm")
        return ImageChops.multiply(back, self.grain)
