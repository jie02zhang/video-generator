"""
测试Skeleton Providers（提升覆盖率）
"""

import pytest
from scripts.providers.dalle_provider import DALLEImageGenerator
from scripts.providers.local_sd_provider import LocalSDImageGenerator
from scripts.providers.runway_provider import RunwayVideoGenerator
from scripts.providers.kling_provider import KlingVideoGenerator
from scripts.core.data_models import ImageGenerationRequest, VideoGenerationRequest
from scripts.core.exceptions import ConfigurationError


class TestDALLEProvider:
    """测试DALL-E Provider"""
    
    def test_init_with_api_key(self):
        """测试初始化（带API密钥）"""
        config = {"api_key": "test-key"}
        generator = DALLEImageGenerator(config=config, mode="standard")
        
        assert generator.api_key == "test-key"
        assert generator.model == "dall-e-3"
    
    def test_init_without_api_key(self, monkeypatch):
        """测试初始化（无API密钥）"""
        # 确保环境变量未设置
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        with pytest.raises(ConfigurationError) as exc_info:
            DALLEImageGenerator(config={}, mode="standard")
        
        assert "api_key" in str(exc_info.value).lower()
    
    def test_generate(self):
        """测试生成图片"""
        config = {"api_key": "test-key"}
        generator = DALLEImageGenerator(config=config, mode="standard")
        
        request = ImageGenerationRequest(
            prompt="测试",
            size="512x512"
        )
        
        response = generator.generate(request)
        
        assert response.success is True
        assert len(response.images) > 0
        assert "dall-e" in response.metadata["provider"]


class TestLocalSDProvider:
    """测试Local SD Provider"""
    
    def test_init_with_config(self):
        """测试初始化"""
        config = {"api_endpoint": "http://localhost:7860"}
        generator = LocalSDImageGenerator(config=config, mode="standard")
        
        assert generator.api_endpoint == "http://localhost:7860"
    
    def test_generate(self):
        """测试生成图片"""
        config = {"api_endpoint": "http://localhost:7860"}
        generator = LocalSDImageGenerator(config=config, mode="standard")
        
        request = ImageGenerationRequest(
            prompt="测试",
            size="512x512"
        )
        
        response = generator.generate(request)
        
        assert response.success is True


class TestRunwayProvider:
    """测试Runway Provider"""
    
    def test_init_with_api_key(self):
        """测试初始化（带API密钥）"""
        config = {"api_key": "test-key"}
        generator = RunwayVideoGenerator(config=config, mode="standard")
        
        assert generator.api_key == "test-key"
        assert generator.model == "gen-3"
    
    def test_init_without_api_key(self):
        """测试初始化（无API密钥）"""
        with pytest.raises(ConfigurationError) as exc_info:
            RunwayVideoGenerator(config={}, mode="standard")
        
        assert "api_key" in str(exc_info.value).lower()
    
    def test_generate(self):
        """测试提交视频生成任务"""
        config = {"api_key": "test-key"}
        generator = RunwayVideoGenerator(config=config, mode="standard")
        
        request = VideoGenerationRequest(
            prompt="测试视频"
        )
        
        response = generator.generate(request)
        
        assert response.success is True
        assert response.task_id != ""
    
    def test_get_task_status(self):
        """测试查询任务状态"""
        config = {"api_key": "test-key"}
        generator = RunwayVideoGenerator(config=config, mode="standard")
        
        # Mock任务ID
        response = generator.get_task_status("test-task")
        
        assert response.task_id == "test-task"
        assert response.success is True


class TestKlingProvider:
    """测试Kling Provider"""
    
    def test_init_with_api_key(self):
        """测试初始化（带API密钥）"""
        config = {"api_key": "test-key"}
        generator = KlingVideoGenerator(config=config, mode="standard")
        
        assert generator.api_key == "test-key"
        assert generator.model == "kling-v1"
    
    def test_init_without_api_key(self):
        """测试初始化（无API密钥）"""
        with pytest.raises(ConfigurationError) as exc_info:
            KlingVideoGenerator(config={}, mode="standard")
        
        assert "api_key" in str(exc_info.value).lower()
    
    def test_generate(self):
        """测试提交视频生成任务"""
        config = {"api_key": "test-key"}
        generator = KlingVideoGenerator(config=config, mode="standard")
        
        request = VideoGenerationRequest(
            prompt="测试视频"
        )
        
        response = generator.generate(request)
        
        assert response.success is True
        assert response.task_id != ""
    
    def test_get_task_status(self):
        """测试查询任务状态"""
        config = {"api_key": "test-key"}
        generator = KlingVideoGenerator(config=config, mode="standard")
        
        # Mock任务ID
        response = generator.get_task_status("test-task")
        
        assert response.task_id == "test-task"
        assert response.success is True
