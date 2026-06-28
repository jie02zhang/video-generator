"""
Mock Provider（用于测试和开发）
"""

import time
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from scripts.core.interfaces import ImageProvider, VideoProvider
from scripts.core.data_models import (
    ImageGenerationRequest, ImageGenerationResponse,
    VideoGenerationRequest, VideoGenerationResponse, TaskStatus
)
from scripts.core.exceptions import TaskTimeoutError


class MockImageGenerator(ImageProvider):
    """Mock图片生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, mode: str = "standard"):
        super().__init__(config, mode)
        self.call_count = 0
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """模拟生成图片"""
        self.call_count += 1
        self.logger.info(f"Mock图片生成: {request.prompt[:30]}...")
        
        # 模拟生成图片路径
        mock_images = []
        for i in range(request.num_images):
            mock_path = f"/tmp/mock_image_{self.call_count}_{i}.png"
            mock_images.append(mock_path)
        
        return ImageGenerationResponse(
            success=True,
            images=mock_images,
            metadata={"provider": "mock", "call_count": self.call_count}
        )


class MockVideoGenerator(VideoProvider):
    """Mock视频生成器（带状态模拟）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, mode: str = "standard"):
        super().__init__(config, mode)
        self.tasks = {}
        self.task_counter = 0
        self.task_status_counter = {}  # 用于模拟状态变化
    
    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResponse:
        """提交视频生成任务"""
        self.task_counter += 1
        task_id = f"mock_task_{self.task_counter}"
        
        self.tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "request": request,
            "poll_count": 0
        }
        self.task_status_counter[task_id] = 0
        
        self.logger.info(f"Mock视频任务提交: {task_id}")
        
        return VideoGenerationResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            success=True
        )
    
    def get_task_status(self, task_id: str) -> VideoGenerationResponse:
        """
        查询任务状态（模拟状态变化）
        
        第1次调用: PENDING
        第2次调用: PROCESSING
        第3次调用: SUCCESS
        """
        if task_id not in self.tasks:
            return VideoGenerationResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                success=False,
                error="Task not found"
            )
        
        task = self.tasks[task_id]
        self.task_status_counter[task_id] += 1
        poll_count = self.task_status_counter[task_id]
        
        # 模拟状态变化
        if poll_count == 1:
            task["status"] = TaskStatus.PENDING
        elif poll_count == 2:
            task["status"] = TaskStatus.PROCESSING
        else:
            task["status"] = TaskStatus.SUCCESS
            task["video_url"] = f"/tmp/mock_video_{task_id}.mp4"
        
        return VideoGenerationResponse(
            task_id=task_id,
            status=task["status"],
            success=(task["status"] == TaskStatus.SUCCESS),
            video_url=task.get("video_url"),
            metadata={"poll_count": poll_count}
        )
