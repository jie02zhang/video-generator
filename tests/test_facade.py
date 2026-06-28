"""
测试 AIStudioSkill Facade
"""

import pytest
from scripts.facade.ai_studio_skill import AIStudioSkill
from scripts.core.data_models import ImageGenerationRequest, VideoGenerationRequest
from scripts.core.exceptions import (
    ModelNotFoundError,
    InvalidParameterError,
    ConfigurationError
)


class TestAIStudioSkill:
    """AIStudioSkill测试类"""
    
    def test_create_beginner_skill(self):
        """测试创建新手模式Skill"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        assert skill is not None
        assert skill.mode == "beginner"
        assert skill.default_image_model == "mock"
        assert skill.default_video_model == "mock"
    
    def test_create_standard_skill(self):
        """测试创建标准模式Skill"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        assert skill is not None
        assert skill.mode == "standard"
    
    def test_set_image_model(self):
        """测试设置图片模型"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        # 设置模型
        skill.set_image_model("local-sd")
        assert skill.default_image_model == "local-sd"
        
        # 验证缓存已清除
        assert skill._image_generator is None
    
    def test_set_video_model(self):
        """测试设置视频模型"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        # 设置模型
        skill.set_video_model("runway")
        assert skill.default_video_model == "runway"
        
        # 验证缓存已清除
        assert skill._video_generator is None
    
    def test_image_generator_property(self):
        """测试image_generator属性（懒加载）"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        # 第一次访问，创建生成器
        generator = skill.image_generator
        assert generator is not None
        
        # 第二次访问，返回缓存
        generator2 = skill.image_generator
        assert generator2 is generator
    
    def test_video_generator_property(self):
        """测试video_generator属性（懒加载）"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        # 第一次访问，创建生成器
        generator = skill.video_generator
        assert generator is not None
        
        # 第二次访问，返回缓存
        generator2 = skill.video_generator
        assert generator2 is generator
    
    def test_generate_image_beginner_mode(self):
        """测试新手模式生成图片（返回路径）"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        result = skill.generate_image(
            prompt="测试图片",
            size="512x512",
            num_images=1
        )
        
        # 新手模式返回字符串（路径）
        assert isinstance(result, str)
        assert "mock_image" in result
    
    def test_generate_image_standard_mode(self):
        """测试标准模式生成图片（返回响应对象）"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        result = skill.generate_image(
            prompt="测试图片",
            size="512x512",
            num_images=1
        )
        
        # 标准模式返回响应对象
        assert hasattr(result, 'success')
        assert result.success is True
        assert len(result.images) > 0
    
    def test_invalid_model_type(self):
        """测试无效的模型类型"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        with pytest.raises(InvalidParameterError) as exc_info:
            skill.set_default_model("invalid_type", "model_name")
        
        assert "不支持的模型类型" in str(exc_info.value)
