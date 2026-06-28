"""
测试AIStudioSkill错误处理（提升覆盖率）
"""

import pytest
from scripts.facade.ai_studio_skill import AIStudioSkill
from scripts.core.data_models import ImageGenerationRequest, VideoGenerationRequest
from scripts.core.exceptions import (
    APIError,
    InvalidParameterError,
    ModelNotFoundError
)
import os


class TestAIStudioSkillErrorHandling:
    """测试AIStudioSkill错误处理"""
    
    def test_generate_image_api_error(self):
        """测试图片生成API错误"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        # Mock image_generator.generate 抛出APIError
        def mock_generate(request):
            raise APIError("API调用失败")
        
        skill.image_generator.generate = mock_generate
        
        with pytest.raises(APIError) as exc_info:
            skill.generate_image(prompt="测试")
        
        assert "API调用失败" in str(exc_info.value)
    
    def test_generate_video_api_error(self):
        """测试视频生成API错误"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        # Mock video_generator.generate 抛出APIError
        def mock_generate(request):
            raise APIError("视频API调用失败")
        
        skill.video_generator.generate = mock_generate
        
        with pytest.raises(APIError) as exc_info:
            skill.generate_video(prompt="测试")
        
        assert "视频API调用失败" in str(exc_info.value)
    
    def test_generate_image_beginner_mode_error(self):
        """测试新手模式图片生成失败"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        # Mock返回失败响应
        from scripts.core.data_models import ImageGenerationResponse
        
        def mock_generate(request):
            return ImageGenerationResponse(
                success=False,
                error="生成失败"
            )
        
        skill.image_generator.generate = mock_generate
        
        with pytest.raises(APIError) as exc_info:
            skill.generate_image(prompt="测试")
        
        assert "图片生成失败" in str(exc_info.value)
    
    def test_generate_video_beginner_mode_error(self):
        """测试新手模式视频生成失败"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        # Mock返回失败响应
        from scripts.core.data_models import VideoGenerationResponse, TaskStatus
        
        def mock_wait_for_completion(task_id, timeout=300, poll_interval=5, progress_callback=None):
            return VideoGenerationResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                success=False,
                error="视频生成失败"
            )
        
        skill.video_generator.generate = lambda req: VideoGenerationResponse(
            task_id="test",
            status=TaskStatus.PENDING,
            success=True
        )
        skill.video_generator.wait_for_completion = mock_wait_for_completion
        
        with pytest.raises(APIError) as exc_info:
            skill.generate_video(prompt="测试")
        
        assert "视频生成失败" in str(exc_info.value)
    
    def test_set_default_model_invalid_type(self):
        """测试设置无效模型类型"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        with pytest.raises(InvalidParameterError) as exc_info:
            skill.set_default_model("invalid_type", "model_name")
        
        assert "不支持的模型类型" in str(exc_info.value)
    
    def test_generate_image_standard_mode_response(self):
        """测试标准模式返回完整响应"""
        skill = AIStudioSkill.create_skill(mode="standard")
        
        response = skill.generate_image(prompt="测试")
        
        # 标准模式返回响应对象
        assert hasattr(response, 'success')
        assert response.success is True
        assert hasattr(response, 'images')
        assert len(response.images) > 0
    
    def test_progress_callback(self):
        """测试进度回调"""
        skill = AIStudioSkill.create_skill(mode="beginner")
        
        # 进度回调应该被调用
        callback_calls = []
        
        # Mock wait_for_completion 来调用进度回调
        from scripts.core.data_models import VideoGenerationResponse, TaskStatus
        
        def mock_wait_for_completion(task_id, timeout=300, poll_interval=5, progress_callback=None):
            # 调用进度回调
            if progress_callback:
                progress_callback(5, timeout)
                progress_callback(10, timeout)
            return VideoGenerationResponse(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                success=True,
                video_url="test.mp4"
            )
        
        skill.video_generator.generate = lambda req: VideoGenerationResponse(
            task_id="test",
            status=TaskStatus.PENDING,
            success=True
        )
        skill.video_generator.wait_for_completion = mock_wait_for_completion
        
        result = skill.generate_video(prompt="测试")
        
        # 验证视频生成成功
        assert result == "test.mp4"
