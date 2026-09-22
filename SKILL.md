---
name: pano-viral-edit
description: 拆解抖音爆款视频结构(钩子/节奏/卡点/字幕/情绪曲线),并套用到影石 Insta360 全景相机素材上,生成剪辑方案与剪映专业版草稿。当用户给出抖音链接要求拆解爆款、分析爆款视频结构、为全景/Insta360/360°素材做剪辑方案、生成剪映草稿、卡点剪辑、reframe 取景建议时使用。
---

# 爆款拆解 × 全景剪辑(pano-viral-edit)

## 概述

输入一条抖音爆款链接 + 一批 Insta360 全景素材,产出:爆款结构拆解 → 素材盘点 → 秒级剪辑方案(edit_plan)→ 可直接在剪映专业版打开的草稿。核心逻辑:**爆款提供结构公式,全景素材提供视角冲击,两者在时间线上对齐 beat**。

## 依赖(首次使用先检查)

- `ffmpeg`/`ffprobe` 在 PATH 中
- `pip install yt-dlp pyJianYingDraft`(国内网络必须加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`,默认源会超时)
- 生成剪映草稿需本机装有剪映专业版(草稿目录默认 `%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft`)
- `.insv` 原始文件不能直接用:先让用户在 Insta360 Studio/App 导出 mp4

## 工作流(四阶段)

建工作目录 `work/<主题>/`,所有中间产物放里面,命名固定,方便复用与断点续做。

### Phase 1:拆解爆款

```bash
python scripts/download_douyin.py <抖音链接> -o work/<主题>/ref
python scripts/extract_media.py work/<主题>/ref/video.mp4 -o work/<主题>/ref
python scripts/analyze_beats.py work/<主题>/ref/audio.wav -o work/<主题>/ref/beats.json
```

然后读 `references/viral-formula.md` 获取拆解框架,用 Read 工具逐张看 `ref/frames/` 抽帧图(帧间隔见 media.json 的 frame_seconds),结合 meta.json(标题/文案/点赞数)与 beats.json(BPM/卡点),写出 `work/<主题>/deconstruction.json`(模板见 viral-formula.md)。拆解结论用一两句话向用户复述钩子类型和节奏公式。

### Phase 2:素材盘点

确认素材目录内均为已导出的 mp4(发现 .insv 则提示先导出,脚本也会自动跳过并警告):

```bash
python scripts/extract_media.py <素材目录> -o work/<主题>/footage
```

读 `references/insta360-reframe.md` 获取视角词表与盘点模板,逐素材看抽帧,写 `work/<主题>/footage_inventory.md`,重点标出**高光时刻秒数**和**可用视角**。

### Phase 3:生成剪辑方案

把 deconstruction.json 的公式套到素材上,产出两个文件:

1. `edit_plan.md`(人读):秒级时间线表 —— 每段:起止秒|素材|素材内起止|reframe 视角(用词表标准词)|转场|字幕文案|卡点对齐说明
2. `edit_plan.json`(机读):直接喂给 Phase 4 的结构,字段定义见 `scripts/make_jianying_draft.py` 顶部 docstring

排方案规则:
- 时长对齐爆款节奏(通常 15-40s),段落切点尽量落在 beats.json 的 beat_grid 上
- 开头 2s 必须是最强视觉冲击(小行星/反小行星/甩切),高潮段(60-80% 进度)给子弹时间/最强高光素材
- 相邻段视角必须有反差;字幕文案沿用爆款的句式而非照搬内容
- 用户可提供 BGM 文件;无则只用原声,并在 edit_plan.md 里注明推荐 BGM 类型/BPM

**edit_plan.md 必须给用户确认后再进 Phase 4**(涉及自动写剪映草稿目录)。

### Phase 4:生成剪映草稿

```bash
python scripts/make_jianying_draft.py work/<主题>/edit_plan.json
```

成功后告诉用户草稿名,让其在剪映专业版草稿列表打开微调(reframe 关键帧需在剪映/Insta360 Studio 里手动精调,草稿完成素材上轨、卡点和字幕)。

## 边界与失败处理

- 抖音链接下载失败:可能是需登录的风控视频,让用户改用本地 mp4 走 extract_media 继续
- analyze_beats 对纯人声无 BGM 的视频 BPM 不可信:在拆解中注明,方案改用"语气停顿"做切点
- 转场名匹配不上时脚本会跳过并警告,不阻断;改用剪映标准转场中文名(如"叠化""闪黑""推近")

## 资源

- `scripts/download_douyin.py` — 抖音链接 → video.mp4 + meta.json
- `scripts/extract_media.py` — 视频/素材目录 → 抽帧 + audio.wav + media.json
- `scripts/analyze_beats.py` — audio.wav → BPM/onset 峰值/beat 网格/每秒能量
- `scripts/make_jianying_draft.py` — edit_plan.json → 剪映专业版草稿
- `references/viral-formula.md` — 爆款拆解框架 + deconstruction.json 模板
- `references/insta360-reframe.md` — 全景视角词表 + 素材盘点模板
