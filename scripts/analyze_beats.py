#!/usr/bin/env python3
"""音频卡点分析:估算 BPM、beat 时刻、onset 峰值和每秒能量曲线。

用法: python analyze_beats.py <audio.wav> [-o beats.json]
实现: 纯 numpy(谱通量 onset + 自相关估速 + 动态峰值拾取),无第三方音频依赖。
"""
import argparse
import json
import sys
import wave

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SR_EXPECT = 16000
WIN, HOP = 1024, 512


def read_wav(path: str):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
        sw = w.getsampwidth()
    if sw == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"不支持的采样位宽: {sw}")
    return x, sr


def onset_envelope(x: np.ndarray, sr: int):
    n_frames = 1 + max(0, len(x) - WIN) // HOP
    window = np.hanning(WIN)
    mags = np.empty((n_frames, WIN // 2 + 1))
    rms = np.empty(n_frames)
    for i in range(n_frames):
        seg = x[i * HOP: i * HOP + WIN]
        if len(seg) < WIN:
            seg = np.pad(seg, (0, WIN - len(seg)))
        mags[i] = np.abs(np.fft.rfft(seg * window))
        rms[i] = np.sqrt(np.mean(seg ** 2) + 1e-12)
    flux = np.maximum(0.0, np.diff(mags, axis=0)).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    flux -= flux.mean()
    flux[flux < 0] = 0.0
    fps = sr / HOP
    return flux, rms, fps


def estimate_bpm(flux: np.ndarray, fps: float) -> float:
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    if ac[0] <= 0:
        return 0.0
    ac = ac / ac[0]
    lo, hi = int(fps * 60 / 200), int(fps * 60 / 60)  # 60~200 BPM
    hi = min(hi, len(ac) - 1)
    if lo >= hi:
        return 0.0
    lag = lo + int(np.argmax(ac[lo:hi]))
    return 60.0 * fps / lag


def pick_peaks(flux: np.ndarray, fps: float, bpm: float):
    if len(flux) == 0 or flux.max() <= 0:
        return []
    thresh = flux.mean() + 1.2 * flux.std()
    min_sep = max(int(fps * 0.25), int(fps * 30 / max(bpm, 1)))  # 不超过半拍间隔
    peaks, last = [], -min_sep
    order = np.argsort(flux)[::-1]
    chosen = np.zeros(len(flux), bool)
    for idx in order:
        if flux[idx] < thresh:
            break
        if not chosen[idx]:
            peaks.append(idx)
            lo, hi = max(0, idx - min_sep), min(len(flux), idx + min_sep + 1)
            chosen[lo:hi] = True
    peaks.sort()
    return [round(p / fps, 3) for p in peaks]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="extract_media.py 生成的 audio.wav")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    x, sr = read_wav(args.audio)
    flux, rms, fps = onset_envelope(x, sr)
    bpm = estimate_bpm(flux, fps)
    peaks = pick_peaks(flux, fps, bpm)

    duration = len(x) / sr
    beat_interval = 60.0 / bpm if bpm > 0 else 0
    # 按 BPM 生成对齐网格(从首个峰值起),供卡点对齐参考
    grid = []
    if bpm > 0 and peaks:
        t = peaks[0]
        while t <= duration:
            grid.append(round(t, 3))
            t += beat_interval

    # 每秒平均能量,用于判断高潮段落
    sec_energy = []
    for s in range(int(duration)):
        lo, hi = int(s * fps), int(min((s + 1) * fps, len(rms)))
        if lo < hi:
            sec_energy.append(round(float(rms[lo:hi].mean()), 5))

    result = {
        "ok": True,
        "duration": round(duration, 2),
        "bpm": round(bpm, 1),
        "beat_interval": round(beat_interval, 3),
        "onset_peaks": peaks,
        "beat_grid": grid,
        "energy_per_second": sec_energy,
    }
    out = args.out or "beats.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, "out": out, "bpm": result["bpm"],
                      "peaks": len(peaks), "duration": result["duration"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
