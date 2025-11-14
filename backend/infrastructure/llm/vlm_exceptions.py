"""
VLM 客户端异常类

功能：
- 定义 VLM 客户端的自定义异常类
- 支持错误恢复和 Fallback 机制
- 提供详细的错误信息和上下文

异常层次结构：
- VLMException: 基础异常类
  - ProviderUnavailableException: Provider 不可用
  - AllProvidersFailedException: 所有 Provider 都失败
  - ValidationException: 响应验证失败
  - TimeoutException: 请求超时
  - QuotaExceededException: 配额超限

作者：AI Python Architect
日期：2025-11-12
"""

from typing import Optional, Dict, Any


class VLMException(Exception):
    """
    VLM 客户端基础异常类

    所有 VLM 相关异常的基类

    字段说明：
    - message: 错误消息
    - provider: 发生错误的 Provider 名称
    - details: 额外的错误详情（字典）

    使用示例：
    ```python
    raise VLMException(
        "Failed to call VLM",
        provider="qwen",
        details={"status_code": 500}
    )
    ```
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 VLM 异常

        Args:
            message: 错误消息
            provider: 发生错误的 Provider 名称
            details: 额外的错误详情
        """
        self.message = message
        self.provider = provider
        self.details = details or {}

        # 构造完整错误消息
        full_message = f"{message}"
        if provider:
            full_message += f" (Provider: {provider})"
        if details:
            full_message += f" - Details: {details}"

        super().__init__(full_message)


class ProviderUnavailableException(VLMException):
    """
    Provider 不可用异常

    当 Provider 无法初始化或暂时不可用时抛出

    使用示例：
    ```python
    raise ProviderUnavailableException(
        "Qwen API Key not found",
        provider="qwen"
    )
    ```
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 Provider 不可用异常

        Args:
            message: 错误消息
            provider: 不可用的 Provider 名称
            details: 额外的错误详情
        """
        super().__init__(f"Provider unavailable: {message}", provider, details)


class AllProvidersFailedException(VLMException):
    """
    所有 Provider 都失败异常

    当 Fallback 链中所有 Provider 都失败时抛出

    使用示例：
    ```python
    raise AllProvidersFailedException(
        "Tried Qwen, ChatGPT, Grok, Claude - all failed",
        details={"attempts": 4, "last_error": "Timeout"}
    )
    ```
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化所有 Provider 失败异常

        Args:
            message: 错误消息
            details: 额外的错误详情（如失败的 Provider 列表、最后一个错误等）
        """
        super().__init__(f"All providers failed: {message}", provider=None, details=details)


class ValidationException(VLMException):
    """
    响应验证失败异常

    当 VLM 返回的响应不符合 Pydantic Schema 时抛出

    使用示例：
    ```python
    raise ValidationException(
        "Response does not match Q02Response schema",
        provider="qwen",
        details={"expected": "Q02Response", "received": {...}}
    )
    ```
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化验证失败异常

        Args:
            message: 错误消息
            provider: 发生验证错误的 Provider 名称
            details: 额外的错误详情（如期望的 Schema、实际收到的数据等）
        """
        super().__init__(f"Validation failed: {message}", provider, details)


class TimeoutException(VLMException):
    """
    请求超时异常

    当 VLM 请求超过超时时间时抛出

    使用示例：
    ```python
    raise TimeoutException(
        "Request timed out after 30 seconds",
        provider="qwen",
        details={"timeout": 30}
    )
    ```
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化超时异常

        Args:
            message: 错误消息
            provider: 超时的 Provider 名称
            details: 额外的错误详情（如超时时间）
        """
        super().__init__(f"Timeout: {message}", provider, details)


class QuotaExceededException(VLMException):
    """
    配额超限异常

    当 Provider 的 API 配额用尽时抛出

    使用示例：
    ```python
    raise QuotaExceededException(
        "Daily quota exceeded",
        provider="qwen",
        details={"daily_limit": 1000, "current_usage": 1000}
    )
    ```
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化配额超限异常

        Args:
            message: 错误消息
            provider: 配额超限的 Provider 名称
            details: 额外的错误详情（如配额限制、当前使用量等）
        """
        super().__init__(f"Quota exceeded: {message}", provider, details)


# ==================== 导出所有异常类 ====================

__all__ = [
    "VLMException",
    "ProviderUnavailableException",
    "AllProvidersFailedException",
    "ValidationException",
    "TimeoutException",
    "QuotaExceededException",
]


if __name__ == "__main__":
    """
    VLM 异常类测试

    验证：
    1. 异常类的创建和继承关系
    2. 错误消息的格式化
    3. Provider 和 details 的传递
    """
    print("=" * 80)
    print("VLM 异常类测试")
    print("=" * 80)

    # 1. 测试基础异常
    print("\n[测试1] 基础 VLMException")
    try:
        raise VLMException(
            "Test error message",
            provider="qwen",
            details={"status_code": 500}
        )
    except VLMException as e:
        print(f"  ✓ 捕获异常: {type(e).__name__}")
        print(f"  - 消息: {e.message}")
        print(f"  - Provider: {e.provider}")
        print(f"  - Details: {e.details}")
        print(f"  - 完整字符串: {str(e)}")

    # 2. 测试 Provider 不可用异常
    print("\n[测试2] ProviderUnavailableException")
    try:
        raise ProviderUnavailableException(
            "API Key not found",
            provider="chatgpt"
        )
    except ProviderUnavailableException as e:
        print(f"  ✓ 捕获异常: {type(e).__name__}")
        print(f"  - 消息: {e.message}")
        print(f"  - Provider: {e.provider}")

    # 3. 测试所有 Provider 失败异常
    print("\n[测试3] AllProvidersFailedException")
    try:
        raise AllProvidersFailedException(
            "All 4 providers failed",
            details={
                "providers_tried": ["qwen", "chatgpt", "grok", "claude"],
                "last_error": "Connection refused"
            }
        )
    except AllProvidersFailedException as e:
        print(f"  ✓ 捕获异常: {type(e).__name__}")
        print(f"  - 消息: {e.message}")
        print(f"  - Details: {e.details}")

    # 4. 测试验证失败异常
    print("\n[测试4] ValidationException")
    try:
        raise ValidationException(
            "Response does not match schema",
            provider="qwen",
            details={
                "expected_schema": "Q02Response",
                "validation_errors": ["choice must be one of [Rosa, Prunus, ...]"]
            }
        )
    except ValidationException as e:
        print(f"  ✓ 捕获异常: {type(e).__name__}")
        print(f"  - 消息: {e.message}")
        print(f"  - Provider: {e.provider}")
        print(f"  - Details: {e.details}")

    # 5. 测试超时异常
    print("\n[测试5] TimeoutException")
    try:
        raise TimeoutException(
            "Request exceeded timeout limit",
            provider="qwen",
            details={"timeout_seconds": 30, "elapsed_seconds": 35}
        )
    except TimeoutException as e:
        print(f"  ✓ 捕获异常: {type(e).__name__}")
        print(f"  - 消息: {e.message}")
        print(f"  - Details: {e.details}")

    # 6. 测试配额超限异常
    print("\n[测试6] QuotaExceededException")
    try:
        raise QuotaExceededException(
            "Daily API quota exhausted",
            provider="qwen",
            details={"daily_limit": 1000, "usage": 1002}
        )
    except QuotaExceededException as e:
        print(f"  ✓ 捕获异常: {type(e).__name__}")
        print(f"  - 消息: {e.message}")
        print(f"  - Provider: {e.provider}")
        print(f"  - Details: {e.details}")

    # 7. 测试异常继承关系
    print("\n[测试7] 异常继承关系")
    try:
        raise ProviderUnavailableException("Test", provider="test")
    except VLMException as e:
        print(f"  ✓ ProviderUnavailableException 是 VLMException 的子类")
        print(f"  - isinstance(e, VLMException): {isinstance(e, VLMException)}")
        print(f"  - isinstance(e, ProviderUnavailableException): {isinstance(e, ProviderUnavailableException)}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
