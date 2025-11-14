"""
Storage 模块

功能：
- 本地图片存储服务
- 存储配置管理
- 存储异常处理

导出类：
- LocalImageStorage: 本地图片存储服务
- StorageConfig: 存储配置模型
- StorageException及其子类: 存储异常
"""

from backend.infrastructure.storage.local_storage import LocalImageStorage
from backend.infrastructure.storage.storage_config import StorageConfig
from backend.infrastructure.storage.storage_exceptions import (
    StorageException,
    StorageConfigError,
    ImageSaveError,
    ImageMoveError,
    ImageDeleteError,
    PathGenerationError,
    InvalidImageFormat,
    ImageTooLargeError,
)

__all__ = [
    # 核心类
    "LocalImageStorage",
    "StorageConfig",
    # 异常类
    "StorageException",
    "StorageConfigError",
    "ImageSaveError",
    "ImageMoveError",
    "ImageDeleteError",
    "PathGenerationError",
    "InvalidImageFormat",
    "ImageTooLargeError",
]
