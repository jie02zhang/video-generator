# Video Generator Skill 安装和使用指南

## 📦 Skill 概述

**Video Generator** 是一个自动化视频生成 Skill，可以帮你快速将图片序列和旁白音频合成为同步的 MP4 视频。

### 核心功能
- ✅ 批量生成旁白音频（支持多种中文语音）
- ✅ 自动同步音频与图片显示时间
- ✅ 输出标准 MP4 格式视频
- ✅ 支持语速调整和语音选择

---

## 📥 安装方法

### 方法1：从 ZIP 文件安装（推荐）

1. **下载 Skill 包**
   - 文件：`video-generator.zip`（已生成）
   - 位置：`C:/Users/zjjsj/.workbuddy/skills/video-generator.zip`

2. **安装到 WorkBuddy**
   - 打开 WorkBuddy
   - 进入 "专家" → "技能管理"
   - 点击 "安装技能"
   - 选择 `video-generator.zip` 文件
   - 确认安装

3. **验证安装**
   - 安装后，在技能列表中应该能看到 "video-generator"
   - 状态显示为 "已启用"

### 方法2：手动安装

1. 解压 `video-generator.zip`
2. 将解压后的 `video-generator/` 文件夹复制到：
   - **用户级（推荐）**：`C:/Users/zjjsj/.workbuddy/skills/`
   - **项目级**：`<你的项目>/.workbuddy/skills/`
3. 重启 WorkBuddy

---

## 🔧 依赖安装

此 Skill 需要以下依赖才能正常工作：

### 1. Python 3.8+
- 下载：https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

### 2. edge-tts（文字转语音）
```bash
pip install edge-tts
```
- 功能：免费、高质量的中文语音合成
- 需要联网使用

### 3. FFmpeg（视频处理）
- 下载：https://ffmpeg.org/download.html
- 安装步骤：
  1. 下载 Windows 版本（如 gyan.dev 构建）
  2. 解压到 `D:/soft/ffmpeg/`（或你喜欢的路径）
  3. 将 `D:/soft/ffmpeg/bin/` 添加到系统 PATH，或在配置文件中指定完整路径

**验证 FFmpeg 安装：**
```bash
ffmpeg -version
```

---

## 🚀 使用方法

### 基本工作流程

1. **准备图片**
   - 将图片按顺序命名（如 `1.png`, `2.png`, ...）
   - 放在一个文件夹中（如 `images/`）

2. **准备旁白文本**
   - 为每张图片写好对应的解说文字

3. **在 WorkBuddy 中触发 Skill**
   - 输入："帮我生成一个视频，图片在 images/ 文件夹"
   - 或："制作教学视频，图片是 1.png 到 8.png"

4. **Skill 自动执行**
   - 生成旁白音频
   - 合成视频
   - 输出 MP4 文件

---

### 详细步骤示例

#### 示例1：生成 AI 概念教学视频

**用户输入：**
```
帮我生成一个AI概念教学视频，包含8张图片：
- 图片路径：images/1.png ~ images/8.png
- 旁白文本：
  1. "AI小白必看！8张图搞懂AI核心概念"
  2. "第一张：AI七层关系，搞懂全局架构"
  3. "第二张：提示词，和AI沟通的正确方式"
  ...（以此类推）
- 语音：女声，温柔型
- 语速：加快20%
- 输出路径：output/ai_video.mp4
```

**Skill 执行步骤：**

1. **创建配置文件** `video_config.json`：
```json
{
  "images": [
    "images/1.png",
    "images/2.png",
    ...
    "images/8.png"
  ],
  "audio_segments": [
    {
      "text": "AI小白必看！8张图搞懂AI核心概念",
      "output": "audio/segment_1.mp3"
    },
    {
      "text": "第一张：AI七层关系，搞懂全局架构",
      "output": "audio/segment_2.mp3"
    },
    ...
  ],
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+20%",
  "output_path": "output/ai_video.mp4",
  "ffmpeg_path": "D:/soft/ffmpeg/bin/ffmpeg.exe"
}
```

2. **生成音频**：
```bash
python scripts/generate_audio.py --config video_config.json
```

3. **生成视频**：
```bash
python scripts/generate_video.py --config video_config.json
```

4. **输出结果**：
   - 最终视频：`output/ai_video.mp4`
   - 音频文件：`audio/segment_1.mp3` ~ `audio/segment_8.mp3`

---

#### 示例2：生成产品宣传视频

**用户输入：**
```
制作一个产品宣传视频：
- 图片文件夹：product/images/
- 语音：男声，专业型
- 语速：正常
- 输出：output/product_ad.mp4
```

**Skill 会询问：**
- "请提供每张图片的旁白文本"
- "确认语音类型：zh-CN-YunxiNeural（男声，沉稳）？"
- "确认语速：+0%（正常）？"

**用户回答后，Skill 自动执行生成流程。**

---

## 🎛️ 高级配置

### 语音类型选择

| 语音 ID | 性别 | 特点 | 适用场景 |
|---------|------|------|-----------|
| `zh-CN-XiaoxiaoNeural` | 女 | 温柔清晰 | 教学、通用 |
| `zh-CN-YunxiNeural` | 男 | 沉稳专业 | 企业宣传、新闻 |
| `zh-CN-XiaoyiNeural` | 女 | 活泼轻快 | 短视频、娱乐 |
| `zh-CN-YunyangNeural` | 男 | 专业正式 | 商务、演讲 |
| `zh-CN-liaoning-XiaobeiNeural` | 女 | 东北口音 | 幽默、接地气 |

**查看所有可用语音：**
```python
import edge_tts
import asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    for voice in voices:
        if voice["Locale"].startswith("zh"):
            print(voice["ShortName"], voice["FriendlyName"])

asyncio.run(list_voices())
```

### 语速调整

在配置文件中修改 `rate` 参数：
- `+0%` - 正常语速
- `+20%` - 加快 20%（推荐）
- `+40%` - 加快 40%（内容较多时）
- `-10%` - 减慢 10%

### 自定义视频参数

编辑 `scripts/generate_video.py`，修改视频编码参数：
- **分辨率**：修改 `-s` 参数（如 `1920x1080`）
- **帧率**：修改 `-r` 参数（如 `30`）
- **视频质量**：修改 `-crf` 参数（如 `23`，数值越小质量越高）

---

## 📁 文件结构

安装后的 Skill 目录结构：

```
video-generator/
├── SKILL.md                      # 技能说明文档
├── scripts/
│   ├── generate_audio.py        # 音频生成脚本
│   └── generate_video.py        # 视频生成脚本
└── references/
    └── usage_guide.md          # 详细使用指南
```

---

## 🛠️ 常见问题

### Q1：音频生成失败
**错误信息：** `edge-tts error: ...`

**可能原因：**
- 网络连接问题
- 文本包含特殊字符

**解决方法：**
1. 检查网络连接
2. 简化文本内容，避免特殊符号
3. 尝试更换语音类型

### Q2：视频生成失败
**错误信息：** `FFmpeg error: ...`

**可能原因：**
- FFmpeg 路径不正确
- 图片或音频文件不存在
- 文件格式不支持

**解决方法：**
1. 检查 `ffmpeg_path` 配置
2. 确认所有文件路径正确
3. 使用常见格式（PNG、JPG、MP3）

### Q3：音频与图片不同步
**可能原因：**
- 音频时长获取不准确

**解决方法：**
1. 安装 `pydub`：`pip install pydub`
2. 脚本会自动获取精确音频时长

### Q4：Skill 未触发
**可能原因：**
- 用户输入未包含触发词

**解决方法：**
1. 使用明确的触发词："生成视频"、"制作视频"、"图片转视频"
2. 查看 `SKILL.md` 中的触发词列表

---

## 📝 更新日志

**v1.0.0** (2026-06-21)
- 初始版本
- 支持图片+音频同步生成视频
- 支持语速调整
- 支持多种语音类型
- 提供详细使用指南

---

## 📞 技术支持

如果遇到问题：
1. 查看脚本输出的错误信息
2. 参考 `references/usage_guide.md`
3. 在 WorkBuddy 中询问："video-generator 报错：[错误信息]"

---

## 🎓 学习资源

- **FFmpeg 官方文档**：https://ffmpeg.org/documentation.html
- **edge-tts GitHub**：https://github.com/rany2/edge-tts
- **WorkBuddy 技能开发指南**：https://www.codebuddy.cn/docs/

---

**技能创建者：** WorkBuddy AI  
**创建日期：** 2026-06-21  
**版本：** 1.0.0
