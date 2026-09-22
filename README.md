# pano-viral-edit

拆解抖音爆款视频的**结构公式**，套用到影石 Insta360 全景素材上，直接生成**剪映专业版草稿**。

爆款负责节奏，全景负责冲击，卡点负责把它们缝在一起。

## 它能做什么

- 给一个抖音链接，自动下载 → 抽帧 → 提出整条视频的钩子类型、分镜节奏、情绪曲线、字幕规律
- 分析音频得出 BPM、onset 峰值、beat 网格（纯 numpy 实现，零音频依赖）
- 盘点你的全景素材目录，标注每段的可用视角（小行星 / FPV / 第三人称跟随 / 子弹时间……）和高光时刻
- 生成秒级剪辑方案，并一键写成剪映专业版草稿——打开剪映就能继续微调

## 工作流

```
抖音链接 → 爆款拆解(deconstruction.json)
         → 素材盘点(footage_inventory.md)
         → 剪辑方案(edit_plan.md / .json)
         → 剪映草稿
```

## 安装

```bash
# 依赖(国内网络务必走镜像)
pip install yt-dlp pyJianYingDraft -i https://pypi.tuna.tsinghua.edu.cn/simple
# 还需要 ffmpeg / ffprobe 在 PATH 中;生成草稿需本机装有剪映专业版
```

把整个文件夹放进你的 skills 目录(Qoder / Claude Code / Codex 均可):

```
~/.qoder/skills/pano-viral-edit/   # 或 ~/.claude/skills/
```

## 用法

对 agent 说:

> 拆解这个抖音视频 <链接>,用我的全景素材 <目录> 做剪辑方案

四阶段自动走完后,剪映草稿列表里会出现新草稿。

## 边界

- `.insv` 原始文件不能直接用,先在 Insta360 Studio/App 导出 mp4
- reframe 关键帧的精调在剪映 / Insta360 Studio 里手动完成,草稿负责素材上轨、卡点和字幕
- 纯口播无 BGM 的视频 BPM 不可信,方案会改用语气停顿做切点

## 结构

- `SKILL.md` — 四阶段工作流主入口
- `scripts/` — 下载 / 抽帧 / 卡点分析 / 草稿生成,全部独立可跑
- `references/` — 爆款拆解框架 + 全景视角词表

## License

MIT
