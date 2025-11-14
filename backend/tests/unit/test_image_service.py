"""
ImageService 单元测试

测试范围：
1. 图片保存功能
2. 准确性标签更新
3. 图片查询
4. 图片删除（软删除）
5. 图片ID生成
6. 异常处理

作者：AI Python Architect
日期：2025-11-13
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from backend.services.image_service import (
    ImageService,
    ImageServiceException,
)
from backend.infrastructure.storage.storage_exceptions import StorageException
from backend.infrastructure.persistence.repositories.image_repo import (
    ImageRepositoryException,
)


class TestImageServiceInitialization:
    """图片服务初始化测试"""

    def test_init_with_custom_paths(self, tmp_path):
        """测试：使用自定义路径初始化"""
        # 准备
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        # Mock依赖
        with patch('backend.services.image_service.LocalImageStorage'), \
             patch('backend.services.image_service.ImageRepository'):
            # 执行
            service = ImageService(storage_path, db_path)

            # 验证
            assert service.storage is not None
            assert service.repository is not None

    def test_init_with_default_paths(self):
        """测试：使用默认路径初始化"""
        # Mock依赖
        with patch('backend.services.image_service.LocalImageStorage'), \
             patch('backend.services.image_service.ImageRepository'):
            # 执行
            service = ImageService()

            # 验证
            assert service.storage is not None
            assert service.repository is not None

    def test_init_storage_failure(self, tmp_path):
        """测试：存储初始化失败"""
        # 准备
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        # Mock存储初始化失败
        with patch('backend.services.image_service.LocalImageStorage', side_effect=StorageException("存储错误")):
            # 执行 & 验证
            with pytest.raises(ImageServiceException, match="存储初始化失败"):
                ImageService(storage_path, db_path)

    def test_init_repository_failure(self, tmp_path):
        """测试：数据库初始化失败"""
        # 准备
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        # Mock数据库初始化失败
        with patch('backend.services.image_service.LocalImageStorage'), \
             patch('backend.services.image_service.ImageRepository', side_effect=ImageRepositoryException("数据库错误")):
            # 执行 & 验证
            with pytest.raises(ImageServiceException, match="数据库初始化失败"):
                ImageService(storage_path, db_path)


class TestImageServiceSaveImage:
    """图片保存功能测试"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """创建Mock的ImageService"""
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        # Mock存储和仓库
        mock_storage = Mock()
        mock_storage.base_path = storage_path
        mock_storage.save_image.return_value = {
            "relative_path": "2025-11-13/img_20251113_001.jpg",
            "full_path": str(storage_path / "2025-11-13/img_20251113_001.jpg")
        }

        mock_repository = Mock()
        mock_repository.save.return_value = None

        with patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):
            service = ImageService(storage_path, db_path)
            service.storage = mock_storage
            service.repository = mock_repository
            return service

    def test_save_image_success(self, mock_service):
        """测试：保存图片成功"""
        # 准备
        image_bytes = b"fake_image_data"

        # 执行
        result = mock_service.save_image(
            image_bytes=image_bytes,
            flower_genus="Rosa",
            diagnosis_id="diag_001",
            disease_id="rose_black_spot",
            disease_name="玫瑰黑斑病",
            confidence_level="confirmed"
        )

        # 验证
        assert "image_id" in result
        assert "file_path" in result
        assert "full_path" in result
        assert result["file_path"] == "2025-11-13/img_20251113_001.jpg"

        # 验证调用
        mock_service.storage.save_image.assert_called_once()
        mock_service.repository.save.assert_called_once()

    def test_save_image_with_minimal_params(self, mock_service):
        """测试：使用最少参数保存图片"""
        # 准备
        image_bytes = b"fake_image_data"

        # 执行
        result = mock_service.save_image(image_bytes=image_bytes)

        # 验证
        assert "image_id" in result
        mock_service.repository.save.assert_called_once()

        # 验证保存的数据包含None值
        saved_data = mock_service.repository.save.call_args[0][0]
        assert saved_data["flower_genus"] is None
        assert saved_data["diagnosis_id"] is None

    def test_save_image_storage_failure(self, mock_service):
        """测试：存储失败"""
        # 准备
        image_bytes = b"fake_image_data"
        mock_service.storage.save_image.side_effect = StorageException("磁盘空间不足")

        # 执行 & 验证
        with pytest.raises(ImageServiceException, match="图片保存失败"):
            mock_service.save_image(image_bytes=image_bytes)

    def test_save_image_repository_failure(self, mock_service):
        """测试：数据库保存失败"""
        # 准备
        image_bytes = b"fake_image_data"
        mock_service.repository.save.side_effect = ImageRepositoryException("数据库连接失败")

        # 执行 & 验证
        with pytest.raises(ImageServiceException, match="元数据保存失败"):
            mock_service.save_image(image_bytes=image_bytes)


class TestImageServiceUpdateAccuracyLabel:
    """准确性标签更新测试"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """创建Mock的ImageService"""
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        mock_storage = Mock()
        mock_storage.base_path = storage_path

        mock_repository = Mock()
        mock_repository.update_accuracy_label.return_value = True
        mock_repository.get_by_id.return_value = {
            "image_id": "img_20251113_001",
            "file_path": "2025-11-13/img_20251113_001.jpg"
        }

        with patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):
            service = ImageService(storage_path, db_path)
            service.storage = mock_storage
            service.repository = mock_repository
            return service

    def test_update_accuracy_label_correct(self, mock_service):
        """测试：标记为正确"""
        # 执行
        updated = mock_service.update_accuracy_label("img_001", "correct")

        # 验证
        assert updated is True
        mock_service.repository.update_accuracy_label.assert_called_once_with("img_001", "correct")

    def test_update_accuracy_label_incorrect(self, mock_service):
        """测试：标记为错误"""
        # 执行
        updated = mock_service.update_accuracy_label("img_001", "incorrect")

        # 验证
        assert updated is True
        mock_service.repository.update_accuracy_label.assert_called_once_with("img_001", "incorrect")

    def test_update_accuracy_label_unknown(self, mock_service):
        """测试：标记为未知"""
        # Mock不移动文件（因为是unknown）
        mock_service.repository.update_accuracy_label.return_value = True

        # 执行
        updated = mock_service.update_accuracy_label("img_001", "unknown")

        # 验证
        assert updated is True

    def test_update_accuracy_label_invalid(self, mock_service):
        """测试：无效的准确性标签"""
        # 执行 & 验证
        with pytest.raises(ImageServiceException, match="无效的准确性标签"):
            mock_service.update_accuracy_label("img_001", "invalid_label")

    def test_update_accuracy_label_not_found(self, mock_service):
        """测试：图片不存在"""
        # Mock返回False
        mock_service.repository.update_accuracy_label.return_value = False

        # 执行
        updated = mock_service.update_accuracy_label("nonexistent", "correct")

        # 验证
        assert updated is False

    def test_update_accuracy_label_repository_failure(self, mock_service):
        """测试：数据库更新失败"""
        # Mock抛出异常
        mock_service.repository.update_accuracy_label.side_effect = ImageRepositoryException("连接失败")

        # 执行 & 验证
        with pytest.raises(ImageServiceException, match="更新准确性标签失败"):
            mock_service.update_accuracy_label("img_001", "correct")


class TestImageServiceQueryImages:
    """图片查询测试"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """创建Mock的ImageService"""
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        mock_storage = Mock()
        mock_repository = Mock()

        with patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):
            service = ImageService(storage_path, db_path)
            service.repository = mock_repository
            return service

    def test_query_images_by_genus(self, mock_service):
        """测试：按种属查询"""
        # Mock返回数据
        mock_service.repository.query.return_value = [
            {"image_id": "img_001", "flower_genus": "Rosa"},
            {"image_id": "img_002", "flower_genus": "Rosa"},
        ]

        # 执行
        images = mock_service.query_images(flower_genus="Rosa")

        # 验证
        assert len(images) == 2
        mock_service.repository.query.assert_called_once_with(
            flower_genus="Rosa",
            is_accurate=None,
            start_date=None,
            end_date=None
        )

    def test_query_images_by_accuracy(self, mock_service):
        """测试：按准确性查询"""
        # Mock返回数据
        mock_service.repository.query.return_value = [
            {"image_id": "img_001", "is_accurate": "correct"},
        ]

        # 执行
        images = mock_service.query_images(is_accurate="correct")

        # 验证
        assert len(images) == 1
        mock_service.repository.query.assert_called_once()

    def test_query_images_by_date_range(self, mock_service):
        """测试：按日期范围查询"""
        # Mock返回数据
        mock_service.repository.query.return_value = []

        start_date = datetime(2025, 11, 1)
        end_date = datetime(2025, 11, 30)

        # 执行
        images = mock_service.query_images(start_date=start_date, end_date=end_date)

        # 验证
        assert len(images) == 0
        mock_service.repository.query.assert_called_once_with(
            flower_genus=None,
            is_accurate=None,
            start_date=start_date,
            end_date=end_date
        )

    def test_query_images_all_filters(self, mock_service):
        """测试：使用所有筛选条件"""
        # Mock返回数据
        mock_service.repository.query.return_value = [
            {
                "image_id": "img_001",
                "flower_genus": "Rosa",
                "is_accurate": "correct",
                "created_at": datetime(2025, 11, 13)
            }
        ]

        # 执行
        images = mock_service.query_images(
            flower_genus="Rosa",
            is_accurate="correct",
            start_date=datetime(2025, 11, 1),
            end_date=datetime(2025, 11, 30)
        )

        # 验证
        assert len(images) == 1

    def test_query_images_repository_failure(self, mock_service):
        """测试：查询失败"""
        # Mock抛出异常
        mock_service.repository.query.side_effect = ImageRepositoryException("查询错误")

        # 执行 & 验证
        with pytest.raises(ImageServiceException, match="查询失败"):
            mock_service.query_images()


class TestImageServiceDeleteImage:
    """图片删除测试"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """创建Mock的ImageService"""
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        mock_storage = Mock()
        mock_repository = Mock()

        with patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):
            service = ImageService(storage_path, db_path)
            service.repository = mock_repository
            return service

    def test_delete_image_success(self, mock_service):
        """测试：删除成功"""
        # Mock返回True
        mock_service.repository.soft_delete.return_value = True

        # 执行
        deleted = mock_service.delete_image("img_001")

        # 验证
        assert deleted is True
        mock_service.repository.soft_delete.assert_called_once_with("img_001")

    def test_delete_image_not_found(self, mock_service):
        """测试：图片不存在"""
        # Mock返回False
        mock_service.repository.soft_delete.return_value = False

        # 执行
        deleted = mock_service.delete_image("nonexistent")

        # 验证
        assert deleted is False

    def test_delete_image_repository_failure(self, mock_service):
        """测试：删除失败"""
        # Mock抛出异常
        mock_service.repository.soft_delete.side_effect = ImageRepositoryException("删除错误")

        # 执行 & 验证
        with pytest.raises(ImageServiceException, match="删除失败"):
            mock_service.delete_image("img_001")


class TestImageServiceHelperMethods:
    """辅助方法测试"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """创建Mock的ImageService"""
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        mock_storage = Mock()
        mock_repository = Mock()

        with patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):
            service = ImageService(storage_path, db_path)
            return service

    def test_generate_image_id_format(self, mock_service):
        """测试：生成的图片ID格式正确"""
        # 执行多次
        ids = [mock_service._generate_image_id() for _ in range(10)]

        # 验证格式：img_YYYYMMDD_NNN
        import re
        pattern = r"^img_\d{8}_\d{3}$"
        for image_id in ids:
            assert re.match(pattern, image_id), f"ID格式错误: {image_id}"

    def test_generate_image_id_contains_date(self, mock_service):
        """测试：图片ID包含当前日期"""
        # 执行
        image_id = mock_service._generate_image_id()

        # 验证包含今天的日期
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        assert today in image_id

    def test_move_to_accuracy_folder_file_exists(self, mock_service, tmp_path):
        """测试：移动文件到准确性文件夹（文件存在）"""
        # 准备
        storage_path = tmp_path / "uploads"
        storage_path.mkdir()

        # 创建原始文件
        original_dir = storage_path / "2025-11-13"
        original_dir.mkdir()
        original_file = original_dir / "img_001.jpg"
        original_file.write_bytes(b"test_data")

        mock_service.storage.base_path = storage_path
        mock_service.repository.get_by_id.return_value = {
            "image_id": "img_001",
            "file_path": "2025-11-13/img_001.jpg"
        }

        # 执行
        mock_service._move_to_accuracy_folder("img_001", "correct")

        # 验证文件被移动
        target_file = original_dir / "correct" / "img_001.jpg"
        assert target_file.exists()
        assert not original_file.exists()

    def test_move_to_accuracy_folder_file_not_exists(self, mock_service, tmp_path, caplog):
        """测试：移动文件到准确性文件夹（文件不存在，应记录警告）"""
        # 准备
        storage_path = tmp_path / "uploads"
        storage_path.mkdir()

        mock_service.storage.base_path = storage_path
        mock_service.repository.get_by_id.return_value = {
            "image_id": "img_001",
            "file_path": "2025-11-13/img_001.jpg"
        }

        # 执行（不应抛出异常）
        mock_service._move_to_accuracy_folder("img_001", "correct")

        # 验证记录了警告
        assert "原文件不存在" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
