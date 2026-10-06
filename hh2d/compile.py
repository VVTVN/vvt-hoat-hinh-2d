"""Gom nhiều tập (Short) thành một video dài.

Trong episodes/<video_dai>/episode.py:
    from hh2d.compile import gom
    TITLE = "10 câu hỏi khoa học..."
    SCENES = [canh_mo_dau...] + gom(__file__, ["trai_dat_ngung_quay", "bau_troi_mau_xanh", ...]) + [canh_ket...]

Mỗi tập được chèn thẻ "Câu hỏi số k" ở đầu; các cảnh outro=True (Đăng ký kênh) bị bỏ.
"""
import dataclasses
import os

from .scene import Actor, Cam, Scene


def _wrap(text, n=24):
    lines, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return "\n".join(lines)


def the_cau_hoi(k, title):
    """Thẻ mở đầu mỗi câu hỏi."""
    return Scene(
        say=f"Câu hỏi số {k}: {title}",
        captions=False,
        transition="zoom",
        fx=["twinkle", ("rays", dict(x=960, y=560, color=(26, 40, 82), speed=.35)), "sparkle"],
        cam=Cam(zoom=(1.0, 1.06), punch=[.9]),
        pad_after=.8,
        actors=[
            Actor("chu", 960, 250, enter="drop", idle="bob", sound="ding",
                  kw=dict(text=f"Câu hỏi #{k}", size=90, color=(255, 214, 80))),
            Actor("chu", 960, 580, enter="pop", enter_at=.9, enter_dur=.6, idle="pulse",
                  kw=dict(text=_wrap(title), size=120)),
            Actor("dau_hoi", 1680, 260, enter="pop", enter_at=.4, idle="wiggle", scale=.8),
            Actor("dau_hoi", 240, 820, enter="pop", enter_at=.6, idle="hop", scale=.6, flip=True),
        ],
    )


def _abs(v, ep_dir):
    if isinstance(v, str) and v.startswith("img:"):
        return os.path.join(ep_dir, "images", v[4:] + ".png")
    if isinstance(v, str) and (v.endswith(".png") or v.endswith(".jpg")) and not os.path.isabs(v):
        return os.path.join(ep_dir, v)
    return v


def gom(goc, ten_tap, danh_so=True, bat_dau=1):
    """goc: __file__ của episode.py video dài. ten_tap: tên thư mục các tập trong episodes/."""
    from .build import load_episode
    root = os.path.dirname(os.path.dirname(os.path.abspath(goc)))
    out = []
    for k, ten in enumerate(ten_tap, bat_dau):
        ep_dir = os.path.join(root, ten)
        ep = load_episode(ep_dir)
        if danh_so:
            out.append(the_cau_hoi(k, getattr(ep, "TITLE", ten)))
        first = True
        for sc in ep.SCENES:
            if sc.outro:
                continue
            actors = [dataclasses.replace(a, what=_abs(a.what, ep_dir)) for a in sc.actors]
            sc = dataclasses.replace(sc, actors=actors, bg=_abs(sc.bg, ep_dir))
            if first:
                sc = dataclasses.replace(sc, transition="whip")
                first = False
            out.append(sc)
    return out
