"""Dựng cả tập thành mp4.

    python -m hh2d.build episodes/trai_dat_ngung_quay
    python -m hh2d.build episodes/trai_dat_ngung_quay --res 1280x720 --scenes 2-4   # xem nhanh vài cảnh
    python -m hh2d.build episodes/trai_dat_ngung_quay --still 3.5 12                 # xuất ảnh tĩnh để soi
    python -m hh2d.build episodes/trai_dat_ngung_quay --tts espeak                   # ép engine giọng
"""
import argparse
import importlib.util
import multiprocessing as mp
import os
import subprocess
import sys
import time

import numpy as np

from . import audio
from .render import Renderer, chunk_words, parse_words

_R = None


def load_episode(ep_dir):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location("episode", os.path.join(ep_dir, "episode.py"))
    ep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ep)
    return ep


def _init(ep_dir, args):
    global _R
    ep = load_episode(ep_dir)   # đăng ký hình vẽ riêng của tập (nếu có) trong tiến trình con
    _R = Renderer(ep_dir, *args)


def _frame(i):
    return _R.frame(i)


def plan(ep_dir, scenes, fps, voice, engine):
    """Tạo giọng từng cảnh, tính thời lượng, phụ đề, độ mở miệng, âm thanh tổng."""
    cache = os.path.join(ep_dir, "cache", "voice")
    voices, used = [], set()
    for k, sc in enumerate(scenes, 1):
        path, name = audio.synth(sc.read or sc.say, cache, voice, engine)
        used.add(name)
        voices.append(audio.trim_silence(audio.read_wav(path)))
        print(f"  giọng cảnh {k:02d}: {len(voices[-1]) / audio.SR:5.2f}s ({name})", flush=True)
    timing, t = [], 0.0
    for sc, v in zip(scenes, voices):
        dur = max(sc.dur, sc.pad_before + len(v) / audio.SR + sc.pad_after)
        dur = round(dur * fps) / fps
        timing.append((t, dur))
        t += dur
    total = t
    print("  mốc cảnh: " + "  ".join(f"{k}:{s:.1f}s" for k, (s, _) in enumerate(timing, 1)) + f"  | tổng {t:.1f}s", flush=True)
    n_frames = int(round(total * fps))
    talk = np.zeros(n_frames + 2, np.float32)
    voice_track = np.zeros(int(total * audio.SR) + audio.SR, np.float32)
    fx_track = np.zeros_like(voice_track)
    captions = []
    for si, (sc, v, (start, dur)) in enumerate(zip(scenes, voices, timing)):
        v0 = start + sc.pad_before
        audio.add(voice_track, v, v0)
        env = audio.envelope(v, fps)
        f0 = int(round(v0 * fps))
        talk[f0:f0 + len(env)] = env[:max(0, len(talk) - f0)]
        if sc.captions:
            chunks = chunk_words(parse_words(sc.say))
            sizes = [sum(len(w) + 1 for w, _ in c) for c in chunks]
            vl = len(v) / audio.SR
            acc = 0
            for ci, c in enumerate(chunks):
                c0 = v0 + vl * acc / sum(sizes)
                acc += sizes[ci]
                c1 = v0 + vl * acc / sum(sizes) if ci < len(chunks) - 1 else start + dur
                captions.append((c0, c1, c))
        # hiệu ứng âm thanh tự động
        if si > 0 and sc.transition == "whip":
            audio.add(fx_track, audio.sfx_whoosh(.35), start, .5)
        for a in sc.actors:
            snd = a.sound
            if snd == "auto":
                snd = {"pop": "pop", "spin_in": "pop", "grow": "pop", "slide_left": "whoosh",
                       "slide_right": "whoosh", "drop": "whoosh", "rise": "whoosh"}.get(a.enter)
                if a.what == "chu" and a.enter:
                    snd = "ding"
            if snd and a.enter:
                audio.add(fx_track, audio.SFX[snd](), start + a.enter_at, .6)
        for f in sc.fx:
            if not isinstance(f, str) and f[0] == "flash":
                audio.add(fx_track, audio.sfx_boom(), start + f[1].get("t", 0), .9)
        for ts, name in sc.sfx:
            audio.add(fx_track, audio.SFX[name](), start + ts, .7)
    return timing, talk, captions, voice_track, fx_track, total, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--tts", default=None, help="korva | edge | espeak")
    ap.add_argument("--scenes", default=None, help="vd 2-4: chỉ dựng cảnh 2 đến 4")
    ap.add_argument("--still", nargs="*", type=float, help="xuất ảnh tĩnh tại các giây")
    ap.add_argument("--music", default=None)
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    ep_dir = os.path.abspath(args.episode)
    ep = load_episode(ep_dir)
    scenes = list(ep.SCENES)
    if args.scenes:
        a, _, b = args.scenes.partition("-")
        scenes = scenes[int(a) - 1:int(b or a)]
    W, H = map(int, args.res.lower().split("x"))
    fps = args.fps
    print(f"Tập: {getattr(ep, 'TITLE', os.path.basename(ep_dir))} | {len(scenes)} cảnh | {W}x{H}@{fps}", flush=True)

    timing, talk, captions, vtrack, fxtrack, total, used = plan(
        ep_dir, scenes, fps, getattr(ep, "VOICE", {}), args.tts)
    out_dir = os.path.join(ep_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    rargs = (scenes, timing, talk, captions, W, H, fps)

    if args.still:
        r = Renderer(ep_dir, *rargs)
        for s in args.still:
            i = int(s * fps)
            from PIL import Image
            Image.frombytes("RGB", (W, H), r.frame(i)).save(os.path.join(out_dir, f"still_{s:g}.png"))
            print("  ảnh:", os.path.join(out_dir, f"still_{s:g}.png"))
        return

    # âm thanh: giọng + hiệu ứng + nhạc nền (tự hạ khi có giọng)
    mix = vtrack + fxtrack
    music = args.music or getattr(ep, "MUSIC", None)
    if music:
        mpath = music if os.path.isabs(music) else os.path.join(ep_dir, music)
        m = audio.load_music(mpath, len(mix) / audio.SR)
        env = np.convolve(np.abs(vtrack), np.ones(audio.SR // 5) / (audio.SR // 5), "same")
        duck = 1 - .6 * np.clip(env * 12, 0, 1)
        mix += m[:len(mix)] * getattr(ep, "MUSIC_VOLUME", .14) * duck
    peak = np.max(np.abs(mix)) or 1
    mix = mix / max(1.0, peak / .95)
    wav = os.path.join(out_dir, "audio.wav")
    audio.write_wav(wav, mix[:int(total * audio.SR)])

    name = args.out or (os.path.basename(ep_dir) + ("" if not args.scenes else f"_canh{args.scenes}") + ".mp4")
    out = os.path.join(out_dir, name)
    n = int(round(total * fps))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.Pool(args.jobs, initializer=_init, initargs=(ep_dir, rargs)) as pool:
        for k, buf in enumerate(pool.imap(_frame, range(n), chunksize=4)):
            ff.stdin.write(buf)
            if k % (fps * 5) == 0:
                print(f"\r  dựng {k}/{n} khung ({time.time() - t0:.0f}s)", end="", flush=True)
    ff.stdin.close()
    ff.wait()
    print(f"\nXong: {out}  ({total:.1f}s, giọng: {', '.join(sorted(used))})")


if __name__ == "__main__":
    main()
