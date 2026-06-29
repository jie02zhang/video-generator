"""
video_generator.py - Video Generator Skill 核心实现

将有序图片序列和旁白音频合成为同步 MP4 视频。
支持多比例输出、黑屏转场效果。

安全说明：
- 所有 FFmpeg 调用通过 _run_safe() 统一超时控制和错误处理
- FFmpeg 路径通过 _resolve_ffmpeg() 安全检测，支持多种配置方式
- 输入文件路径经过 exists 校验，防止路径遍历
"""

import subprocess
import os
import shutil
import json
import asyncio
import tempfile
import stat
from typing import List, Tuple, Optional, Dict


class VideoProcessor:
    """
    视频处理器。
    封装所有 FFmpeg 操作，统一错误处理和安全检查。
    """

    # 支持的输出比例预设
    RATIO_PRESETS: Dict[str, Tuple[int, int]] = {
        "9:16": (1080, 1920),
        "16:9": (1920, 1080),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
    }

    def __init__(self, ffmpeg_path: Optional[str] = None, allowed_dirs: Optional[List[str]] = None):
        """
        初始化处理器。

        :param ffmpeg_path: 指定的 FFmpeg 路径
        :param allowed_dirs: 允许访问的目录白名单（防止路径遍历）
        """
        self.ffmpeg = self._resolve_ffmpeg(ffmpeg_path)
        self.tmp_files: List[str] = []
        self.allowed_dirs = [os.path.abspath(d) for d in (allowed_dirs or [])]

    @staticmethod
    def _resolve_ffmpeg(path: Optional[str]) -> str:
        """安全地解析 FFmpeg 可执行文件路径"""
        if path:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"指定的 FFmpeg 路径不存在: {path}")
            return path

        # 环境变量
        for env_var in ("FFMPEG_PATH", "FFMPEG"):
            env_path = os.environ.get(env_var)
            if env_path and os.path.isfile(env_path):
                return env_path

        # 系统 PATH
        path_from_system = shutil.which("ffmpeg")
        if path_from_system:
            return path_from_system

        # 常见安装路径
        candidates = [
            "/usr/local/bin/ffmpeg",
            "/usr/bin/ffmpeg",
            "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
            "C:/soft/ffmpeg/bin/ffmpeg.exe",
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        raise RuntimeError(
            "未找到 FFmpeg 可执行文件。\n"
            "请安装 FFmpeg (https://ffmpeg.org) 并添加到系统 PATH，\n"
            "或设置环境变量 FFMPEG_PATH 指向 ffmpeg 可执行文件。"
        )

    def _validate_path(self, path: str, check_allowed: bool = True) -> str:
        """
        验证路径安全性（防止路径遍历）

        :param path: 待验证路径
        :param check_allowed: 是否检查白名单目录
        :return: 规范化后的绝对路径
        :raises PermissionError: 路径不在白名单内
        """
        abs_path = os.path.abspath(path)

        if check_allowed and self.allowed_dirs:
            if not any(abs_path.startswith(allowed) for allowed in self.allowed_dirs):
                raise PermissionError(f"路径不在允许的目录内: {abs_path}")

        return abs_path

    def _run_safe(
        self,
        cmd: List[str],
        description: str = "FFmpeg 操作",
        timeout: int = 300,
    ) -> None:
        """
        安全执行 FFmpeg 命令。
        统一超时控制、错误捕获和日志记录。

        :param cmd: FFmpeg 命令参数列表
        :param description: 操作描述（用于错误信息）
        :param timeout: 超时时间（秒）
        :raises RuntimeError: 命令执行失败时抛出
        """
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip()[-500:] or "未知错误（无 stderr 输出）"
                raise RuntimeError(
                    f"{description} 失败 (exit code={result.returncode}):\n{error_msg}"
                )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"{description} 超时（>{timeout}秒），请检查输入文件是否正常")
        except FileNotFoundError as e:
            raise RuntimeError(f"无法执行 FFmpeg：{e}")
        except Exception as e:
            raise RuntimeError(f"{description} 发生异常：{e}")

    def _vf_pad(self, ratio: str = "9:16") -> str:
        """生成 FFmpeg pad 滤镜字符串（等比缩放 + 黑边填充，不裁切）"""
        w, h = self.RATIO_PRESETS.get(ratio, (1080, 1920))
        return (
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
        )

    def make_segment(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        ratio: str = "9:16",
    ) -> str:
        """
        单个图片 + 音频 → 完整 MP4 片段（含 video + audio 双流）

        :param image_path: 输入图片路径
        :param audio_path: 输入音频路径
        :param output_path: 输出 MP4 路径
        :param ratio: 视频比例
        :return: 输出文件路径
        """
        # 路径安全检查
        image_path = self._validate_path(image_path)
        audio_path = self._validate_path(audio_path)
        output_path = self._validate_path(output_path)

        for p, label in [(image_path, "图片"), (audio_path, "音频")]:
            if not os.path.isfile(p):
                raise FileNotFoundError(f"{label}文件不存在: {p}")

        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-pix_fmt", "yuv420p", "-r", "30", "-g", "30",
            "-vf", self._vf_pad(ratio),
            "-shortest",
            "-avoid_negative_ts", "make_zero",
            output_path,
        ]
        self._run_safe(cmd, f"合成片段 [{os.path.basename(image_path)}]")
        return output_path

    def make_title_clip(
        self,
        title_image_path: str,
        output_path: str,
        duration: float = 3.0,
        ratio: str = "9:16",
    ) -> str:
        """
        标题页图片 → MP4（含静音 AAC 音频轨道，保证流结构一致）

        :param title_image_path: 标题页图片路径
        :param output_path: 输出 MP4 路径
        :param duration: 标题页持续时间（秒）
        :param ratio: 视频比例
        :return: 输出文件路径
        """
        title_image_path = self._validate_path(title_image_path)
        output_path = self._validate_path(output_path)

        if not os.path.isfile(title_image_path):
            raise FileNotFoundError(f"标题页图片不存在: {title_image_path}")

        tmp_video = output_path + ".tmp_vid.mp4"
        tmp_audio = output_path + ".tmp_aud.m4a"
        self.tmp_files.extend([tmp_video, tmp_audio])

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
            ], "生成标题页视频轨")

            # 生成静音 AAC 轨道
            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "192k",
                tmp_audio,
            ], "生成标题页静音轨")

            # 合并视频轨和音频轨
            self._run_safe([
                self.ffmpeg, "-y",
                "-i", tmp_video, "-i", tmp_audio,
                "-c:v", "copy", "-c:a", "copy",
                "-shortest",
                output_path,
            ], "合并标题页音视频")
        finally:
            self._cleanup_tmp()

        return output_path

    def make_black_frame(
        self,
        output_path: str,
        duration: float = 0.5,
        ratio: str = "9:16",
    ) -> str:
        """
        生成黑屏过渡帧（含静音 AAC 轨道）

        :param output_path: 输出 MP4 路径
        :param duration: 黑屏持续时间（秒）
        :param ratio: 视频比例
        :return: 输出文件路径
        """
        output_path = self._validate_path(output_path)
        w, h = self.RATIO_PRESETS.get(ratio, (1080, 1920))
        tmp_v = output_path + ".tmp_v.mp4"
        tmp_a = output_path + ".tmp_a.m4a"
        self.tmp_files.extend([tmp_v, tmp_a])

        try:
            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:size={w}x{h}:d={duration}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", "30",
                tmp_v,
            ], "生成黑屏视频帧")

            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-c:a", "aac", "-b:a", "192k",
                tmp_a,
            ], "生成黑屏静音轨")

            self._run_safe([
                self.ffmpeg, "-y",
                "-i", tmp_v, "-i", tmp_a,
                "-c:v", "copy", "-c:a", "copy",
                output_path,
            ], "合并黑屏帧")
        finally:
            self._cleanup_tmp()

        return output_path

    def concat_clips(
        self,
        clip_list: List[str],
        final_output_path: str,
    ) -> str:
        """
        拼接多个 MP4 片段（所有片段必须具有相同的流结构）

        :param clip_list: 片段路径列表
        :param final_output_path: 最终输出路径
        :return: 输出文件路径
        """
        final_output_path = self._validate_path(final_output_path)

        for clip in clip_list:
            clip = self._validate_path(clip)
            if not os.path.isfile(clip):
                raise FileNotFoundError(f"待拼接片段不存在: {clip}")

        concat_file = final_output_path + ".concat.txt"
        self.tmp_files.append(concat_file)

        try:
            with open(concat_file, "w", encoding="utf-8") as f:
                for clip_path in clip_list:
                    # 转义单引号（防止命令注入）
                    safe_path = os.path.abspath(clip_path).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            self._run_safe([
                self.ffmpeg, "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-movflags", "+faststart",
                final_output_path,
            ], f"拼接 {len(clip_list)} 个片段")
        finally:
            self._cleanup_tmp()

        return final_output_path

    def _cleanup_tmp(self) -> None:
        """清理临时文件（设置安全权限）"""
        for tmp in self.tmp_files:
            if os.path.exists(tmp):
                try:
                    # Windows: 先设置只读属性，然后删除
                    if os.name == 'nt':
                        os.chmod(tmp, stat.S_IREAD)
                    os.remove(tmp)
                except OSError:
                    pass
        self.tmp_files.clear()

    def verify_output(self, video_path: str) -> Tuple[bool, Dict]:
        """
        验证输出视频文件的完整性

        :param video_path: 视频文件路径
        :return: (是否通过, 检查详情字典)
        """
        video_path = self._validate_path(video_path, check_allowed=False)

        if not os.path.isfile(video_path):
            return False, {"文件存在": False}

        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                video_path,
            ], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return False, {"ffprobe": "无法读取文件"}

            info = json.loads(result.stdout)
            streams = info.get("streams", [])

            has_video = any(
                s.get("codec_type") == "video"
                for s in streams
            )
            has_audio = any(
                s.get("codec_type") == "audio"
                for s in streams
            )

            checks = {
                "文件存在": True,
                "视频流": has_video,
                "音频流": has_audio,
            }
            return all(checks.values()), checks

        except Exception as e:
            return False, {"验证异常": str(e)}


# ===== 标题页图片生成（PIL，跨平台） =====

def create_title_image(
    output_path: str,
    title: str,
    subtitle: str = "",
    tag: str = "干货教学",
    channel: str = "@频道名",
    width: int = 1080,
    height: int = 1920,
) -> str:
    """
    使用 PIL 生成中文标题页图片（避免 FFmpeg drawtext 中文乱码问题）

    字体加载采用跨平台回退策略，自动检测系统中文字体。

    :param output_path: 输出图片路径
    :param title: 主标题
    :param subtitle: 副标题
    :param tag: 标签文字
    :param channel: 频道名
    :param width: 图片宽度
    :param height: 图片高度
    :return: 输出图片路径
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError(
            "未安装 Pillow。请运行：pip install Pillow"
        )

    img = Image.new("RGB", (width, height), color=(26, 26, 46))
    draw = ImageDraw.Draw(img)

    # 跨平台中文字体检测
    font_candidates = [
        "/System/Library/Fonts/PingFang.ttc",              # macOS
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 备选
        "C:/Windows/Fonts/msyh.ttc",                       # Windows
        "C:/Windows/Fonts/simhei.ttf",                     # Windows 备选
    ]

    font_path = None
    for candidate in font_candidates:
        if os.path.isfile(candidate):
            font_path = candidate
            break

    if font_path is None:
        raise RuntimeError(
            "未找到中文字体。\n"
            "请安装系统中文字体，或通过 FONT_PATH 环境变量指定字体文件路径。"
        )

    def load_font(size: int):
        return ImageFont.truetype(font_path, size)

    def center_text(text: str, y_pos: int, font, fill_color) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_pos), text, font=font, fill=fill_color)

    cy = height // 2
    center_text(title, cy - 120, load_font(72), (255, 255, 255))
    if subtitle:
        center_text(subtitle, cy - 30, load_font(48), (160, 176, 255))

    # 标签背景（黄色圆角矩形）
    tag_w, tag_h = 180, 50
    draw.rounded_rectangle([
        (width - tag_w) // 2, cy + 60,
        (width + tag_w) // 2, cy + 60 + tag_h,
    ], radius=25, fill=(255, 204, 0))
    center_text(tag, cy + 68, load_font(36), (30, 30, 30))

    if channel:
        center_text(channel, cy + 180, load_font(28), (136, 136, 136))

    img.save(output_path)
    return output_path


# ===== 语音合成（edge-tts） =====

async def generate_audio(
    text: str,
    output_path: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+20%",
) -> str:
    """
    使用 edge-tts 将文本合成为语音 MP3

    :param text: 旁白文本
    :param output_path: 输出 MP3 路径
    :param voice: edge-tts 语音 ID
    :param rate: 语速（如 "+20%" 表示加速 20%）
    :return: 输出文件路径
    """
    try:
        import edge_tts
    except ImportError:
        raise RuntimeError(
            "未安装 edge-tts。请运行：pip install edge-tts"
        )

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)
    return output_path


def generate_audio_sync(
    text: str,
    output_path: str,
    voice: str = "zh-CN-XiaoxiaoNeural",
    rate: str = "+20%",
) -> str:
    """同步版本的语音合成（方便非 async 环境调用）"""
    return asyncio.run(generate_audio(text, output_path, voice, rate))


# ===== 完整视频生成流程 =====

def generate_video(
    image_audio_pairs: List[Tuple[str, str]],
    output_path: str,
    title_config: Optional[Dict] = None,
    ratio: str = "9:16",
    transition: bool = True,
    transition_duration: float = 0.5,
    allowed_dirs: Optional[List[str]] = None,
) -> str:
    """
    完整视频生成流程。

    :param image_audio_pairs: [(图片路径, 音频路径), ...]
    :param output_path: 最终视频输出路径
    :param title_config: 标题页配置，格式：
        {"title": "...", "subtitle": "...", "tag": "...", "channel": "..."}
        为 None 时不生成标题页
    :param ratio: 视频比例
    :param transition: 是否启用黑屏转场
    :param transition_duration: 转场持续时间（秒）
    :return: 最终视频路径
    """
    proc = VideoProcessor(allowed_dirs=allowed_dirs)
    clips: List[str] = []
    work_dir = os.path.dirname(os.path.abspath(output_path)) or "."

    # 如果提供了 allowed_dirs，验证 work_dir
    if allowed_dirs:
        work_dir = proc._validate_path(work_dir)

    # 1. 标题页（可选）
    if title_config:
        title_img = os.path.join(work_dir, "_title.png")
        title_mp4 = os.path.join(work_dir, "_title.mp4")
        create_title_image(title_img, **title_config)
        proc.make_title_clip(title_img, title_mp4, ratio=ratio)
        clips.append(title_mp4)

    # 2. 内容片段
    for i, (img, aud) in enumerate(image_audio_pairs, 1):
        seg_path = os.path.join(work_dir, f"_seg_{i:02d}.mp4")
        proc.make_segment(img, aud, seg_path, ratio=ratio)
        clips.append(seg_path)

        # 插入黑屏转场（最后一段之后不加）
        if transition and i < len(image_audio_pairs):
            black_path = os.path.join(work_dir, f"_trans_{i:02d}.mp4")
            proc.make_black_frame(black_path, duration=transition_duration, ratio=ratio)
            clips.append(black_path)

    # 3. 拼接
    final_path = proc.concat_clips(clips, output_path)

    # 4. 验证
    ok, details = proc.verify_output(final_path)
    if not ok:
        raise RuntimeError(f"输出视频验证失败：{details}")

    return final_path


# ===== CLI 入口 =====

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video Generator - 图片序列转视频")
    parser.add_argument("--images", nargs="+", required=True, help="图片文件路径列表")
    parser.add_argument("--audios", nargs="+", required=True, help="音频文件路径列表")
    parser.add_argument("--output", required=True, help="输出视频路径")
    parser.add_argument("--ratio", default="9:16", help="视频比例（默认 9:16）")
    parser.add_argument("--title", help="标题页主标题（不提供则不生成标题页）")
    parser.add_argument("--subtitle", default="", help="标题页副标题")
    parser.add_argument("--no-transition", action="store_true", help="禁用转场效果")
    parser.add_argument("--allowed-dirs", nargs="+", help="允许访问的目录白名单（防止路径遍历）")
    args = parser.parse_args()

    if len(args.images) != len(args.audios):
        print("错误：图片数量和音频数量必须相同")
        exit(1)

    title_cfg = None
    if args.title:
        title_cfg = {"title": args.title, "subtitle": args.subtitle}

    result = generate_video(
        image_audio_pairs=list(zip(args.images, args.audios)),
        output_path=args.output,
        title_config=title_cfg,
        ratio=args.ratio,
        transition=not args.no_transition,
        allowed_dirs=args.allowed_dirs,
    )

    print(f"视频生成成功：{result}")
