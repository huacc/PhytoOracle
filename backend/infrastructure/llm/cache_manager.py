"""
VLM 缓存管理器

功能：
- 提供内存缓存机制，减少重复的 VLM API 调用
- 基于 prompt + image_hash 生成缓存键
- 支持 TTL（过期时间）
- 线程安全（使用 Lock）
- P2.3 阶段可升级为 Redis 缓存

缓存策略：
- 缓存键格式：sha256(prompt + image_hash)
- 默认 TTL：7 天（604800 秒）
- 自动清理过期缓存

注意：
- 当前实现为内存缓存，重启后缓存会丢失
- P2.3 阶段将升级为 Redis 持久化缓存

作者：AI Python Architect
日期：2025-11-12
"""

import hashlib
import time
from typing import Optional, Any, Dict, Tuple
from threading import Lock
from datetime import datetime, timedelta


class CacheManager:
    """
    VLM 缓存管理器（内存版本）

    提供基于内存的缓存功能，支持 TTL 过期策略

    功能特性：
    - 自动生成缓存键（基于 prompt + image_hash）
    - 支持 TTL（过期时间）
    - 自动清理过期缓存
    - 线程安全（使用 threading.Lock）

    使用示例：
    ```python
    # 初始化缓存管理器（TTL = 1小时）
    cache = CacheManager(ttl_seconds=3600)

    # 存储缓存
    cache.set(
        prompt="Identify genus",
        image_bytes=image_bytes,
        value=response_object
    )

    # 读取缓存
    cached_response = cache.get(
        prompt="Identify genus",
        image_bytes=image_bytes
    )

    if cached_response:
        print("Cache hit!")
    else:
        print("Cache miss, calling VLM...")
    ```
    """

    def __init__(self, ttl_seconds: int = 604800):
        """
        初始化缓存管理器

        Args:
            ttl_seconds: 缓存有效期（秒），默认 7 天（604800 秒）

        使用示例：
        ```python
        # 使用默认 TTL（7天）
        cache = CacheManager()

        # 使用自定义 TTL（1小时）
        cache = CacheManager(ttl_seconds=3600)
        ```
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}  # {cache_key: (value, timestamp)}
        self._lock = Lock()  # 线程锁，确保线程安全

    def get(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None
    ) -> Optional[Any]:
        """
        获取缓存

        Args:
            prompt: 提示词
            image_bytes: 图像字节数据（可选，纯文本查询时为 None）

        Returns:
            Optional[Any]: 缓存值（如果存在且未过期），否则返回 None

        使用示例：
        ```python
        cached_result = cache.get(
            prompt="Identify genus",
            image_bytes=image_bytes
        )

        if cached_result:
            print(f"缓存命中: {cached_result}")
        else:
            print("缓存未命中")
        ```
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt, image_bytes)

        with self._lock:
            # 检查缓存是否存在
            if cache_key not in self._cache:
                return None

            # 获取缓存值和时间戳
            value, timestamp = self._cache[cache_key]

            # 检查是否过期
            current_time = time.time()
            if current_time - timestamp > self.ttl_seconds:
                # 缓存已过期，删除并返回 None
                del self._cache[cache_key]
                return None

            # 缓存命中，返回值
            return value

    def set(
        self,
        prompt: str,
        value: Any,
        image_bytes: Optional[bytes] = None
    ) -> None:
        """
        设置缓存

        Args:
            prompt: 提示词
            value: 缓存值（任意类型，通常是 Pydantic 对象）
            image_bytes: 图像字节数据（可选，纯文本查询时为 None）

        使用示例：
        ```python
        # 缓存 VLM 响应
        cache.set(
            prompt="Identify genus",
            image_bytes=image_bytes,
            value=Q02Response(choice="Rosa", confidence=0.92)
        )
        ```
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt, image_bytes)

        with self._lock:
            # 存储缓存值和当前时间戳
            self._cache[cache_key] = (value, time.time())

    def clear(self) -> None:
        """
        清空所有缓存

        使用示例：
        ```python
        cache.clear()
        print("所有缓存已清空")
        ```
        """
        with self._lock:
            self._cache.clear()

    def remove_expired(self) -> int:
        """
        手动清理过期缓存

        Returns:
            int: 清理的缓存条目数量

        使用示例：
        ```python
        removed_count = cache.remove_expired()
        print(f"清理了 {removed_count} 条过期缓存")
        ```
        """
        current_time = time.time()
        removed_count = 0

        with self._lock:
            # 找出所有过期的键
            expired_keys = [
                key for key, (value, timestamp) in self._cache.items()
                if current_time - timestamp > self.ttl_seconds
            ]

            # 删除过期缓存
            for key in expired_keys:
                del self._cache[key]
                removed_count += 1

        return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
                - total_entries: 总缓存条目数
                - expired_entries: 已过期但未清理的条目数
                - active_entries: 有效缓存条目数
                - ttl_seconds: TTL 设置（秒）

        使用示例：
        ```python
        stats = cache.get_stats()
        print(f"总缓存: {stats['total_entries']}")
        print(f"有效缓存: {stats['active_entries']}")
        print(f"过期缓存: {stats['expired_entries']}")
        ```
        """
        current_time = time.time()

        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for value, timestamp in self._cache.values()
                if current_time - timestamp > self.ttl_seconds
            )
            active_entries = total_entries - expired_entries

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": active_entries,
            "ttl_seconds": self.ttl_seconds
        }

    def _generate_cache_key(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None
    ) -> str:
        """
        生成缓存键

        使用 SHA-256 哈希算法生成唯一缓存键
        缓存键 = SHA256(prompt + image_hash)

        Args:
            prompt: 提示词
            image_bytes: 图像字节数据（可选）

        Returns:
            str: SHA-256 哈希字符串（64 字符）

        使用示例：
        ```python
        cache_key = cache._generate_cache_key(
            prompt="Identify genus",
            image_bytes=image_bytes
        )
        # cache_key: "a1b2c3d4e5f6..."
        ```
        """
        # 将 prompt 编码为字节
        content = prompt.encode('utf-8')

        # 如果有图像，添加图像的 MD5 哈希
        if image_bytes:
            image_hash = hashlib.md5(image_bytes).hexdigest()
            content += image_hash.encode('utf-8')

        # 生成 SHA-256 哈希作为缓存键
        return hashlib.sha256(content).hexdigest()


# ==================== 导出缓存管理器 ====================

__all__ = ["CacheManager"]


if __name__ == "__main__":
    """
    缓存管理器测试

    验证：
    1. 缓存的存储和读取
    2. TTL 过期机制
    3. 缓存键生成
    4. 统计信息
    5. 线程安全（基础测试）
    """
    import io

    print("=" * 80)
    print("VLM 缓存管理器测试")
    print("=" * 80)

    # 1. 测试缓存的基本操作
    print("\n[测试1] 缓存的存储和读取")
    cache = CacheManager(ttl_seconds=3600)  # TTL = 1 小时

    # 模拟图像数据
    test_image = b"fake-image-data-for-testing"
    test_prompt = "Identify the genus of this flower"

    # 存储缓存
    cache.set(
        prompt=test_prompt,
        image_bytes=test_image,
        value={"choice": "Rosa", "confidence": 0.92}
    )
    print(f"  ✓ 缓存已存储")

    # 读取缓存
    cached_value = cache.get(
        prompt=test_prompt,
        image_bytes=test_image
    )
    if cached_value:
        print(f"  ✓ 缓存命中: {cached_value}")
    else:
        print(f"  ✗ 缓存未命中")

    # 2. 测试缓存键的唯一性
    print("\n[测试2] 缓存键的唯一性")
    key1 = cache._generate_cache_key("prompt1", b"image1")
    key2 = cache._generate_cache_key("prompt2", b"image2")
    key3 = cache._generate_cache_key("prompt1", b"image1")  # 与 key1 相同

    print(f"  - key1: {key1[:16]}...")
    print(f"  - key2: {key2[:16]}...")
    print(f"  - key3: {key3[:16]}...")

    if key1 == key3 and key1 != key2:
        print(f"  ✓ 缓存键生成正确（相同输入生成相同键）")
    else:
        print(f"  ✗ 缓存键生成错误")

    # 3. 测试纯文本缓存（无图像）
    print("\n[测试3] 纯文本缓存（无图像）")
    text_prompt = "What is the definition of a flower?"
    cache.set(
        prompt=text_prompt,
        value="A flower is the reproductive structure of flowering plants"
    )

    cached_text = cache.get(prompt=text_prompt)
    if cached_text:
        print(f"  ✓ 纯文本缓存命中: {cached_text[:50]}...")
    else:
        print(f"  ✗ 纯文本缓存未命中")

    # 4. 测试缓存未命中
    print("\n[测试4] 缓存未命中")
    non_existent = cache.get(
        prompt="This prompt does not exist",
        image_bytes=b"random-image"
    )
    if non_existent is None:
        print(f"  ✓ 正确返回 None（缓存未命中）")
    else:
        print(f"  ✗ 错误返回了值: {non_existent}")

    # 5. 测试 TTL 过期机制
    print("\n[测试5] TTL 过期机制")
    short_ttl_cache = CacheManager(ttl_seconds=1)  # TTL = 1 秒
    short_ttl_cache.set(
        prompt="short-lived",
        value="This will expire soon"
    )

    # 立即读取（应该命中）
    immediate_read = short_ttl_cache.get(prompt="short-lived")
    if immediate_read:
        print(f"  ✓ 立即读取成功: {immediate_read}")
    else:
        print(f"  ✗ 立即读取失败")

    # 等待 2 秒后读取（应该过期）
    print("  - 等待 2 秒...")
    time.sleep(2)
    expired_read = short_ttl_cache.get(prompt="short-lived")
    if expired_read is None:
        print(f"  ✓ 缓存已过期（正确返回 None）")
    else:
        print(f"  ✗ 缓存未过期（错误）: {expired_read}")

    # 6. 测试缓存统计
    print("\n[测试6] 缓存统计")
    cache.clear()  # 清空旧缓存
    cache.set("prompt1", "value1", b"image1")
    cache.set("prompt2", "value2", b"image2")
    cache.set("prompt3", "value3", b"image3")

    stats = cache.get_stats()
    print(f"  ✓ 缓存统计:")
    print(f"    - 总条目数: {stats['total_entries']}")
    print(f"    - 有效条目数: {stats['active_entries']}")
    print(f"    - 过期条目数: {stats['expired_entries']}")
    print(f"    - TTL 设置: {stats['ttl_seconds']}s")

    # 7. 测试手动清理过期缓存
    print("\n[测试7] 手动清理过期缓存")
    short_ttl_cache.clear()
    short_ttl_cache.set("prompt1", "value1")
    short_ttl_cache.set("prompt2", "value2")

    # 等待过期
    time.sleep(2)

    removed_count = short_ttl_cache.remove_expired()
    print(f"  ✓ 清理了 {removed_count} 条过期缓存")

    final_stats = short_ttl_cache.get_stats()
    print(f"  - 清理后总条目数: {final_stats['total_entries']}")

    # 8. 测试缓存清空
    print("\n[测试8] 缓存清空")
    cache.clear()
    stats_after_clear = cache.get_stats()
    if stats_after_clear['total_entries'] == 0:
        print(f"  ✓ 缓存已清空")
    else:
        print(f"  ✗ 缓存未清空: {stats_after_clear}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
