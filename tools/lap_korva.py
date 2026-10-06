"""Ghép lại assets KorvaTTS từ repo korva-assets (đã đóng gói bằng dong_goi_korva.py).

    python tools/lap_korva.py ../korva-assets ~/.cache/hh2d/korva
"""
import os
import re
import shutil
import sys


def lap(src, dst):
    src = os.path.join(src, "assets")
    parts = {}
    for root, _, files in os.walk(src):
        for f in files:
            s = os.path.join(root, f)
            rel = os.path.relpath(s, src)
            m = re.match(r"(.*)\.part(\d\d)$", rel)
            if m:
                parts.setdefault(m.group(1), []).append(s)
                continue
            d = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
    for rel, ps in parts.items():
        d = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        with open(d, "wb") as fo:
            for p in sorted(ps):
                with open(p, "rb") as fi:
                    shutil.copyfileobj(fi, fo)
    return dst


if __name__ == "__main__":
    print("Xong:", lap(os.path.expanduser(sys.argv[1]), os.path.expanduser(sys.argv[2])))
