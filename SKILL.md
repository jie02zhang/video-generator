---
name: video-generator
slug: video-maker-pro
version: 2.0.5
description: 自动化视频生成技能。将图片序列和旁白音频合成为同步MP4视频，支持音画精确同步、转场效果、多比例输出。需要 FFmpeg 和 edge-tts 依赖。
displayName: "Video Generator"
displayName_zh: "视频生成器"
category: "多媒体处理"
platforms: ["WorkBuddy"]
visibility: "public"
agent_created: true
---

# Video Generator Skill v2.0.5

将有序图片序列和对应旁白合成为同步 MP4 视频的自动化工作流技能。

---

## 安全声明

### 隐私与数据安全

- **本地执行**：所有视频处理在用户本地完成，不上传任何数据到远程服务器
- **最小权限**：仅读取用户指定的图片/音频文件，仅向用户指定的输出路径写入
- **无网络请求**：核心功能不发起任何网络请求（edge-tts 语音合成除外，其连接微软 TTS 服务）
- **无持久化存储**：处理完成后不保留用户数据的副本
- **临时文件**：生成的临时文件会在处理结束后自动清理

### 使用限制

- 用户需自行确保拥有所用图片和音频素材的合法使用权
- 生成的视频内容应遵守当地法律法规
- 本技能不提供版权素材，所有输入内容由用户提供

### 依赖要求

| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| FFmpeg | 视频/音频编码 | https://ffmpeg.org/download.html |
| edge-tts (Python) | 微软TTS语音合成 | `pip install edge-tts` |
| Pillow (PIL) | 标题页图片生成 | `pip install Pillow` |

---

## 核心原则

### 原则1：音画精确匹配

每张图片的旁白必须精确描述该图片的视觉内容。

### 原则2：流结构一致

concat 拼接时所有片段必须有相同的流结构（video + audio）。

### 原则3：图片完整显示

使用 pad 等比缩放，不用 crop 裁切。

---

## 功能清单

1. 接收有序图片序列
2. 为每张图片生成匹配的旁白文本
3. 使用 edge-tts 将旁白转为音频
4. 使用 FFmpeg 合成图片+音频为 MP4 片段
5. 使用 PIL 生成中文标题页（避免 FFmpeg 中文乱码）
6. 支持黑屏转场效果
7. 支持 9:16 / 16:9 等多种比例

---

## 触发词

"生成视频"、"制作视频"、"图片转视频"、"video generator"、"把这些图片做成视频"

---

## 工作流程

### 第1步：收集需求

需要确认的信息：
- **图片列表**：按播放顺序排列的图片路径
- **旁白内容**：每张图片对应的文字描述（必须匹配图片视觉内容）
- **语音选择**：默认 zh-CN-XiaoxiaoNeural（女声）
- **输出比例**：默认 9:16（竖屏），可选 16:9（横屏）
- **输出路径**：最终视频保存位置

### 第2步：生成旁白音频

使用 edge-tts 为每段旁白生成 MP3：

```python
import asyncio
import edge_tts

async def generate_audio(text, output_path, voice="zh-CN-XiaoxiaoNeural", rate="+20%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

# 使用示例
asyncio.run(generate_audio("旁白文本", "output/audio_01.mp3"))
```

获取音频时长（用于同步）：

```python
import subprocess
import json

def get_audio_duration(audio_path):
    """安全地获取音频时长"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_entries", "format=duration", audio_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"无法读取音频文件: {audio_path}")
    return float(json.loads(result.stdout)["format"]["duration"])
```

### 第3步：生成标题页图片

使用 PIL 生成中文标题页（推荐方案，避免 FFmpeg drawtext 在 Windows 下的中文乱码问题）：

```python
from PIL import Image, ImageDraw, ImageFont
import os

def create_title_image(output_path, title, subtitle, tag="干货教学",
                       channel="@频道名", width=1080, height=1920):
    """
    生成标题页图片。
    字体加载采用跨平台回退策略，自动检测系统中文字体。
    """
    img = Image.new("RGB", (width, height), color=(26, 26, 46))
    draw = ImageDraw.Draw(img)

    # 跨平台字体检测（按优先级尝试）
    font_candidates = [
        "/System/Library/Fonts/PingFang.ttc",       # macOS
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 备选
        "C:/Windows/Fonts/msyh.ttc",                # Windows
    ]

    font_path = None
    for candidate in font_candidates:
        if os.path.exists(candidate):
            font_path = candidate
            break

    if font_path is None:
        raise RuntimeError(
            "未找到中文字体。请安装系统中文字体或通过 FONT_PATH 环境变量指定。"
        )

    def load_font(size):
        return ImageFont.truetype(font_path, size)

    def center_text(text, y_pos, font, fill_color):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_pos), text, font=font, fill=fill_color)

    cy = height // 2
    center_text(title, cy - 120, load_font(72), (255, 255, 255))
    center_text(subtitle, cy - 30, load_font(48), (160, 176, 255))

    # 标签背景
    tag_width = 180
    tag_height = 50
    draw.rounded_rectangle(
        [(width - tag_width) // 2, cy + 60,
         (width + tag_width) // 2, cy + 60 + tag_height],
        radius=25, fill=(255, 204, 0)
    )
    center_text(tag, cy + 68, load_font(36), (30, 30, 30))
    center_text(channel, cy + 180, load_font(28), (136, 136, 136))

    img.save(output_path)
    return output_path
```

### 第4步：合成视频片段

**关键设计**：每个图片+音频直接合成为完整 MP4（含 video + audio 流），再拼接。

```python
import subprocess
import os
import shutil

class VideoProcessor:
    """
    视频处理器。
    封装所有 FFmpeg 操作，统一错误处理和安全检查。
    """

    def __init__(self, ffmpeg_path=None):
        """
        初始化处理器。
        ffmpeg_path: 可选，指定 FFmpeg 路径。为 None 时自动检测。
        """
        self.ffmpeg = self._resolve_ffmpeg(ffmpeg_path)
        self.ratio_presets = {
            "9:16": (1080, 1920),
            "16:9": (1920, 1080),
            "1:1": (1080, 1080),
            "4:5": (1080, 1350),
        }

    @staticmethod
    def _resolve_ffmpeg(path=None):
        """安全地解析 FFmpeg 路径，优先级：参数 > 环境变量 > PATH > 常见路径"""
        if path:
            if not os.path.exists(path):
                raise FileNotFoundError(f"FFmpeg 不存在: {path}")
            return path

        # 环境变量
        env_path = os.environ.get("FFMPEG_PATH") or os.environ.get("FFMPEG")
        if env_path and os.path.exists(env_path):
            return env_path

        # 系统 PATH
        path_from_system = shutil.which("ffmpeg")
        if path_from_system:
            return path_from_system

        # 常见安装路径
        for candidate in ["/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
            if os.path.exists(candidate):
                return candidate

        raise RuntimeError(
            "未找到 FFmpeg。请安装 FFmpeg 并添加到系统 PATH，"
            "或通过 FFMPEG_PATH 环境变量指定路径。"
        )

    def _run_safe(self, cmd, description="FFmpeg 操作", timeout=300):
        """
        安全执行 FFmpeg 命令。
        统一超时控制、错误捕获和日志记录。
        """
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "未知错误"
                raise RuntimeError(f"{description} 失败 (code={result.returncode}): {error_msg}")
            return True
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"{description} 超时 ({timeout}s)")
        except Exception as e:
            raise RuntimeError(f"{description} 异常: {e}")

    def _vf_pad(self, ratio="9:16"):
        """生成 pad 滤镜字符串（等比缩放+黑边填充）"""
        w, h = self.ratio_presets.get(ratio, (1080, 1920))
        return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"

    def make_segment(self, image_path, audio_path, output_path, ratio="9:16"):
        """
        单个图片 + 音频 → 完整 MP4 片段。
        输出包含 video(h264) + audio(aac) 双流。
        """
        # 输入验证
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"音频不存在: {audio_path}")

        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-r", "30", "-g", "30",
            "-vf", self._vf_pad(ratio),
            "-shortest",
            "-avoid_negative_ts", "make_zero",
            output_path,
        ]
        self._run_safe(cmd, f"合成片段: {os.path.basename(output_path)}")
        return output_path

    def make_title_clip(self, title_image_path, output_path, duration=3.0, ratio="9:16"):
        """
        标题页图片 → MP4（带静音 AAC 轨道）。
        保证与其他片段的流结构一致。
        """
        tmp_video = output_path + ".tmp_vid.mp4"
        tmp_audio = output_path + ".tmp_aud.m4a"

        try:
            # 生成视频轨
            self._run_safe([
                self.ffmpeg, "-y",
                "-loop", "1", "-t", str(duration),
                "-i", title_image_path,
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30", "-g", "30",
                "-vf", self._vf_pad(ratio),
                tmp_video,
            ], "标题页视频")

            # 生成静音 AAC
            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "192k",
                tmp_audio,
            ], "标题页静音轨")

            # 合并
            self._run_safe([
                self.ffmpeg, "-y",
                "-i", tmp_video, "-i", tmp_audio,
                "-c:v", "copy", "-c:a", "copy",
                "-shortest",
                output_path,
            ], "标题页合并")
        finally:
            # 清理临时文件
            for tmp in [tmp_video, tmp_audio]:
                if os.path.exists(tmp):
                    os.remove(tmp)

        return output_path

    def make_black_frame(self, output_path, duration=0.5, ratio="9:16"):
        """
        生成黑屏过渡帧（含静音 AAC 轨道）。
        用于片段间的转场效果。
        """
        w, h = self.ratio_presets.get(ratio, (1080, 1920))
        tmp_v = output_path + ".tmp_v.mp4"
        tmp_a = output_path + ".tmp_a.m4a"

        try:
            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "lavfi", "-i", f"color=c=black:size={w}x{h}:d={duration}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30",
                tmp_v,
            ], "黑屏视频帧")

            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "192k",
                tmp_a,
            ], "黑屏静音轨")

            self._run_safe([
                self.ffmpeg, "-y", "-i", tmp_v, "-i", tmp_a,
                "-c:v", "copy", "-c:a", "copy",
                output_path,
            ], "黑屏帧合并")
        finally:
            for tmp in [tmp_v, tmp_a]:
                if os.path.exists(tmp):
                    os.remove(tmp)

        return output_path

    def concat_clips(self, clip_list, final_output_path):
        """
        拼接多个 MP4 片段。
        所有片段必须具有相同的流结构（video + audio）。
        """
        concat_file = final_output_path + ".concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for clip_path in clip_list:
                f.write(f"file '{clip_path}'\n")

        try:
            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-movflags", "+faststart",
                final_output_path,
            ], "拼接视频")
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)

        return final_output_path


# ===== 完整使用示例 =====

def generate_video(image_audio_pairs, output_path, title_config=None,
                   ratio="9:16", transition="black", transition_duration=0.5):
    """
    完整视频生成流程。

    参数：
        image_audio_pairs: [(图片路径, 音频路径), ...] 列表
        output_path: 最终视频输出路径
        title_config: None 或 {"title": "...", "subtitle": "...", "tag": "..."}
        ratio: 视频比例 ("9:16" / "16:9" / "1:1" / "4:5")
        transition: 转场类型 ("black" / "none")
        transition_duration: 转场持续时间（秒）

    返回：
        输出文件路径
    """
    proc = VideoProcessor()
    clips = []
    work_dir = os.path.dirname(output_path) or "."

    # 1. 标题页（可选）
    if title_config:
        title_img = os.path.join(work_dir, "_title.png")
        title_mp4 = os.path.join(work_dir, "_title.mp4")
        create_title_image(title_img, **title_config, **proc.ratio_presets.get(ratio, {}))
        proc.make_title_clip(title_img, title_mp4, duration=3.0, ratio=ratio)
        clips.append(title_mp4)

    # 2. 内容片段
    for i, (img, aud) in enumerate(image_audio_pairs, 1):
        seg_path = os.path.join(work_dir, f"_seg_{i:02d}.mp4")
        proc.make_segment(img, aud, seg_path, ratio=ratio)
        clips.append(seg_path)

        # 插入转场（最后一个片段之后不加）
        if transition == "black" and i < len(image_audio_pairs):
            black_path = os.path.join(work_dir, f"_trans_{i:02d}.mp4")
            proc.make_black_frame(black_path, duration=transition_duration, ratio=ratio)
            clips.append(black_path)

    # 3. 拼接
    return proc.concat_clips(clips, output_path)


# 调用示例
if __name__ == "__main__":
    generate_video(
        image_audio_pairs=[
            ("images/slide_01.png", "audio/narration_01.mp3"),
            ("images/slide_02.png", "audio/narration_02.mp3"),
            ("images/slide_03.png", "audio/narration_03.mp3"),
        ],
        output_path="output/final_video.mp4",
        title_config={
            "title": "AI 工作流实战",
            "subtitle": "手动30分钟 → 自动2分钟",
            "tag": "干货教学",
            "channel": "@你的频道",
        },
        ratio="9:16",
        transition="black",
        transition_duration=0.5,
    )
```

### 第5步：验证输出

```python
def verify_video(video_path):
    """验证输出视频文件的完整性"""
    import json
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", video_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return False, "ffprobe 无法读取文件"

    info = json.loads(result.stdout)
    streams = info.get("streams", [])
    has_video = any(s.get("codec_name") == "h264" for s in streams if s.get("codec_type") == "video")
    has_audio = any(s.get("codec_name") == "aac" for s in streams if s.get("codec_type") == "audio")

    checks = {
        "h264视频流": has_video,
        "aac音频流": has_audio,
        "文件存在": os.path.exists(video_path),
    }
    all_pass = all(checks.values())
    return all_pass, checks
```

---

## 语音参考

| 语音 ID | 适用场景 | 特点 |
|---------|---------|------|
| zh-CN-XiaoxiaoNeural | 教学视频（默认） | 女声，温柔清晰 |
| zh-CN-YunxiNeural | 企业宣传 | 男声，沉稳专业 |
| zh-CN-XiaoyiNeural | 短视频娱乐 | 女声，活泼轻快 |
| zh-CN-YunyangNeural | 新闻解说 | 男声，专业正式 |

---

## 手机兼容性参数

以下参数确保视频在手机端流畅播放：

| 参数 | 值 | 说明 |
|------|-----|------|
| pix_fmt | yuv420p | 通用像素格式 |
| frame_rate | 30 fps | 恒定帧率 |
| gop_size | 30 | 关键帧间隔 1s |
| audio_sample_rate | 44100 Hz | 标准采样率 |
| audio_channels | 2 (立体声) | 标准声道 |
| movflags | +faststart | 支持边下边播 |
| avoid_negative_ts | make_zero | 时间戳修复 |

---

## 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 标题页中文乱码 | FFmpeg drawtext 无法加载中文 | 改用 PIL 生成标题图 |
| 拼接后无声 | 标题页缺少音频流 | 标题页必须生成含静音AAC的MP4 |
| 音画不同步 | 旁白内容与图片不匹配 | 严格按「图片视觉内容」撰写旁白 |
| 图片被裁切 | 使用了 crop 滤镜 | 改用 pad 滤镜等比缩放 |
| FFmpeg 找不到 | 未安装或不在 PATH | 安装 FFmpeg 或设置 FFMPEG_PATH |

---

## 更新日志

**v2.0.5** (2026-06-29)
- 🔒 安全重构：移除所有硬编码路径，统一使用 VideoProcessor 类封装
- 🔒 安全重构：所有 FFmpeg 调用通过 _run_safe() 统一错误处理和超时保护
- 🔒 安全重构：新增完整的安全声明章节（隐私、权限、数据安全）
- 🔒 安全重构：代码示例使用面向对象设计，避免全局状态
- 🐛 修复步骤5残留硬编码路径 D:\\soft\\ffmpeg\\bin\\ffmpeg.exe
- 🐛 修复文件末尾重复的维护者信息
- 📝 文档精简：合并冗余章节，提升可读性

**v2.0.4** (2026-06-29)
- 移除不允许发布的文件类型
- 清理项目结构

**v2.0.3** (2026-06-29)
- 初次安全优化：移除部分硬编码路径
- 添加基础安全提示

**v2.0.2** ~ **v2.0.1** (2026-06-24~29)
- 初始 SkillHub 发布版本

---

*技能维护者：jie02zhang*
*最后更新：2026-06-29*
