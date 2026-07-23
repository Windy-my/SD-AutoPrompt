"""Configuration settings for SD-AutoPromote."""

import os
from typing import Optional
from dataclasses import dataclass

from config.providers import PROVIDERS, get_provider


@dataclass
class AppConfig:
    """Application configuration."""
    
    # LLM settings
    llm_provider: str = "openai"
    api_key: str = ""
    model_name: str = "GPT-4o"  # UI 显示名
    
    # App settings
    app_title: str = "SD-AutoPromote - 图像提示词提取工具"
    server_port: int = 7860
    
    # Image settings
    supported_formats: tuple = (".png", ".jpg", ".jpeg")
    max_image_size_mb: int = 20
    
    # Vision model fallback
    use_vision_fallback: bool = True
    
    def get_model_id(self) -> str:
        """从 UI 显示名反查实际的 model ID。"""
        from config.providers import get_model_id
        return get_model_id(self.llm_provider, self.model_name)
    
    def get_base_url(self) -> str:
        """获取当前供应商的 API base URL。"""
        p = get_provider(self.llm_provider)
        return p.base_url if p else ""
    
    def has_vision(self) -> bool:
        """当前选择的模型是否支持图片输入。"""
        from config.providers import supports_vision_by_provider
        return supports_vision_by_provider(self.llm_provider, self.model_name)


# Global singleton config
config = AppConfig()
