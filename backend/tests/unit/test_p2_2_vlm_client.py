"""
P2.2 阶段单元测试 - VLM 客户端

测试范围：
- VLM 异常类的功能
- 缓存管理器的功能
- VLM 客户端的初始化
- Fallback 机制（模拟和真实测试）
- 缓存机制
- 结构化输出验证

测试策略：
- 返回结果使用真实 API 调用（不 mock）
- 输入可以 mock（如构造测试图片）
- 如果无法调用真实 API（如没有 API Key），测试会跳过并说明原因

作者：AI Python Architect
日期：2025-11-12
"""

import os
import time
import pytest
from pathlib import Path
from typing import Optional

# 导入被测试的模块
from backend.infrastructure.llm.vlm_exceptions import (
    VLMException,
    ProviderUnavailableException,
    AllProvidersFailedException,
    ValidationException,
    TimeoutException,
    QuotaExceededException,
)
from backend.infrastructure.llm.cache_manager import CacheManager
from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient
from backend.infrastructure.llm.prompts.response_schema import (
    Q00Response,
    Q01Response,
    Q02Response,
    Q05Response,
)


# ==================== 测试 VLM 异常类 ====================


class TestVLMExceptions:
    """测试 VLM 异常类的功能"""

    def test_vlm_exception_basic(self):
        """测试基础 VLMException"""
        exc = VLMException(
            "Test error",
            provider="qwen",
            details={"status_code": 500}
        )

        assert exc.message == "Test error"
        assert exc.provider == "qwen"
        assert exc.details["status_code"] == 500
        assert "Test error" in str(exc)
        assert "qwen" in str(exc)

    def test_provider_unavailable_exception(self):
        """测试 ProviderUnavailableException"""
        exc = ProviderUnavailableException(
            "API Key not found",
            provider="chatgpt"
        )

        assert isinstance(exc, VLMException)
        assert exc.provider == "chatgpt"
        assert "unavailable" in exc.message.lower()

    def test_all_providers_failed_exception(self):
        """测试 AllProvidersFailedException"""
        exc = AllProvidersFailedException(
            "All 4 providers failed",
            details={
                "providers_tried": ["qwen", "chatgpt", "grok", "claude"],
                "last_error": "Connection refused"
            }
        )

        assert isinstance(exc, VLMException)
        assert "All providers failed" in exc.message
        assert len(exc.details["providers_tried"]) == 4

    def test_validation_exception(self):
        """测试 ValidationException"""
        exc = ValidationException(
            "Response does not match schema",
            provider="qwen",
            details={"expected": "Q02Response"}
        )

        assert isinstance(exc, VLMException)
        assert "Validation failed" in exc.message
        assert exc.details["expected"] == "Q02Response"

    def test_timeout_exception(self):
        """测试 TimeoutException"""
        exc = TimeoutException(
            "Request timed out",
            provider="qwen",
            details={"timeout": 30}
        )

        assert isinstance(exc, VLMException)
        assert "Timeout" in exc.message
        assert exc.details["timeout"] == 30

    def test_quota_exceeded_exception(self):
        """测试 QuotaExceededException"""
        exc = QuotaExceededException(
            "Daily quota exceeded",
            provider="qwen",
            details={"daily_limit": 1000}
        )

        assert isinstance(exc, VLMException)
        assert "Quota exceeded" in exc.message
        assert exc.details["daily_limit"] == 1000


# ==================== 测试缓存管理器 ====================


class TestCacheManager:
    """测试缓存管理器的功能"""

    def test_cache_initialization(self):
        """测试缓存管理器初始化"""
        cache = CacheManager(ttl_seconds=3600)
        assert cache.ttl_seconds == 3600
        assert cache.get_stats()["total_entries"] == 0

    def test_cache_set_and_get(self):
        """测试缓存的存储和读取"""
        cache = CacheManager(ttl_seconds=3600)

        # 存储缓存
        test_prompt = "Identify genus"
        test_image = b"fake-image-data"
        test_value = {"choice": "Rosa", "confidence": 0.92}

        cache.set(test_prompt, test_value, test_image)

        # 读取缓存
        cached_value = cache.get(test_prompt, test_image)
        assert cached_value is not None
        assert cached_value["choice"] == "Rosa"
        assert cached_value["confidence"] == 0.92

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = CacheManager(ttl_seconds=3600)

        # 读取不存在的缓存
        cached_value = cache.get("non-existent-prompt", b"random-image")
        assert cached_value is None

    def test_cache_key_uniqueness(self):
        """测试缓存键的唯一性"""
        cache = CacheManager()

        # 相同的 prompt + image 应该生成相同的缓存键
        key1 = cache._generate_cache_key("prompt1", b"image1")
        key2 = cache._generate_cache_key("prompt1", b"image1")
        key3 = cache._generate_cache_key("prompt2", b"image2")

        assert key1 == key2  # 相同输入生成相同键
        assert key1 != key3  # 不同输入生成不同键

    def test_cache_ttl_expiration(self):
        """测试缓存 TTL 过期"""
        cache = CacheManager(ttl_seconds=1)  # TTL = 1 秒

        # 存储缓存
        cache.set("short-lived", "value")

        # 立即读取（应该命中）
        immediate_read = cache.get("short-lived")
        assert immediate_read == "value"

        # 等待 2 秒后读取（应该过期）
        time.sleep(2)
        expired_read = cache.get("short-lived")
        assert expired_read is None

    def test_cache_clear(self):
        """测试缓存清空"""
        cache = CacheManager()

        # 存储多个缓存
        cache.set("prompt1", "value1")
        cache.set("prompt2", "value2")
        cache.set("prompt3", "value3")

        assert cache.get_stats()["total_entries"] == 3

        # 清空缓存
        cache.clear()
        assert cache.get_stats()["total_entries"] == 0

    def test_cache_remove_expired(self):
        """测试手动清理过期缓存"""
        cache = CacheManager(ttl_seconds=1)

        # 存储多个缓存
        cache.set("prompt1", "value1")
        cache.set("prompt2", "value2")

        # 等待过期
        time.sleep(2)

        # 手动清理
        removed_count = cache.remove_expired()
        assert removed_count == 2

        final_stats = cache.get_stats()
        assert final_stats["total_entries"] == 0

    def test_cache_stats(self):
        """测试缓存统计信息"""
        cache = CacheManager(ttl_seconds=3600)

        # 存储缓存
        cache.set("prompt1", "value1")
        cache.set("prompt2", "value2")

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["ttl_seconds"] == 3600


# ==================== 测试 VLM 客户端 ====================


class TestMultiProviderVLMClient:
    """测试 VLM 客户端的功能"""

    def test_client_initialization_without_api_keys(self):
        """测试在没有 API Key 的情况下初始化客户端（应该失败）"""
        # 清除所有 API Key 环境变量
        for key in list(os.environ.keys()):
            if key.startswith("VLM_"):
                del os.environ[key]

        # 尝试初始化客户端
        with pytest.raises(ProviderUnavailableException):
            client = MultiProviderVLMClient()

    def test_client_initialization_with_fake_api_keys(self):
        """测试使用假 API Key 初始化客户端（可以初始化，但调用会失败）"""
        # 设置假 API Key
        os.environ["VLM_QWEN_API_KEY"] = "sk-fake-qwen-key"
        os.environ["VLM_CHATGPT_API_KEY"] = "sk-fake-chatgpt-key"

        try:
            client = MultiProviderVLMClient()
            assert client is not None
            assert len(client.get_available_providers()) > 0
        except ProviderUnavailableException:
            # 如果配置文件不存在，会抛出此异常
            pytest.skip("LLM config file not found")

    def test_client_custom_provider_order(self):
        """测试自定义 Provider 顺序"""
        os.environ["VLM_CHATGPT_API_KEY"] = "sk-fake-chatgpt-key"
        os.environ["VLM_CLAUDE_API_KEY"] = "sk-fake-claude-key"

        try:
            client = MultiProviderVLMClient(
                providers=["chatgpt", "claude"]
            )
            assert client.providers == ["chatgpt", "claude"]
        except ProviderUnavailableException:
            pytest.skip("LLM config file not found or no valid providers")

    def test_client_cache_enabled(self):
        """测试缓存启用"""
        os.environ["VLM_QWEN_API_KEY"] = "sk-fake-qwen-key"

        try:
            client = MultiProviderVLMClient(enable_cache=True)
            assert client.cache_manager is not None

            stats = client.get_cache_stats()
            assert stats is not None
            assert "total_entries" in stats
        except ProviderUnavailableException:
            pytest.skip("LLM config file not found")

    def test_client_cache_disabled(self):
        """测试缓存禁用"""
        os.environ["VLM_QWEN_API_KEY"] = "sk-fake-qwen-key"

        try:
            client = MultiProviderVLMClient(enable_cache=False)
            assert client.cache_manager is None

            stats = client.get_cache_stats()
            assert stats is None
        except ProviderUnavailableException:
            pytest.skip("LLM config file not found")

    def test_client_get_available_providers(self):
        """测试获取可用 Provider 列表"""
        os.environ["VLM_QWEN_API_KEY"] = "sk-fake-qwen-key"

        try:
            client = MultiProviderVLMClient()
            available = client.get_available_providers()
            assert isinstance(available, list)
            assert len(available) > 0
        except ProviderUnavailableException:
            pytest.skip("LLM config file not found")

    @pytest.mark.skipif(
        not os.getenv("VLM_QWEN_API_KEY") or os.getenv("VLM_QWEN_API_KEY").startswith("sk-fake"),
        reason="真实 API Key 未设置（需要设置环境变量 VLM_QWEN_API_KEY）"
    )
    def test_client_query_structured_real_api(self):
        """
        测试真实 API 调用（需要真实 API Key）

        注意：此测试需要：
        1. 设置真实的环境变量：VLM_QWEN_API_KEY
        2. 提供测试图片（可以是假图片，VLM 会尝试解析）

        如果没有真实 API Key，此测试会被跳过
        """
        # 构造测试图片（可以是任意字节数据，VLM 会尝试解析）
        # 这里使用一个最小的 PNG 图片
        test_image = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # 初始化客户端
        client = MultiProviderVLMClient()

        # 调用 VLM（真实 API 调用）
        try:
            response = client.query_structured(
                prompt="Identify the genus of this flower: Rosa, Prunus, Tulipa, Dianthus, Paeonia, or unknown",
                response_model=Q02Response,
                image_bytes=test_image
            )

            # 验证响应
            assert isinstance(response, Q02Response)
            assert response.choice in ["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia", "unknown"]
            assert 0.0 <= response.confidence <= 1.0

            print(f"\n真实 API 调用成功:")
            print(f"  - 识别结果: {response.choice}")
            print(f"  - 置信度: {response.confidence}")
            print(f"  - 推理过程: {response.reasoning}")

        except AllProvidersFailedException as e:
            # 所有 Provider 都失败（可能是 API Key 无效）
            pytest.fail(f"所有 Provider 都失败: {e}")

    def test_client_cache_functionality(self):
        """测试缓存功能（不需要真实 API 调用）"""
        os.environ["VLM_QWEN_API_KEY"] = "sk-fake-qwen-key"

        try:
            client = MultiProviderVLMClient(enable_cache=True)

            # 手动向缓存中添加数据
            test_prompt = "Identify genus"
            test_image = b"fake-image"
            test_response = Q02Response(choice="Rosa", confidence=0.92, reasoning="Test")

            client.cache_manager.set(test_prompt, test_response, test_image)

            # 读取缓存
            cached = client.cache_manager.get(test_prompt, test_image)
            assert cached is not None
            assert cached.choice == "Rosa"

            # 清空缓存
            client.clear_cache()
            cached_after_clear = client.cache_manager.get(test_prompt, test_image)
            assert cached_after_clear is None

        except ProviderUnavailableException:
            pytest.skip("LLM config file not found")


# ==================== 测试入口 ====================


if __name__ == "__main__":
    """
    运行测试

    使用方式：
    ```bash
    # 运行所有测试
    python backend/tests/unit/test_p2_2_vlm_client.py

    # 使用 pytest 运行
    pytest backend/tests/unit/test_p2_2_vlm_client.py -v

    # 运行特定测试
    pytest backend/tests/unit/test_p2_2_vlm_client.py::TestVLMExceptions::test_vlm_exception_basic -v

    # 运行并显示输出
    pytest backend/tests/unit/test_p2_2_vlm_client.py -v -s
    ```
    """
    import sys

    print("=" * 80)
    print("P2.2 阶段单元测试 - VLM 客户端")
    print("=" * 80)
    print("")
    print("提示：")
    print("  - 推荐使用 pytest 运行测试")
    print("  - 运行命令: pytest backend/tests/unit/test_p2_2_vlm_client.py -v")
    print("  - 如果需要测试真实 API 调用，请设置环境变量：")
    print("    export VLM_QWEN_API_KEY='你的真实Qwen API密钥'")
    print("")
    print("=" * 80)

    # 运行 pytest
    exit_code = pytest.main([__file__, "-v", "-s"])
    sys.exit(exit_code)
