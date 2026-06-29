---
name: video-generator
slug: video-maker-pro
version: 3.1.0
description: 自动化视频生成技能。接收有序图片序列和旁白文本，自动生成带语音同步的MP4视频。支持多比例输出、转场效果。需本地安装 FFmpeg 和 edge-tts。
displayName: "Video Generator"
displayName_zh: "视频生成器"
category: "多媒体处理"
platforms: ["WorkBuddy"]
visibility: "public"
agent_created: true
---

# Video Generator Skill

接收有序图片序列和旁白文本，自动生成音画同步的 MP4 视频。

---

## 安全声明

### 数据处理

- 所有视频处理在用户本地完成，技能本身不发起网络请求（edge-tts 语音合成为可选依赖，由其自身连接微软 TTS 服务）
- 仅读取用户明确指定的输入文件，仅向用户明确指定的输出路径写入文件
- 不收集、不上传、不持久化任何用户数据

### 权限范围

- 文件读取：仅读取用户提供的图片和音频文件路径
- 文件写入：仅向用户指定的输出目录写入生成的视频文件
- 系统命令：通过 Python subprocess 调用本地 FFmpeg 可执行文件（用户需自行安装 FFmpeg）

### 使用责任

- 用户需确保所用图片、音频素材拥有合法使用权
- 生成的视频内容由用户负责，应遵守当地法律法规
- 本技能不提供任何版权素材

---

## 依赖安装

使用前需确保以下依赖已安装：

| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| FFmpeg | 视频编码处理 | 从 https://ffmpeg.org 下载，添加到系统 PATH |
| edge-tts | 语音合成（可选） | `pip install edge-tts` |
| Pillow | 标题图生成（可选） | `pip install Pillow` |

安装完成后，技能脚本会自动检测 FFmpeg 路径（支持环境变量 `FFMPEG_PATH`、系统 PATH、常见安装路径三种方式）。

---

## 触发词

当用户输入包含以下意图时启用此技能：

- "生成视频" / "制作视频" / "图片转视频"
- "把这些图片做成视频"
- "video generator" / "make video"

---

## 使用流程

### 第1步：收集输入

需要以下信息：

| 参数 | 说明 | 示例 |
|------|------|------|
| 图片列表 | 按播放顺序排列的图片文件路径 | `["slide1.png", "slide2.png"]` |
| 旁白文本 | 每段图片对应的解说词 | `["第一张图介绍...", "第二张图展示..."]` |
| 输出比例 | 视频宽高比 | `"9:16"`（竖屏）或 `"16:9"`（横屏） |
| 语音 | edge-tts 语音 ID | `"zh-CN-XiaoxiaoNeural"`（默认女声） |

### 第2步：生成旁白音频（可选）

如果用户提供的是文本旁白，技能可调用 edge-tts 自动生成 MP3 音频文件。

语音参考：

| 语音 ID | 特点 |
|---------|------|
| zh-CN-XiaoxiaoNeural | 女声，温柔清晰（教学视频推荐） |
| zh-CN-YunxiNeural | 男声，沉稳专业 |
| zh-CN-XiaoyiNeural | 女声，活泼轻快（短视频推荐） |

### 第3步：执行视频生成

调用技能主脚本 `scripts/video_generator.py`，传入图片列表和音频列表，自动完成：

1. 将每张图片与其对应音频合成为 MP4 片段（含 video + audio 双流）
2. 可选：在片段间插入黑屏转场
3. 拼接所有片段为完整视频
4. 输出标准化 MP4 文件（H.264 + AAC，兼容手机播放）

### 第4步：验证输出

技能自动验证输出视频是否包含完整的 video 流和 audio 流，如有异常会报错并停止。

---

## 配置参考

技能行为可通过 `config.yaml` 调整：

```yaml
# 视频编码参数
video:
  codec: "libx264"
  crf: 18
  preset: "ultrafast"
  fps: 30

# 音频编码参数
audio:
  codec: "aac"
  bitrate: "192k"
  sample_rate: 44100

# 默认比例
default_ratio: "9:16"

# 转场
transition:
  enabled: true
  type: "black"        # 黑屏过渡
  duration: 0.5         # 秒
```

---

## 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| FFmpeg 找不到 | 未安装或不在 PATH | 安装 FFmpeg，或设置环境变量 FFMPEG_PATH |
| 标题中文乱码 | FFmpeg drawtext 字体问题 | 技能已改用 PIL 生成标题图，需确保系统有中文字体 |
| 拼接后无声 | 片段缺少音频流 | 技能自动为无音频片段添加静音轨道，确保流结构一致 |
| 图片被裁切 | 比例不匹配 | 技能使用 pad 等比缩放（黑边填充），不会裁切图片 |

---

## 文件结构

```
video-generator/
├── SKILL.md              # 本文件（使用说明）
├── config.yaml           # 默认配置
├── scripts/
│   └── video_generator.py   # 核心实现（VideoProcessor 类）
├── README.md             # 详细文档
└── README_zh.md          # 中文详细文档
```

所有可执行代码均在 `scripts/video_generator.py` 中，通过 `VideoProcessor` 类封装，统一处理 FFmpeg 路径检测、超时控制和错误处理。

---

## 更新日志

**v3.1.0** (2026-06-29)
- 🔒 彻底重构：SKILL.md 移除所有可执行代码，仅保留使用说明
- 🔒 彻底重构：核心实现全部移至 scripts/video_generator.py
- 🔒 安全声明：新增完整的数据处理、权限范围、使用责任章节
- 📝 文档优化：使用流程改为步骤描述，移除代码块

**v2.0.5** (2026-06-29)
- 安全优化（未通过审核，v3.1.0 重新设计）

---

*维护者：jie02zhang*
*最后更新：2026-06-29*
