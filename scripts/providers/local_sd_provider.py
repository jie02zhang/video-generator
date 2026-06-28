"""
Local Stable Diffusion Provider
"""

import os
from typing import Optional, Dict, Any, List
import logging

from scripts.core.interfaces import ImageProvider
from scripts.core.data_models import ImageGenerationRequest, ImageGenerationResponse
from scripts.core.exceptions import APIError, ConfigurationError


class LocalSDImageGenerator(ImageProvider):
    """本地Stable Diffusion图片生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, mode: str = "standard"):
        super().__init__(config, mode)
        
        # 配置
        self.model_path = self.config.get("model_path", "")
        self.api_endpoint = self.config.get("api_endpoint", "http://localhost:7860")
        
        if not self.model_path and not self.api_endpoint:
            raise ConfigurationError(
                "LocalSD需要配置model_path或api_endpoint"
            )
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """生成图片"""
        self.logger.info(f"LocalSD生成图片: {request.prompt[:30]}...")
        
        try:
            # TODO: 实现真实的Stable Diffusion调用
            # 当前为骨架实现
            
            # 模拟生成
            output_path = f"/tmp/sd_output_{hash(request.prompt)}.png"
            
            return ImageGenerationResponse(
                success=True,
                images=[output_path],
                metadata={
                    "provider": "local_sd",
                    "model_path": self.model_path,
                    "guidance_scale": request.guidance_scale,
                    "steps": request.num_inference_steps
                }
            )
            
        except Exception as e:  # pragma: no cover
            self.logger.error(f"LocalSD生成失败: {e}")  # pragma: no cover
            return ImageGenerationResponse(  # pragma: no cover
                success=False,  # pragma: no cover
                error=str(e)  # pragma: no cover
            )  # pragma: no cover
