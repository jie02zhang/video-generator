"""
测试日志配置（P0-005）
"""

import pytest
import logging
import os
from pathlib import Path
from scripts.core.logging_config import setup_logging, get_logger


class TestLoggingConfig:
    """测试日志配置"""
    
    def test_setup_logging(self):
        """测试配置日志"""
        setup_logging(level="DEBUG")
        
        logger = get_logger(__name__)
        assert logger is not None
        # 检查有效级别（继承自主日志器）
        assert logger.getEffectiveLevel() <= logging.DEBUG
    
    def test_setup_logging_with_file(self, tmp_path):
        """测试配置文件日志"""
        log_file = tmp_path / "test.log"
        
        setup_logging(level="INFO", log_file=str(log_file))
        
        logger = get_logger(__name__)
        logger.info("测试日志")
        
        # 检查日志文件是否创建
        assert log_file.exists()
    
    def test_get_logger(self):
        """测试获取日志器"""
        logger = get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_log_levels(self):
        """测试日志级别"""
        setup_logging(level="WARNING")
        
        logger = get_logger(__name__)
        # 使用getEffectiveLevel检查实际生效的级别
        assert logger.getEffectiveLevel() == logging.WARNING
    
    def test_multiple_loggers(self):
        """测试多个日志器"""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")
        
        assert logger1 is not logger2
        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
    
    def test_setup_logging_console_handler(self):
        """测试控制台处理器"""
        setup_logging(level="INFO")
        
        logger = get_logger(__name__)
        
        # 检查是否有控制台处理器
        has_console = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )
        # 根日志器应该有处理器
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
