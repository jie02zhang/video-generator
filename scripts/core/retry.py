"""
重试机制（P0-001）
"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
from scripts.core.exceptions import RateLimitError


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
        on_retry: 重试回调函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # 检查是否还有重试机会
                    if attempt < max_retries:
                        # 计算等待时间
                        wait_time = delay * (backoff_factor ** attempt)
                        
                        # 如果是速率限制错误，使用retry_after
                        if isinstance(e, RateLimitError) and e.retry_after:
                            wait_time = e.retry_after
                        
                        # 重试回调
                        if on_retry:
                            try:
                                on_retry(attempt + 1, e)
                            except Exception as callback_error:
                                logging.getLogger(__name__).warning(
                                    f"重试回调失败: {callback_error}"
                                )
                        
                        logging.getLogger(__name__).warning(
                            f"第 {attempt + 1} 次重试 {func.__name__}，"
                            f"等待 {wait_time} 秒。错误: {e}"
                        )
                        time.sleep(wait_time)
                    else:
                        # 重试次数用尽
                        logging.getLogger(__name__).error(
                            f"{func.__name__} 重试 {max_retries} 次后仍然失败"
                        )
                        raise last_exception
            
        return wrapper
    return decorator


class RetryManager:
    """重试管理器"""
    
    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(__name__)
    
    def execute(
        self,
        func: Callable,
        *args,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        执行函数并重试
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            exceptions: 需要重试的异常类型
            **kwargs: 关键字参数
        
        Returns:
            函数执行结果
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    wait_time = self.delay * (self.backoff_factor ** attempt)
                    
                    # 速率限制特殊处理
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait_time = e.retry_after
                    
                    self.logger.warning(
                        f"第 {attempt + 1} 次重试 {func.__name__}，"
                        f"等待 {wait_time} 秒"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"{func.__name__} 重试 {self.max_retries} 次后仍然失败"
                    )
                    raise last_exception
