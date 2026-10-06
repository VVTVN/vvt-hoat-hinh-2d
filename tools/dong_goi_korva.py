"""Đóng gói thư mục assets KorvaTTS để đẩy lên GitHub (cắt file > 90MB thành nhiều phần).

    python tools/dong_goi_korva.py F:\\AI_WORK\\KORVATTS\\assets F:\\AI_WORK\\korva-assets
"""
import os
import shutil
import sys

PART = 90 * 1024 * 1024


def main(src, dst):
    for root, _, files in os.walk(src):
        for f in files:
            s = os.path.join(root, f)
            rel = os.path.relpath(s, src)
            d = os.path.join(dst, "assets", rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            size = os.path.getsize(s)
            if size <= PART:
                shutil.copy2(s, d)
                print("chép", rel)
                continue
            with open(s, "rb") as fi:
                k = 0
                while True:
                    buf = fi.read(PART)
                    if not buf:
                        break
                    with open(f"{d}.part{k:02d}", "wb") as fo:
                        fo.write(buf)
                    k += 1
            print(f"cắt {rel} -> {k} phần")
    with open(os.path.join(dst, "README.md"), "w", encoding="utf-8") as fo:
        fo.write("Model KorvaTTS (bản riêng, private) cho repo vvt-hoat-hinh-2d. "
                 "Ghép lại bằng tools/lap_korva.py.\n")
    print("Xong:", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
