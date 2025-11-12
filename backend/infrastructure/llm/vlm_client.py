"""
VLM 客户端 - 多 Provider Fallback 机制

功能：
- 提供统一的 VLM 客户端接口
- 支持多 Provider Fallback（Qwen → ChatGPT → Grok → Claude）
- 集成 P2.1 的 InstructorClient（确保结构化输出）
- 集成缓存管理器（减少重复调用）
- 健壮的错误处理和重试机制

设计理念：
- VLMClient 是抽象基类，定义接口规范
- MultiProviderVLMClient 是实现类，封装 Fallback 逻辑
- 深度复用 P2.1 的 InstructorClient，不重复实现
- 为 P2.3 的 Redis 缓存预留接口

使用示例：
```python
from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient
from backend.infrastructure.llm.prompts.response_schema import Q02Response

# 初始化客户端（自动从配置文件和环境变量加载）
client = MultiProviderVLMClient()

# 查询 VLM（自动 Fallback + 缓存）
response = client.query_structured(
    prompt="Identify the genus of this flower",
    response_model=Q02Response,
    image_bytes=image_bytes
)

print(f"识别结果: {response.choice}")  # Rosa, Prunus, etc.
print(f"置信度: {response.confidence}")  # 0.0-1.0
```

作者：AI Python Architect
日期：2025-11-12
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel

# 复用 P2.1 的成果
from backend.infrastructure.llm.instructor_client import InstructorClient
from backend.infrastructure.llm.llm_config import LLMConfig, ProviderConfig, load_llm_config
from backend.infrastructure.llm.cache_manager import CacheManager
from backend.infrastructure.llm.vlm_exceptions import (
    VLMException,
    ProviderUnavailableException,
    AllProvidersFailedException,
    ValidationException,
    TimeoutException,
)
# Import Qwen VL adapter for non-OpenAI compatible providers
from backend.infrastructure.llm.adapters.qwen_adapter import QwenVLAdapter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VLMClient(ABC):
    """
    VLM 客户端抽象基类

    定义了所有 VLM 客户端必须实现的接口

    功能规范：
    - query_text: 查询纯文本（无图像）
    - query_image: 查询图像 + 文本
    - query_structured: 查询并返回结构化输出（集成 Instructor）

    使用示例：
    ```python
    # 不直接使用基类，而是使用实现类
    client = MultiProviderVLMClient()

    # 调用 query_structured
    response = client.query_structured(
        prompt="Identify genus",
        response_model=Q02Response,
        image_bytes=image_bytes
    )
    ```
    """

    @abstractmethod
    def query_text(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """
        查询纯文本（无图像）

        Args:
            prompt: 提示词
            **kwargs: 其他参数（如 model, temperature）

        Returns:
            str: VLM 返回的文本

        Raises:
            VLMException: VLM 调用失败
        """
        pass

    @abstractmethod
    def query_image(
        self,
        prompt: str,
        image_bytes: bytes,
        **kwargs
    ) -> str:
        """
        查询图像 + 文本

        Args:
            prompt: 提示词
            image_bytes: 图像字节数据
            **kwargs: 其他参数

        Returns:
            str: VLM 返回的文本

        Raises:
            VLMException: VLM 调用失败
        """
        pass

    @abstractmethod
    def query_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        image_bytes: Optional[bytes] = None,
        **kwargs
    ) -> BaseModel:
        """
        查询并返回结构化输出（集成 Instructor）

        Args:
            prompt: 提示词
            response_model: Pydantic 模型类（如 Q02Response）
            image_bytes: 可选的图像字节数据
            **kwargs: 其他参数

        Returns:
            BaseModel: 符合 response_model 的结构化输出

        Raises:
            VLMException: VLM 调用失败
            ValidationException: 响应验证失败
        """
        pass


class MultiProviderVLMClient(VLMClient):
    """
    多 Provider VLM 客户端（Fallback 机制）

    功能特性：
    - 支持多 Provider Fallback（Qwen → ChatGPT → Grok → Claude）
    - 自动从配置文件和环境变量加载 Provider 配置
    - 集成 P2.1 的 InstructorClient（确保结构化输出）
    - 集成缓存管理器（减少重复调用）
    - 详细的错误日志和重试逻辑

    Fallback 顺序：
    1. Qwen VL Plus（默认，国内访问快）
    2. ChatGPT (gpt-4o)（国际标杆）
    3. Grok Vision（xAI 新秀）
    4. Claude（Anthropic 高质量）

    使用示例：
    ```python
    # 初始化客户端（使用默认配置）
    client = MultiProviderVLMClient()

    # 初始化客户端（自定义 Provider 顺序）
    client = MultiProviderVLMClient(
        providers=["chatgpt", "claude"],  # 只使用 ChatGPT 和 Claude
        enable_cache=False  # 禁用缓存
    )

    # 查询结构化输出（自动 Fallback）
    response = client.query_structured(
        prompt="Identify the genus",
        response_model=Q02Response,
        image_bytes=image_bytes
    )
    ```
    """

    def __init__(
        self,
        providers: Optional[List[str]] = None,
        enable_cache: bool = True,
        cache_ttl: int = 604800,  # 7 天
        config_path: Optional[Path] = None
    ):
        """
        初始化多 Provider VLM 客户端

        Args:
            providers: Provider 列表（默认：["qwen", "chatgpt", "grok", "claude"]）
            enable_cache: 是否启用缓存（默认：True）
            cache_ttl: 缓存 TTL（秒，默认：7 天）
            config_path: 配置文件路径（默认：backend/config/llm_config.json）

        使用示例：
        ```python
        # 使用默认配置
        client = MultiProviderVLMClient()

        # 自定义 Provider 顺序
        client = MultiProviderVLMClient(
            providers=["chatgpt", "claude"]
        )

        # 禁用缓存
        client = MultiProviderVLMClient(enable_cache=False)
        ```
        """
        # 1. 加载 LLM 配置（复用 P2.1 的 load_llm_config）
        self.config = load_llm_config(config_path)
        logger.info(f"Loaded LLM config: {len(self.config.providers)} providers available")

        # 2. 确定 Fallback 顺序
        self.providers = providers or ["qwen", "chatgpt", "grok", "claude"]
        logger.info(f"Fallback order: {self.providers}")

        # Provider 名称映射表（支持旧版配置文件中的名称）
        self.provider_name_mapping = {
            "qwen": ["qwen", "qwen_vl"],
            "chatgpt": ["chatgpt", "gpt4o"],
            "grok": ["grok", "grok_vision"],
            "claude": ["claude", "claude3"],
        }

        # 3. 初始化 InstructorClient 实例（复用 P2.1）
        self.instructor_clients: Dict[str, InstructorClient] = {}
        for provider_name in self.providers:
            try:
                # 尝试多个可能的 Provider 名称（兼容旧版配置）
                provider_config = None
                actual_provider_name = provider_name

                for possible_name in self.provider_name_mapping.get(provider_name, [provider_name]):
                    try:
                        provider_config = self.config.get_provider_config(possible_name)
                        actual_provider_name = possible_name
                        break
                    except KeyError:
                        continue

                if provider_config is None:
                    logger.warning(f"Provider '{provider_name}' not found in config")
                    continue

                # 获取 API Key（尝试多个可能的环境变量名称）
                api_key = None
                for possible_name in self.provider_name_mapping.get(provider_name, [provider_name]):
                    api_key = self.config.get_api_key(possible_name)
                    if api_key:
                        break

                if not api_key:
                    logger.warning(
                        f"Provider '{provider_name}' API Key not found "
                        f"(environment variable: VLM_{provider_name.upper()}_API_KEY)"
                    )
                    continue

                # 初始化适配器或 InstructorClient
                # Qwen使用自定义adapter（非OpenAI兼容），其他使用InstructorClient
                if provider_name == "qwen" or actual_provider_name == "qwen_vl":
                    self.instructor_clients[provider_name] = QwenVLAdapter(
                        api_key=api_key,
                        base_url=provider_config.base_url,
                        model=provider_config.model,
                        max_retries=provider_config.max_retries,
                        timeout=provider_config.timeout
                    )
                    logger.info(f"Initialized Qwen adapter: {provider_name} ({provider_config.model})")
                else:
                    self.instructor_clients[provider_name] = InstructorClient(
                        api_key=api_key,
                        base_url=provider_config.base_url,
                        model=provider_config.model,
                        max_retries=provider_config.max_retries,
                        timeout=provider_config.timeout
                    )
                    logger.info(f"Initialized provider: {provider_name} ({provider_config.model})")

            except Exception as e:
                logger.warning(f"Failed to initialize provider '{provider_name}': {e}")
                continue

        # 4. 检查是否有可用的 Provider
        if not self.instructor_clients:
            raise ProviderUnavailableException(
                "No providers available. Please check your API keys and configuration.",
                details={"providers_tried": self.providers}
            )

        # 5. 初始化缓存管理器
        self.cache_manager = CacheManager(ttl_seconds=cache_ttl) if enable_cache else None
        if self.cache_manager:
            logger.info(f"Cache enabled (TTL: {cache_ttl}s)")

    def query_text(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """
        查询纯文本（无图像）

        注意：当前实现主要用于图像 + 文本的多模态查询
        纯文本查询暂不支持（可在未来版本扩展）

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            str: VLM 返回的文本

        Raises:
            NotImplementedError: 当前版本不支持纯文本查询
        """
        raise NotImplementedError(
            "Pure text query is not supported in current version. "
            "Use query_structured() with image_bytes=None instead."
        )

    def query_image(
        self,
        prompt: str,
        image_bytes: bytes,
        **kwargs
    ) -> str:
        """
        查询图像 + 文本（返回非结构化文本）

        注意：推荐使用 query_structured() 以获得结构化输出
        此方法仅用于需要非结构化文本的场景

        Args:
            prompt: 提示词
            image_bytes: 图像字节数据
            **kwargs: 其他参数

        Returns:
            str: VLM 返回的文本

        Raises:
            AllProvidersFailedException: 所有 Provider 都失败
        """
        # 使用 Fallback 机制调用 VLM
        last_exception = None

        for provider_name in self.providers:
            client = self.instructor_clients.get(provider_name)
            if not client:
                continue

            try:
                logger.info(f"Querying provider: {provider_name}")

                # 调用 VLM（不使用 Instructor，直接返回文本）
                # 注意：这里需要直接调用 OpenAI 客户端，而不是 Instructor
                # 暂不实现，推荐使用 query_structured()

                raise NotImplementedError(
                    "Non-structured query not implemented. "
                    "Please use query_structured() instead."
                )

            except Exception as e:
                last_exception = e
                logger.warning(f"Provider '{provider_name}' failed: {e}")
                continue

        # 所有 Provider 都失败
        raise AllProvidersFailedException(
            f"All providers failed to process request",
            details={
                "providers_tried": self.providers,
                "last_error": str(last_exception)
            }
        )

    def query_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        image_bytes: Optional[bytes] = None,
        **kwargs
    ) -> BaseModel:
        """
        查询并返回结构化输出（核心方法）

        使用 Fallback 机制调用 VLM，确保返回符合 response_model 的结构化输出
        自动处理缓存、重试、Fallback

        Args:
            prompt: 提示词
            response_model: Pydantic 模型类（如 Q02Response）
            image_bytes: 可选的图像字节数据
            **kwargs: 其他参数（如 temperature, top_p）

        Returns:
            BaseModel: 符合 response_model 的 Pydantic 对象

        Raises:
            AllProvidersFailedException: 所有 Provider 都失败
            ValidationException: 响应验证失败

        使用示例：
        ```python
        from backend.infrastructure.llm.prompts.response_schema import Q02Response

        client = MultiProviderVLMClient()

        # 查询花卉种属
        response = client.query_structured(
            prompt="Identify the genus of this flower",
            response_model=Q02Response,
            image_bytes=image_bytes
        )

        print(f"识别结果: {response.choice}")
        print(f"置信度: {response.confidence}")
        ```
        """
        # 1. 检查缓存
        if self.cache_manager and image_bytes:
            cached_result = self.cache_manager.get(prompt, image_bytes)
            if cached_result:
                logger.info("Cache hit! Returning cached result.")
                return cached_result

        # 2. 使用 Fallback 机制调用 VLM
        last_exception = None

        for provider_name in self.providers:
            client = self.instructor_clients.get(provider_name)
            if not client:
                logger.debug(f"Provider '{provider_name}' not available, skipping...")
                continue

            try:
                logger.info(f"Querying provider: {provider_name} with model {client.model}")

                # 调用 P2.1 的 InstructorClient（深度复用）
                result = client.query(
                    prompt=prompt,
                    image_bytes=image_bytes,
                    response_model=response_model,
                    **kwargs
                )

                # 成功！记录日志
                logger.info(
                    f"Provider '{provider_name}' succeeded. "
                    f"Result: {result.model_dump_json(indent=None)}"
                )

                # 3. 缓存结果
                if self.cache_manager and image_bytes:
                    self.cache_manager.set(prompt, result, image_bytes)
                    logger.debug("Result cached.")

                return result

            except TimeoutError as e:
                last_exception = TimeoutException(
                    f"Request timed out",
                    provider=provider_name,
                    details={"timeout": client.timeout}
                )
                logger.warning(f"Provider '{provider_name}' timed out: {e}")
                continue

            except Exception as e:
                last_exception = e
                logger.warning(f"Provider '{provider_name}' failed: {type(e).__name__}: {e}")
                continue

        # 4. 所有 Provider 都失败
        raise AllProvidersFailedException(
            f"All {len(self.providers)} providers failed to process request",
            details={
                "providers_tried": self.providers,
                "available_providers": list(self.instructor_clients.keys()),
                "last_error": str(last_exception),
                "last_error_type": type(last_exception).__name__
            }
        )

    def get_available_providers(self) -> List[str]:
        """
        获取当前可用的 Provider 列表

        Returns:
            List[str]: 可用的 Provider 名称列表

        使用示例：
        ```python
        client = MultiProviderVLMClient()
        available = client.get_available_providers()
        print(f"可用 Providers: {available}")
        ```
        """
        return list(self.instructor_clients.keys())

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存统计信息

        Returns:
            Optional[Dict[str, Any]]: 缓存统计（如果启用缓存）

        使用示例：
        ```python
        client = MultiProviderVLMClient()
        stats = client.get_cache_stats()
        if stats:
            print(f"缓存命中率: {stats['active_entries']} / {stats['total_entries']}")
        ```
        """
        if self.cache_manager:
            return self.cache_manager.get_stats()
        return None

    def clear_cache(self) -> None:
        """
        清空缓存

        使用示例：
        ```python
        client = MultiProviderVLMClient()
        client.clear_cache()
        print("缓存已清空")
        ```
        """
        if self.cache_manager:
            self.cache_manager.clear()
            logger.info("Cache cleared.")


# ==================== 导出类 ====================

__all__ = [
    "VLMClient",
    "MultiProviderVLMClient",
]


if __name__ == "__main__":
    """
    VLM 客户端测试

    注意：此测试需要：
    1. 配置文件：backend/config/llm_config.json
    2. 环境变量：VLM_QWEN_API_KEY, VLM_CHATGPT_API_KEY 等
    3. 测试图片（可选）

    由于这些前置条件，测试将跳过实际的 API 调用
    """
    from backend.infrastructure.llm.prompts.response_schema import Q02Response

    print("=" * 80)
    print("VLM 客户端测试")
    print("=" * 80)

    # 1. 测试客户端初始化
    print("\n[测试1] 客户端初始化")
    try:
        # 设置测试环境变量
        os.environ["VLM_QWEN_API_KEY"] = "sk-test-qwen-key"
        os.environ["VLM_CHATGPT_API_KEY"] = "sk-test-chatgpt-key"

        client = MultiProviderVLMClient()
        print(f"  ✓ 客户端初始化成功")
        print(f"  - 可用 Providers: {client.get_available_providers()}")
        print(f"  - Fallback 顺序: {client.providers}")

    except ProviderUnavailableException as e:
        print(f"  ⚠ Provider 不可用: {e}")
        print(f"  提示：请设置环境变量（VLM_QWEN_API_KEY 等）")

    except Exception as e:
        print(f"  ✗ 初始化失败: {type(e).__name__}: {e}")

    # 2. 测试缓存功能
    print("\n[测试2] 缓存功能")
    if 'client' in locals():
        stats = client.get_cache_stats()
        if stats:
            print(f"  ✓ 缓存已启用")
            print(f"  - 总条目数: {stats['total_entries']}")
            print(f"  - 有效条目数: {stats['active_entries']}")
            print(f"  - TTL: {stats['ttl_seconds']}s")
        else:
            print(f"  ⊘ 缓存未启用")
    else:
        print(f"  ⊘ 跳过（客户端未初始化）")

    # 3. 提示如何进行实际测试
    print("\n[提示] 如何进行实际 VLM 调用测试:")
    print("  1. 设置真实的环境变量:")
    print("     export VLM_QWEN_API_KEY='你的真实Qwen API密钥'")
    print("     export VLM_CHATGPT_API_KEY='你的真实ChatGPT API密钥'")
    print("")
    print("  2. 准备测试代码:")
    print("     ```python")
    print("     from pathlib import Path")
    print("     from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient")
    print("     from backend.infrastructure.llm.prompts.response_schema import Q02Response")
    print("")
    print("     # 初始化客户端")
    print("     client = MultiProviderVLMClient()")
    print("")
    print("     # 读取测试图片")
    print("     image_bytes = Path('test_flower.jpg').read_bytes()")
    print("")
    print("     # 调用 VLM（自动 Fallback + 缓存）")
    print("     response = client.query_structured(")
    print("         prompt='Identify the genus of this flower',")
    print("         response_model=Q02Response,")
    print("         image_bytes=image_bytes")
    print("     )")
    print("")
    print("     # 查看结果")
    print("     print(f'识别结果: {response.choice}')  # Rosa, Prunus, etc.")
    print("     print(f'置信度: {response.confidence}')  # 0.0-1.0")
    print("     print(f'推理过程: {response.reasoning}')  # 可选")
    print("     ```")

    # 4. 测试 Fallback 机制（模拟）
    print("\n[测试3] Fallback 机制（模拟）")
    print("  说明：Fallback 机制在实际调用中自动生效")
    print("  - 首先尝试 Qwen VL Plus")
    print("  - 如果 Qwen 失败，自动切换到 ChatGPT")
    print("  - 如果 ChatGPT 失败，自动切换到 Grok")
    print("  - 如果 Grok 失败，自动切换到 Claude")
    print("  - 如果所有 Provider 都失败，抛出 AllProvidersFailedException")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
