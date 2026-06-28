"""
Provider工厂
"""

from typing import Optional, Dict, Any, Type
from scripts.core.interfaces import ImageProvider, VideoProvider
from scripts.core.exceptions import ModelNotFoundError, ConfigurationError
from scripts.core.logging_config import get_logger


class ProviderFactory:
    """Provider工厂"""
    
    # 注册表
    _image_providers: Dict[str, Type[ImageProvider]] = {}
    _video_providers: Dict[str, Type[VideoProvider]] = {}
    
    # 初始化：注册默认providers
    @classmethod
    def _init_default_providers(cls):
        """初始化默认providers"""
        if not cls._image_providers:
            # 延迟导入，避免循环导入
            from scripts.providers.mock_provider import MockImageGenerator
            cls._image_providers['mock'] = MockImageGenerator
            cls._image_providers['mock-provider'] = MockImageGenerator
        
        if not cls._video_providers:
            from scripts.providers.mock_provider import MockVideoGenerator
            cls._video_providers['mock'] = MockVideoGenerator
            cls._video_providers['mock-provider'] = MockVideoGenerator
    
    @classmethod
    def register_image_provider(cls, name: str, provider_class: Type[ImageProvider]) -> None:
        """注册图片生成Provider"""
        cls._image_providers[name] = provider_class
    
    @classmethod
    def register_video_provider(cls, name: str, provider_class: Type[VideoProvider]) -> None:
        """注册视频生成Provider"""
        cls._video_providers[name] = provider_class
    
    @classmethod
    def create_image_generator(
        cls,
        model_name: str = "mock",
        mode: str = "standard",
        config: Optional[Dict[str, Any]] = None
    ) -> ImageProvider:
        """
        创建图片生成器
        
        Args:
            model_name: 模型名称
            mode: 模式 (beginner/standard/expert)
            config: 配置字典
        
        Returns:
            ImageProvider: 图片生成Provider实例
        """
        # 初始化默认providers
        cls._init_default_providers()
        
        if model_name not in cls._image_providers:
            raise ModelNotFoundError(f"未找到图片生成模型: {model_name}")
        
        provider_class = cls._image_providers[model_name]
        return provider_class(config=config, mode=mode)
    
    @classmethod
    def create_video_generator(
        cls,
        model_name: str = "mock",
        mode: str = "standard",
        config: Optional[Dict[str, Any]] = None
    ) -> VideoProvider:
        """
        创建视频生成器
        
        Args:
            model_name: 模型名称
            mode: 模式 (beginner/standard/expert)
            config: 配置字典
        
        Returns:
            VideoProvider: 视频生成Provider实例
        """
        # 初始化默认providers
        cls._init_default_providers()
        
        if model_name not in cls._video_providers:
            raise ModelNotFoundError(f"未找到视频生成模型: {model_name}")
        
        provider_class = cls._video_providers[model_name]
        return provider_class(config=config, mode=mode)
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        import os
        import yaml
        
        # 默认配置路径
        if not config_path:
            # 查找默认配置文件
            default_paths = [
                "config.yaml",
                os.path.join(os.path.dirname(__file__), "../../config.yaml"),
                os.path.join(os.path.dirname(__file__), "../config.yaml")
            ]
            for path in default_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        if not config_path or not os.path.exists(config_path):
            # 返回默认配置
            return {
                "default_image_model": "mock",
                "default_video_model": "mock",
                "models": {}
            }
        
        # 加载YAML配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config or {}
