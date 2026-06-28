"""
测试速率限制处理（P0-002）
"""

import pytest
import time
from unittest.mock import Mock, patch

from scripts.providers.mock_provider import MockVideoGenerator
from scripts.core.data_models import VideoGenerationResponse, TaskStatus
from scripts.core.exceptions import RateLimitError, TaskTimeoutError


class TestRateLimitHandling:
    """测试速率限制处理"""
    
    def test_wait_for_completion_handles_rate_limit(self):
        """测试wait_for_completion处理速率限制"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(
            Mock(prompt="测试视频")
        )
        task_id = response.task_id
        
        # Mock get_task_status 第一次抛出RateLimitError，第二次返回成功
        call_count = 0
        original_get_status = generator.get_task_status
        
        def mock_get_status(task_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("速率限制", retry_after=1)
            return original_get_status(task_id)
        
        generator.get_task_status = mock_get_status
        
        # 应该成功处理速率限制并完成
        start_time = time.time()
        final_response = generator.wait_for_completion(
            task_id,
            timeout=30,
            poll_interval=1
        )
        elapsed = time.time() - start_time
        
        assert final_response.success is True
        assert elapsed >= 1  # 至少等待了1秒（retry_after）
    
    def test_wait_for_completion_rate_limit_exhausted(self):
        """测试速率限制导致超时"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(
            Mock(prompt="测试视频")
        )
        task_id = response.task_id
        
        # Mock get_task_status 总是抛出RateLimitError
        def mock_get_status_always_rate_limit(task_id):
            raise RateLimitError("速率限制", retry_after=2)
        
        generator.get_task_status = mock_get_status_always_rate_limit
        
        # 应该超时
        with pytest.raises(TaskTimeoutError) as exc_info:
            generator.wait_for_completion(
                task_id,
                timeout=5,  # 短超时
                poll_interval=1
            )
        
        assert "超时" in str(exc_info.value)
    
    def test_wait_for_completion_progress_callback(self):
        """测试进度回调"""
        generator = MockVideoGenerator()
        
        # 创建任务
        response = generator.generate(
            Mock(prompt="测试视频")
        )
        task_id = response.task_id
        
        # 进度回调
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        # 运行（Mock会快速完成）
        final_response = generator.wait_for_completion(
            task_id,
            timeout=30,
            poll_interval=0.1,
            progress_callback=progress_callback
        )
        
        assert final_response.success is True
        # 应该至少调用了一次进度回调
        assert len(progress_calls) > 0
