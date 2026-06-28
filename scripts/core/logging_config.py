"""
日志配置（P0-005）
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        max_bytes: 日志文件最大大小
        backup_count: 备份文件数量
    """
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称（通常是模块名 __name__）
    
    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


# 默认配置
DEFAULT_LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "logs",
    "video-generator.log"
)

# 自动配置（如果直接运行此模块）
if __name__ == "__main__":  # pragma: no cover
    setup_logging(level="DEBUG", log_file=DEFAULT_LOG_FILE)
    
    # 测试
    logger = get_logger(__name__)
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
