# 视频生成器使用指南

## 功能概述

这个 Skill 可以帮你快速生成同步的视频内容：
1. 上传图片（按顺序）
2. 为每张图片生成对应的旁白音频
3. 将图片和音频合成为 MP4 视频
4. 确保音频与图片内容精确同步

---

## 安装要求

### 必需工具
1. **Python 3.8+**
2. **edge-tts** - 文字转语音（免费）
   ```bash
   pip install edge-tts
   ```
3. **FFmpeg** - 视频处理工具
   - 下载：https://ffmpeg.org/download.html
   - 安装后添加到系统 PATH，或记录安装路径

### 可选工具
- **pydub** - 音频处理（用于精确获取音频时长）
  ```bash
  pip install pydub
  ```

---

## 使用流程

### 步骤1：准备图片
将你的图片按顺序命名并放在一个文件夹中：
```
images/
├── 1.png  # 第一张图片
├── 2.png  # 第二张图片
├── 3.png  # 第三张图片
└── ...
```

**要求：**
- 图片格式：PNG、JPG、JPEG
- 分辨率：建议 1080x1920（竖屏）或 1920x1080（横屏）
- 命名：按播放顺序排列

---

### 步骤2：准备旁白文本
创建一个 JSON 配置文件（`video_config.json`）：

```json
{
  "images": [
    "images/1.png",
    "images/2.png",
    "images/3.png"
  ],
  "audio_segments": [
    {
      "text": "这是第一张图片的旁白内容。",
      "output": "audio/segment_1.mp3"
    },
    {
      "text": "这是第二张图片的旁白内容。",
      "output": "audio/segment_2.mp3"
    },
    {
      "text": "这是第三张图片的旁白内容。",
      "output": "audio/segment_3.mp3"
    }
  ],
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+20%",
  "output_path": "output/final_video.mp4",
  "ffmpeg_path": "D:/soft/ffmpeg/bin/ffmpeg.exe"
}
```

**配置说明：**
- `images` - 图片文件路径列表（按顺序）
- `audio_segments` - 音频段落配置
  - `text` - 旁白文本
  - `output` - 输出音频文件路径
- `voice` - 语音类型（见下方列表）
- `rate` - 语速调整（`+20%` 加快，`-10%` 减慢）
- `output_path` - 最终视频输出路径
- `ffmpeg_path` - FFmpeg 可执行文件路径

---

### 步骤3：生成音频
运行音频生成脚本：

```bash
python scripts/generate_audio.py --config video_config.json
```

**输出：**
- 音频文件将保存在 `audio/` 文件夹
- 文件名：`segment_1.mp3`, `segment_2.mp3`, ...

---

### 步骤4：生成视频
运行视频生成脚本：

```bash
python scripts/generate_video.py --config video_config.json
```

**输出：**
- 最终视频：`output/final_video.mp4`
- 视频特点：
  - 每张图片显示时间 = 对应音频的时长
  - 音频与图片完全同步
  - 格式：MP4（H.264 视频 + AAC 音频）

---

## 语音类型选择

### 中文语音
| 语音 ID | 特点 | 适用场景 |
|---------|------|-----------|
| `zh-CN-XiaoxiaoNeural` | 女声，温柔 | 通用、教学 |
| `zh-CN-YunxiNeural` | 男声，沉稳 | 新闻、解说 |
| `zh-CN-XiaoyiNeural` | 女声，活泼 | 短视频、娱乐 |
| `zh-CN-YunyangNeural` | 男声，专业 | 企业宣传 |
| `zh-CN-liaoning-XiaobeiNeural` | 女声，东北口音 | 幽默、接地气 |

### 查看所有可用语音
```python
import edge_tts
voices = await edge_tts.list_voices()
for voice in voices:
    if voice["Locale"].startswith("zh"):
        print(voice["ShortName"], voice["FriendlyName"])
```

---

## 高级技巧

### 1. 调整语速
在配置文件中修改 `rate` 参数：
- `+0%` - 正常语速
- `+20%` - 加快 20%（推荐）
- `+40%` - 加快 40%（内容较多时）
- `-10%` - 减慢 10%

### 2. 精确同步
如果需要更精确的同步（毫秒级）：
1. 安装 `pydub`：`pip install pydub`
2. 脚本会自动获取每段音频的精确时长
3. 图片显示时间会完全匹配音频时长

### 3. 批量处理
如果有多个视频要生成：
1. 创建多个配置文件：`config1.json`, `config2.json`, ...
2. 批量运行脚本：
   ```bash
   for config in *.json; do
     python scripts/generate_video.py --config $config
   done
   ```

### 4. 自定义输出格式
修改 `scripts/generate_video.py` 中的视频编码参数：
- 分辨率：修改 `-s` 参数（如 `1080x1920`）
- 帧率：修改 `-r` 参数（如 `30`）
- 视频质量：修改 `-crf` 参数（如 `23`，数值越小质量越高）

---

## 常见问题

### Q1：音频生成失败
**可能原因：**
- 网络连接问题（edge-tts 需要联网）
- 文本包含特殊字符

**解决方法：**
- 检查网络连接
- 简化文本内容，避免特殊符号

### Q2：视频生成失败
**可能原因：**
- FFmpeg 路径不正确
- 图片或音频文件不存在
- 文件格式不支持

**解决方法：**
- 检查 `ffmpeg_path` 配置
- 确认所有文件路径正确
- 使用常见格式（PNG、JPG、MP3）

### Q3：音频与图片不同步
**可能原因：**
- 音频时长获取不准确
- 图片切换时间设置错误

**解决方法：**
- 安装 `pydub` 获取精确时长
- 手动检查配置文件中的时长设置

### Q4：视频画质不满意
**调整方法：**
- 使用更高分辨率的图片
- 修改视频编码参数（见高级技巧 4）
- 使用更高质量的音频（bitrate 256k+）

---

## 示例项目

### 示例1：教学视频（8张图片）
```json
{
  "images": [
    "images/1.png",
    "images/2.png",
    ...
    "images/8.png"
  ],
  "audio_segments": [
    {"text": "开场白...", "output": "audio/1.mp3"},
    {"text": "第一张图讲解...", "output": "audio/2.mp3"},
    ...
  ],
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+20%",
  "output_path": "output/teaching_video.mp4",
  "ffmpeg_path": "D:/soft/ffmpeg/bin/ffmpeg.exe"
}
```

### 示例2：产品宣传视频
```json
{
  "images": ["product/cover.png", "product/features.png", ...],
  "audio_segments": [...],
  "voice": "zh-CN-YunxiNeural",
  "rate": "+0%",
  "output_path": "output/product_ad.mp4"
}
```

---

## 技术支持

如果遇到问题：
1. 查看脚本输出的错误信息
2. 检查配置文件格式是否正确
3. 确认所有依赖已安装
4. 在 WorkBuddy 中询问："视频生成器报错：[错误信息]"

---

## 更新日志

**v1.0.0** (2026-06-21)
- 初始版本
- 支持图片+音频同步生成视频
- 支持语速调整
- 支持多种语音类型
