"""Nét vẽ tay: đường rung, tô bút chì, chữ viết tay. Mọi hình đều vẽ qua Pen."""
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

INK = (25, 22, 30)
WHITE = (250, 250, 246)
YELLOW = (255, 214, 80)
RED = (225, 60, 50)

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "fonts", "PatrickHand-Regular.ttf")


@lru_cache(maxsize=64)
def font(size):
    return ImageFont.truetype(FONT_PATH, max(6, int(size)))


def jitter_path(pts, rng, amp=2.0, step=7.0):
    """Chia nhỏ đường rồi cộng nhiễu mượt -> nét run tay."""
    out = []
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        for i in range(n):
            t = i / n
            s += L / n
            out.append((x0 + (x1 - x0) * t + amp * (math.sin(s * .031 + ph[0]) + .5 * math.sin(s * .11 + ph[1])),
                        y0 + (y1 - y0) * t + amp * (math.sin(s * .027 + ph[2]) + .5 * math.sin(s * .13 + ph[3]))))
    out.append(pts[-1])
    return out


def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            inside = not inside
        j = i
    return inside


class Pen:
    """Vẽ theo toạ độ nội bộ (gốc = tâm layer), tự nhân tỉ lệ s."""

    def __init__(self, img, rng, s=1.0, cx=None, cy=None):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.rng = rng
        self.s = s
        self.cx = img.width / 2 if cx is None else cx
        self.cy = img.height / 2 if cy is None else cy

    def P(self, x, y):
        return (self.cx + x * self.s, self.cy + y * self.s)

    def W(self, w):
        return max(1, int(round(w * self.s)))

    def line(self, pts, color=INK, w=5, amp=2.0, closed=False):
        pts = [self.P(*p) for p in pts]
        if closed:
            pts = pts + [pts[0]]
        p = jitter_path(pts, self.rng, amp * min(1.5, self.s), 7 * max(.5, self.s))
        self.d.line(p, fill=color, width=self.W(w), joint="curve")
        if w >= 3:
            r = self.rng
            p2 = [(x + r.uniform(-.8, .8), y + r.uniform(-.8, .8)) for x, y in p]
            self.d.line(p2, fill=color, width=max(1, self.W(w) // 2))

    def poly(self, pts, fill=None, outline=INK, w=5, amp=1.5):
        if fill is not None:
            self.d.polygon([self.P(*p) for p in pts], fill=fill)
        if outline is not None and w:
            self.line(pts, outline, w, amp, closed=True)

    def circle_pts(self, x, y, r, ry=None, n=56, extra=.25):
        ry = r if ry is None else ry
        a0 = self.rng.uniform(0, 6.28)
        return [(x + r * math.cos(a0 + (2 * math.pi + extra) * i / n),
                 y + ry * math.sin(a0 + (2 * math.pi + extra) * i / n)) for i in range(n + 1)]

    def circle(self, x, y, r, fill=None, outline=INK, w=5, ry=None):
        ry = r if ry is None else ry
        if fill is not None:
            (x0, y0), (x1, y1) = self.P(x - r, y - ry), self.P(x + r, y + ry)
            self.d.ellipse([x0, y0, x1, y1], fill=fill)
        if outline is not None and w:
            self.line(self.circle_pts(x, y, r, ry), outline, w, amp=1.2)

    def dot(self, x, y, r, fill=INK):
        (x0, y0), (x1, y1) = self.P(x - r, y - r), self.P(x + r, y + r)
        self.d.ellipse([x0, y0, x1, y1], fill=fill)

    def hatch(self, box, color, n=40, angle=.8, length=24, w=2, mask=None):
        x0, y0, x1, y1 = box
        dx, dy = math.cos(angle) * length / 2, math.sin(angle) * length / 2
        for _ in range(n):
            x, y = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
            if mask is not None and not point_in_poly(x, y, mask):
                continue
            self.d.line([self.P(x - dx, y - dy), self.P(x + dx, y + dy)], fill=color, width=self.W(w))

    def text(self, x, y, s, size, fill=WHITE, stroke=INK, sw=None, anchor="mm"):
        f = font(size * self.s)
        sw = max(2, int(size * self.s / 12)) if sw is None else self.W(sw)
        self.d.text(self.P(x, y), s, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)

    def star4(self, x, y, r, fill=(255, 236, 160)):
        k = .22
        pts = [(x, y - r), (x + r * k, y - r * k), (x + r, y), (x + r * k, y + r * k),
               (x, y + r), (x - r * k, y + r * k), (x - r, y), (x - r * k, y - r * k)]
        self.poly(pts, fill, INK, 3, amp=.5)


def arc_pts(x, y, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(x + r * math.cos(a0 + (a1 - a0) * i / n), y + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
