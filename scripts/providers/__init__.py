"""
Providers包初始化和注册
"""

from scripts.core.factory import ProviderFactory
from scripts.providers.mock_provider import MockImageGenerator, MockVideoGenerator
from scripts.providers.local_sd_provider import LocalSDImageGenerator
from scripts.providers.dalle_provider import DALLEImageGenerator
from scripts.providers.runway_provider import RunwayVideoGenerator
from scripts.providers.kling_provider import KlingVideoGenerator


def register_all_providers():
    """注册所有Provider"""
    
    # 图片生成Provider
    ProviderFactory.register_image_provider("mock", MockImageGenerator)
    ProviderFactory.register_image_provider("local-sd", LocalSDImageGenerator)
    ProviderFactory.register_image_provider("dall-e", DALLEImageGenerator)
    
    # 视频生成Provider
    ProviderFactory.register_video_provider("mock", MockVideoGenerator)
    ProviderFactory.register_video_provider("runway", RunwayVideoGenerator)
    ProviderFactory.register_video_provider("kling", KlingVideoGenerator)
    
    print("✅ 所有Provider注册完成")


# 自动注册（当导入此模块时）
register_all_providers()
