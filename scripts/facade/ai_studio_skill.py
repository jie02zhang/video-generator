"""
AI Studio Skill Facade
视频生成技能的统一入口
"""

from typing import Optional, Dict, Any, Union
import os

from scripts.core.interfaces import ImageProvider, VideoProvider
from scripts.core.data_models import (
    ImageGenerationRequest, ImageGenerationResponse,
    VideoGenerationRequest, VideoGenerationResponse
)
from scripts.core.exceptions import (
    VideoGeneratorError,
    ModelNotFoundError,
    InvalidParameterError,
    APIError,
    ConfigurationError
)
from scripts.core.factory import ProviderFactory
from scripts.core.logging_config import setup_logging, get_logger


def create_skill(
    mode: str = "beginner",
    config_path: Optional[str] = None,
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> "AIStudioSkill":
    """
    创建AI Studio Skill实例（快捷函数）
    
    Args:
        mode: 运行模式 (beginner/standard/professional)
        config_path: 配置文件路径
        log_level: 日志级别
        log_file: 日志文件路径
    
    Returns:
        AIStudioSkill: 配置好的Skill实例
    """
    return AIStudioSkill(
        config_path=config_path,
        mode=mode,
        log_level=log_level,
        log_file=log_file
    )


class AIStudioSkill:
    """
    AI Studio Skill 门面类
    
    提供统一的API用于生成图片和视频
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        mode: str = "standard",
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ):
        """
        初始化AI Studio Skill
        
        Args:
            config_path: 配置文件路径
            mode: 运行模式 (beginner/standard/expert)
            log_level: 日志级别
            log_file: 日志文件路径
        """
        # 配置日志
        setup_logging(level=log_level, log_file=log_file)
        self.logger = get_logger(__name__)
        
        # 加载配置
        self.config = ProviderFactory.load_config(config_path)
        self.mode = mode
        
        # 默认模型
        self.default_image_model = self.config.get("default_image_model", "mock")
        self.default_video_model = self.config.get("default_video_model", "mock")
        
        # 缓存的生成器（懒加载）
        self._image_generator = None
        self._video_generator = None
        
        self.logger.info(f"AIStudioSkill 初始化完成，模式: {mode}")
    
    @property
    def image_generator(self) -> ImageProvider:
        """
        图片生成器（懒加载）
        
        Returns:
            ImageProvider: 图片生成Provider实例
        """
        if not hasattr(self, '_image_generator') or self._image_generator is None:
            self._image_generator = ProviderFactory.create_image_generator(
                self.default_image_model or 'mock',
                self.mode
            )
            self.logger.debug(f"创建图片生成器: {self.default_image_model}")
        return self._image_generator
    
    @property
    def video_generator(self) -> VideoProvider:
        """
        视频生成器（懒加载）
        
        Returns:
            VideoProvider: 视频生成Provider实例
        """
        if not hasattr(self, '_video_generator') or self._video_generator is None:
            self._video_generator = ProviderFactory.create_video_generator(
                self.default_video_model or 'mock',
                self.mode
            )
            self.logger.debug(f"创建视频生成器: {self.default_video_model}")
        return self._video_generator
    
    def set_default_model(self, model_type: str, model_name: str) -> None:
        """
        设置默认模型
        
        Args:
            model_type: 模型类型 ('image' 或 'video')
            model_name: 模型名称
        """
        if model_type == 'image':
            self.default_image_model = model_name
            self._image_generator = None  # 清除缓存
            self.logger.info(f"默认图片模型设置为: {model_name}")
        elif model_type == 'video':
            self.default_video_model = model_name
            self._video_generator = None  # 清除缓存
            self.logger.info(f"默认视频模型设置为: {model_name}")
        else:
            raise InvalidParameterError(f"不支持的模型类型: {model_type}")
    
    def set_image_model(self, model_name: str) -> None:
        """
        设置图片生成模型（快捷方法）
        
        Args:
            model_name: 模型名称
        """
        self.set_default_model('image', model_name)
    
    def set_video_model(self, model_name: str) -> None:
        """
        设置视频生成模型（快捷方法）
        
        Args:
            model_name: 模型名称
        """
        self.set_default_model('video', model_name)
    
    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "512x512",
        num_images: int = 1,
        save_path: Optional[str] = None
    ) -> Union[str, ImageGenerationResponse]:
        """
        生成图片
        
        Args:
            prompt: 提示词
            negative_prompt: 负面提示词
            size: 图片尺寸
            num_images: 生成数量
            save_path: 保存路径
        
        Returns:
            Union[str, ImageGenerationResponse]: 
                - beginner模式: 返回保存路径（字符串）
                - standard/expert模式: 返回完整响应对象
        """
        self.logger.info(f"开始生成图片: {prompt[:50]}...")
        
        # 创建请求
        request = ImageGenerationRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            num_images=num_images
        )
        
        # 调用Provider
        response = self.image_generator.generate(request)
        
        self.logger.info(f"图片生成完成: 成功={response.success}")
        
        # 根据模式返回不同结果
        if self.mode == "beginner":
            # 新手模式：返回第一个图片的路径
            if response.success and response.images:
                return response.images[0]
            else:
                raise APIError(f"图片生成失败: {response.error}")
        else:
            # 标准/专家模式：返回完整响应
            return response
    
    def generate_video(
        self,
        prompt: str,
        duration: str = "5s",
        aspect_ratio: str = "16:9",
        image_path: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> Union[str, VideoGenerationResponse]:
        """
        生成视频
        
        Args:
            prompt: 提示词
            duration: 视频时长
            aspect_ratio: 宽高比
            image_path: 参考图片路径
            save_path: 保存路径
        
        Returns:
            Union[str, VideoGenerationResponse]:
                - beginner模式: 返回保存路径（字符串）
                - standard/expert模式: 返回完整响应对象
        """
        self.logger.info(f"开始生成视频: {prompt[:50]}...")
        
        # 创建请求
        request = VideoGenerationRequest(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            image_path=image_path
        )
        
        # 提交任务
        response = self.video_generator.generate(request)
        
        # 等待完成
        final_response = self.video_generator.wait_for_completion(
            response.task_id,
            timeout=300,
            progress_callback=self._progress_callback if self.mode == "beginner" else None
        )
        
        self.logger.info(f"视频生成完成: 成功={final_response.success}")
        
        # 根据模式返回不同结果
        if self.mode == "beginner":
            if final_response.success and final_response.video_url:
                return final_response.video_url
            else:
                raise APIError(f"视频生成失败: {final_response.error}")
        else:
            return final_response
    
    def _progress_callback(self, current: int, total: int) -> None:
        """进度回调（新手模式）"""
        progress = int((current / total) * 100)
        self.logger.info(f"视频生成进度: {progress}% ({current}/{total}秒)")
    
    @classmethod
    def create_skill(
        cls,
        config_path: Optional[str] = None,
        mode: str = "beginner"
    ) -> "AIStudioSkill":
        """
        工厂方法：创建Skill实例（便于测试）
        
        Args:
            config_path: 配置文件路径
            mode: 运行模式
        
        Returns:
            AIStudioSkill: Skill实例
        """
        return cls(config_path=config_path, mode=mode)
