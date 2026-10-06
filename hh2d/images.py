"""Ảnh AI cho tập phim + tách nền trắng thành PNG trong suốt.

Cách FREE (khuyên dùng): tự tạo ảnh trên Gemini/Bing (web, miễn phí) theo prompt trong episode.py,
lưu vào episodes/<tap>/images/<ten>.png rồi tách nền:
    python -m hh2d.images --cutout episodes/<tap>/images/giao_su_vay.png

Cách tự động (cần GEMINI_API_KEY, gói free của API có thể bị giới hạn/không có tạo ảnh):
    python -m hh2d.images episodes/<tap>              # tạo mọi ảnh trong IMAGES còn thiếu
    python -m hh2d.images episodes/<tap> nen_lab -f   # tạo lại một ảnh

Trong episode.py:
    STYLE = "hand-drawn doodle, colored pencil texture, thick black outlines, cute, simple"
    CHARACTER = "images/nhan_vat.png"          # ảnh gốc nhân vật để giữ đồng nhất (tuỳ chọn)
    IMAGES = {
        "nen_lab":      dict(prompt="a cozy science lab", kind="bg"),
        "giao_su_vay":  dict(prompt="the character waving hello", kind="cutout", ref=True),
    }
Dùng trong cảnh: Actor("img:giao_su_vay", 500, 600, width=420)   |   Scene(bg="img:nen_lab", ...)
"""
import argparse
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MODEL = os.environ.get("HH2D_IMAGE_MODEL", "gemini-2.5-flash-image")


def remove_white_bg(img, tol=30, feather=1.2):
    """Xoá nền trắng/sáng nối liền với mép ảnh (giữ phần trắng bên trong nét viền đen)."""
    img = img.convert("RGBA")
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    light = (rgb.min(axis=2) > 255 - tol * 2) & ((rgb.max(axis=2) - rgb.min(axis=2)) < tol)
    m = Image.fromarray(np.uint8(light) * 255).copy()   # copy: ảnh từ numpy là chỉ-đọc
    w, h = m.size
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
             [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    px = m.load()
    for xy in border:
        if px[xy] == 255:
            ImageDraw.floodfill(m, xy, 128, thresh=0)
    bg = np.asarray(m) == 128
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    a = Image.fromarray(alpha)
    if feather:
        a = a.filter(ImageFilter.GaussianBlur(feather))
        a = Image.fromarray(np.minimum(np.asarray(a).astype(np.int16) * 2, 255).astype(np.uint8))
    out = img.copy()
    out.putalpha(a)
    box = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return out.crop(box) if box else out


def generate(prompt, refs=(), aspect=None):
    from google import genai
    from google.genai import types
    client = genai.Client()   # đọc GEMINI_API_KEY
    contents = [prompt] + [Image.open(r) for r in refs]
    try:
        cfg = types.GenerateContentConfig(response_modalities=["IMAGE"],
                                          image_config=types.ImageConfig(aspect_ratio=aspect) if aspect else None)
    except (TypeError, AttributeError):
        cfg = types.GenerateContentConfig(response_modalities=["IMAGE"])
    resp = client.models.generate_content(model=MODEL, contents=contents, config=cfg)
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return Image.open(io.BytesIO(part.inline_data.data))
    raise RuntimeError("API không trả về ảnh: " + str(resp.text if hasattr(resp, "text") else resp)[:300])


def build_prompt(spec, style):
    p = spec["prompt"]
    if spec.get("ref"):
        p = "Same character as in the reference image, same face, outfit and drawing style. " + p
    if spec.get("kind") == "cutout":
        p += ". Full body, centered, isolated on a plain pure white background, no shadow, no ground, no text."
    else:
        p += ". Wide 16:9 background scene, no characters, no text, leave empty space in the middle."
    return f"{p} Style: {style}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?")
    ap.add_argument("names", nargs="*")
    ap.add_argument("-f", "--force", action="store_true")
    ap.add_argument("--cutout", nargs="+", help="tách nền trắng các file ảnh (ghi đè thành PNG)")
    args = ap.parse_args()

    if args.cutout:
        for f in args.cutout:
            out = os.path.splitext(f)[0] + ".png"
            remove_white_bg(Image.open(f)).save(out)
            print("tách nền:", out)
        return
    if not args.episode:
        ap.error("cần thư mục tập hoặc --cutout")
    from .build import load_episode
    ep_dir = os.path.abspath(args.episode)
    ep = load_episode(ep_dir)
    style = getattr(ep, "STYLE", "hand-drawn doodle, colored pencil texture, thick black outlines, cute and simple")
    char = getattr(ep, "CHARACTER", None)
    char = os.path.join(ep_dir, char) if char else None
    os.makedirs(os.path.join(ep_dir, "images"), exist_ok=True)
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        sys.exit("Thiếu GEMINI_API_KEY. Lấy free ở https://aistudio.google.com/apikey rồi: set GEMINI_API_KEY=...")
    for name, spec in getattr(ep, "IMAGES", {}).items():
        if args.names and name not in args.names:
            continue
        out = os.path.join(ep_dir, "images", name + ".png")
        if os.path.exists(out) and not args.force:
            continue
        refs = [char] if spec.get("ref") and char and os.path.exists(char) else []
        print("tạo ảnh:", name, flush=True)
        img = generate(build_prompt(spec, style), refs, None if spec.get("kind") == "cutout" else "16:9")
        if spec.get("kind") == "cutout":
            img = remove_white_bg(img)
        img.save(out)


if __name__ == "__main__":
    main()
