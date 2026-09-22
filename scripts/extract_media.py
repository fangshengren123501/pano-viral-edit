#!/usr/bin/env python3
"""视频/素材媒体提取:抽帧(JPEG) + 提取音轨(wav) + 输出 media.json。

用法:
  python extract_media.py <视频文件或素材目录> -o <输出目录> [--max-frames 48] [--width 960]
  - 输入单个视频: 在输出目录生成 frames/ audio.wav media.json
  - 输入目录: 对目录内每个视频建子目录分别提取(用于素材盘点)
依赖: 系统 PATH 中有 ffmpeg / ffprobe。
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def fail(msg: str) -> int:
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    return 1


def probe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True)
    return float(r.stdout.strip())


def extract_one(video: str, outdir: str, max_frames: int, width: int) -> dict:
    os.makedirs(outdir, exist_ok=True)
    frames_dir = os.path.join(outdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    duration = probe_duration(video)
    # 帧数不超过 max_frames;抽帧 fps 限制在 [0.2, 2.0]
    fps = min(2.0, max(0.2, max_frames / max(duration, 0.1)))
    expect = min(max_frames, max(1, math.ceil(duration * fps)))

    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", video,
         "-vf", f"fps={fps:.3f},scale={width}:-2", "-q:v", "3",
         os.path.join(frames_dir, "%03d.jpg")],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 抽帧失败: {r.stderr[:200]}")

    audio_path = os.path.join(outdir, "audio.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", video,
         "-vn", "-ac", "1", "-ar", "16000", audio_path],
        capture_output=True, text=True)

    frame_files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".jpg"))
    media = {
        "video": os.path.abspath(video),
        "duration": round(duration, 2),
        "frame_fps": round(fps, 3),
        "frame_count": len(frame_files),
        "frame_seconds": round(duration / max(len(frame_files), 1), 2),
        "frames_dir": os.path.abspath(frames_dir),
        "audio": os.path.abspath(audio_path) if os.path.exists(audio_path) else None,
    }
    with open(os.path.join(outdir, "media.json"), "w", encoding="utf-8") as f:
        json.dump(media, f, ensure_ascii=False, indent=2)
    return media


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="视频文件,或包含多个视频的素材目录")
    ap.add_argument("-o", "--outdir", default=".")
    ap.add_argument("--max-frames", type=int, default=48)
    ap.add_argument("--width", type=int, default=960)
    args = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        return fail("未找到 ffmpeg/ffprobe,请先安装并加入 PATH")

    if os.path.isfile(args.input):
        try:
            media = extract_one(args.input, args.outdir, args.max_frames, args.width)
        except Exception as e:
            return fail(str(e))
        print(json.dumps({"ok": True, "media": media}, ensure_ascii=False))
        return 0

    if os.path.isdir(args.input):
        results = []
        for name in sorted(os.listdir(args.input)):
            p = os.path.join(args.input, name)
            if not (os.path.isfile(p) and os.path.splitext(name)[1].lower() in VIDEO_EXTS):
                continue
            if name.lower().endswith(".insv"):
                continue
            sub = os.path.join(args.outdir, os.path.splitext(name)[0])
            try:
                results.append({"file": name, "media": extract_one(p, sub, args.max_frames, args.width)})
            except Exception as e:
                results.append({"file": name, "error": str(e)[:150]})
        skipped_insv = [n for n in os.listdir(args.input) if n.lower().endswith(".insv")]
        print(json.dumps({
            "ok": True, "count": len(results), "items": results,
            "insv_skipped": skipped_insv,
            "insv_hint": ".insv 需先在 Insta360 Studio/App 导出为 mp4 后再盘点" if skipped_insv else None,
        }, ensure_ascii=False))
        return 0

    return fail(f"输入不存在: {args.input}")


if __name__ == "__main__":
    sys.exit(main())
