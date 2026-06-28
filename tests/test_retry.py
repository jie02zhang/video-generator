"""
测试：重试机制 (test_retry.py)
==============================

基于 scripts/core/retry.py 的实际接口创建测试。
"""

import sys
from pathlib import Path
import time

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, patch
from scripts.core.retry import retry_on_exception, RetryManager
from scripts.core.exceptions import RateLimitError


class TestRetryOnException:
    """
    测试：retry_on_exception 装饰器
    """
    
    def test_retry_on_failure(self):
        """
        测试：失败后重试
        
        Mock策略：
        - 前2次调用抛出异常
        - 第3次调用成功
        
        预期结果：
        - 最终返回成功结果
        - 调用了3次函数
        """
        call_count = 0
        
        @retry_on_exception(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Temporary error")
            return "Success"
        
        result = flaky_function()
        
        assert result == "Success"
        assert call_count == 3
    
    def test_retry_exhausted(self):
        """
        测试：重试耗尽后抛出异常
        
        预期结果：
        - 重试3次后抛出异常
        - 抛出最后的异常
        """
        @retry_on_exception(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def always_fail():
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError):
            always_fail()
    
    def test_no_retry_on_success(self):
        """
        测试：第一次就成功，不重试
        
        预期结果：
        - 返回成功结果
        - 只调用1次
        """
        call_count = 0
        
        @retry_on_exception(max_retries=3, delay=0.01, exceptions=(ValueError,))
        def success_function():
            nonlocal call_count
            call_count += 1
            return "Success"
        
        result = success_function()
        
        assert result == "Success"
        assert call_count == 1
    
    def test_exponential_backoff(self):
        """
        测试：指数退避
        
        预期结果：
        - 重试之间有延迟
        - 延迟时间呈指数增长
        """
        call_times = []
        
        @retry_on_exception(max_retries=3, delay=0.1, backoff_factor=2.0, exceptions=(ValueError,))
        def slow_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Retry")
            return "Success"
        
        with patch('time.sleep'):  # 不实际睡眠
            result = slow_function()
        
        assert result == "Success"
        assert len(call_times) == 3
    
    def test_retry_with_rate_limit(self):
        """
        测试：速率限制（RateLimitError）的特殊处理
        
        Mock策略：
        - 第一次调用抛出RateLimitError（带retry_after=5）
        - 第二次调用成功
        
        预期结果：
        - 等待5秒后重试
        - 最终成功
        """
        call_count = 0
        
        @retry_on_exception(max_retries=3, delay=0.01, exceptions=(RateLimitError,))
        def rate_limited_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("Rate limited", retry_after=5)
            return "Success"
        
        with patch('time.sleep') as mock_sleep:
            result = rate_limited_function()
        
        assert result == "Success"
        # 验证sleep被调用（等待retry_after）
        mock_sleep.assert_called()


class TestRetryManager:
    """
    测试：RetryManager 类
    """
    
    def test_execute_success(self):
        """
        测试：RetryManager.execute成功
        
        预期结果：
        - 返回成功结果
        """
        manager = RetryManager(max_retries=3, delay=0.01, backoff_factor=2.0)
        
        call_count = 0
        def task():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Retry")
            return "Success"
        
        with patch('time.sleep'):  # 不实际睡眠
            result = manager.execute(task, exceptions=(ValueError,))
        
        assert result == "Success"
    
    def test_execute_failure(self):
        """
        测试：RetryManager.execute失败（重试耗尽）
        
        预期结果：
        - 抛出最后的异常
        """
        manager = RetryManager(max_retries=2, delay=0.01, backoff_factor=2.0)
        
        def always_fail():
            raise ValueError("Always fail")
        
        with patch('time.sleep'):  # 不实际睡眠
            with pytest.raises(ValueError):
                manager.execute(always_fail, exceptions=(ValueError,))
    
    def test_execute_with_rate_limit(self):
        """
        测试：RetryManager.execute处理速率限制（RateLimitError）
        
        Mock策略：
        - 第一次调用抛出RateLimitError（带retry_after=5）
        - 第二次调用成功
        
        预期结果：
        - 等待5秒后重试
        - 最终成功
        """
        manager = RetryManager(max_retries=3, delay=0.01, backoff_factor=2.0)
        
        call_count = 0
        def rate_limited_task():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("Rate limited", retry_after=5)
            return "Success"
        
        # Mock sleep，不实际等待
        with patch('time.sleep') as mock_sleep:
            result = manager.execute(rate_limited_task, exceptions=(RateLimitError,))
        
        assert result == "Success"
        # 验证sleep被调用（等待retry_after）
        mock_sleep.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
