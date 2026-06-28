---
name: video-generator
slug: video-maker-pro
version: 1.5.0
description: 自动化视频生成技能。将图片和音频合成为同步的MP4视频，支持热点话题自动获取、旁白脚本生成、音画精确同步、转场效果（黑屏过渡）、多比例输出、封面图生成。触发词：生成视频、制作视频、图片转视频、video generator、video制作、热点视频
displayName: "Video Generator"
displayName_zh: "视频生成器"
displayName_en: "Video Generator"
display_name: "Video Generator"
display_name_zh: "视频生成器"
display_name_en: "Video Generator"
visibility: "public"
agent_created: true
---

# Video Generator Skill v1.5.0

自动化视频生成完整工作流程，将有序图片序列和对应旁白合成为同步的MP4视频。

---

## ⚠️ 关键原则（必读）

### 原则1：音画必须精确匹配

**每张图片的旁白必须精确描述该图片的视觉内容**，不能讲A图内容却配B图。

错误示例：
> 图片是「AI工作流流程图」，旁白却在讲「低代码平台搭建」❌

正确示例：
> 图片是「AI工作流流程图」，旁白逐条讲解流程图中的每个步骤 ✅

### 原则2：所有片段必须有相同的流结构

concat `copy` 模式要求所有输入文件有**完全相同的流结构**（都有video+audio，或都有video-only）。
**标题页也必须生成带静音AAC轨道的MP4**，否则concat时音频会被丢弃。

### 原则3：图片完整显示，不裁切

使用 `pad` 而非 `crop`，等比缩放图片完整显示，黑边填充剩余区域。

---

## 功能概述

1. **热点获取** - 自动从多个平台获取当前热门AI话题，作为视频选题参考
2. **图片准备** - 接收用户上传的有序图片序列
3. **旁白生成** - 为每张图片撰写精确匹配其视觉内容的旁白文本
4. **音频生成** - 使用 edge-tts 生成高质量旁白音频
5. **视频合成** - 使用 FFmpeg 将图片和音频合成为标准MP4视频
6. **标题页生成** - 使用PIL生成中文标题页图片（避免FFmpeg中文乱码）

---

## 何时使用此技能

当用户输入包含以下意图时，使用此技能：

- "帮我生成一个视频" / "制作教学视频"
- "把这些图片做成视频"
- "生成视频，图片是..."
- "热点视频" / "帮我找个热点话题做视频"
- `video generator` / `video制作`

---

## 使用流程

### 步骤0：获取热点话题（可选）

在生成视频前，先帮助用户找到当前热门话题，提高视频曝光率。

**执行流程：**

```
1. 询问用户视频方向（AI工具/AI工作流/大模型/运维+AI/其他）
2. 根据方向，用 WebSearch 搜索2-3个相关热点来源
3. 整理成「热点选题清单」给用户选择
4. 用户选定话题后，进入步骤1
```

**输出格式：**

```
📢 当前AI视频热点选题（YYYY-MM-DD）

1. 【话题名称】竞争度：高/中/低
   - 为什么火：[一句话]
   - 视频角度：[建议]
```

---

### 步骤1：收集需求 + 撰写旁白脚本

**明确信息：**

1. **图片文件** - 有序图片路径列表（按播放顺序）
2. **旁白文本** - **每张图片的视觉内容描述**（必须精确匹配图片！）
3. **语音偏好** - 默认：`zh-CN-XiaoxiaoNeural`
4. **语速调整** - 默认：`+20%`（短视频节奏）
5. **输出路径** - 最终视频保存位置
6. **是否需要标题页** - 默认：是（开头3-5秒）

**⚠️ 旁白撰写规范：**

旁白必须**严格描述当前图片的视觉内容**，按以下模板撰写：

```
图片内容：[描述图片中有什么元素、文字、图表]
旁白脚本：[开场白指向图片内容] + [逐条讲解图片元素] + [过渡到下一张]
```

示例（图片=「手动vs自动对比图」）：
```
图片内容：左半边「手动模式」图标+复制粘贴截图，右半边「自动化工具」图标+机器人
旁白脚本：
  "看左边，手动模式就是复制粘贴、手动填表、导出数据，忙得焦头烂额还容易出错。
   右边呢？自动化工具，机器人按规则自动执行，效率直接拉满。
   这就是AI自动化工作流的核心价值。"
```

---

### 步骤2：生成音频

使用 `edge-tts` 为每段旁白生成MP3音频。

```python
import asyncio, edge_tts

async def gen(text, output_path, voice='zh-CN-XiaoxiaoNeural', rate='+20%'):
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(output_path)

asyncio.run(gen("旁白内容", "audio/segment_01.mp3"))
```

**获取精确时长（用于图片显示时长）：**

```python
import subprocess
def get_duration(mp3_path):
    r = subprocess.run(
        ['ffprobe','-v','quiet','-show_entries','format=duration',
         '-of','default=noprint_wrappers=1:nokey=1', mp3_path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())
```

---

### 步骤3：生成标题页图片（PIL，避免中文乱码）

**⚠️ 不要用FFmpeg `drawtext` 渲染中文！** Windows下中文字体加载不可靠，会产生乱码方块。

**正确方案：用PIL生成标题页图片**

```python
from PIL import Image, ImageDraw, ImageFont

def make_title_image(output_path, title, subtitle, tag="干货教学", channel="@你的频道名"):
    W, H = 1080, 1920
    img  = Image.new('RGB', (W, H), color=(26, 26, 46))  # 深蓝底
    draw = ImageDraw.Draw(img)
    
    # 字体路径（Windows）
    font_path = r'C:\Windows\Fonts\msyh.ttc'
    f_title = ImageFont.truetype(font_path, 72)
    f_sub   = ImageFont.truetype(font_path, 48)
    f_tag   = ImageFont.truetype(font_path, 36)
    f_ch    = ImageFont.truetype(font_path, 28)
    
    def ct(text, y, font, fill):
        bbox = draw.textbbox((0,0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W-tw)//2, y), text, font=font, fill=fill)
    
    cy = H // 2
    ct(title,   cy-120, f_title, (255,255,255))           # 白色主标题
    ct(subtitle, cy-30,  f_sub,   (160,176,255))          # 蓝色副标题
    # 黄色标签
    draw.rounded_rectangle([(W-180)//2, cy+60, (W+180)//2, cy+110],
                           radius=25, fill=(255,204,0))
    ct(tag, cy+68, f_tag, (30,30,30))                    # 黑色标签文字
    ct(channel, cy+180, f_ch,  (136,136,136))            # 灰色频道名
    img.save(output_path)

make_title_image('output/title.png', 'AI工作流实战', '手动30分钟 -> 自动2分钟')
```

---

### 步骤4：合成视频（关键！音频不丢失方案）

**推荐方案：每段图片+音频直接合成完整MP4，再拼接**

此方案避免「视频concat + 音频concat + mux」的音频丢失问题。

```python
import subprocess, os

FFMPEG = r'D:\soft\ffmpeg\bin\ffmpeg.exe'
VF_PAD = 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black'

def make_segment_mp4(img_path, audio_path, out_path):
    """图片 + 音频 → 完整MP4（一步合成，音频不丢失）"""
    cmd = [
        FFMPEG, '-y',
        '-loop', '1',
        '-i', img_path,
        '-i', audio_path,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
        '-pix_fmt', 'yuv420p', '-r', '30', '-g', '30',
        '-vf', VF_PAD,
        '-shortest',
        '-avoid_negative_ts', 'make_zero',
        out_path
    ]
    subprocess.run(cmd, capture_output=True)
    return os.path.exists(out_path)

def make_title_mp4_with_audio(title_img_path, out_path, duration=3):
    """标题页图片 → MP4（带静音AAC轨道，保证流结构一致）"""
    # 生成视频部分
    tmp_vid = out_path + '.tmp_v.mp4'
    subprocess.run([
        FFMPEG, '-y', '-loop','1','-t',str(duration),
        '-i', title_img_path,
        '-c:v','libx264','-preset','ultrafast','-crf','18',
        '-pix_fmt','yuv420p','-r','30','-g','30',
        '-vf', VF_PAD,
        tmp_vid
    ], capture_output=True)
    
    # 生成静音AAC
    tmp_aud = out_path + '.tmp_a.m4a'
    subprocess.run([
        FFMPEG, '-y',
        '-f','lavfi','-i',f'anullsrc=r=44100:cl=stereo',
        '-t',str(duration),
        '-c:a','aac','-b:a','192k','-ar','44100','-ac','2',
        tmp_aud
    ], capture_output=True)
    
    # 合成
    subprocess.run([
        FFMPEG, '-y',
        '-i', tmp_vid, '-i', tmp_aud,
        '-c:v','copy','-c:a','copy',
        '-shortest',
        out_path
    ], capture_output=True)
    
    # 清理临时
    for t in [tmp_vid, tmp_aud]:
        if os.path.exists(t): os.remove(t)
    return os.path.exists(out_path)

def concat_mp4s(mp4_list, final_path):
    """拼接多个完整MP4（都含video+audio，用copy模式）"""
    concat_txt = final_path + '.concat.txt'
    with open(concat_txt, 'w', encoding='utf-8') as f:
        for p in mp4_list:
            f.write(f"file '{p}'\n")
    
    subprocess.run([
        FFMPEG, '-y',
        '-f','concat','-safe','0',
        '-i', concat_txt,
        '-c','copy',
        '-movflags','+faststart',
        final_path
    ], capture_output=True)
    
    os.remove(concat_txt)
    return os.path.exists(final_path)

# 完整流程示例：
segments = [
    ('output/title.png',   None,              3),    # 标题页（特殊处理）
    ('images/1.png',       'audio/segment_01.mp3', None),
    ('images/2.png',       'audio/segment_02.mp3', None),
]

# 1. 生成标题页MP4（带静音轨道）
make_title_mp4_with_audio('output/title.png', 'output/_title.mp4', duration=3)

# 2. 生成内容片段MP4
clips = ['output/_title.mp4']
for i, (img, audio, _) in enumerate(segments[1:], 1):
    out = f'output/_clip_{i:02d}.mp4'
    make_segment_mp4(img, audio, out)
    clips.append(out)

# 3. 拼接
concat_mp4s(clips, 'output/final_video.mp4')
```

---

### 步骤5：转场效果（黑屏过渡帧）

**方案：在片段之间插入短黑屏MP4，再用 concat copy 拼接**

这是目前最稳定可靠的转场方案，100% 兼容，不依赖复杂的 `filter_complex`。

**为什么不用 xfade？**
- `xfade`/`acrossfade` 需要构造超长 `filter_complex` 字符串
- Windows/Git-Bash 下 `subprocess.run([...])` 会篡改字符串，导致 `option not found` 错误
- 黑屏帧方案完全规避此问题

**转场类型：**

| 类型 | 说明 | 推荐场景 |
|------|------|----------|
| `black` | 黑屏硬切（插入0.3-0.5s黑屏帧） | 通用，干净利落 |
| `none` | 无转场（直接拼接） | 快节奏视频 |

**Python 实现（完整示例）：**

```python
import subprocess, os

FFMPEG = r'D:\soft\ffmpeg\bin\ffmpeg.exe'
RATIO_PRESETS = {'9:16': (1080, 1920), '16:9': (1920, 1080)}

def make_black_clip(output_path, duration=0.5, ratio='9:16'):
    """生成纯黑MP4过渡帧（含静音AAC轨道）"""
    W, H = RATIO_PRESETS[ratio]
    tmp_v = output_path + '.tmp_v.mp4'
    tmp_a = output_path + '.tmp_a.m4a'

    # 1. 生成黑屏视频
    subprocess.run([
        FFMPEG, '-y',
        '-f', 'lavfi', '-i', f'color=c=black:size={W}x{H}:d={duration}',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-r', '30',
        tmp_v
    ], capture_output=True)

    # 2. 生成静音AAC
    subprocess.run([
        FFMPEG, '-y',
        '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo',
        '-t', str(duration),
        '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
        tmp_a
    ], capture_output=True)

    # 3. 合成 video + audio
    subprocess.run([
        FFMPEG, '-y', '-i', tmp_v, '-i', tmp_a,
        '-c:v', 'copy', '-c:a', 'copy',
        output_path
    ], capture_output=True)

    # 清理临时文件
    for t in [tmp_v, tmp_a]:
        if os.path.exists(t):
            os.remove(t)

def insert_black_transitions(clip_paths, transition_duration=0.5, ratio='9:16'):
    """在片段之间插入黑屏过渡帧，返回新的片段列表"""
    if len(clip_paths) < 2 or transition_duration <= 0:
        return clip_paths[:]

    out_dir = os.path.dirname(clip_paths[0]) or '.'
    new_clips = []

    for i, cp in enumerate(clip_paths):
        new_clips.append(cp)
        if i < len(clip_paths) - 1:
            black_path = os.path.join(out_dir, f'_black_trans_{i:02d}.mp4')
            make_black_clip(black_path, transition_duration, ratio)
            new_clips.append(black_path)

    return new_clips

# 使用：
# clips = ['_title.mp4', 'seg_01.mp4', 'seg_02.mp4', ...]
# clips_with_transitions = insert_black_transitions(clips, duration=0.5, ratio='9:16')
# concat_mp4s(clips_with_transitions, 'output/final_video.mp4')
```

**关键要求：黑屏帧也必须含 audio 流**

concat `copy` 模式要求所有片段流结构一致。黑屏帧必须生成 `video + audio` 的 MP4，不能只有视频流。

---

### 步骤6：验证输出

检查生成的视频文件：

```bash
ffprobe -v quiet -print_format json -show_format -show_streams output/final_video.mp4
```

**必须验证：**
- ✅ 有 `video` 流（codec=h264）
- ✅ 有 `audio` 流（codec=aac）
- ✅ 音频时长 ≈ 视频时长
- ✅ 播放测试：音画同步，无乱码

---

## 手机播放优化参数

| 参数 | 作用 | 推荐值 |
|------|------|--------|
| `-pix_fmt yuv420p` | 像素格式（手机必需） | yuv420p |
| `-r 30` | 恒定帧率 | 30fps |
| `-g 30` | 关键帧间隔（1秒） | 30 |
| `-ar 44100` | 音频采样率（标准） | 44100 |
| `-ac 2` | 音频声道（立体声） | 2 |
| `-movflags +faststart` | 移动端快速启动 | +faststart |
| `-avoid_negative_ts make_zero` | 修复时间戳 | make_zero |
| `-shortest` | 以较短的流为准 | （音频结束即停） |

---

## 图片处理规范

**必须使用 `pad` 而非 `crop`：**

```
# ❌ 错误：会裁切图片内容
-vf scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920

# ✅ 正确：等比缩放完整显示，黑边填充
-vf scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black
```

---

## 语音类型推荐

| 场景 | 推荐语音 | 特点 |
|------|---------|------|
| 教学视频 | `zh-CN-XiaoxiaoNeural` | 女声，温柔清晰 |
| 企业宣传 | `zh-CN-YunxiNeural` | 男声，沉稳专业 |
| 短视频/娱乐 | `zh-CN-XiaoyiNeural` | 女声，活泼轻快 |
| 新闻解说 | `zh-CN-YunyangNeural` | 男声，专业正式 |

---

## 常见错误和解决方案

### 错误1：标题页中文乱码
- **原因**：FFmpeg `drawtext` 在Windows下无法加载中文字体
- **解决**：用PIL生成标题页图片，再用FFmpeg合成视频

### 错误2：concat后视频无声
- **原因**：标题页MP4无声轨，concat `copy` 模式丢弃音频
- **解决**：标题页也生成带静音AAC轨道的MP4，所有片段流结构一致

### 错误3：音画不一致（旁白讲A图内容却配B图）
- **原因**：旁白脚本未精确匹配图片内容
- **解决**：撰写旁白时严格按「描述图片视觉内容」模板，每段只讲对应图片

### 错误4：图片内容被裁切
- **原因**：使用了 `crop` 过滤器
- **解决**：改用 `pad` 过滤器，等比缩放完整显示

### 错误5：FFmpeg not found
- **解决**：检查FFmpeg安装路径，或使用绝对路径

### 错误6：转场效果失败（xfade 报错）
- **原因**：`xfade`/`acrossfade` 的 `filter_complex` 字符串在 Windows/Git-Bash 下被 `subprocess.run()` 篡改
- **解决**：改用黑屏帧方案（见步骤5），100% 兼容

### 错误7：黑屏帧无声轨，concat 后音频异常
- **原因**：黑屏过渡帧只含视频流，concat copy 时流结构不一致
- **解决**：`make_black_clip()` 必须生成含静音 AAC 轨道的 MP4

---

## 转场效果参考

### 黑屏帧方案（推荐）

**原理**：在片段之间插入纯黑 MP4 文件（含静音 AAC 轨道），再用 concat copy 模式拼接。

**优点**：
- 100% 兼容，不依赖复杂滤镜
- 无平台差异（Windows/Mac/Linux 均可用）
- 调试方便（黑屏帧是独立文件，可单独检查）

**参数说明**：

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `transition` | 转场类型 | `black`（黑屏硬切） |
| `transition_duration` | 黑屏持续时间 | 0.3–0.5s（短视频） |
| `ratio` | 黑屏帧尺寸 | 与视频比例一致（自动匹配） |

**配置文件示例**：

```json
{
  "transition": "black",
  "transition_duration": 0.5,
  "ratio": "9:16"
}
```

**与其他方案对比**：

| 方案 | 稳定性 | 复杂度 | 推荐度 |
|------|--------|--------|--------|
| 黑屏帧 + concat copy | ⭐⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐⭐ |
| `xfade` + `acrossfade` | ⭐⭐ | 高 | ❌ 不推荐 |
| 直接拼接（无转场） | ⭐⭐⭐⭐⭐ | 最低 | ⭐⭐⭐ |

### 为什么不用 xfade？

`xfade` 需要构造超长 `filter_complex` 字符串，例如：

```
[0][1]xfade=duration=0.5:transition=fade[01];
[01][2]xfade=duration=0.5:transition=fade[012];
...
```

在 Python 中通过 `subprocess.run([...])` 调用时，Windows/Git-Bash 会篡改超长字符串（空格、引号、冒号被重新解析），导致 FFmpeg 报 `Option not found` 错误（returncode=2880417800）。

黑屏帧方案完全规避此问题，代价只是极少量文件大小（0.5s 黑屏帧约 50–100KB）。

---

## 更新日志

**v1.5.0** (2026-06-24)
- ✅ 转场效果改用黑屏帧方案（100% 稳定，替代 xfade）
- ✅ 新增 `make_black_clip()` 生成纯黑过渡帧（含静音AAC轨道）
- ✅ 新增 `insert_black_transitions()` 自动在片段间插入转场
- ✅ 文档新增「步骤5：转场效果」和「转场效果参考」章节
- ✅ 修复 Windows/Git-Bash 下 `filter_complex` 字符串篡改导致 xfade 失败的问题
- ✅ 更新常见错误章节（新增错误6、错误7）

**v1.4.0** (2026-06-24)
- ✅ 新增字幕生成 + 烧录功能（SRT 文件 + FFmpeg subtitles/drawtext）
- ✅ 新增 AI 脚本生成（`auto_script.py`，Vision API 分析图片内容）
- ✅ 新增热点话题获取（`fetch_hot_topics_v2.py`，6个平台）
- ✅ 新增多比例支持（`RATIO_PRESETS`：9:16 / 16:9 / 1:1 / 4:5）
- ✅ 新增封面图自动生成（`generate_cover()`）
- ✅ 脚本版本升级：`generate_video_v2.py` v2.0，`generate_subtitle.py` v1.1

**v1.3.0** (2026-06-24)
- ✅ 修复图片裁切问题（`crop` → `pad`，完整显示图片）
- ✅ 修复标题页中文乱码（FFmpeg drawtext → PIL生成标题图片）
- ✅ 修复concat后音频丢失（标题页也生成带静音AAC轨道的MP4）
- ✅ 新增「音画匹配规范」：旁白必须精确描述对应图片内容
- ✅ 新增完整Python合成示例代码（步骤4）
- ✅ 新增常见错误排查章节
- ✅ 优化手机播放参数（新增 `-shortest` 参数说明）

**v1.2.0** (2026-06-24)
- 新增「热点获取」功能（步骤0）
- 支持6个热点来源

**v1.1.0** (2026-06-22)
- 添加手机播放优化方案
- 改进视频生成工作流程（分片生成再合并）

**v1.0.0** (2026-06-21)
- 初始版本

---

**技能维护者：** WorkBuddy AI  
**最后更新：** 2026-06-24
