"""
补充测试：达到99%覆盖率
"""

import pytest
from scripts.core.data_models import ImageGenerationRequest
from scripts.core.exceptions import ValidationError


class TestDataModelsEdgeCases:
    """测试数据模型边缘情况（达到99%覆盖率）"""
    
    def test_negative_num_inference_steps(self):
        """测试负数推理步数（覆盖data_models.py:60）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="测试",
                num_inference_steps=0  # 应该触发验证错误
            )
        
        assert "推理步数必须大于0" in str(exc_info.value)
