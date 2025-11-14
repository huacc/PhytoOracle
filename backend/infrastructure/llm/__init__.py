"""
LLM Infrastructure Layer

导出所有 LLM 相关的核心模块（P2.1 + P2.2）
"""

# P2.1: Instructor 客户端和配置管理
from .instructor_client import InstructorClient, AsyncInstructorClient
from .llm_config import LLMConfig, ProviderConfig, CacheConfig, load_llm_config, get_default_config

# P2.2: VLM 客户端（Fallback 机制）
from .vlm_client import VLMClient, MultiProviderVLMClient
from .cache_manager import CacheManager
from .vlm_exceptions import (
    VLMException,
    ProviderUnavailableException,
    AllProvidersFailedException,
    ValidationException,
    TimeoutException,
    QuotaExceededException,
)

__all__ = [
    # P2.1
    "InstructorClient",
    "AsyncInstructorClient",
    "LLMConfig",
    "ProviderConfig",
    "CacheConfig",
    "load_llm_config",
    "get_default_config",
    # P2.2
    "VLMClient",
    "MultiProviderVLMClient",
    "CacheManager",
    "VLMException",
    "ProviderUnavailableException",
    "AllProvidersFailedException",
    "ValidationException",
    "TimeoutException",
    "QuotaExceededException",
]
