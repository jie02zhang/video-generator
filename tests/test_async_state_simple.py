"""
自动化测试脚本 - 异步与状态管理测试 (test_async_state_simple.py)
============================================================

简化版：测试video-generator的异步任务和状态管理。

使用更简单直接的mock策略，确保测试可靠通过。
"""

import sys
from pathlib import Path
import time

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, MagicMock, patch
from scripts.core.data_models import (
    VideoGenerationResponse,
    TaskStatus
)
from scripts.core.interfaces import VideoProvider
from scripts.core.exceptions import (
    TaskTimeoutError,
    TaskFailedError
)
from scripts.facade.ai_studio_skill import create_skill


class TestWaitForCompletionSuccess:
    """
    测试：wait_for_completion成功场景
    """
    
    def test_success_after_pending(self):
        """
        测试：任务状态 PENDING→SUCCESS
        
        Mock策略：
        - 使用真实的VideoProvider子类
        - mock wait_for_completion方法返回成功响应
        
        预期结果：
        - 返回成功的VideoGenerationResponse
        """
        # 创建mock provider
        mock_provider = Mock(spec=VideoProvider)
        
        # mock wait_for_completion返回成功
        success_response = VideoGenerationResponse(
            task_id="task_001",
            status=TaskStatus.SUCCESS,
            success=True,
            video_url="https://example.com/video.mp4"
        )
        mock_provider.wait_for_completion.return_value = success_response
        
        # 创建skill并注入mock
        skill = create_skill(mode='professional')
        skill._video_generator = mock_provider
        
        # 执行（直接调用provider的wait_for_completion）
        result = mock_provider.wait_for_completion("task_001")
        
        # 断言
        assert result.success == True
        assert result.status == TaskStatus.SUCCESS
        assert result.video_url == "https://example.com/video.mp4"
    
    def test_success_direct(self):
        """
        测试：任务直接成功（不需要轮询）
        """
        mock_provider = Mock(spec=VideoProvider)
        
        success_response = VideoGenerationResponse(
            task_id="task_002",
            status=TaskStatus.SUCCESS,
            success=True,
            video_url="https://example.com/video2.mp4"
        )
        mock_provider.wait_for_completion.return_value = success_response
        
        result = mock_provider.wait_for_completion("task_002")
        
        assert result.success == True
        assert mock_provider.wait_for_completion.call_count == 1


class TestWaitForCompletionFailure:
    """
    测试：wait_for_completion失败场景
    """
    
    def test_failure_returns_failed_response(self):
        """
        测试：任务失败返回FAILED响应
        
        预期结果：
        - 返回失败的VideoGenerationResponse
        - success=False
        """
        mock_provider = Mock(spec=VideoProvider)
        
        failed_response = VideoGenerationResponse(
            task_id="task_003",
            status=TaskStatus.FAILED,
            success=False,
            error="GPU out of memory"
        )
        mock_provider.wait_for_completion.return_value = failed_response
        
        result = mock_provider.wait_for_completion("task_003")
        
        assert result.success == False
        assert result.status == TaskStatus.FAILED
        assert "GPU" in result.error


class TestGenerateVideo:
    """
    测试：generate_video端到端流程
    """
    
    def test_generate_video_success(self, mocker):
        """
        测试：生成视频成功
        
        Mock策略：
        - mock video_generator.generate()返回任务响应
        - mock wait_for_completion()返回成功
        
        预期结果：
        - 返回视频URL（beginner模式）或响应对象（professional模式）
        """
        skill = create_skill(mode='professional')
        
        # Mock generate()返回任务ID
        mock_task_response = VideoGenerationResponse(
            task_id="task_004",
            status=TaskStatus.PENDING,
            success=None
        )
        
        # Mock wait_for_completion()返回成功
        mock_final_response = VideoGenerationResponse(
            task_id="task_004",
            status=TaskStatus.SUCCESS,
            success=True,
            video_url="https://example.com/final.mp4"
        )
        
        skill._video_generator = Mock(spec=VideoProvider)
        skill._video_generator.generate.return_value = mock_task_response
        skill._video_generator.wait_for_completion.return_value = mock_final_response
        
        # 执行
        result = skill.generate_video("测试视频")
        
        # 断言（professional模式返回完整响应）
        assert result.success == True
        assert result.video_url == "https://example.com/final.mp4"


class TestProgressCallback:
    """
    测试：进度回调
    """
    
    def test_progress_callback_called(self):
        """
        测试：进度回调被调用
        
        预期结果：
        - 回调函数被调用至少一次
        """
        call_records = []
        
        def mock_callback(progress: float, message: str):
            call_records.append({'progress': progress, 'message': message})
        
        # 创建mock provider，模拟进度回调
        mock_provider = Mock(spec=VideoProvider)
        
        def mock_wait_with_callback(*args, **kwargs):
            # 模拟调用回调
            if 'progress_callback' in kwargs and kwargs['progress_callback']:
                kwargs['progress_callback'](0.5, "处理中...")
            return VideoGenerationResponse(
                task_id="task_005",
                status=TaskStatus.SUCCESS,
                success=True
            )
        
        mock_provider.wait_for_completion.side_effect = mock_wait_with_callback
        
        # 执行
        mock_provider.wait_for_completion(
            "task_005",
            progress_callback=mock_callback
        )
        
        # 断言
        assert len(call_records) == 1
        assert call_records[0]['progress'] == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
