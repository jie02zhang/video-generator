"""
测试自定义异常类
"""

import pytest
from scripts.core.exceptions import (
    VideoGeneratorError,
    ModelNotFoundError,
    InvalidParameterError,
    APIError,
    RateLimitError,
    AuthenticationError,
    TaskTimeoutError,
    TaskFailedError,
    ConfigurationError,
    ValidationError,
    ContentPolicyViolationError
)


class TestExceptions:
    """测试异常类"""
    
    def test_base_exception(self):
        """测试基础异常"""
        error = VideoGeneratorError("基础错误")
        assert str(error) == "基础错误"
    
    def test_model_not_found_error(self):
        """测试模型未找到异常"""
        error = ModelNotFoundError("模型未找到")
        assert isinstance(error, VideoGeneratorError)
        assert str(error) == "模型未找到"
    
    def test_invalid_parameter_error(self):
        """测试无效参数异常"""
        error = InvalidParameterError("无效参数")
        assert isinstance(error, VideoGeneratorError)
        assert str(error) == "无效参数"
    
    def test_api_error(self):
        """测试API错误"""
        error = APIError("API错误", status_code=500)
        assert isinstance(error, VideoGeneratorError)
        assert error.status_code == 500
    
    def test_rate_limit_error(self):
        """测试速率限制错误"""
        error = RateLimitError("速率限制", retry_after=30)
        assert isinstance(error, APIError)
        assert error.status_code == 429
        assert error.retry_after == 30
    
    def test_authentication_error(self):
        """测试认证错误"""
        error = AuthenticationError("认证失败")
        assert isinstance(error, APIError)
    
    def test_task_timeout_error(self):
        """测试任务超时错误"""
        error = TaskTimeoutError("任务超时")
        assert isinstance(error, VideoGeneratorError)
    
    def test_configuration_error(self):
        """测试配置错误"""
        error = ConfigurationError("配置错误")
        assert isinstance(error, VideoGeneratorError)
    
    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("验证失败")
        assert isinstance(error, VideoGeneratorError)
    
    def test_content_policy_violation_error(self):
        """测试内容策略违规错误"""
        error = ContentPolicyViolationError("内容违规")
        assert isinstance(error, APIError)
