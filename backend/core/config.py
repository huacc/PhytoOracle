"""
核心配置模块

功能：
- 从环境变量加载配置
- 提供全局配置访问
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    应用配置类

    从环境变量或 .env 文件加载配置
    """

    # ==================== 项目基础配置 ====================
    PROJECT_NAME: str = "PhytoOracle"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="运行环境: development/production")
    DEBUG: bool = Field(default=True, description="调试模式")

    # ==================== API 配置 ====================
    API_HOST: str = Field(default="0.0.0.0", description="API 服务主机")
    API_PORT: int = Field(default=8000, description="API 服务端口")

    # ==================== 数据库配置 ====================
    DB_HOST: str = Field(default="192.168.0.119", description="PostgreSQL 主机")
    DB_PORT: int = Field(default=5432, description="PostgreSQL 端口")
    DB_NAME: str = Field(default="phytooracle", description="数据库名称")
    DB_USER: str = Field(default="admin", description="数据库用户名")
    DB_PASSWORD: str = Field(default="123456", description="数据库密码")
    DB_POOL_MIN_SIZE: int = Field(default=5, description="连接池最小连接数")
    DB_POOL_MAX_SIZE: int = Field(default=20, description="连接池最大连接数")

    @property
    def DATABASE_URL(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ==================== Redis 配置 ====================
    REDIS_HOST: str = Field(default="192.168.0.119", description="Redis 主机")
    REDIS_PORT: int = Field(default=6379, description="Redis 端口")
    REDIS_PASSWORD: str = Field(default="123456", description="Redis 密码")
    REDIS_DB: int = Field(default=0, description="Redis 数据库编号")

    @property
    def REDIS_URL(self) -> str:
        """生成 Redis 连接URL"""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ==================== VLM 配置 ====================
    # 注意：VLM API Key 不应写入配置文件，应从外部安全配置读取
    # 这里仅定义配置项，实际使用时从 llm_config.json 读取
    VLM_PROVIDER: str = Field(default="qwen", description="VLM 提供商: qwen/chatgpt/grok/claude")
    VLM_CACHE_TTL: int = Field(default=3600, description="VLM 缓存过期时间(秒)")
    VLM_TIMEOUT: int = Field(default=30, description="VLM API 超时时间(秒)")

    # ==================== 存储配置 ====================
    STORAGE_BASE_PATH: Path = Field(
        default=PROJECT_ROOT / "storage" / "images",
        description="图片存储根目录"
    )

    # ==================== 知识库配置 ====================
    KNOWLEDGE_BASE_PATH: Path = Field(
        default=PROJECT_ROOT / "knowledge_base",
        description="知识库JSON文件根目录"
    )

    # ==================== 安全配置 ====================
    SECRET_KEY: str = Field(default="phytooracle-secret-key-change-in-production", description="JWT密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_EXPIRE_MINUTES: int = Field(default=10080, description="JWT过期时间(分钟，默认7天)")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


if __name__ == "__main__":
    # 测试配置加载
    print(f"项目名称: {settings.PROJECT_NAME}")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"存储路径: {settings.STORAGE_BASE_PATH}")
    print(f"知识库路径: {settings.KNOWLEDGE_BASE_PATH}")
