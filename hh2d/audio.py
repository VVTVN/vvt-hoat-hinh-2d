"""Giọng đọc (KorvaTTS -> edge-tts -> espeak-ng), hiệu ứng âm thanh tự tổng hợp, trộn tiếng."""
import hashlib
import os
import re
import shutil
import subprocess
import wave

import numpy as np

SR = 44100

# KorvaTTS giống repo vvt-tin-tuc: máy Đại Ca để ở F:\AI_WORK\KORVATTS
KORVA_LOCAL_EXE = r"F:\AI_WORK\KORVATTS\.venv\Scripts\korvatts.exe"
KORVA_LOCAL_ASSETS = r"F:\AI_WORK\KORVATTS\assets"


def clean_text(s):
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def _korva_exe():
    exe = os.environ.get("KORVATTS_EXE") or (KORVA_LOCAL_EXE if os.path.exists(KORVA_LOCAL_EXE) else "korvatts")
    return exe if (os.path.exists(exe) or shutil.which(exe)) else None


def _tts_korva(text, out, voice):
    exe = _korva_exe()
    if not exe:
        raise RuntimeError("không thấy korvatts")
    assets = os.environ.get("KORVATTS_ASSETS") or (KORVA_LOCAL_ASSETS if os.path.exists(KORVA_LOCAL_ASSETS) else "")
    cmd = [exe, "synth"] + (["--assets-dir", assets] if assets else []) + [
        "-v", voice.get("voice", "thanh_phong"), "-l", "vi", "--speed", str(voice.get("speed", 1.4)),
        "--steps", str(voice.get("steps", 32)), "-o", out, text]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError("korvatts lỗi: " + (r.stderr or r.stdout)[-400:])


def _tts_edge(text, out, voice):
    import asyncio
    import edge_tts
    v = voice.get("edge_voice", "vi-VN-NamMinhNeural")
    rate = voice.get("edge_rate", "+8%")
    mp3 = out + ".mp3"
    asyncio.run(edge_tts.Communicate(text, v, rate=rate).save(mp3))
    _to_wav(mp3, out)
    os.remove(mp3)


def _tts_espeak(text, out, voice):
    if not shutil.which("espeak-ng"):
        raise RuntimeError("không có espeak-ng")
    subprocess.run(["espeak-ng", "-v", "vi", "-s", "165", "-p", "45", "-w", out, text], check=True)


ENGINES = {"korva": _tts_korva, "edge": _tts_edge, "espeak": _tts_espeak}


def _to_wav(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR),
                    "-sample_fmt", "s16", dst], check=True)


def synth(text, cache_dir, voice=None, engine=None):
    """Tạo giọng (có cache). Trả về (đường_dẫn_wav, tên_engine)."""
    voice = voice or {}
    text = clean_text(text)
    order = [engine] if engine else (os.environ.get("HH2D_TTS", "").split(",") if os.environ.get("HH2D_TTS")
                                      else ["korva", "edge", "espeak"])
    os.makedirs(cache_dir, exist_ok=True)
    errors = []
    for name in order:
        key = hashlib.sha1(f"{name}|{sorted(voice.items())}|{text}".encode()).hexdigest()[:16]
        final = os.path.join(cache_dir, f"{name}_{key}.wav")
        if os.path.exists(final):
            return final, name
        raw = final + ".raw.wav"
        try:
            ENGINES[name](text, raw, voice)
            _to_wav(raw, final)
            os.remove(raw)
            return final, name
        except Exception as e:  # thử engine kế tiếp
            errors.append(f"{name}: {e}")
            if os.path.exists(raw):
                os.remove(raw)
    raise RuntimeError("Không tạo được giọng:\n  " + "\n  ".join(errors))


def read_wav(path):
    with wave.open(path) as w:
        n = w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() > 1:
            data = data.reshape(-1, w.getnchannels()).mean(axis=1)
        if w.getframerate() != SR:
            raise ValueError(f"{path}: cần {SR} Hz")
    return data


def write_wav(path, data):
    data = np.clip(data, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())


def trim_silence(x, thr=0.01):
    idx = np.nonzero(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(.03 * SR)), min(len(x), idx[-1] + int(.08 * SR))
    return x[a:b]


def envelope(x, fps):
    """Độ mở miệng 0..1 theo từng khung hình."""
    hop = SR // fps
    n = len(x) // hop + 1
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    ref = np.percentile(rms[rms > 1e-3], 90) if np.any(rms > 1e-3) else 1
    env = np.clip(rms / (ref + 1e-9), 0, 1)
    # nhép miệng có nhịp: nhân thêm dao động âm tiết
    return np.convolve(env, [.25, .5, .25], mode="same")


# ---------------------------------------------------------------- hiệu ứng âm thanh
def _t(d):
    return np.arange(int(d * SR)) / SR


def sfx_pop():
    t = _t(.12)
    f = 500 + 1800 * t / .12
    return .35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)


def sfx_whoosh(d=.45):
    rng = np.random.default_rng(1)
    n = rng.normal(0, 1, len(_t(d)))
    k = np.ones(30) / 30
    n = np.convolve(n, k, "same") - np.convolve(n, np.ones(200) / 200, "same")
    t = _t(d)
    env = np.sin(np.pi * t / d) ** 2
    return .5 * n * env


def sfx_boom():
    t = _t(.9)
    rng = np.random.default_rng(2)
    low = np.sin(2 * np.pi * (70 - 30 * t) * t) * np.exp(-t * 5)
    noise = np.convolve(rng.normal(0, 1, len(t)), np.ones(60) / 60, "same") * np.exp(-t * 7)
    return .6 * low + .5 * noise


def sfx_ding():
    t = _t(.6)
    return .22 * (np.sin(2 * np.pi * 1320 * t) + .5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 6)


SFX = {"pop": sfx_pop, "whoosh": sfx_whoosh, "boom": sfx_boom, "ding": sfx_ding}


def add(track, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(clip))
    track[i:j] += clip[:j - i] * gain


def load_music(path, total):
    tmp = path + ".hh2d.wav"
    _to_wav(path, tmp)
    m = read_wav(tmp)
    os.remove(tmp)
    reps = int(np.ceil(total * SR / len(m)))
    return np.tile(m, reps)[:int(total * SR)]
