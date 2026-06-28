"""
测试Interfaces（提升覆盖率到99%）
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from scripts.core.interfaces import BaseProvider, ImageProvider, VideoProvider
from scripts.core.data_models import (
    ImageGenerationRequest, VideoGenerationRequest, VideoGenerationResponse, TaskStatus
)
from scripts.core.exceptions import (
    RateLimitError, TaskTimeoutError, ContentPolicyViolationError,
    ValidationError, APIError
)
from scripts.providers.mock_provider import MockVideoGenerator


class TestBaseProvider:
    """测试BaseProvider"""
    
    def test_validate_request(self):
        """测试validate_request方法"""
        provider = MockImageProvider()
        
        # 不应该抛出异常
        request = ImageGenerationRequest(prompt="测试")
        provider.validate_request(request)  # Should pass
    
    def test_handle_api_error_content_policy(self):
        """测试内容策略违规处理"""
        provider = MockImageProvider()
        
        # 模拟内容策略违规
        exception = Exception("content policy violation")
        
        with pytest.raises(ContentPolicyViolationError) as exc_info:
            provider.handle_api_error(exception)
        
        assert "安全策略" in str(exc_info.value)
    
    def test_handle_api_error_other(self):
        """测试其他API错误"""
        provider = MockImageProvider()
        
        exception = Exception("其他错误")
        
        with pytest.raises(Exception) as exc_info:
            provider.handle_api_error(exception)
        
        assert "其他错误" in str(exc_info.value)


class TestVideoProviderWaitForCompletion:
    """测试VideoProvider的wait_for_completion方法"""
    
    def test_wait_for_completion_success(self):
        """测试成功完成"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(VideoGenerationRequest(prompt="测试"))
        task_id = response.task_id
        
        # 等待完成
        final_response = generator.wait_for_completion(
            task_id,
            timeout=30,
            poll_interval=0.1
        )
        
        assert final_response.success is True
        assert final_response.status == TaskStatus.SUCCESS
    
    def test_wait_for_completion_timeout(self):
        """测试超时"""
        generator = MockVideoGenerator()
        
        # 创建任务但不让它完成（通过Mock）
        response = generator.generate(VideoGenerationRequest(prompt="测试"))
        task_id = response.task_id
        
        # Mock get_task_status 永远返回PROCESSING
        def mock_status(task_id):
            return VideoGenerationResponse(
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                success=False
            )
        
        generator.get_task_status = mock_status
        
        # 应该超时
        with pytest.raises(TaskTimeoutError) as exc_info:
            generator.wait_for_completion(
                task_id,
                timeout=1,  # 短超时
                poll_interval=0.2
            )
        
        assert "超时" in str(exc_info.value)
    
    def test_wait_for_completion_with_progress_callback(self):
        """测试进度回调"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(VideoGenerationRequest(prompt="测试"))
        task_id = response.task_id
        
        # 进度回调
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # 等待完成
        final_response = generator.wait_for_completion(
            task_id,
            timeout=30,
            poll_interval=0.1,
            progress_callback=progress_callback
        )
        
        assert final_response.success is True
        assert len(progress_calls) > 0
    
    def test_wait_for_completion_content_policy_violation(self):
        """测试内容策略违规"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(VideoGenerationRequest(prompt="测试"))
        task_id = response.task_id
        
        # Mock get_task_status 抛出ContentPolicyViolationError
        def mock_status_with_violation(task_id):
            raise ContentPolicyViolationError("内容违规")
        
        generator.get_task_status = mock_status_with_violation
        
        # 应该抛出异常
        with pytest.raises(ContentPolicyViolationError) as exc_info:
            generator.wait_for_completion(
                task_id,
                timeout=30,
                poll_interval=0.1
            )
        
        assert "内容违规" in str(exc_info.value)
    
    def test_wait_for_completion_api_error(self):
        """测试API错误（应该继续轮询）"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(VideoGenerationRequest(prompt="测试"))
        task_id = response.task_id
        
        # Mock: 第一次抛出APIError，第二次返回成功
        call_count = 0
        original_get_status = generator.get_task_status
        
        def mock_status_with_error(task_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIError("临时API错误")
            return original_get_status(task_id)
        
        generator.get_task_status = mock_status_with_error
        
        # 应该成功（错误后被忽略，继续轮询）
        final_response = generator.wait_for_completion(
            task_id,
            timeout=30,
            poll_interval=0.1
        )
        
        assert final_response.success is True


class MockImageProvider(ImageProvider):
    """Mock ImageProvider用于测试"""
    
    def generate(self, request: ImageGenerationRequest):
        from scripts.core.data_models import ImageGenerationResponse
        return ImageGenerationResponse(success=True, images=["test.png"])
