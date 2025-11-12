"""
VLM Provider适配器

为不同的VLM提供商提供统一的接口适配器。

目前支持的适配器：
- QwenVLAdapter: 千问VL (阿里云DashScope API)

作者：AI Python Architect
日期：2025-11-13
"""

from backend.infrastructure.llm.adapters.qwen_adapter import QwenVLAdapter

__all__ = [
    "QwenVLAdapter",
]
