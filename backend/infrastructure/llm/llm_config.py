"""
LLM 配置管理模块

功能：
- 管理 VLM Provider 的配置（API Key、Base URL、模型名称等）
- 从 JSON 配置文件或环境变量加载配置
- 敏感信息（API Key）从环境变量读取，不写入配置文件
- 支持多 Provider 配置（Qwen、ChatGPT、Grok、Claude）

配置文件示例（llm_config.json）：
```json
{
    "default_provider": "qwen",
    "providers": {
        "qwen": {
            "model": "qwen-vl-plus",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "timeout": 30,
            "max_retries": 3
        },
        "chatgpt": {
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
            "max_retries": 3
        }
    },
    "cache": {
        "enabled": true,
        "ttl": 604800
    }
}
```

环境变量（敏感信息）：
- VLM_QWEN_API_KEY: Qwen API 密钥
- VLM_CHATGPT_API_KEY: ChatGPT API 密钥
- VLM_GROK_API_KEY: Grok API 密钥
- VLM_CLAUDE_API_KEY: Claude API 密钥

作者：AI Python Architect
日期：2025-11-12
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ProviderConfig(BaseModel):
    """
    单个 VLM Provider 的配置

    字段说明：
    - model: 模型名称（如 "qwen-vl-plus"）
    - base_url: API 基础 URL
    - timeout: 超时时间（秒）
    - max_retries: 最大重试次数
    - api_key: API 密钥（运行时从环境变量读取，不存储在配置文件中）

    使用示例：
    ```python
    config = ProviderConfig(
        model="qwen-vl-plus",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=30,
        max_retries=3
    )
    ```
    """
    model_config = ConfigDict(extra="allow")  # 允许额外字段

    model: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API 基础 URL")
    timeout: int = Field(default=30, description="超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")

    # API Key 不存储在配置文件中，运行时从环境变量读取
    api_key: Optional[str] = Field(default=None, exclude=True, description="API 密钥（从环境变量读取）")


class CacheConfig(BaseModel):
    """
    缓存配置

    字段说明：
    - enabled: 是否启用缓存
    - ttl: 缓存过期时间（秒，默认7天）

    使用示例：
    ```python
    cache_config = CacheConfig(enabled=True, ttl=604800)
    ```
    """
    enabled: bool = Field(default=True, description="是否启用缓存")
    ttl: int = Field(default=604800, description="缓存过期时间（秒，默认7天）")


class LLMConfig(BaseModel):
    """
    LLM 总配置

    字段说明：
    - default_provider: 默认 Provider（如 "qwen"）
    - providers: Provider 配置字典（键为 Provider 名称）
    - cache: 缓存配置

    使用示例：
    ```python
    config = LLMConfig(
        default_provider="qwen",
        providers={
            "qwen": ProviderConfig(...)
        },
        cache=CacheConfig(enabled=True, ttl=604800)
    )
    ```
    """
    model_config = ConfigDict(extra="allow")

    default_provider: str = Field(..., description="默认 Provider 名称")
    providers: Dict[str, ProviderConfig] = Field(..., description="Provider 配置字典")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="缓存配置")

    def get_provider_config(self, provider_name: Optional[str] = None) -> ProviderConfig:
        """
        获取指定 Provider 的配置

        Args:
            provider_name: Provider 名称（如果为 None，使用 default_provider）

        Returns:
            ProviderConfig: Provider 配置对象

        Raises:
            KeyError: 如果 Provider 不存在

        使用示例：
        ```python
        config = load_llm_config()
        qwen_config = config.get_provider_config("qwen")
        ```
        """
        provider = provider_name or self.default_provider
        if provider not in self.providers:
            raise KeyError(f"Provider '{provider}' not found in configuration")
        return self.providers[provider]

    def get_api_key(self, provider_name: Optional[str] = None) -> Optional[str]:
        """
        从环境变量获取 API Key

        环境变量格式：VLM_{PROVIDER}_API_KEY（全大写）
        例如：VLM_QWEN_API_KEY, VLM_CHATGPT_API_KEY

        Args:
            provider_name: Provider 名称（如果为 None，使用 default_provider）

        Returns:
            Optional[str]: API Key（如果环境变量存在）

        使用示例：
        ```python
        config = load_llm_config()
        api_key = config.get_api_key("qwen")  # 从 VLM_QWEN_API_KEY 读取
        ```
        """
        provider = provider_name or self.default_provider
        env_var_name = f"VLM_{provider.upper()}_API_KEY"
        return os.getenv(env_var_name)


def load_llm_config(config_path: Optional[Path] = None) -> LLMConfig:
    """
    加载 LLM 配置文件

    Args:
        config_path: 配置文件路径（如果为 None，使用默认路径）

    Returns:
        LLMConfig: 配置对象

    Raises:
        FileNotFoundError: 如果配置文件不存在

    使用示例：
    ```python
    # 使用默认路径
    config = load_llm_config()

    # 使用自定义路径
    config = load_llm_config(Path("custom_config.json"))
    ```
    """
    # 默认配置文件路径：backend/config/llm_config.json
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "llm_config.json"

    if not config_path.exists():
        # 如果配置文件不存在，使用默认配置
        return get_default_config()

    # 读取 JSON 配置文件
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    # 兼容旧版配置文件格式（转换为新格式）
    # 旧版使用 "active_provider"，新版使用 "default_provider"
    if "active_provider" in config_data and "default_provider" not in config_data:
        config_data["default_provider"] = config_data.pop("active_provider")

    # 转换 providers 格式（如果需要）
    # 旧版的 providers 字段可能包含额外的元数据，需要映射到 ProviderConfig
    if "providers" in config_data:
        new_providers = {}
        for provider_name, provider_data in config_data["providers"].items():
            # 提取 ProviderConfig 所需的字段
            new_providers[provider_name] = {
                "model": provider_data.get("model", "unknown"),
                "base_url": provider_data.get("base_url", ""),
                "timeout": provider_data.get("timeout", 30),
                "max_retries": provider_data.get("max_retries", 3),
            }
        config_data["providers"] = new_providers

    # 如果没有 cache 配置，使用默认值
    if "cache" not in config_data:
        config_data["cache"] = {"enabled": True, "ttl": 604800}

    # 解析为 Pydantic 对象
    return LLMConfig(**config_data)


def get_default_config() -> LLMConfig:
    """
    获取默认配置（当配置文件不存在时使用）

    Returns:
        LLMConfig: 默认配置对象

    使用示例：
    ```python
    config = get_default_config()
    ```
    """
    return LLMConfig(
        default_provider="qwen",
        providers={
            "qwen": ProviderConfig(
                model="qwen-vl-plus",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                timeout=30,
                max_retries=3
            ),
            "chatgpt": ProviderConfig(
                model="gpt-4o",
                base_url="https://api.openai.com/v1",
                timeout=30,
                max_retries=3
            ),
            "grok": ProviderConfig(
                model="grok-vision",
                base_url="https://api.x.ai/v1",
                timeout=30,
                max_retries=3
            ),
            "claude": ProviderConfig(
                model="claude-3-5-sonnet-20241022",
                base_url="https://api.anthropic.com/v1",
                timeout=30,
                max_retries=3
            )
        },
        cache=CacheConfig(enabled=True, ttl=604800)
    )


def save_llm_config(config: LLMConfig, config_path: Optional[Path] = None):
    """
    保存 LLM 配置到文件

    注意：API Key 不会保存到文件中（已在 ProviderConfig 中设置 exclude=True）

    Args:
        config: 配置对象
        config_path: 配置文件路径（如果为 None，使用默认路径）

    使用示例：
    ```python
    config = get_default_config()
    save_llm_config(config)  # 保存到默认路径
    ```
    """
    # 默认配置文件路径
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "llm_config.json"

    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存为 JSON（API Key 会被排除）
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(exclude_none=True), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    """
    LLM 配置管理模块测试

    验证：
    1. 默认配置生成
    2. 配置文件保存和加载
    3. API Key 从环境变量读取
    4. Provider 配置获取
    """
    print("=" * 80)
    print("LLM 配置管理模块测试")
    print("=" * 80)

    # 1. 测试默认配置生成
    print("\n[测试1] 默认配置生成")
    default_config = get_default_config()
    print(f"  ✓ 默认 Provider: {default_config.default_provider}")
    print(f"  ✓ 支持的 Providers: {list(default_config.providers.keys())}")
    print(f"  ✓ 缓存配置: enabled={default_config.cache.enabled}, ttl={default_config.cache.ttl}s")

    # 2. 测试 Provider 配置获取
    print("\n[测试2] Provider 配置获取")
    try:
        qwen_config = default_config.get_provider_config("qwen")
        print(f"  ✓ Qwen 配置:")
        print(f"    - 模型: {qwen_config.model}")
        print(f"    - Base URL: {qwen_config.base_url}")
        print(f"    - 超时: {qwen_config.timeout}s")
        print(f"    - 重试次数: {qwen_config.max_retries}")
    except Exception as e:
        print(f"  ✗ 获取配置失败: {e}")

    # 3. 测试 API Key 读取（模拟）
    print("\n[测试3] API Key 从环境变量读取")
    # 设置测试环境变量
    os.environ["VLM_QWEN_API_KEY"] = "sk-test-qwen-key"
    os.environ["VLM_CHATGPT_API_KEY"] = "sk-test-chatgpt-key"

    api_key = default_config.get_api_key("qwen")
    if api_key:
        print(f"  ✓ Qwen API Key: {api_key[:10]}... (已隐藏)")
    else:
        print("  ⚠ Qwen API Key 未设置（环境变量 VLM_QWEN_API_KEY）")

    api_key = default_config.get_api_key("chatgpt")
    if api_key:
        print(f"  ✓ ChatGPT API Key: {api_key[:10]}... (已隐藏)")
    else:
        print("  ⚠ ChatGPT API Key 未设置（环境变量 VLM_CHATGPT_API_KEY）")

    # 4. 测试配置保存（保存到临时路径）
    print("\n[测试4] 配置保存")
    try:
        temp_config_path = Path(__file__).parent / "test_llm_config.json"
        save_llm_config(default_config, temp_config_path)
        print(f"  ✓ 配置已保存到: {temp_config_path}")

        # 验证 API Key 未被保存
        with open(temp_config_path, "r") as f:
            saved_content = f.read()
        if "api_key" not in saved_content and "sk-test" not in saved_content:
            print("  ✓ API Key 未写入配置文件（符合安全要求）")
        else:
            print("  ✗ API Key 被意外写入配置文件（安全风险！）")

        # 测试加载
        loaded_config = load_llm_config(temp_config_path)
        if loaded_config.default_provider == default_config.default_provider:
            print("  ✓ 配置加载成功")
        else:
            print("  ✗ 配置加载失败")

        # 清理临时文件
        temp_config_path.unlink()
        print("  ✓ 临时文件已清理")
    except Exception as e:
        print(f"  ✗ 配置保存/加载失败: {e}")

    # 5. 使用提示
    print("\n[使用提示] 如何配置 API Key:")
    print("  在生产环境中，请设置以下环境变量：")
    print("  ")
    print("  # Linux/Mac:")
    print("  export VLM_QWEN_API_KEY='你的Qwen API密钥'")
    print("  export VLM_CHATGPT_API_KEY='你的ChatGPT API密钥'")
    print("  ")
    print("  # Windows PowerShell:")
    print("  $env:VLM_QWEN_API_KEY='你的Qwen API密钥'")
    print("  $env:VLM_CHATGPT_API_KEY='你的ChatGPT API密钥'")
    print("  ")
    print("  注意：不要将 API Key 写入配置文件或代码中！")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
