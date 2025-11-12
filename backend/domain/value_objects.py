"""
值对象（Value Objects）

功能：
- 定义不可变的值对象
- 使用dataclass实现，确保不可变性（frozen=True）
- 提供业务逻辑封装和验证

值对象清单：
- ImageHash: 图片哈希值对象
- DiagnosisId: 诊断ID值对象
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class ImageHash:
    """
    图片哈希值对象

    功能：
    - 存储图片的MD5和SHA256哈希值
    - 用于图片去重和完整性校验
    - 不可变对象（frozen=True）

    属性：
    - md5: MD5哈希值（32字符十六进制）
    - sha256: SHA256哈希值（64字符十六进制，可选）

    使用示例：
    ```python
    # 从字节流创建哈希对象
    image_bytes = open("image.jpg", "rb").read()
    image_hash = ImageHash.from_bytes(image_bytes)
    print(image_hash.md5)    # 输出: a1b2c3d4...
    print(image_hash.sha256) # 输出: e5f6g7h8...

    # 直接创建哈希对象
    image_hash = ImageHash(md5="a1b2c3d4...", sha256="e5f6g7h8...")
    ```
    """
    md5: str
    sha256: Optional[str] = None

    @classmethod
    def from_bytes(cls, image_bytes: bytes) -> "ImageHash":
        """
        从图片字节流创建哈希对象

        Args:
            image_bytes: 图片字节流

        Returns:
            ImageHash: 哈希值对象

        示例：
        ```python
        with open("image.jpg", "rb") as f:
            image_bytes = f.read()
        image_hash = ImageHash.from_bytes(image_bytes)
        ```
        """
        import hashlib
        return cls(
            md5=hashlib.md5(image_bytes).hexdigest(),
            sha256=hashlib.sha256(image_bytes).hexdigest()
        )


@dataclass(frozen=True)
class DiagnosisId:
    """
    诊断ID值对象

    功能：
    - 存储诊断的唯一标识符
    - 验证ID格式（diag_YYYYMMDD_NNN）
    - 不可变对象（frozen=True）

    属性：
    - value: 诊断ID字符串

    ID格式：
    - 前缀: diag_
    - 日期: YYYYMMDD（8位数字）
    - 序号: NNN（3位数字，001-999）
    - 示例: diag_20251112_001

    使用示例：
    ```python
    # 自动生成诊断ID
    diagnosis_id = DiagnosisId.generate()
    print(diagnosis_id.value)  # 输出: diag_20251112_042

    # 从现有字符串创建诊断ID
    diagnosis_id = DiagnosisId(value="diag_20251112_001")

    # 格式错误会抛出异常
    try:
        invalid_id = DiagnosisId(value="invalid_id")
    except ValueError as e:
        print(e)  # 输出: Invalid diagnosis ID format: invalid_id
    ```
    """
    value: str

    def __post_init__(self):
        """
        初始化后验证ID格式

        Raises:
            ValueError: 如果ID格式不符合 diag_YYYYMMDD_NNN 格式

        正则表达式说明：
        - ^: 字符串开头
        - diag_: 固定前缀
        - \\d{8}: 8位数字（日期）
        - _: 下划线分隔符
        - \\d{3}: 3位数字（序号）
        - $: 字符串结尾
        """
        if not re.match(r"^diag_\d{8}_\d{3}$", self.value):
            raise ValueError(f"Invalid diagnosis ID format: {self.value}")

    @classmethod
    def generate(cls) -> "DiagnosisId":
        """
        自动生成诊断ID

        生成规则：
        - 前缀: diag_
        - 日期: 当前日期（YYYYMMDD）
        - 序号: 随机数（001-999）

        Returns:
            DiagnosisId: 新生成的诊断ID对象

        注意：
        - 这里使用随机序号，实际生产环境建议使用数据库自增序号
        - 随机序号存在冲突风险（概率约1/1000）

        示例：
        ```python
        diagnosis_id = DiagnosisId.generate()
        print(diagnosis_id.value)  # 输出: diag_20251112_042
        ```
        """
        from datetime import datetime
        import random

        date_str = datetime.now().strftime("%Y%m%d")
        seq = random.randint(1, 999)
        return cls(f"diag_{date_str}_{seq:03d}")


def main():
    """
    值对象使用示例

    演示如何：
    1. 从文件创建ImageHash对象
    2. 直接创建ImageHash对象
    3. 自动生成DiagnosisId
    4. 从字符串创建DiagnosisId
    5. 验证DiagnosisId格式
    6. 验证不可变性
    """
    print("=" * 80)
    print("值对象（Value Objects）使用示例")
    print("=" * 80)

    # 1. 从字节流创建ImageHash对象
    print("\n[示例1] 从字节流创建ImageHash对象")
    # 创建示例图片字节流
    sample_image_bytes = b"This is a sample image content for testing"

    image_hash = ImageHash.from_bytes(sample_image_bytes)
    print(f"  [OK] 成功创建ImageHash对象")
    print(f"  - MD5: {image_hash.md5}")
    print(f"  - SHA256: {image_hash.sha256[:16]}...（已截断）")

    # 2. 直接创建ImageHash对象
    print("\n[示例2] 直接创建ImageHash对象")
    image_hash2 = ImageHash(
        md5="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        sha256="e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3h4i5j6"
    )
    print(f"  [OK] 成功创建ImageHash对象")
    print(f"  - MD5: {image_hash2.md5}")
    print(f"  - SHA256: {image_hash2.sha256[:16]}...（已截断）")

    # 3. 仅使用MD5创建ImageHash对象
    print("\n[示例3] 仅使用MD5创建ImageHash对象")
    image_hash3 = ImageHash(md5="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6")
    print(f"  [OK] 成功创建ImageHash对象（仅MD5）")
    print(f"  - MD5: {image_hash3.md5}")
    print(f"  - SHA256: {image_hash3.sha256}")  # None

    # 4. 自动生成DiagnosisId
    print("\n[示例4] 自动生成DiagnosisId")
    diagnosis_id1 = DiagnosisId.generate()
    diagnosis_id2 = DiagnosisId.generate()
    diagnosis_id3 = DiagnosisId.generate()

    print(f"  [OK] 成功生成3个DiagnosisId")
    print(f"  - ID 1: {diagnosis_id1.value}")
    print(f"  - ID 2: {diagnosis_id2.value}")
    print(f"  - ID 3: {diagnosis_id3.value}")

    # 5. 从字符串创建DiagnosisId（合法格式）
    print("\n[示例5] 从字符串创建DiagnosisId（合法格式）")
    diagnosis_id4 = DiagnosisId(value="diag_20251112_001")
    print(f"  [OK] 成功创建DiagnosisId: {diagnosis_id4.value}")

    # 6. 从字符串创建DiagnosisId（非法格式）
    print("\n[示例6] 从字符串创建DiagnosisId（非法格式）")
    invalid_ids = [
        "invalid_id",
        "diag_2025111_001",    # 日期位数不足
        "diag_20251112_01",    # 序号位数不足
        "diag_20251112_1000",  # 序号位数过多
        "DIAG_20251112_001",   # 大写前缀
    ]

    for invalid_id in invalid_ids:
        try:
            DiagnosisId(value=invalid_id)
            print(f"  [FAIL] {invalid_id}: 应该失败但没有抛出异常")
        except ValueError as e:
            print(f"  [OK] {invalid_id}: 格式验证失败（符合预期）")

    # 7. 验证不可变性（frozen=True）
    print("\n[示例7] 验证不可变性（frozen=True）")

    # 7.1 尝试修改ImageHash
    print("  测试 ImageHash 不可变性:")
    try:
        image_hash.md5 = "new_md5_value"  # 尝试修改
        print("    [FAIL] ImageHash可被修改（不符合预期）")
    except Exception as e:
        print(f"    [OK] ImageHash不可修改: {type(e).__name__}")

    # 7.2 尝试修改DiagnosisId
    print("  测试 DiagnosisId 不可变性:")
    try:
        diagnosis_id1.value = "diag_20251113_999"  # 尝试修改
        print("    [FAIL] DiagnosisId可被修改（不符合预期）")
    except Exception as e:
        print(f"    [OK] DiagnosisId不可修改: {type(e).__name__}")

    # 8. 实际使用场景：图片去重
    print("\n[示例8] 实际使用场景：图片去重")
    # 模拟两个相同的图片
    image1_bytes = b"Exact same image content"
    image2_bytes = b"Exact same image content"
    image3_bytes = b"Different image content"

    hash1 = ImageHash.from_bytes(image1_bytes)
    hash2 = ImageHash.from_bytes(image2_bytes)
    hash3 = ImageHash.from_bytes(image3_bytes)

    print(f"  图片1和图片2是否相同: {hash1.md5 == hash2.md5}")
    print(f"  图片1和图片3是否相同: {hash1.md5 == hash3.md5}")

    # 9. 实际使用场景：诊断ID生成与验证
    print("\n[示例9] 实际使用场景：诊断ID生成与验证")

    # 模拟诊断系统生成ID
    new_diagnosis_id = DiagnosisId.generate()
    print(f"  新诊断生成ID: {new_diagnosis_id.value}")

    # 模拟从数据库读取ID并验证
    db_id_value = "diag_20251110_042"  # 从数据库读取的ID字符串
    try:
        db_diagnosis_id = DiagnosisId(value=db_id_value)
        print(f"  数据库ID验证通过: {db_diagnosis_id.value}")
    except ValueError:
        print(f"  数据库ID格式错误: {db_id_value}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
