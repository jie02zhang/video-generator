# Video Generator Skill

自动化视频生成技能，将有序图片序列和旁白音频合成为同步的 MP4 视频。

---

## 功能特性

- 📷 **图片序列 + 旁白 → 视频**：自动将多张图片和对应旁白合成为完整视频
- 🎙️ **语音合成**：集成 edge-tts，自动将文本旁白转为语音（支持多种语言和声音）
- 🖼️ **标题页生成**：使用 PIL 生成中文标题页（避免 FFmpeg 中文乱码）
- 🎬 **转场效果**：支持黑屏过渡效果
- 📱 **多比例输出**：支持 9:16（竖屏）、16:9（横屏）、1:1、4:5 等多种比例
- ✅ **输出验证**：自动验证生成视频的完整性（video 流 + audio 流）

---

## 快速开始

### 1. 安装依赖

```bash
# 安装 FFmpeg（必需）
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: 从 https://ffmpeg.org 下载，添加到 PATH

# 安装 Python 依赖（可选）
pip install edge-tts Pillow
```

### 2. 准备输入文件

- **图片**：按播放顺序排列的图片文件（如 `slide1.png`, `slide2.png`）
- **旁白**：每段图片对应的 MP3 音频文件

### 3. 运行视频生成

```bash
python scripts/video_generator.py \
  --images slide1.png slide2.png slide3.png \
  --audios audio1.mp3 audio2.mp3 audio3.mp3 \
  --output output/final_video.mp4 \
  --title "我的视频标题"
```

---

## 使用流程

### 步骤1：收集需求

| 参数 | 说明 | 示例 |
|------|------|------|
| 图片列表 | 按播放顺序排列的图片路径 | `["slide1.png", "slide2.png"]` |
| 旁白文本 | 每段图片对应的解说词 | `["第一张图介绍...", "第二张图展示..."]` |
| 输出比例 | 视频宽高比 | `"9:16"`（竖屏）或 `"16:9"`（横屏） |
| 语音 | edge-tts 语音 ID | `"zh-CN-XiaoxiaoNeural"`（默认女声） |

### 步骤2：生成旁白音频（可选）

如果用户提供的是文本旁白，技能可调用 edge-tts 自动生成 MP3 音频文件。

语音参考：

| 语音 ID | 特点 |
|---------|------|
| zh-CN-XiaoxiaoNeural | 女声，温柔清晰（教学视频推荐） |
| zh-CN-YunxiNeural | 男声，沉稳专业 |
| zh-CN-XiaoyiNeural | 女声，活泼轻快（短视频推荐） |

### 步骤3：执行视频生成

调用技能主脚本 `scripts/video_generator.py`，传入图片列表和音频列表，自动完成：

1. 将每张图片与其对应音频合成为 MP4 片段（含 video + audio 双流）
2. 可选：在片段间插入黑屏转场
3. 拼接所有片段为完整视频
4. 输出标准化 MP4 文件（H.264 + AAC，兼容手机播放）

### 步骤4：验证输出

技能自动验证输出视频是否包含完整的 video 流和 audio 流，如有异常会报错并停止。

---

## 配置说明

技能行为可通过 `config.yaml` 调整（可选）：

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

## 技术架构

```
video-generator/
├── SKILL.md              # 技能使用说明
├── config.yaml           # 默认配置
├── scripts/
│   └── video_generator.py   # 核心实现（VideoProcessor 类）
├── README.md             # 本文件
└── README_zh.md          # 中文详细文档
```

所有可执行代码均在 `scripts/video_generator.py` 中，通过 `VideoProcessor` 类封装，统一处理 FFmpeg 路径检测、超时控制和错误处理。

---

## 安全说明

- **本地执行**：所有视频处理在用户本地完成，不上传任何数据到远程服务器
- **最小权限**：仅读取用户指定的图片/音频文件，仅向用户指定的输出路径写入
- **无持久化存储**：处理完成后不保留用户数据的副本

---

## 许可证

MIT License © 2024 jie02zhang

---

## 更新日志

**v3.1.0** (2026-06-29)
- 🔒 彻底重构：SKILL.md 移除所有可执行代码，仅保留使用说明
- 🔒 彻底重构：核心实现全部移至 scripts/video_generator.py
- 🔒 安全声明：新增完整的数据处理、权限范围、使用责任章节
- 📝 文档优化：使用流程改为步骤描述，移除代码块

---

**维护者**：jie02zhang  
**最后更新**：2026-06-29
