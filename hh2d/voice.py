"""Tạo giọng KorvaTTS cho các tập và lưu vào giong/ (có trong repo) để máy khác dùng lại.

Chạy trên máy có KorvaTTS (máy Đại Ca):
    python -m hh2d.voice episodes/bau_troi_mau_xanh episodes/trai_dat_ngung_quay
    python -m hh2d.voice --all                 # mọi tập trong episodes/
rồi commit + push thư mục giong/.
"""
import argparse
import glob
import os
import subprocess

from . import audio
from .build import load_episode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tts", default="korva")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    eps = args.episodes or []
    if args.all:
        eps = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(root, "episodes", "*", "episode.py")))
    os.makedirs(audio.GIONG_DIR, exist_ok=True)
    made = 0
    for ep_dir in eps:
        ep_dir = os.path.abspath(ep_dir)
        ep = load_episode(ep_dir)
        voice = getattr(ep, "VOICE", {})
        for k, sc in enumerate(ep.SCENES, 1):
            text = sc.read or sc.say
            out = os.path.join(audio.GIONG_DIR, f"{args.tts}_{audio.voice_key(args.tts, voice, text)}.flac")
            if os.path.exists(out):
                continue
            wav, name = audio.synth(text, os.path.join(ep_dir, "cache", "voice"), voice, args.tts)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "flac", out], check=True)
            made += 1
            print(f"  {os.path.basename(ep_dir)} cảnh {k:02d}: {audio.clean_text(text)[:60]}", flush=True)
    print(f"Xong: {made} câu mới trong {audio.GIONG_DIR}")


if __name__ == "__main__":
    main()
