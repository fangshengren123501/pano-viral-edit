#!/usr/bin/env python3
"""把 edit_plan.json 生成剪映专业版草稿。

用法: python make_jianying_draft.py <edit_plan.json> [--draft-root <剪映草稿目录>] [--name 覆盖草稿名]
edit_plan.json 结构:
{
  "name": "草稿名",
  "width": 1080, "height": 1920, "fps": 30,
  "segments": [
    {"file": "素材.mp4", "start": 0, "duration": 2.5,
     "source_start": 3.0, "speed": 1.0,
     "transition": "推近", "fade": [0.2, 0.2],
     "scale": 1.1, "rotation": 0, "flip_horizontal": false,
     "text": "字幕文案", "text_size": 9, "text_color": [1, 1, 0.2]}
  ],
  "music": {"file": "bgm.mp3", "volume": 0.7}
}
start/duration 为成片时间线秒数;source_start 为素材内起始秒。
依赖: pip install pyJianYingDraft
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_DRAFT_ROOT = os.path.expandvars(
    r"%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft")


def fail(msg: str, **extra) -> int:
    print(json.dumps({"ok": False, "error": msg, **extra}, ensure_ascii=False))
    return 1


def find_transition(draft_mod, name: str):
    """按中文名模糊匹配转场枚举,匹配不到返回 None。"""
    name = name.strip()
    if not name or name in ("无", "硬切"):
        return None
    members = list(draft_mod.TransitionType)
    for t in members:
        if t.name == name:
            return t
    for t in members:
        if name in t.name or t.name in name:
            return t
    return "UNMATCHED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", help="edit_plan.json 路径")
    ap.add_argument("--draft-root", default=DEFAULT_DRAFT_ROOT)
    ap.add_argument("--name", default=None, help="覆盖 plan 中的草稿名")
    args = ap.parse_args()

    try:
        import pyJianYingDraft as draft
    except ImportError:
        return fail("缺少 pyJianYingDraft: pip install pyJianYingDraft -i https://pypi.tuna.tsinghua.edu.cn/simple")

    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)

    segments = plan.get("segments", [])
    if not segments:
        return fail("plan.segments 为空")

    missing = [s["file"] for s in segments if not os.path.exists(s.get("file", ""))]
    music = plan.get("music")
    if music and not os.path.exists(music.get("file", "")):
        missing.append(music["file"])
    if missing:
        return fail("素材文件不存在", missing=missing)

    if not os.path.isdir(args.draft_root):
        return fail(f"剪映草稿目录不存在(剪映专业版未安装或路径不同): {args.draft_root}")

    name = args.name or plan.get("name") or "pano_viral_edit"
    width, height, fps = plan.get("width", 1080), plan.get("height", 1920), plan.get("fps", 30)

    warnings = []
    folder = draft.DraftFolder(args.draft_root)
    script = folder.create_draft(name, width, height, fps, allow_replace=True)
    script.append_track(draft.TrackSpec(draft.TrackType.video, name="main"))
    script.append_track(draft.TrackSpec(draft.TrackType.text, name="captions"))
    if music:
        script.append_track(draft.TrackSpec(draft.TrackType.audio, name="music"))

    total = 0.0
    for i, seg in enumerate(segments):
        start, duration = float(seg["start"]), float(seg["duration"])
        speed = float(seg.get("speed", 1.0))
        source_start = float(seg.get("source_start", 0.0))
        total = max(total, start + duration)

        clip = None
        if any(k in seg for k in ("scale", "rotation", "flip_horizontal", "flip_vertical")):
            clip = draft.ClipSettings(
                scale_x=float(seg.get("scale", 1.0)),
                scale_y=float(seg.get("scale", 1.0)),
                rotation=float(seg.get("rotation", 0.0)),
                flip_horizontal=bool(seg.get("flip_horizontal", False)),
                flip_vertical=bool(seg.get("flip_vertical", False)),
            )
        v = draft.VideoSegment(
            seg["file"],
            draft.trange(f"{start}s", f"{duration}s"),
            source_timerange=draft.trange(f"{source_start}s", f"{duration * speed}s"),
            speed=speed,
            volume=float(seg.get("volume", 1.0)),
            clip_settings=clip,
        )
        if seg.get("transition"):
            t = find_transition(draft, seg["transition"])
            if t == "UNMATCHED":
                warnings.append(f"第{i+1}段转场名未匹配,已跳过: {seg['transition']}")
            elif t is not None:
                v.add_transition(t, duration=f"{seg.get('transition_duration', 0.5)}s")
        if seg.get("fade"):
            fin, fout = seg["fade"]
            v.add_fade(f"{fin}s", f"{fout}s")
        script.add_segment(v, track="main")

        text = seg.get("text")
        if text:
            style = draft.TextStyle(
                size=float(seg.get("text_size", 8)),
                bold=bool(seg.get("text_bold", True)),
                color=tuple(seg.get("text_color", [1.0, 1.0, 1.0])),
            )
            script.add_segment(
                draft.TextSegment(text, draft.trange(f"{start}s", f"{duration}s"), style=style),
                track="captions")

    if music:
        a = draft.AudioSegment(
            music["file"],
            draft.trange(f"{music.get('start', 0)}s", f"{total}s"),
            volume=float(music.get("volume", 0.8)),
        )
        script.add_segment(a, track="music")

    script.save()
    print(json.dumps({
        "ok": True,
        "draft_name": name,
        "draft_dir": os.path.join(args.draft_root, name),
        "duration": round(total, 2),
        "segments": len(segments),
        "warnings": warnings,
        "next": "打开剪映专业版,在草稿列表中找到该草稿继续微调",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
