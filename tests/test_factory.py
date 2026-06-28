"""
测试Provider工厂
"""

import pytest
from scripts.core.factory import ProviderFactory
from scripts.core.exceptions import ModelNotFoundError, ConfigurationError
from scripts.providers.mock_provider import MockImageGenerator, MockVideoGenerator


class TestProviderFactory:
    """测试Provider工厂"""
    
    def test_create_image_generator_mock(self):
        """测试创建Mock图片生成器"""
        generator = ProviderFactory.create_image_generator(
            model_name="mock",
            mode="standard"
        )
        
        assert isinstance(generator, MockImageGenerator)
    
    def test_create_video_generator_mock(self):
        """测试创建Mock视频生成器"""
        generator = ProviderFactory.create_video_generator(
            model_name="mock",
            mode="standard"
        )
        
        assert isinstance(generator, MockVideoGenerator)
    
    def test_create_image_generator_not_found(self):
        """测试创建不存在的图片生成器"""
        with pytest.raises(ModelNotFoundError) as exc_info:
            ProviderFactory.create_image_generator(
                model_name="nonexistent",
                mode="standard"
            )
        
        assert "未找到图片生成模型" in str(exc_info.value)
    
    def test_create_video_generator_not_found(self):
        """测试创建不存在的视频生成器"""
        with pytest.raises(ModelNotFoundError) as exc_info:
            ProviderFactory.create_video_generator(
                model_name="nonexistent",
                mode="standard"
            )
        
        assert "未找到视频生成模型" in str(exc_info.value)
    
    def test_load_config_default(self):
        """测试加载默认配置"""
        config = ProviderFactory.load_config()
        
        assert isinstance(config, dict)
        assert "default_image_model" in config
        assert "default_video_model" in config
    
    def test_register_provider(self):
        """测试注册Provider"""
        # 注册一个新Provider
        class TestProvider(MockImageGenerator):
            pass
        
        ProviderFactory.register_image_provider("test", TestProvider)
        
        generator = ProviderFactory.create_image_generator(
            model_name="test",
            mode="standard"
        )
        
        assert isinstance(generator, TestProvider)
