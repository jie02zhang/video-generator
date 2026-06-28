"""
测试数据模型
"""

import pytest
from scripts.core.data_models import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    VideoGenerationRequest,
    VideoGenerationResponse,
    TaskStatus,
    ImageSize,
    VideoDuration
)
from scripts.core.exceptions import ValidationError


class TestImageGenerationRequest:
    """测试图片生成请求"""
    
    def test_valid_request(self):
        """测试有效请求"""
        request = ImageGenerationRequest(
            prompt="一只可爱的猫咪",
            size=ImageSize.SQUARE,
            num_images=1
        )
        
        assert request.prompt == "一只可爱的猫咪"
        assert request.size == ImageSize.SQUARE
        assert request.num_images == 1
    
    def test_empty_prompt(self):
        """测试空提示词"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(prompt="")
        
        assert "提示词不能为空" in str(exc_info.value)
    
    def test_negative_num_images(self):
        """测试负数生成数量"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="测试",
                num_images=0
            )
        
        assert "必须大于0" in str(exc_info.value)
    
    def test_negative_guidance_scale(self):
        """测试负数引导尺度"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="测试",
                guidance_scale=-1.0
            )
        
        assert "必须大于等于0" in str(exc_info.value)


class TestVideoGenerationRequest:
    """测试视频生成请求"""
    
    def test_valid_request(self):
        """测试有效请求"""
        request = VideoGenerationRequest(
            prompt="日落时分的海滩",
            duration=VideoDuration.SHORT_5S,
            aspect_ratio="16:9"
        )
        
        assert request.prompt == "日落时分的海滩"
        assert request.duration == VideoDuration.SHORT_5S
        assert request.aspect_ratio == "16:9"
    
    def test_empty_prompt(self):
        """测试空提示词"""
        with pytest.raises(ValidationError) as exc_info:
            VideoGenerationRequest(prompt="")
        
        assert "提示词不能为空" in str(exc_info.value)


class TestVideoGenerationResponse:
    """测试视频生成响应"""
    
    def test_is_completed(self):
        """测试is_completed方法"""
        # 成功
        response = VideoGenerationResponse(
            task_id="test",
            status=TaskStatus.SUCCESS
        )
        assert response.is_completed() is True
        
        # 失败
        response.status = TaskStatus.FAILED
        assert response.is_completed() is True
        
        # 处理中
        response.status = TaskStatus.PROCESSING
        assert response.is_completed() is False
    
    def test_is_success(self):
        """测试is_success方法"""
        response = VideoGenerationResponse(
            task_id="test",
            status=TaskStatus.SUCCESS
        )
        assert response.is_success() is True
        
        response.status = TaskStatus.FAILED
        assert response.is_success() is False
    
    def test_is_failed(self):
        """测试is_failed方法（P0修复）"""
        response = VideoGenerationResponse(
            task_id="test",
            status=TaskStatus.FAILED
        )
        assert response.is_failed() is True
        
        response.status = TaskStatus.SUCCESS
        assert response.is_failed() is False
