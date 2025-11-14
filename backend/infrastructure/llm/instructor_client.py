"""
Instructor 客户端集成 - 确保 VLM 输出符合 Pydantic 模型

功能：
- 使用 Instructor 库包装 VLM API 客户端
- 自动验证 VLM 输出符合 Pydantic Schema
- 自动重试（最多3次）
- 支持多 Provider（Qwen、ChatGPT、Grok、Claude）
- 提供类型安全的结构化输出

注意：
- 本模块是 P2.1 阶段的核心实现
- 实际的 VLM 客户端将在 P2.2 阶段完整实现
- 此处仅提供 Instructor 集成的核心封装

作者：AI Python Architect
日期：2025-11-12
"""

import os
import base64
import hashlib
from pathlib import Path
from typing import Type, Optional, TypeVar, Generic
from pydantic import BaseModel

try:
    import instructor
    from openai import OpenAI, AsyncOpenAI
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
    instructor = None
    OpenAI = None
    AsyncOpenAI = None


T = TypeVar('T', bound=BaseModel)


class InstructorClient(Generic[T]):
    """
    Instructor 客户端包装器

    使用 Instructor 库确保 VLM 输出严格符合 Pydantic 模型
    提供自动验证和重试机制

    功能特性：
    - 自动验证：确保 VLM 输出符合指定的 Pydantic Schema
    - 自动重试：验证失败时自动重试（最多3次）
    - 多 Provider 支持：统一接口支持多个 VLM Provider
    - 类型安全：返回类型明确的 Pydantic 对象

    使用示例：
    ```python
    from backend.infrastructure.llm.prompts import Q02Response

    # 初始化客户端（使用 Qwen VL Plus）
    client = InstructorClient(
        api_key="your-api-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-vl-plus"
    )

    # 调用 VLM，自动验证输出
    response = client.query(
        prompt="Identify the genus of this flower",
        image_bytes=image_bytes,
        response_model=Q02Response
    )

    # response 是一个 Q02Response 对象，100% 符合 Schema
    print(response.choice)  # "Rosa"
    print(response.confidence)  # 0.92
    ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-vl-plus",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        初始化 Instructor 客户端

        Args:
            api_key: API 密钥（如果不提供，从环境变量 VLM_API_KEY 读取）
            base_url: API 基础 URL（如果不提供，从环境变量 VLM_BASE_URL 读取）
            model: 模型名称（默认：qwen-vl-plus）
            max_retries: 最大重试次数（默认：3）
            timeout: 超时时间（秒，默认：30）

        Raises:
            ImportError: 如果 instructor 库未安装
            ValueError: 如果 API Key 未提供且环境变量中也没有

        使用示例：
        ```python
        # 方式1：显式传入 API Key
        client = InstructorClient(
            api_key="sk-xxx",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 方式2：从环境变量读取
        # export VLM_API_KEY="sk-xxx"
        # export VLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
        client = InstructorClient()
        ```
        """
        if not INSTRUCTOR_AVAILABLE:
            raise ImportError(
                "instructor library is not installed. "
                "Install it with: pip install instructor openai"
            )

        # 从环境变量或参数获取 API Key
        self.api_key = api_key or os.getenv("VLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key not provided. Either pass 'api_key' parameter or set 'VLM_API_KEY' environment variable."
            )

        # 从环境变量或参数获取 Base URL
        self.base_url = base_url or os.getenv("VLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        # 初始化 OpenAI 客户端
        self.openai_client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        # 使用 Instructor 包装客户端（启用自动验证和重试）
        self.client = instructor.from_openai(self.openai_client)

    def query(
        self,
        prompt: str,
        image_bytes: bytes,
        response_model: Type[T],
        **kwargs
    ) -> T:
        """
        查询 VLM 并返回结构化输出

        使用 Instructor 自动验证 VLM 输出是否符合 response_model
        如果验证失败，自动重试（最多 max_retries 次）

        Args:
            prompt: 提示词文本
            image_bytes: 图片二进制数据
            response_model: Pydantic 响应模型类（如 Q02Response）
            **kwargs: 其他参数（如 temperature、top_p 等）

        Returns:
            T: 符合 response_model 的 Pydantic 对象

        Raises:
            Exception: 如果所有重试都失败

        使用示例：
        ```python
        from backend.infrastructure.llm.prompts import Q02Response, Q0_2_GENUS_PROMPT

        # 读取图片
        with open("flower.jpg", "rb") as f:
            image_bytes = f.read()

        # 调用 VLM
        response = client.query(
            prompt=Q0_2_GENUS_PROMPT,
            image_bytes=image_bytes,
            response_model=Q02Response
        )

        # response 是一个 Q02Response 对象，100% 符合 Schema
        assert isinstance(response, Q02Response)
        assert response.choice in ["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia", "unknown"]
        ```
        """
        # 将图片编码为 base64
        image_base64 = self._encode_image(image_bytes)

        # 构造消息（OpenAI Vision API 格式）
        messages = [
            {
                "role": "system",
                "content": "You are a JSON API. Always respond with valid JSON, no additional text."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        # 使用 Instructor 调用（自动验证 + 重试）
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model,  # 指定响应模型（Instructor 会自动验证）
            max_retries=self.max_retries,  # 自动重试次数
            **kwargs
        )

        # response 已经是 Pydantic 对象，100% 符合 response_model
        return response

    def _encode_image(self, image_bytes: bytes) -> str:
        """
        将图片二进制数据编码为 base64 字符串

        Args:
            image_bytes: 图片二进制数据

        Returns:
            str: base64 编码后的字符串

        使用示例：
        ```python
        with open("flower.jpg", "rb") as f:
            image_bytes = f.read()

        encoded = client._encode_image(image_bytes)
        # encoded: "iVBORw0KGgoAAAANSUhEUgAA..."
        ```
        """
        return base64.b64encode(image_bytes).decode('utf-8')

    def get_cache_key(self, image_bytes: bytes, question_id: str) -> str:
        """
        生成缓存键（用于 Redis 缓存）

        缓存键格式：vlm:{image_hash}:{question_id}

        Args:
            image_bytes: 图片二进制数据
            question_id: 问题ID（如 "Q0.2"）

        Returns:
            str: 缓存键

        使用示例：
        ```python
        cache_key = client.get_cache_key(image_bytes, "Q0.2")
        # cache_key: "vlm:a1b2c3d4:Q0.2"
        ```
        """
        image_hash = hashlib.md5(image_bytes).hexdigest()[:8]
        return f"vlm:{image_hash}:{question_id}"


class AsyncInstructorClient(Generic[T]):
    """
    异步版本的 Instructor 客户端

    用于异步场景（FastAPI 异步路由）

    使用示例：
    ```python
    async def diagnose_async(image_bytes: bytes):
        client = AsyncInstructorClient()

        response = await client.query(
            prompt=Q0_2_GENUS_PROMPT,
            image_bytes=image_bytes,
            response_model=Q02Response
        )

        return response
    ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-vl-plus",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """初始化异步客户端（参数与同步版本相同）"""
        if not INSTRUCTOR_AVAILABLE:
            raise ImportError("instructor library is not installed")

        self.api_key = api_key or os.getenv("VLM_API_KEY")
        if not self.api_key:
            raise ValueError("API Key not provided")

        self.base_url = base_url or os.getenv("VLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        # 初始化异步 OpenAI 客户端
        self.openai_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        # 使用 Instructor 包装异步客户端
        self.client = instructor.from_openai(self.openai_client)

    async def query(
        self,
        prompt: str,
        image_bytes: bytes,
        response_model: Type[T],
        **kwargs
    ) -> T:
        """异步查询 VLM（参数与同步版本相同）"""
        image_base64 = self._encode_image(image_bytes)

        messages = [
            {
                "role": "system",
                "content": "You are a JSON API. Always respond with valid JSON, no additional text."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        # 异步调用
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model,
            max_retries=self.max_retries,
            **kwargs
        )

        return response

    def _encode_image(self, image_bytes: bytes) -> str:
        """将图片编码为 base64（与同步版本相同）"""
        return base64.b64encode(image_bytes).decode('utf-8')


if __name__ == "__main__":
    """
    Instructor 客户端测试

    注意：此测试需要：
    1. 安装 instructor 库：pip install instructor openai
    2. 设置环境变量：VLM_API_KEY 和 VLM_BASE_URL
    3. 提供测试图片

    由于这些前置条件，测试将跳过实际的 API 调用
    """
    print("=" * 80)
    print("Instructor 客户端测试")
    print("=" * 80)

    # 1. 测试库是否可用
    print("\n[测试1] Instructor 库可用性检查")
    if INSTRUCTOR_AVAILABLE:
        print("  ✓ instructor 库已安装")
        print(f"  - instructor 版本: {instructor.__version__ if hasattr(instructor, '__version__') else '未知'}")
    else:
        print("  ✗ instructor 库未安装")
        print("  提示：运行 'pip install instructor openai' 安装")

    # 2. 测试客户端初始化
    print("\n[测试2] 客户端初始化（不实际调用 API）")
    try:
        # 模拟初始化（使用假 API Key）
        if INSTRUCTOR_AVAILABLE:
            os.environ["VLM_API_KEY"] = "sk-test-fake-key-for-demo"
            os.environ["VLM_BASE_URL"] = "https://test.example.com/v1"

            client = InstructorClient()
            print("  ✓ 同步客户端初始化成功")
            print(f"  - 模型: {client.model}")
            print(f"  - 重试次数: {client.max_retries}")
            print(f"  - 超时: {client.timeout}s")

            async_client = AsyncInstructorClient()
            print("  ✓ 异步客户端初始化成功")
        else:
            print("  ⊘ 跳过（instructor 未安装）")
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")

    # 3. 测试辅助方法
    print("\n[测试3] 辅助方法测试")
    try:
        if INSTRUCTOR_AVAILABLE and 'client' in locals():
            # 测试图片编码
            test_image = b"fake-image-data-for-testing"
            encoded = client._encode_image(test_image)
            print(f"  ✓ 图片编码: {encoded[:20]}...")

            # 测试缓存键生成
            cache_key = client.get_cache_key(test_image, "Q0.2")
            print(f"  ✓ 缓存键生成: {cache_key}")
        else:
            print("  ⊘ 跳过（客户端未初始化）")
    except Exception as e:
        print(f"  ✗ 辅助方法测试失败: {e}")

    # 4. 提示如何进行实际测试
    print("\n[提示] 如何进行实际 API 测试:")
    print("  1. 设置真实的环境变量:")
    print("     export VLM_API_KEY='你的真实API密钥'")
    print("     export VLM_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'")
    print("")
    print("  2. 准备测试代码:")
    print("     ```python")
    print("     from pathlib import Path")
    print("     from backend.infrastructure.llm.prompts import Q02Response, Q0_2_GENUS_PROMPT")
    print("     from backend.infrastructure.llm.instructor_client import InstructorClient")
    print("")
    print("     # 初始化客户端")
    print("     client = InstructorClient()")
    print("")
    print("     # 读取测试图片")
    print("     image_bytes = Path('test_flower.jpg').read_bytes()")
    print("")
    print("     # 调用 VLM")
    print("     response = client.query(")
    print("         prompt=Q0_2_GENUS_PROMPT,")
    print("         image_bytes=image_bytes,")
    print("         response_model=Q02Response")
    print("     )")
    print("")
    print("     # 验证结果")
    print("     print(f'识别结果: {response.choice}')  # Rosa, Prunus, etc.")
    print("     print(f'置信度: {response.confidence}')  # 0.0-1.0")
    print("     ```")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
