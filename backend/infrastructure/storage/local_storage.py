"""
本地图片存储（Local Image Storage）

功能：
- 按准确率+花卉名+日期分类存储图片
- 支持图片的保存、移动、删除操作
- 生成规范化的文件路径
- 支持异步操作
- 集成P0阶段的ImageHash值对象

路径规范：
storage/images/{accuracy_label}/{genus}/{year-month}/{day}/{diagnosis_id}.jpg
- accuracy_label: unlabeled / correct / incorrect
- genus: 花卉属（例如: rosa）
- year-month: 年-月（例如: 2025-11）
- day: 日（例如: 13）
- diagnosis_id: 诊断ID（例如: diag_20251113_001）

设计决策：
- Layer 1 模块，无外部依赖
- 异步设计（async/await）
- 配置化管理
- 复用P0的ImageHash值对象
"""

from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import shutil
import asyncio

from backend.domain.value_objects import ImageHash
from backend.infrastructure.storage.storage_config import StorageConfig
from backend.infrastructure.storage.storage_exceptions import (
    ImageSaveError,
    ImageMoveError,
    ImageDeleteError,
    PathGenerationError,
    InvalidImageFormat,
    ImageTooLargeError,
)


class LocalImageStorage:
    """
    本地图片存储服务

    职责：
    1. 按准确率+花卉名+日期分类存储图片
    2. 生成唯一的文件路径
    3. 支持图片的保存、移动、删除操作
    4. 计算图片哈希（用于去重和完整性校验）

    路径规范：
    storage/images/{accuracy_label}/{genus}/{year-month}/{day}/{diagnosis_id}.jpg

    属性：
        config: 存储配置对象
        base_path: 存储根目录的绝对路径

    使用示例：
    ```python
    # 初始化存储服务
    storage = LocalImageStorage()

    # 保存图片
    saved_path = await storage.save(
        image_bytes=image_bytes,
        diagnosis_id="diag_20251113_001",
        plant_genus="rosa",
        accuracy_label="unlabeled"
    )

    # 移动图片（准确性标注）
    new_path = await storage.move(
        old_path=saved_path,
        new_accuracy_label="correct"
    )

    # 删除图片
    await storage.delete(saved_path)
    ```
    """

    def __init__(self, config: Optional[StorageConfig] = None, base_path: Optional[str] = None):
        """
        初始化本地图片存储服务

        Args:
            config: 存储配置对象，如果为None则从配置文件加载
            base_path: 存储根目录（覆盖config中的base_path，主要用于测试）

        使用示例：
        ```python
        # 使用默认配置
        storage = LocalImageStorage()

        # 使用自定义配置
        config = StorageConfig(max_file_size=5 * 1024 * 1024)
        storage = LocalImageStorage(config=config)

        # 使用自定义base_path（测试用）
        storage = LocalImageStorage(base_path="tests/storage_test")
        ```
        """
        # 加载配置
        self.config = config or StorageConfig.load()

        # 如果提供了base_path参数，覆盖配置中的base_path
        if base_path is not None:
            # 获取项目根目录
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.base_path = project_root / base_path
        else:
            self.base_path = self.config.get_absolute_base_path()

        # 确保base_path存在
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_path(
        self,
        diagnosis_id: str,
        plant_genus: str,
        accuracy_label: str = "unlabeled",
        file_extension: str = ".jpg"
    ) -> Path:
        """
        生成规范化的文件路径

        路径格式：storage/images/{accuracy_label}/{genus}/{year-month}/{day}/{diagnosis_id}.jpg

        Args:
            diagnosis_id: 诊断ID（例如: diag_20251113_001）
            plant_genus: 花卉属（例如: rosa）
            accuracy_label: 准确率标签（unlabeled / correct / incorrect）
            file_extension: 文件扩展名（默认: .jpg）

        Returns:
            Path: 文件的绝对路径

        Raises:
            PathGenerationError: 路径生成失败

        使用示例：
        ```python
        storage = LocalImageStorage()
        path = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )
        # 输出: D:/项目管理/PhytoOracle/storage/images/unlabeled/rosa/2025-11/13/diag_20251113_001.jpg
        ```
        """
        try:
            # 验证accuracy_label
            valid_labels = ["unlabeled", "correct", "incorrect"]
            if accuracy_label not in valid_labels:
                raise PathGenerationError(
                    f"无效的accuracy_label: {accuracy_label}",
                    context={
                        "accuracy_label": accuracy_label,
                        "valid_labels": valid_labels
                    }
                )

            # 验证diagnosis_id格式（应为diag_YYYYMMDD_NNN）
            import re
            if not re.match(r"^diag_\d{8}_\d{3}$", diagnosis_id):
                raise PathGenerationError(
                    f"诊断ID格式不正确: {diagnosis_id}",
                    context={
                        "diagnosis_id": diagnosis_id,
                        "expected_format": "diag_YYYYMMDD_NNN"
                    }
                )

            # 从diagnosis_id中提取日期信息（diag_20251113_001 -> 20251113）
            date_str = diagnosis_id.split("_")[1]
            year = date_str[0:4]
            month = date_str[4:6]
            day = date_str[6:8]
            year_month = f"{year}-{month}"

            # 标准化plant_genus（转换为小写）
            plant_genus = plant_genus.lower()

            # 标准化文件扩展名
            if not file_extension.startswith("."):
                file_extension = f".{file_extension}"
            file_extension = file_extension.lower()

            # 构建文件路径
            # storage/images/{accuracy_label}/{genus}/{year-month}/{day}/{diagnosis_id}.jpg
            file_path = (
                self.base_path
                / accuracy_label
                / plant_genus
                / year_month
                / day
                / f"{diagnosis_id}{file_extension}"
            )

            return file_path

        except PathGenerationError:
            # 重新抛出PathGenerationError
            raise
        except Exception as e:
            # 捕获其他异常并转换为PathGenerationError
            raise PathGenerationError(
                f"路径生成失败: {e}",
                context={
                    "diagnosis_id": diagnosis_id,
                    "plant_genus": plant_genus,
                    "accuracy_label": accuracy_label
                }
            )

    async def save(
        self,
        image_bytes: bytes,
        diagnosis_id: str,
        plant_genus: str,
        accuracy_label: str = "unlabeled",
        original_filename: Optional[str] = None
    ) -> Tuple[str, ImageHash]:
        """
        异步保存图片到本地文件系统

        Args:
            image_bytes: 图片字节数据
            diagnosis_id: 诊断ID（例如: diag_20251113_001）
            plant_genus: 花卉属（例如: rosa）
            accuracy_label: 准确率标签（unlabeled / correct / incorrect）
            original_filename: 原始文件名（可选，用于提取扩展名）

        Returns:
            Tuple[str, ImageHash]: (文件路径, 图片哈希对象)

        Raises:
            ImageTooLargeError: 图片大小超过限制
            InvalidImageFormat: 图片格式不支持
            ImageSaveError: 图片保存失败

        使用示例：
        ```python
        storage = LocalImageStorage()
        image_bytes = open("image.jpg", "rb").read()

        saved_path, image_hash = await storage.save(
            image_bytes=image_bytes,
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        print(f"图片已保存到: {saved_path}")
        print(f"图片哈希: {image_hash.md5}")
        ```
        """
        try:
            # 1. 验证文件大小
            if len(image_bytes) > self.config.max_file_size:
                raise ImageTooLargeError(
                    "图片大小超过限制",
                    context={
                        "image_size": len(image_bytes),
                        "max_size": self.config.max_file_size
                    }
                )

            # 2. 确定文件扩展名
            if original_filename:
                file_extension = Path(original_filename).suffix.lower()
            else:
                file_extension = ".jpg"  # 默认扩展名

            # 3. 验证文件格式
            if not self.config.is_extension_allowed(file_extension):
                raise InvalidImageFormat(
                    "不支持的图片格式",
                    context={
                        "format": file_extension,
                        "allowed_formats": self.config.allowed_extensions
                    }
                )

            # 4. 计算图片哈希（使用P0的ImageHash值对象）
            image_hash = ImageHash.from_bytes(image_bytes)

            # 5. 生成文件路径
            file_path = self.get_path(
                diagnosis_id=diagnosis_id,
                plant_genus=plant_genus,
                accuracy_label=accuracy_label,
                file_extension=file_extension
            )

            # 6. 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 7. 异步保存文件
            # 使用asyncio.to_thread在线程池中执行IO操作，避免阻塞事件循环
            await asyncio.to_thread(self._write_file, file_path, image_bytes)

            # 8. 返回文件路径（字符串）和图片哈希
            return str(file_path), image_hash

        except (ImageTooLargeError, InvalidImageFormat, PathGenerationError):
            # 重新抛出已知异常
            raise
        except Exception as e:
            # 捕获其他异常并转换为ImageSaveError
            raise ImageSaveError(
                f"图片保存失败: {e}",
                context={
                    "diagnosis_id": diagnosis_id,
                    "plant_genus": plant_genus,
                    "accuracy_label": accuracy_label
                }
            )

    @staticmethod
    def _write_file(file_path: Path, image_bytes: bytes) -> None:
        """
        同步写入文件（供asyncio.to_thread调用）

        Args:
            file_path: 文件路径
            image_bytes: 图片字节数据

        Raises:
            IOError: 文件写入失败
        """
        with open(file_path, "wb") as f:
            f.write(image_bytes)

    async def move(
        self,
        old_path: str,
        new_accuracy_label: str
    ) -> str:
        """
        移动图片文件（用于准确性标注）

        当用户标注图片的准确性时，需要将图片从unlabeled移动到correct或incorrect

        Args:
            old_path: 旧文件路径（字符串）
            new_accuracy_label: 新的准确率标签（correct / incorrect）

        Returns:
            str: 新文件路径（字符串）

        Raises:
            ImageMoveError: 图片移动失败

        使用示例：
        ```python
        storage = LocalImageStorage()

        # 保存图片（初始标记为unlabeled）
        saved_path, _ = await storage.save(
            image_bytes=image_bytes,
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 用户标注为正确
        new_path = await storage.move(
            old_path=saved_path,
            new_accuracy_label="correct"
        )

        print(f"图片已移动: {old_path} -> {new_path}")
        ```
        """
        try:
            old_path_obj = Path(old_path)

            # 1. 验证旧文件是否存在
            if not old_path_obj.exists():
                raise ImageMoveError(
                    "旧文件不存在",
                    context={"old_path": old_path}
                )

            # 2. 验证new_accuracy_label
            valid_labels = ["correct", "incorrect"]
            if new_accuracy_label not in valid_labels:
                raise ImageMoveError(
                    f"无效的accuracy_label: {new_accuracy_label}",
                    context={
                        "new_accuracy_label": new_accuracy_label,
                        "valid_labels": valid_labels
                    }
                )

            # 3. 从旧路径中解析信息
            # 路径格式: {base_path}/{accuracy_label}/{genus}/{year-month}/{day}/{diagnosis_id}.jpg
            # 需要找到base_path的位置
            parts = old_path_obj.parts

            # 尝试找到base_path的结束位置（通过匹配accuracy_label）
            valid_accuracy_labels = ["unlabeled", "correct", "incorrect"]
            accuracy_idx = -1
            for i, part in enumerate(parts):
                if part in valid_accuracy_labels:
                    accuracy_idx = i
                    break

            if accuracy_idx == -1 or len(parts) < accuracy_idx + 5:
                raise ImageMoveError(
                    "旧路径格式不正确",
                    context={
                        "old_path": old_path,
                        "expected_format": "{base_path}/{accuracy_label}/{genus}/{year-month}/{day}/{diagnosis_id}.ext"
                    }
                )

            # 提取genus, year-month, day, filename（从accuracy_label之后的位置）
            plant_genus = parts[accuracy_idx + 1]
            year_month = parts[accuracy_idx + 2]
            day = parts[accuracy_idx + 3]
            filename = parts[accuracy_idx + 4]

            # 从filename提取diagnosis_id和扩展名
            diagnosis_id = filename.split(".")[0]
            file_extension = "." + filename.split(".")[-1]

            # 4. 生成新路径
            new_path_obj = self.get_path(
                diagnosis_id=diagnosis_id,
                plant_genus=plant_genus,
                accuracy_label=new_accuracy_label,
                file_extension=file_extension
            )

            # 5. 确保新目录存在
            new_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # 6. 异步移动文件
            await asyncio.to_thread(shutil.move, str(old_path_obj), str(new_path_obj))

            # 7. 返回新文件路径（字符串）
            return str(new_path_obj)

        except ImageMoveError:
            # 重新抛出ImageMoveError
            raise
        except Exception as e:
            # 捕获其他异常并转换为ImageMoveError
            raise ImageMoveError(
                f"图片移动失败: {e}",
                context={
                    "old_path": old_path,
                    "new_accuracy_label": new_accuracy_label
                }
            )

    async def delete(self, file_path: str) -> bool:
        """
        删除图片文件

        Args:
            file_path: 文件路径（字符串）

        Returns:
            bool: 删除是否成功

        Raises:
            ImageDeleteError: 图片删除失败

        使用示例：
        ```python
        storage = LocalImageStorage()

        # 删除图片
        success = await storage.delete(file_path)
        if success:
            print("图片已删除")
        else:
            print("图片不存在或删除失败")
        ```
        """
        try:
            file_path_obj = Path(file_path)

            # 验证文件是否存在
            if not file_path_obj.exists():
                return False

            # 异步删除文件
            await asyncio.to_thread(file_path_obj.unlink)

            return True

        except Exception as e:
            raise ImageDeleteError(
                f"图片删除失败: {e}",
                context={"file_path": file_path}
            )

    async def read(self, file_path: str) -> bytes:
        """
        读取图片文件

        Args:
            file_path: 文件路径（字符串）

        Returns:
            bytes: 图片字节数据

        Raises:
            FileNotFoundError: 文件不存在
            IOError: 文件读取失败

        使用示例：
        ```python
        storage = LocalImageStorage()

        # 读取图片
        image_bytes = await storage.read(file_path)
        print(f"图片大小: {len(image_bytes)} 字节")
        ```
        """
        try:
            file_path_obj = Path(file_path)

            # 验证文件是否存在
            if not file_path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 异步读取文件
            image_bytes = await asyncio.to_thread(self._read_file, file_path_obj)

            return image_bytes

        except FileNotFoundError:
            raise
        except Exception as e:
            raise IOError(f"文件读取失败: {e}")

    @staticmethod
    def _read_file(file_path: Path) -> bytes:
        """
        同步读取文件（供asyncio.to_thread调用）

        Args:
            file_path: 文件路径

        Returns:
            bytes: 文件内容
        """
        with open(file_path, "rb") as f:
            return f.read()

    def get_storage_stats(self) -> dict:
        """
        获取存储统计信息

        Returns:
            dict: 存储统计信息（文件数量、总大小等）

        使用示例：
        ```python
        storage = LocalImageStorage()
        stats = storage.get_storage_stats()
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {stats['total_size_mb']:.2f} MB")
        ```
        """
        total_files = 0
        total_size = 0

        # 遍历所有文件
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "base_path": str(self.base_path)
        }


def main():
    """
    LocalImageStorage 使用示例

    演示如何：
    1. 初始化存储服务
    2. 生成文件路径
    3. 保存图片
    4. 移动图片（准确性标注）
    5. 读取图片
    6. 删除图片
    7. 获取存储统计信息
    """
    import asyncio

    async def run_examples():
        print("=" * 80)
        print("LocalImageStorage 使用示例")
        print("=" * 80)

        # 示例1：初始化存储服务
        print("\n[示例1] 初始化存储服务")
        storage = LocalImageStorage(base_path="tests/storage_test")
        print(f"  [OK] 存储服务初始化成功")
        print(f"  - base_path: {storage.base_path}")

        # 示例2：生成文件路径
        print("\n[示例2] 生成文件路径")
        file_path = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )
        print(f"  [OK] 文件路径生成成功")
        print(f"  - 路径: {file_path}")

        # 示例3：保存图片
        print("\n[示例3] 保存图片")
        # 创建一个简单的测试图片（BMP格式，最小的有效图片）
        # BMP header + 1x1 pixel (白色)
        test_image_bytes = (
            b'BM'  # 文件类型
            b'\x3e\x00\x00\x00'  # 文件大小（62字节）
            b'\x00\x00\x00\x00'  # 保留字段
            b'\x36\x00\x00\x00'  # 数据偏移
            b'\x28\x00\x00\x00'  # 信息头大小
            b'\x01\x00\x00\x00'  # 宽度
            b'\x01\x00\x00\x00'  # 高度
            b'\x01\x00'  # 颜色平面数
            b'\x18\x00'  # 每像素位数（24位）
            b'\x00\x00\x00\x00'  # 压缩方式
            b'\x08\x00\x00\x00'  # 图像大小
            b'\x00\x00\x00\x00'  # 水平分辨率
            b'\x00\x00\x00\x00'  # 垂直分辨率
            b'\x00\x00\x00\x00'  # 颜色数
            b'\x00\x00\x00\x00'  # 重要颜色数
            b'\xff\xff\xff\x00'  # 像素数据（白色）
        )

        # 保存为JPG（因为配置只允许jpg, png）
        # 这里我们直接用字节数据模拟
        fake_jpg_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * 100  # JPG魔数 + 填充

        saved_path, image_hash = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled",
            original_filename="test.jpg"
        )
        print(f"  [OK] 图片保存成功")
        print(f"  - 保存路径: {saved_path}")
        print(f"  - MD5哈希: {image_hash.md5}")
        print(f"  - SHA256哈希: {image_hash.sha256[:16]}... (已截断)")

        # 示例4：验证文件存在
        print("\n[示例4] 验证文件存在")
        file_exists = Path(saved_path).exists()
        print(f"  [{'OK' if file_exists else 'FAIL'}] 文件存在: {file_exists}")

        # 示例5：读取图片
        print("\n[示例5] 读取图片")
        read_bytes = await storage.read(saved_path)
        print(f"  [OK] 图片读取成功")
        print(f"  - 文件大小: {len(read_bytes)} 字节")
        print(f"  - 内容一致: {read_bytes == fake_jpg_bytes}")

        # 示例6：移动图片（准确性标注）
        print("\n[示例6] 移动图片（准确性标注）")
        new_path = await storage.move(
            old_path=saved_path,
            new_accuracy_label="correct"
        )
        print(f"  [OK] 图片移动成功")
        print(f"  - 旧路径: {saved_path}")
        print(f"  - 新路径: {new_path}")
        print(f"  - 旧文件存在: {Path(saved_path).exists()}")
        print(f"  - 新文件存在: {Path(new_path).exists()}")

        # 示例7：再次移动图片（标记为incorrect）
        print("\n[示例7] 再次移动图片（标记为incorrect）")
        final_path = await storage.move(
            old_path=new_path,
            new_accuracy_label="incorrect"
        )
        print(f"  [OK] 图片移动成功")
        print(f"  - 旧路径: {new_path}")
        print(f"  - 新路径: {final_path}")

        # 示例8：获取存储统计信息
        print("\n[示例8] 获取存储统计信息")
        stats = storage.get_storage_stats()
        print(f"  [OK] 存储统计信息获取成功")
        print(f"  - 总文件数: {stats['total_files']}")
        print(f"  - 总大小: {stats['total_size_mb']:.4f} MB")
        print(f"  - 存储路径: {stats['base_path']}")

        # 示例9：删除图片
        print("\n[示例9] 删除图片")
        delete_success = await storage.delete(final_path)
        print(f"  [{'OK' if delete_success else 'FAIL'}] 图片删除成功: {delete_success}")
        print(f"  - 文件存在: {Path(final_path).exists()}")

        # 示例10：异常处理 - 图片过大
        print("\n[示例10] 异常处理 - 图片过大")
        try:
            large_image_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * (11 * 1024 * 1024)  # 11MB
            await storage.save(
                image_bytes=large_image_bytes,
                diagnosis_id="diag_20251113_002",
                plant_genus="rosa",
                accuracy_label="unlabeled"
            )
            print(f"  [FAIL] 应该抛出ImageTooLargeError但没有")
        except ImageTooLargeError as e:
            print(f"  [OK] 捕获到ImageTooLargeError（符合预期）")
            print(f"  - 错误信息: {e.message}")

        # 示例11：异常处理 - 无效的诊断ID格式
        print("\n[示例11] 异常处理 - 无效的诊断ID格式")
        try:
            file_path = storage.get_path(
                diagnosis_id="invalid_id",
                plant_genus="rosa",
                accuracy_label="unlabeled"
            )
            print(f"  [FAIL] 应该抛出PathGenerationError但没有")
        except PathGenerationError as e:
            print(f"  [OK] 捕获到PathGenerationError（符合预期）")
            print(f"  - 错误信息: {e.message}")

        print("\n" + "=" * 80)
        print("示例执行完毕")
        print("=" * 80)

    # 运行异步示例
    asyncio.run(run_examples())


if __name__ == "__main__":
    main()
