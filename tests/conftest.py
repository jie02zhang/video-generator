"""
自动化测试脚本框架 - conftest.py
=====================================

本文件定义公共的fixtures和mock配置，供所有测试文件使用。

测试策略：
1. 使用unittest.mock模拟所有外部API调用（Hugging Face, Edge TTS, FFmpeg）
2. 使用pytest-mock进行灵活的mock管理
3. 所有测试离线运行，零API成本
4. 模拟4种API响应：成功、失败、超时、内容违规
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional, Dict, Any

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.core.data_models import (
    ImageGenerationResponse,
    VideoGenerationResponse,
    TaskStatus,
    ImageGenerationRequest,
    VideoGenerationRequest
)
from scripts.core.exceptions import (
    APIError,
    ValidationError,
    TaskTimeoutError,
    ContentPolicyViolationError,
    ModelNotFoundError
)


# ==================== Mock配置常量 ====================

class MockResponse:
    """模拟HTTP响应对象"""
    def __init__(self, status_code: int, json_data: Optional[Dict] = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# ==================== Fixtures: 基础配置 ====================

@pytest.fixture
def mock_config():
    """提供模拟的配置字典"""
    return {
        'models': {
            'image': {
                'default': 'local-sd',
                'available': ['local-sd', 'dalle2', 'dalle3', 'flux', 'sdxl']
            },
            'video': {
                'default': 'runway',
                'available': ['runway', 'kling']
            }
        },
        'api_keys': {
            'openai': 'mock-openai-key',
            'runway': 'mock-runway-key',
            'kling': 'mock-kling-key'
        },
        'huggingface': {
            'api_url': 'https://api-inference.huggingface.co/models/',
            'token': None  # 免费API
        }
    }


@pytest.fixture
def temp_dir(tmp_path):
    """创建临时目录用于测试文件操作"""
    return tmp_path / "test_output"


# ==================== Fixtures: Mock API响应 ====================

@pytest.fixture
def mock_successful_image_response():
    """模拟成功的图片生成API响应"""
    return ImageGenerationResponse(
        success=True,
        image_url="https://huggingface.co/spaces/xxx/image.png",
        metadata={"model": "flux", "inference_time": 15.2}
    )


@pytest.fixture
def mock_failed_image_response():
    """模拟失败的图片生成API响应"""
    return ImageGenerationResponse(
        success=False,
        error="Model is currently loading, please wait"
    )


@pytest.fixture
def mock_task_status_sequence():
    """
    模拟异步任务状态序列
    返回：用于mock的side_effect列表
    """
    return [
        VideoGenerationResponse(
            task_id="task_001",
            status=TaskStatus.PENDING,
            success=None
        ),
        VideoGenerationResponse(
            task_id="task_001",
            status=TaskStatus.PROCESSING,
            success=None
        ),
        VideoGenerationResponse(
            task_id="task_001",
            status=TaskStatus.SUCCESS,
            success=True,
            video_url="https://api.example.com/videos/task_001.mp4"
        )
    ]


# ==================== Fixtures: Mock外部服务 ====================

@pytest.fixture
def mock_huggingface_api():
    """
    模拟Hugging Face API调用
    
    Mock策略：
    - 成功：返回200 + base64编码的图片数据
    - 失败：返回503 + "Model is loading"
    - 内容违规：返回400 + "Content policy violation"
    - 超时：抛出Timeout异常
    """
    with patch('scripts.providers.dalle_provider.requests.post') as mock_post:
        # 默认返回成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output': [{'image': 'base64_encoded_image_data'}]
        }
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response
        
        # 提供控制接口，让测试可以动态修改返回值
        mock_post.get_side_effect = mock_post.side_effect
        mock_post.set_side_effect = lambda effect: setattr(mock_post, 'side_effect', effect)
        
        yield mock_post


@pytest.fixture
def mock_edge_tts():
    """
    模拟Edge TTS音频生成
    
    Mock策略：
    - 成功：生成MP3文件
    - 失败：抛出Exception
    """
    with patch('scripts.generate_video.LedgeTTS') as mock_tts:
        mock_instance = MagicMock()
        mock_instance.generate_speech = MagicMock(return_value=True)
        mock_tts.return_value = mock_instance
        yield mock_tts


@pytest.fixture
def mock_ffmpeg():
    """
    模拟FFmpeg视频合成
    
    Mock策略：
    - 成功：返回0退出码，生成MP4文件
    - 失败：返回非零退出码，抛出CalledProcessError
    """
    with patch('subprocess.run') as mock_run:
        mock_completed = Mock()
        mock_completed.returncode = 0
        mock_completed.stdout = "ffmpeg version 4.4"
        mock_completed.stderr = ""
        mock_run.return_value = mock_completed
        yield mock_run


# ==================== Fixtures: Mock异常场景 ====================

@pytest.fixture
def mock_api_timeout():
    """模拟API超时异常"""
    def raise_timeout(*args, **kwargs):
        import requests
        raise requests.exceptions.Timeout("Connection timed out")
    
    return raise_timeout


@pytest.fixture
def mock_api_rate_limit():
    """模拟API限流(429 Too Many Requests)"""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.headers = {'Retry-After': '30'}
    mock_response.json.return_value = {'error': 'Rate limit exceeded'}
    mock_response.raise_for_status = lambda: (_ for _ in ()).throw(
        Exception("429 Client Error: Too Many Requests")
    )
    return mock_response


@pytest.fixture
def mock_content_policy_violation():
    """模拟内容策略违规(400 Bad Request)"""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        'error': {
            'message': 'Content policy violation',
            'type': 'content_policy_violation'
        }
    }
    mock_response.raise_for_status = lambda: (_ for _ in ()).throw(
        Exception("400 Client Error: Bad Request")
    )
    return mock_response


# ==================== Fixtures: Mock文件操作 ====================

@pytest.fixture
def mock_image_file(temp_dir):
    """创建模拟的图片文件"""
    temp_dir.mkdir(parents=True, exist_ok=True)
    image_path = temp_dir / "test_image.png"
    
    # 创建一个最小的PNG文件（1x1像素）
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
        0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    with open(image_path, 'wb') as f:
        f.write(png_data)
    
    return str(image_path)


@pytest.fixture
def mock_audio_file(temp_dir):
    """创建模拟的音频文件"""
    temp_dir.mkdir(parents=True, exist_ok=True)
    audio_path = temp_dir / "test_audio.mp3"
    
    # 创建一个最小的MP3文件（空文件即可，因为我们使用mock）
    audio_path.touch()
    
    return str(audio_path)


# ==================== Fixtures: Mock进度回调 ====================

@pytest.fixture
def mock_progress_callback():
    """模拟进度回调函数，记录调用次数和参数"""
    call_records = []
    
    def callback(progress: float, message: str):
        call_records.append({
            'progress': progress,
            'message': message
        })
    
    callback.records = call_records
    return callback


# ==================== Pytest插件配置 ====================

def pytest_runtest_setup(item):
    """每个测试前的设置"""
    # 确保测试环境隔离
    pass


def pytest_runtest_teardown(item):
    """每个测试后的清理"""
    # 清理临时文件
    pass
