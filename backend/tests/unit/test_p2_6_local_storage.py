"""
P2.6 本地图片存储（LocalImageStorage）单元测试

测试范围：
1. LocalImageStorage类实例化
2. get_path() 方法：路径生成规范
3. save() 方法：图片保存功能
4. move() 方法：文件移动功能（准确性标注）
5. delete() 方法：文件删除功能
6. read() 方法：文件读取功能
7. 异常处理：各种错误情况
8. StorageConfig配置管理

验收标准（G2.6）：
- [x] LocalImageStorage类可成功实例化
- [x] save() 方法测试通过（生成正确的文件路径，保存图片成功）
- [x] move() 方法测试通过（移动文件到correct/incorrect文件夹）
- [x] get_path() 方法测试通过（路径生成规范正确）
- [x] 单元测试覆盖率 ≥ 90%
"""

import pytest
from pathlib import Path
import shutil
import asyncio

from backend.infrastructure.storage import (
    LocalImageStorage,
    StorageConfig,
    StorageException,
    ImageSaveError,
    ImageMoveError,
    PathGenerationError,
    InvalidImageFormat,
    ImageTooLargeError,
)
from backend.domain.value_objects import ImageHash


# ==================== Fixtures ====================

@pytest.fixture
def project_root():
    """获取项目根目录"""
    return Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def test_storage_path(project_root):
    """测试用的存储路径"""
    return "tests/storage_test_p2_6"


@pytest.fixture
def storage(test_storage_path):
    """创建LocalImageStorage实例（用于测试）"""
    storage = LocalImageStorage(base_path=test_storage_path)
    yield storage
    # 清理测试目录
    if storage.base_path.exists():
        shutil.rmtree(storage.base_path)


@pytest.fixture
def storage_config():
    """创建测试用的StorageConfig"""
    return StorageConfig(
        base_path="tests/storage_test",
        max_file_size=5 * 1024 * 1024,  # 5MB
        allowed_extensions=[".jpg", ".jpeg", ".png"]
    )


@pytest.fixture
def fake_jpg_bytes():
    """创建假的JPG图片字节数据"""
    # JPG魔数 + 一些填充数据
    return b'\xff\xd8\xff\xe0' + b'\x00' * 100


@pytest.fixture
def fake_png_bytes():
    """创建假的PNG图片字节数据"""
    # PNG魔数 + 一些填充数据
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


# ==================== 测试类1: 初始化测试 ====================

class TestLocalImageStorageInitialization:
    """测试LocalImageStorage的初始化"""

    def test_initialization_with_default_config(self, test_storage_path):
        """测试使用默认配置初始化"""
        storage = LocalImageStorage(base_path=test_storage_path)
        assert storage.config is not None
        assert storage.base_path.exists()

        # 清理
        shutil.rmtree(storage.base_path)

    def test_initialization_with_custom_config(self, test_storage_path, storage_config):
        """测试使用自定义配置初始化"""
        storage = LocalImageStorage(config=storage_config, base_path=test_storage_path)
        assert storage.config.max_file_size == 5 * 1024 * 1024
        assert storage.base_path.exists()

        # 清理
        shutil.rmtree(storage.base_path)

    def test_initialization_creates_base_directory(self, test_storage_path):
        """测试初始化时会创建base_path目录"""
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        test_path = project_root / test_storage_path

        # 确保目录不存在
        if test_path.exists():
            shutil.rmtree(test_path)

        storage = LocalImageStorage(base_path=test_storage_path)
        assert storage.base_path.exists()
        assert storage.base_path.is_dir()

        # 清理
        shutil.rmtree(storage.base_path)


# ==================== 测试类2: get_path() 方法测试 ====================

class TestGetPath:
    """测试get_path()方法：路径生成规范"""

    def test_get_path_unlabeled(self, storage):
        """测试生成unlabeled路径"""
        file_path = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 验证路径格式
        assert "unlabeled" in str(file_path)
        assert "rosa" in str(file_path)
        assert "2025-11" in str(file_path)
        assert "13" in str(file_path)
        assert "diag_20251113_001.jpg" in str(file_path)

    def test_get_path_correct(self, storage):
        """测试生成correct路径"""
        file_path = storage.get_path(
            diagnosis_id="diag_20251113_002",
            plant_genus="rosa",
            accuracy_label="correct"
        )

        assert "correct" in str(file_path)
        assert "rosa" in str(file_path)

    def test_get_path_incorrect(self, storage):
        """测试生成incorrect路径"""
        file_path = storage.get_path(
            diagnosis_id="diag_20251113_003",
            plant_genus="rosa",
            accuracy_label="incorrect"
        )

        assert "incorrect" in str(file_path)
        assert "rosa" in str(file_path)

    def test_get_path_different_extensions(self, storage):
        """测试不同文件扩展名"""
        # JPG
        path_jpg = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            file_extension=".jpg"
        )
        assert path_jpg.suffix == ".jpg"

        # PNG
        path_png = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            file_extension=".png"
        )
        assert path_png.suffix == ".png"

        # 不带点的扩展名（应自动添加）
        path_jpeg = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            file_extension="jpeg"
        )
        assert path_jpeg.suffix == ".jpeg"

    def test_get_path_invalid_accuracy_label(self, storage):
        """测试无效的accuracy_label"""
        with pytest.raises(PathGenerationError) as exc_info:
            storage.get_path(
                diagnosis_id="diag_20251113_001",
                plant_genus="rosa",
                accuracy_label="invalid_label"
            )
        assert "无效的accuracy_label" in str(exc_info.value)

    def test_get_path_invalid_diagnosis_id(self, storage):
        """测试无效的diagnosis_id格式"""
        with pytest.raises(PathGenerationError) as exc_info:
            storage.get_path(
                diagnosis_id="invalid_id",
                plant_genus="rosa",
                accuracy_label="unlabeled"
            )
        assert "诊断ID格式不正确" in str(exc_info.value)

    def test_get_path_genus_case_insensitive(self, storage):
        """测试plant_genus大小写不敏感"""
        path1 = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="Rosa",
            accuracy_label="unlabeled"
        )
        path2 = storage.get_path(
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 应该生成相同的路径（都转换为小写）
        assert str(path1) == str(path2)


# ==================== 测试类3: save() 方法测试 ====================

class TestSaveMethod:
    """测试save()方法：图片保存功能"""

    @pytest.mark.asyncio
    async def test_save_image_success(self, storage, fake_jpg_bytes):
        """测试成功保存图片"""
        saved_path, image_hash = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_001",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 验证返回的路径（使用Path标准化路径分隔符）
        saved_path_normalized = Path(saved_path).as_posix()
        assert "unlabeled/rosa/2025-11/13" in saved_path_normalized
        assert "diag_20251113_001" in saved_path_normalized

        # 验证文件存在
        assert Path(saved_path).exists()

        # 验证图片哈希
        assert isinstance(image_hash, ImageHash)
        assert image_hash.md5 is not None
        assert image_hash.sha256 is not None

    @pytest.mark.asyncio
    async def test_save_image_with_png(self, storage, fake_png_bytes):
        """测试保存PNG图片"""
        saved_path, image_hash = await storage.save(
            image_bytes=fake_png_bytes,
            diagnosis_id="diag_20251113_002",
            plant_genus="rosa",
            accuracy_label="unlabeled",
            original_filename="test.png"
        )

        # 验证文件扩展名
        assert saved_path.endswith(".png")
        assert Path(saved_path).exists()

    @pytest.mark.asyncio
    async def test_save_image_too_large(self, storage):
        """测试保存过大的图片"""
        # 创建一个超过10MB的图片
        large_image_bytes = b'\xff\xd8\xff\xe0' + b'\x00' * (11 * 1024 * 1024)

        with pytest.raises(ImageTooLargeError) as exc_info:
            await storage.save(
                image_bytes=large_image_bytes,
                diagnosis_id="diag_20251113_003",
                plant_genus="rosa",
                accuracy_label="unlabeled"
            )
        assert "图片大小超过限制" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_image_invalid_format(self, storage):
        """测试保存不支持的格式"""
        # BMP格式（不在allowed_extensions中）
        bmp_bytes = b'BM' + b'\x00' * 100

        with pytest.raises(InvalidImageFormat) as exc_info:
            await storage.save(
                image_bytes=bmp_bytes,
                diagnosis_id="diag_20251113_004",
                plant_genus="rosa",
                accuracy_label="unlabeled",
                original_filename="test.bmp"
            )
        assert "不支持的图片格式" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_creates_directory_structure(self, storage, fake_jpg_bytes):
        """测试save()会自动创建目录结构"""
        saved_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_005",
            plant_genus="prunus",  # 使用不同的属名
            accuracy_label="unlabeled"
        )

        # 验证目录结构存在
        path_obj = Path(saved_path)
        assert path_obj.parent.exists()
        assert path_obj.parent.parent.exists()  # year-month
        assert path_obj.parent.parent.parent.exists()  # genus


# ==================== 测试类4: move() 方法测试 ====================

class TestMoveMethod:
    """测试move()方法：文件移动功能（准确性标注）"""

    @pytest.mark.asyncio
    async def test_move_unlabeled_to_correct(self, storage, fake_jpg_bytes):
        """测试从unlabeled移动到correct"""
        # 1. 先保存图片
        old_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_010",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 2. 移动到correct
        new_path = await storage.move(
            old_path=old_path,
            new_accuracy_label="correct"
        )

        # 验证（使用Path标准化路径分隔符）
        new_path_normalized = Path(new_path).as_posix()
        assert "correct/rosa/" in new_path_normalized
        assert Path(new_path).exists()
        assert not Path(old_path).exists()  # 旧文件已删除

    @pytest.mark.asyncio
    async def test_move_unlabeled_to_incorrect(self, storage, fake_jpg_bytes):
        """测试从unlabeled移动到incorrect"""
        # 1. 先保存图片
        old_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_011",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 2. 移动到incorrect
        new_path = await storage.move(
            old_path=old_path,
            new_accuracy_label="incorrect"
        )

        # 验证（使用Path标准化路径分隔符）
        new_path_normalized = Path(new_path).as_posix()
        assert "incorrect/rosa/" in new_path_normalized
        assert Path(new_path).exists()
        assert not Path(old_path).exists()

    @pytest.mark.asyncio
    async def test_move_correct_to_incorrect(self, storage, fake_jpg_bytes):
        """测试从correct移动到incorrect（修正标注）"""
        # 1. 先保存为unlabeled
        unlabeled_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_012",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 2. 移动到correct
        correct_path = await storage.move(
            old_path=unlabeled_path,
            new_accuracy_label="correct"
        )

        # 3. 再移动到incorrect
        incorrect_path = await storage.move(
            old_path=correct_path,
            new_accuracy_label="incorrect"
        )

        # 验证（使用Path标准化路径分隔符）
        incorrect_path_normalized = Path(incorrect_path).as_posix()
        assert "incorrect/rosa/" in incorrect_path_normalized
        assert Path(incorrect_path).exists()
        assert not Path(correct_path).exists()

    @pytest.mark.asyncio
    async def test_move_file_not_exists(self, storage):
        """测试移动不存在的文件"""
        with pytest.raises(ImageMoveError) as exc_info:
            await storage.move(
                old_path="/path/to/nonexistent/file.jpg",
                new_accuracy_label="correct"
            )
        assert "旧文件不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_move_invalid_accuracy_label(self, storage, fake_jpg_bytes):
        """测试使用无效的accuracy_label"""
        # 1. 先保存图片
        old_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_013",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 2. 尝试移动到无效的标签
        with pytest.raises(ImageMoveError) as exc_info:
            await storage.move(
                old_path=old_path,
                new_accuracy_label="invalid_label"
            )
        assert "无效的accuracy_label" in str(exc_info.value)


# ==================== 测试类5: delete() 和 read() 方法测试 ====================

class TestDeleteAndReadMethods:
    """测试delete()和read()方法"""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, storage, fake_jpg_bytes):
        """测试删除存在的文件"""
        # 1. 先保存图片
        saved_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_020",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 2. 删除文件
        success = await storage.delete(saved_path)

        # 验证
        assert success is True
        assert not Path(saved_path).exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage):
        """测试删除不存在的文件"""
        success = await storage.delete("/path/to/nonexistent/file.jpg")
        assert success is False

    @pytest.mark.asyncio
    async def test_read_existing_file(self, storage, fake_jpg_bytes):
        """测试读取存在的文件"""
        # 1. 先保存图片
        saved_path, _ = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_021",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )

        # 2. 读取文件
        read_bytes = await storage.read(saved_path)

        # 验证
        assert read_bytes == fake_jpg_bytes
        assert len(read_bytes) == len(fake_jpg_bytes)

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, storage):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            await storage.read("/path/to/nonexistent/file.jpg")


# ==================== 测试类6: 存储统计测试 ====================

class TestStorageStats:
    """测试存储统计功能"""

    def test_get_storage_stats_empty(self, storage):
        """测试空存储的统计信息"""
        stats = storage.get_storage_stats()

        assert stats["total_files"] == 0
        assert stats["total_size"] == 0
        assert stats["total_size_mb"] == 0.0
        assert stats["base_path"] == str(storage.base_path)

    @pytest.mark.asyncio
    async def test_get_storage_stats_with_files(self, storage, fake_jpg_bytes):
        """测试有文件时的统计信息"""
        # 保存3个文件
        await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_030",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )
        await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_031",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )
        await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_032",
            plant_genus="prunus",
            accuracy_label="correct"
        )

        stats = storage.get_storage_stats()

        assert stats["total_files"] == 3
        assert stats["total_size"] > 0
        assert stats["total_size_mb"] > 0


# ==================== 测试类7: StorageConfig测试 ====================

class TestStorageConfig:
    """测试StorageConfig配置管理"""

    def test_create_default_config(self):
        """测试创建默认配置"""
        config = StorageConfig()

        assert config.base_path == "storage/images"
        assert config.max_file_size == 10 * 1024 * 1024
        assert ".jpg" in config.allowed_extensions

    def test_create_custom_config(self):
        """测试创建自定义配置"""
        config = StorageConfig(
            base_path="custom/path",
            max_file_size=5 * 1024 * 1024,
            allowed_extensions=[".jpg", ".png"]
        )

        assert config.base_path == "custom/path"
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.allowed_extensions == [".jpg", ".png"]

    def test_config_validation_empty_base_path(self):
        """测试base_path为空时的验证"""
        with pytest.raises(ValueError):
            StorageConfig(base_path="")

    def test_config_validation_absolute_base_path(self):
        """测试base_path为绝对路径时的验证"""
        with pytest.raises(ValueError):
            StorageConfig(base_path="D:/absolute/path")

    def test_config_validation_negative_max_file_size(self):
        """测试max_file_size为负数时的验证"""
        with pytest.raises(ValueError):
            StorageConfig(max_file_size=-1)

    def test_config_validation_empty_extensions(self):
        """测试allowed_extensions为空时的验证"""
        with pytest.raises(ValueError):
            StorageConfig(allowed_extensions=[])

    def test_config_is_extension_allowed(self):
        """测试is_extension_allowed()方法"""
        config = StorageConfig(allowed_extensions=[".jpg", ".png"])

        assert config.is_extension_allowed(".jpg") is True
        assert config.is_extension_allowed("jpg") is True  # 不带点也可以
        assert config.is_extension_allowed(".PNG") is True  # 大小写不敏感
        assert config.is_extension_allowed(".bmp") is False

    def test_config_get_absolute_base_path(self):
        """测试get_absolute_base_path()方法"""
        config = StorageConfig(base_path="storage/images")
        abs_path = config.get_absolute_base_path()

        assert abs_path.is_absolute()
        assert abs_path.name == "images"


# ==================== 测试类8: 集成测试 ====================

class TestIntegration:
    """集成测试：完整的图片生命周期"""

    @pytest.mark.asyncio
    async def test_full_image_lifecycle(self, storage, fake_jpg_bytes):
        """测试完整的图片生命周期"""
        # 1. 保存图片（unlabeled）
        saved_path, image_hash = await storage.save(
            image_bytes=fake_jpg_bytes,
            diagnosis_id="diag_20251113_100",
            plant_genus="rosa",
            accuracy_label="unlabeled"
        )
        assert Path(saved_path).exists()
        assert "unlabeled" in saved_path

        # 2. 读取图片
        read_bytes = await storage.read(saved_path)
        assert read_bytes == fake_jpg_bytes

        # 3. 移动到correct
        correct_path = await storage.move(
            old_path=saved_path,
            new_accuracy_label="correct"
        )
        assert Path(correct_path).exists()
        assert "correct" in correct_path
        assert not Path(saved_path).exists()

        # 4. 再移动到incorrect
        incorrect_path = await storage.move(
            old_path=correct_path,
            new_accuracy_label="incorrect"
        )
        assert Path(incorrect_path).exists()
        assert "incorrect" in incorrect_path
        assert not Path(correct_path).exists()

        # 5. 删除图片
        delete_success = await storage.delete(incorrect_path)
        assert delete_success is True
        assert not Path(incorrect_path).exists()

    @pytest.mark.asyncio
    async def test_multiple_images_same_genus(self, storage, fake_jpg_bytes):
        """测试同一属的多个图片"""
        # 保存多个玫瑰属的图片
        paths = []
        for i in range(1, 4):
            path, _ = await storage.save(
                image_bytes=fake_jpg_bytes,
                diagnosis_id=f"diag_20251113_{i:03d}",
                plant_genus="rosa",
                accuracy_label="unlabeled"
            )
            paths.append(path)

        # 验证所有文件都存在
        for path in paths:
            assert Path(path).exists()
            assert "rosa" in path

        # 验证统计信息
        stats = storage.get_storage_stats()
        assert stats["total_files"] == 3


def main():
    """
    运行所有单元测试

    执行命令：
    ```bash
    # 运行所有P2.6测试
    python -m pytest backend/tests/unit/test_p2_6_local_storage.py -v

    # 运行特定测试类
    python -m pytest backend/tests/unit/test_p2_6_local_storage.py::TestSaveMethod -v

    # 运行特定测试
    python -m pytest backend/tests/unit/test_p2_6_local_storage.py::TestSaveMethod::test_save_image_success -v

    # 生成覆盖率报告
    python -m pytest backend/tests/unit/test_p2_6_local_storage.py --cov=backend.infrastructure.storage --cov-report=html
    ```
    """
    print("=" * 80)
    print("P2.6 本地图片存储（LocalImageStorage）单元测试")
    print("=" * 80)
    print("\n执行命令:")
    print("  python -m pytest backend/tests/unit/test_p2_6_local_storage.py -v")
    print("\n测试范围:")
    print("  1. LocalImageStorage类实例化")
    print("  2. get_path() 方法：路径生成规范")
    print("  3. save() 方法：图片保存功能")
    print("  4. move() 方法：文件移动功能")
    print("  5. delete() 和 read() 方法")
    print("  6. 存储统计功能")
    print("  7. StorageConfig配置管理")
    print("  8. 集成测试：完整图片生命周期")
    print("\n验收标准（G2.6）:")
    print("  - [x] LocalImageStorage类可成功实例化")
    print("  - [x] save() 方法测试通过")
    print("  - [x] move() 方法测试通过")
    print("  - [x] get_path() 方法测试通过")
    print("  - [x] 单元测试覆盖率 ≥ 90%")
    print("=" * 80)


if __name__ == "__main__":
    main()
