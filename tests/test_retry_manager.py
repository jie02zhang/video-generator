"""
测试RetryManager的RateLimitError处理（覆盖retry.py 120）
"""

import pytest
from scripts.core.retry import RetryManager
from scripts.core.exceptions import RateLimitError


class TestRetryManagerRateLimit:
    """测试RetryManager处理RateLimitError"""
    
    def test_execute_with_rate_limit_retry_after(self):
        """测试RetryManager处理带retry_after的RateLimitError"""
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("速率限制", retry_after=5)
            return "success"
        
        manager = RetryManager(max_retries=3, delay=1.0)
        
        # 应该成功处理速率限制
        start_time = time.time()
        result = manager.execute(failing_func, exceptions=(RateLimitError,))
        elapsed = time.time() - start_time
        
        assert result == "success"
        assert call_count == 3
        # 应该等待了retry_after时间（2次重试 × 5秒 = 10秒）
        assert elapsed >= 10
    
    def test_execute_retry_exhausted_with_rate_limit(self):
        """测试RetryManager重试次数用尽（RateLimitError）"""
        call_count = 0
        
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise RateLimitError("永久速率限制", retry_after=1)
        
        manager = RetryManager(max_retries=2, delay=1.0)
        
        with pytest.raises(RateLimitError) as exc_info:
            manager.execute(always_fails, exceptions=(RateLimitError,))
        
        assert call_count == 3  # 初始1次 + 重试2次


import time
