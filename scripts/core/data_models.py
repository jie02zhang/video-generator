"""
数据模型定义
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import time

from scripts.core.exceptions import ValidationError


class ImageSize(str, Enum):
    """图片尺寸"""
    SQUARE = "512x512"
    LANDSCAPE = "768x512"
    PORTRAIT = "512x768"
    HD = "1024x1024"
    FULL_HD = "1920x1080"
    PORTRAIT_HD = "1080x1920"


class VideoDuration(str, Enum):
    """视频时长"""
    SHORT_5S = "5s"
    MEDIUM_10S = "10s"
    LONG_15S = "15s"
    EXTENDED_30S = "30s"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ImageGenerationRequest:
    """图片生成请求"""
    prompt: str
    negative_prompt: Optional[str] = None
    size: ImageSize = ImageSize.SQUARE
    num_images: int = 1
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 20
    model_name: Optional[str] = None
    
    def __post_init__(self):
        if not self.prompt or not self.prompt.strip():
            raise ValidationError("提示词不能为空")
        if self.num_images < 1:
            raise ValidationError("生成数量必须大于0")
        if self.guidance_scale < 0:
            raise ValidationError("引导尺度必须大于等于0")
        if self.num_inference_steps < 1:
            raise ValidationError("推理步数必须大于0")


@dataclass
class ImageGenerationResponse:
    """图片生成响应"""
    success: bool
    images: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoGenerationRequest:
    """视频生成请求"""
    prompt: str
    negative_prompt: Optional[str] = None
    duration: VideoDuration = VideoDuration.SHORT_5S
    aspect_ratio: str = "16:9"
    model_name: Optional[str] = None
    image_path: Optional[str] = None  # 参考图片
    
    def __post_init__(self):
        if not self.prompt or not self.prompt.strip():
            raise ValidationError("提示词不能为空")


@dataclass
class VideoGenerationResponse:
    """视频生成响应"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    success: bool = False
    video_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_completed(self) -> bool:
        """检查任务是否完成"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def is_success(self) -> bool:
        """检查任务是否成功"""
        return self.status == TaskStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED
