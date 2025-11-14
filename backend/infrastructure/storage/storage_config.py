"""
存储配置管理（Storage Configuration）

功能：
- 定义存储配置模型
- 支持从JSON文件加载配置
- 支持保存配置到JSON文件
- 提供配置验证和默认值

配置项：
- base_path: 存储根目录
- max_file_size: 最大文件大小（字节）
- allowed_extensions: 允许的文件扩展名
- create_thumbnails: 是否创建缩略图
- thumbnail_size: 缩略图尺寸
"""

from pathlib import Path
from typing import List, Tuple, Optional
import json
from pydantic import BaseModel, Field, field_validator


class StorageConfig(BaseModel):
    """
    存储配置模型

    使用Pydantic V2进行数据验证

    属性：
        base_path: 存储根目录（相对于项目根目录）
        max_file_size: 最大文件大小（字节），默认10MB
        allowed_extensions: 允许的文件扩展名列表
        create_thumbnails: 是否创建缩略图（可选功能）
        thumbnail_size: 缩略图尺寸（宽, 高）

    使用示例：
    ```python
    # 从配置文件加载
    config = StorageConfig.load()

    # 创建默认配置
    config = StorageConfig()

    # 自定义配置
    config = StorageConfig(
        base_path="storage/images",
        max_file_size=5 * 1024 * 1024,  # 5MB
        allowed_extensions=[".jpg", ".png"]
    )
    ```
    """

    # 存储根目录（相对于项目根目录）
    base_path: str = Field(
        default="storage/images",
        description="存储根目录，相对于项目根目录"
    )

    # 最大文件大小（字节）
    max_file_size: int = Field(
        default=10 * 1024 * 1024,
        description="最大文件大小（字节），默认10MB"
    )

    # 允许的文件扩展名
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png"],
        description="允许的文件扩展名列表"
    )

    # 是否创建缩略图
    create_thumbnails: bool = Field(
        default=False,
        description="是否创建缩略图（可选功能）"
    )

    # 缩略图尺寸
    thumbnail_size: Tuple[int, int] = Field(
        default=(200, 200),
        description="缩略图尺寸（宽, 高）"
    )

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, v: str) -> str:
        """
        验证base_path格式

        Args:
            v: base_path值

        Returns:
            str: 验证后的base_path

        Raises:
            ValueError: 如果base_path格式不正确
        """
        if not v:
            raise ValueError("base_path不能为空")

        # 禁止使用绝对路径
        if Path(v).is_absolute():
            raise ValueError("base_path必须是相对路径，不能使用绝对路径")

        return v

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """
        验证max_file_size格式

        Args:
            v: max_file_size值

        Returns:
            int: 验证后的max_file_size

        Raises:
            ValueError: 如果max_file_size格式不正确
        """
        if v <= 0:
            raise ValueError("max_file_size必须大于0")

        # 警告：如果文件大小超过50MB
        if v > 50 * 1024 * 1024:
            print(f"警告: max_file_size={v / (1024 * 1024):.2f}MB 过大，可能影响性能")

        return v

    @field_validator("allowed_extensions")
    @classmethod
    def validate_allowed_extensions(cls, v: List[str]) -> List[str]:
        """
        验证allowed_extensions格式

        Args:
            v: allowed_extensions值

        Returns:
            List[str]: 验证后的allowed_extensions

        Raises:
            ValueError: 如果allowed_extensions格式不正确
        """
        if not v:
            raise ValueError("allowed_extensions不能为空")

        # 确保所有扩展名以点开头
        normalized = []
        for ext in v:
            if not ext.startswith("."):
                ext = f".{ext}"
            normalized.append(ext.lower())

        return normalized

    @field_validator("thumbnail_size")
    @classmethod
    def validate_thumbnail_size(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """
        验证thumbnail_size格式

        Args:
            v: thumbnail_size值

        Returns:
            Tuple[int, int]: 验证后的thumbnail_size

        Raises:
            ValueError: 如果thumbnail_size格式不正确
        """
        width, height = v
        if width <= 0 or height <= 0:
            raise ValueError("thumbnail_size的宽度和高度必须大于0")

        if width > 1000 or height > 1000:
            raise ValueError("thumbnail_size的宽度和高度不能超过1000")

        return v

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "StorageConfig":
        """
        从配置文件加载配置

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径

        Returns:
            StorageConfig: 配置对象

        Raises:
            FileNotFoundError: 配置文件不存在时返回默认配置（不抛出异常）

        使用示例：
        ```python
        # 从默认路径加载
        config = StorageConfig.load()

        # 从指定路径加载
        config = StorageConfig.load(Path("/path/to/config.json"))
        ```
        """
        if config_path is None:
            # 使用相对路径定位项目根目录
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            config_path = project_root / "backend" / "config" / "storage_config.json"

        # 如果配置文件不存在，返回默认配置
        if not config_path.exists():
            print(f"警告: 配置文件不存在 {config_path}，使用默认配置")
            return cls()

        # 加载配置文件
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            print(f"警告: 配置文件加载失败 {e}，使用默认配置")
            return cls()

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径

        Raises:
            IOError: 配置文件保存失败

        使用示例：
        ```python
        # 保存到默认路径
        config.save()

        # 保存到指定路径
        config.save(Path("/path/to/config.json"))
        ```
        """
        if config_path is None:
            # 使用相对路径定位项目根目录
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            config_path = project_root / "backend" / "config" / "storage_config.json"

        # 确保配置目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存配置文件
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"配置已保存到: {config_path}")
        except Exception as e:
            raise IOError(f"配置文件保存失败: {e}")

    def get_absolute_base_path(self) -> Path:
        """
        获取存储根目录的绝对路径

        Returns:
            Path: 存储根目录的绝对路径

        使用示例：
        ```python
        config = StorageConfig.load()
        abs_path = config.get_absolute_base_path()
        print(abs_path)  # 输出: D:/项目管理/PhytoOracle/storage/images
        ```
        """
        # 使用相对路径定位项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        return project_root / self.base_path

    def is_extension_allowed(self, extension: str) -> bool:
        """
        检查文件扩展名是否被允许

        Args:
            extension: 文件扩展名（例如：".jpg"、"jpg"）

        Returns:
            bool: 如果扩展名被允许则返回True，否则返回False

        使用示例：
        ```python
        config = StorageConfig.load()
        print(config.is_extension_allowed(".jpg"))   # True
        print(config.is_extension_allowed("jpg"))    # True
        print(config.is_extension_allowed(".bmp"))   # False
        ```
        """
        # 标准化扩展名格式
        if not extension.startswith("."):
            extension = f".{extension}"
        extension = extension.lower()

        return extension in self.allowed_extensions


def main():
    """
    存储配置使用示例

    演示如何：
    1. 创建默认配置
    2. 创建自定义配置
    3. 从文件加载配置
    4. 保存配置到文件
    5. 验证配置参数
    6. 使用配置进行文件操作
    """
    print("=" * 80)
    print("存储配置（Storage Configuration）使用示例")
    print("=" * 80)

    # 示例1：创建默认配置
    print("\n[示例1] 创建默认配置")
    config = StorageConfig()
    print(f"  [OK] 默认配置创建成功")
    print(f"  - base_path: {config.base_path}")
    print(f"  - max_file_size: {config.max_file_size / (1024 * 1024):.2f} MB")
    print(f"  - allowed_extensions: {config.allowed_extensions}")
    print(f"  - create_thumbnails: {config.create_thumbnails}")
    print(f"  - thumbnail_size: {config.thumbnail_size}")

    # 示例2：创建自定义配置
    print("\n[示例2] 创建自定义配置")
    custom_config = StorageConfig(
        base_path="storage/images",
        max_file_size=5 * 1024 * 1024,  # 5MB
        allowed_extensions=[".jpg", ".png"],
        create_thumbnails=True,
        thumbnail_size=(300, 300)
    )
    print(f"  [OK] 自定义配置创建成功")
    print(f"  - base_path: {custom_config.base_path}")
    print(f"  - max_file_size: {custom_config.max_file_size / (1024 * 1024):.2f} MB")
    print(f"  - allowed_extensions: {custom_config.allowed_extensions}")
    print(f"  - create_thumbnails: {custom_config.create_thumbnails}")
    print(f"  - thumbnail_size: {custom_config.thumbnail_size}")

    # 示例3：保存配置到文件
    print("\n[示例3] 保存配置到文件")
    try:
        custom_config.save()
        print(f"  [OK] 配置已保存")
    except Exception as e:
        print(f"  [失败] {e}")

    # 示例4：从文件加载配置
    print("\n[示例4] 从文件加载配置")
    loaded_config = StorageConfig.load()
    print(f"  [OK] 配置加载成功")
    print(f"  - base_path: {loaded_config.base_path}")
    print(f"  - max_file_size: {loaded_config.max_file_size / (1024 * 1024):.2f} MB")

    # 示例5：获取绝对路径
    print("\n[示例5] 获取绝对路径")
    abs_path = loaded_config.get_absolute_base_path()
    print(f"  [OK] 绝对路径: {abs_path}")

    # 示例6：验证文件扩展名
    print("\n[示例6] 验证文件扩展名")
    test_extensions = [".jpg", "jpg", ".png", ".bmp", ".gif"]
    for ext in test_extensions:
        is_allowed = loaded_config.is_extension_allowed(ext)
        status = "✓" if is_allowed else "✗"
        print(f"  {status} {ext}: {'允许' if is_allowed else '不允许'}")

    # 示例7：验证配置参数（非法情况）
    print("\n[示例7] 验证配置参数（非法情况）")

    # 7.1 base_path为空
    print("  测试1: base_path为空")
    try:
        invalid_config = StorageConfig(base_path="")
        print("    [失败] 应该抛出ValueError但没有")
    except ValueError as e:
        print(f"    [OK] 验证失败（符合预期）: {e}")

    # 7.2 base_path为绝对路径
    print("  测试2: base_path为绝对路径")
    try:
        invalid_config = StorageConfig(base_path="D:/absolute/path")
        print("    [失败] 应该抛出ValueError但没有")
    except ValueError as e:
        print(f"    [OK] 验证失败（符合预期）: {e}")

    # 7.3 max_file_size为负数
    print("  测试3: max_file_size为负数")
    try:
        invalid_config = StorageConfig(max_file_size=-1)
        print("    [失败] 应该抛出ValueError但没有")
    except ValueError as e:
        print(f"    [OK] 验证失败（符合预期）: {e}")

    # 7.4 allowed_extensions为空列表
    print("  测试4: allowed_extensions为空列表")
    try:
        invalid_config = StorageConfig(allowed_extensions=[])
        print("    [失败] 应该抛出ValueError但没有")
    except ValueError as e:
        print(f"    [OK] 验证失败（符合预期）: {e}")

    # 7.5 thumbnail_size为负数
    print("  测试5: thumbnail_size为负数")
    try:
        invalid_config = StorageConfig(thumbnail_size=(-100, 200))
        print("    [失败] 应该抛出ValueError但没有")
    except ValueError as e:
        print(f"    [OK] 验证失败（符合预期）: {e}")

    # 示例8：实际场景 - 检查文件是否符合配置要求
    print("\n[示例8] 实际场景 - 检查文件是否符合配置要求")

    def check_file(config: StorageConfig, filename: str, file_size: int):
        """检查文件是否符合配置要求"""
        # 检查文件扩展名
        ext = Path(filename).suffix
        if not config.is_extension_allowed(ext):
            return False, f"不支持的文件格式: {ext}"

        # 检查文件大小
        if file_size > config.max_file_size:
            max_size_mb = config.max_file_size / (1024 * 1024)
            current_size_mb = file_size / (1024 * 1024)
            return False, f"文件过大: {current_size_mb:.2f}MB (最大: {max_size_mb:.2f}MB)"

        return True, "文件符合要求"

    test_files = [
        ("image.jpg", 5 * 1024 * 1024),     # 5MB JPG
        ("photo.png", 2 * 1024 * 1024),     # 2MB PNG
        ("large.jpg", 15 * 1024 * 1024),    # 15MB JPG（超过限制）
        ("image.bmp", 1 * 1024 * 1024),     # 1MB BMP（不支持的格式）
    ]

    for filename, file_size in test_files:
        is_valid, message = check_file(loaded_config, filename, file_size)
        status = "✓" if is_valid else "✗"
        size_mb = file_size / (1024 * 1024)
        print(f"  {status} {filename} ({size_mb:.2f}MB): {message}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
