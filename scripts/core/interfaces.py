"""
Provider接口定义
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any
import time
import logging

from scripts.core.data_models import (
    ImageGenerationRequest, ImageGenerationResponse,
    VideoGenerationRequest, VideoGenerationResponse, TaskStatus
)
from scripts.core.exceptions import (
    TaskTimeoutError, RateLimitError, TaskFailedError,
    ContentPolicyViolationError, APIError
)


class BaseProvider(ABC):
    """Provider基础类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, mode: str = "standard"):
        self.config = config or {}
        self.mode = mode
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_request(self, request) -> None:
        """验证请求（子类可重写）"""
        pass
    
    def handle_api_error(self, e: Exception) -> None:
        """统一API错误处理"""
        if "content policy" in str(e).lower() or "safety" in str(e).lower():
            raise ContentPolicyViolationError(
                "内容不符合安全策略，请修改提示词后重试"
            )
        raise e


class ImageProvider(BaseProvider, ABC):
    """图片生成Provider接口"""
    
    @abstractmethod
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """生成图片"""
        pass  # pragma: no cover


class VideoProvider(BaseProvider, ABC):
    """视频生成Provider接口"""
    
    @abstractmethod
    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResponse:
        """提交视频生成任务"""
        pass  # pragma: no cover
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> VideoGenerationResponse:
        """查询任务状态"""
        pass  # pragma: no cover
    
    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> VideoGenerationResponse:
        """
        等待任务完成（P0-002: 修复速率限制处理）
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            progress_callback: 进度回调函数 (current_seconds, total_seconds)
        
        Returns:
            VideoGenerationResponse: 最终结果
        """
        start_time = time.time()
        last_status = None
        
        while True:
            elapsed = int(time.time() - start_time)
            
            # 检查超时
            if elapsed >= timeout:
                raise TaskTimeoutError(f"任务 {task_id} 超时（{timeout}秒）")
            
            # 进度回调
            if progress_callback:
                try:
                    progress_callback(elapsed, timeout)
                except Exception as e:
                    self.logger.warning(f"进度回调失败: {e}")
            
            try:
                # 查询状态
                response = self.get_task_status(task_id)
                
                # 状态变化日志
                if response.status != last_status:
                    self.logger.info(f"任务 {task_id} 状态变化: {last_status} → {response.status}")
                    last_status = response.status
                
                # 完成
                if response.is_completed():
                    if response.is_success():
                        self.logger.info(f"任务 {task_id} 成功完成")
                    else:
                        self.logger.error(f"任务 {task_id} 失败: {response.error}")
                    return response
                
            except RateLimitError as e:
                # P0-002: 智能处理速率限制
                retry_after = e.retry_after or poll_interval
                self.logger.warning(
                    f"遇到速率限制，等待 {retry_after} 秒后重试"
                )
                time.sleep(retry_after)
                continue
                
            except ContentPolicyViolationError:
                # P0-004: 内容策略违规
                self.logger.error(f"任务 {task_id} 内容策略违规")
                raise
                
            except Exception as e:
                self.logger.error(f"查询任务 {task_id} 状态失败: {e}")
                # 继续轮询，不立即失败
            
            # 等待下次轮询
            time.sleep(poll_interval)
