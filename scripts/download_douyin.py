#!/usr/bin/env python3
"""下载抖音视频 + 保存元数据。

用法: python download_douyin.py <抖音链接> -o <输出目录>
输出: <输出目录>/video.mp4 和 <输出目录>/meta.json,stdout 打印一行 JSON 状态。
依赖: pip install yt-dlp(国内网络请加 -i https://pypi.tuna.tsinghua.edu.cn/simple)
"""
import argparse
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

META_KEYS = [
    "id", "title", "description", "duration", "uploader", "uploader_id",
    "upload_date", "like_count", "comment_count", "repost_count", "view_count",
    "webpage_url", "tags",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="抖音分享链接或视频页链接")
    ap.add_argument("-o", "--outdir", default=".", help="输出目录")
    args = ap.parse_args()

    try:
        import yt_dlp
    except ImportError:
        print(json.dumps({"ok": False, "error": "缺少 yt-dlp,请先: pip install yt-dlp -i https://pypi.tuna.tsinghua.edu.cn/simple"}, ensure_ascii=False))
        return 1

    import os
    os.makedirs(args.outdir, exist_ok=True)
    outtmpl = os.path.join(args.outdir, "video.%(ext)s")

    opts = {
        "outtmpl": outtmpl,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
        },
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(args.url, download=True)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"下载失败: {type(e).__name__}: {e}"}, ensure_ascii=False))
        return 1

    meta = {k: info.get(k) for k in META_KEYS if info.get(k) is not None}
    meta_path = os.path.join(args.outdir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    video_path = None
    for ext in ("mp4", "webm", "mkv"):
        p = os.path.join(args.outdir, f"video.{ext}")
        if os.path.exists(p):
            video_path = p
            break

    print(json.dumps({
        "ok": True,
        "video": video_path,
        "meta": meta_path,
        "title": meta.get("title", "")[:60],
        "duration": meta.get("duration"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
