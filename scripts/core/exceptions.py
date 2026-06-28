"""
自定义异常类
"""

from typing import Optional, Any


class VideoGeneratorError(Exception):
    """视频生成器基础异常"""
    pass


class ModelNotFoundError(VideoGeneratorError):
    """模型未找到"""
    pass


class InvalidParameterError(VideoGeneratorError):
    """无效参数"""
    pass


class APIError(VideoGeneratorError):
    """API调用错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(APIError):
    """速率限制错误"""
    def __init__(self, message: str = "API rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """认证错误"""
    pass


class TaskTimeoutError(VideoGeneratorError):
    """任务超时"""
    pass


class TaskFailedError(VideoGeneratorError):
    """任务失败"""
    pass


class ConfigurationError(VideoGeneratorError):
    """配置错误"""
    pass


class ValidationError(VideoGeneratorError):
    """数据验证错误"""
    pass


class ContentPolicyViolationError(APIError):
    """内容策略违规"""
    pass


class PromptInjectionError(VideoGeneratorError):
    """Prompt注入攻击"""
    pass


class APITimeoutError(APIError):
    """API超时"""
    pass


class DiskSpaceError(VideoGeneratorError):
    """磁盘空间不足"""
    pass
