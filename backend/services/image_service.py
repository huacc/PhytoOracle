"""
图片服务 (ImageService)

功能：
- 实现图片保存和元数据管理
- 支持准确性标注和图片查询
- 集成LocalImageStorage和ImageRepository
- 实现软删除机制

实现阶段：P3.6

架构说明：
- 属于应用服务层（Application Service Layer）
- 封装P2.6的LocalImageStorage和ImageRepository
- 被API层（P4）调用

作者：AI Python Architect
日期：2025-11-13
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.infrastructure.storage.local_storage import LocalImageStorage
from backend.infrastructure.persistence.repositories.image_repo import (
    ImageRepository,
    ImageRepositoryException
)
from backend.infrastructure.storage.storage_exceptions import StorageException


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageServiceException(Exception):
    """
    图片服务异常基类
    """
    pass


class ImageService:
    """
    图片服务类

    核心功能：
    1. 图片保存（save_image方法）
    2. 图片元数据持久化（调用ImageRepository）
    3. 准确性标注（update_accuracy_label方法）
    4. 图片查询（query_images方法）
    5. 图片删除（delete_image方法，软删除）

    架构说明：
    - 属于应用服务层（Application Service Layer）
    - 依赖基础设施层的 LocalImageStorage 和 ImageRepository
    - 被 API 层调用

    使用示例：
    ```python
    from pathlib import Path
    from backend.services.image_service import ImageService

    # 初始化服务
    storage_path = Path("uploads")
    db_path = Path("data/images.db")
    service = ImageService(storage_path, db_path)

    # 保存图片
    image_bytes = open("rose.jpg", "rb").read()
    result = service.save_image(
        image_bytes=image_bytes,
        flower_genus="Rosa",
        diagnosis_id="diag_20251113_001",
        disease_id="rose_black_spot"
    )
    print(f"图片已保存: {result['image_id']}")

    # 查询图片
    images = service.query_images(flower_genus="Rosa")
    ```
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        db_path: Optional[Path] = None
    ):
        """
        初始化图片服务

        Args:
            storage_path: 图片存储路径（默认：backend/uploads）
            db_path: 数据库路径（默认：backend/data/images.db）

        Raises:
            ImageServiceException: 初始化失败
        """
        # 默认路径
        if storage_path is None:
            project_root = Path(__file__).resolve().parent.parent
            storage_path = project_root / "uploads"

        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent
            db_path = project_root / "data" / "images.db"

        # 初始化LocalImageStorage
        try:
            self.storage = LocalImageStorage(str(storage_path))
            logger.info(f"LocalImageStorage 初始化完成: {storage_path}")
        except StorageException as e:
            logger.error(f"LocalImageStorage 初始化失败: {e}")
            raise ImageServiceException(f"存储初始化失败: {e}")

        # 初始化ImageRepository
        try:
            self.repository = ImageRepository(db_path)
            logger.info(f"ImageRepository 初始化完成: {db_path}")
        except ImageRepositoryException as e:
            logger.error(f"ImageRepository 初始化失败: {e}")
            raise ImageServiceException(f"数据库初始化失败: {e}")

        logger.info("ImageService 初始化完成")

    def save_image(
        self,
        image_bytes: bytes,
        flower_genus: Optional[str] = None,
        diagnosis_id: Optional[str] = None,
        disease_id: Optional[str] = None,
        disease_name: Optional[str] = None,
        confidence_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存图片和元数据

        Args:
            image_bytes: 图片字节数据
            flower_genus: 花卉种属（可选）
            diagnosis_id: 诊断ID（可选）
            disease_id: 疾病ID（可选）
            disease_name: 疾病名称（可选）
            confidence_level: 置信度级别（可选）

        Returns:
            Dict[str, Any]: 保存结果
            ```python
            {
                "image_id": "img_20251113_001",
                "file_path": "/uploads/2025-11-13/img_20251113_001.jpg",
                "full_path": "/absolute/path/to/uploads/2025-11-13/img_20251113_001.jpg"
            }
            ```

        Raises:
            ImageServiceException: 保存失败

        使用示例：
        ```python
        with open("rose.jpg", "rb") as f:
            image_bytes = f.read()

        result = service.save_image(
            image_bytes=image_bytes,
            flower_genus="Rosa",
            diagnosis_id="diag_20251113_001",
            disease_id="rose_black_spot",
            disease_name="玫瑰黑斑病",
            confidence_level="confirmed"
        )
        ```
        """
        logger.info("开始保存图片和元数据")

        try:
            # 1. 生成图片ID
            image_id = self._generate_image_id()
            logger.info(f"  生成图片ID: {image_id}")

            # 2. 保存图片到本地存储（使用image_id作为文件名）
            save_result = self.storage.save_image(
                image_bytes=image_bytes,
                filename=f"{image_id}.jpg"
            )
            logger.info(f"  图片保存成功: {save_result['relative_path']}")

            # 3. 保存元数据到数据库
            image_data = {
                "image_id": image_id,
                "file_path": save_result["relative_path"],
                "flower_genus": flower_genus,
                "diagnosis_id": diagnosis_id,
                "disease_id": disease_id,
                "disease_name": disease_name,
                "confidence_level": confidence_level
            }
            self.repository.save(image_data)
            logger.info(f"  元数据保存成功")

            # 4. 返回结果
            result = {
                "image_id": image_id,
                "file_path": save_result["relative_path"],
                "full_path": save_result["full_path"]
            }

            logger.info(f"图片和元数据保存完成: {image_id}")
            return result

        except StorageException as e:
            logger.error(f"图片保存失败: {e}")
            raise ImageServiceException(f"图片保存失败: {e}")
        except ImageRepositoryException as e:
            logger.error(f"元数据保存失败: {e}")
            raise ImageServiceException(f"元数据保存失败: {e}")
        except Exception as e:
            logger.error(f"保存失败（未知错误）: {e}")
            raise ImageServiceException(f"保存失败: {e}")

    def update_accuracy_label(
        self,
        image_id: str,
        is_accurate: str
    ) -> bool:
        """
        更新准确性标签

        用于用户标注诊断结果的准确性，实现主动学习反馈循环

        Args:
            image_id: 图片ID
            is_accurate: 准确性标签（'correct' / 'incorrect' / 'unknown'）

        Returns:
            bool: True if updated, False if not found

        Raises:
            ImageServiceException: 更新失败

        使用示例：
        ```python
        # 标记诊断结果为正确
        updated = service.update_accuracy_label("img_20251113_001", "correct")
        if updated:
            print("标注成功")

        # 标记诊断结果为错误（需要人工审核）
        updated = service.update_accuracy_label("img_20251113_002", "incorrect")
        ```
        """
        logger.info(f"更新准确性标签: {image_id} -> {is_accurate}")

        # 验证准确性标签
        valid_labels = ["correct", "incorrect", "unknown"]
        if is_accurate not in valid_labels:
            raise ImageServiceException(
                f"无效的准确性标签: {is_accurate}，有效值：{valid_labels}"
            )

        try:
            # 更新数据库中的准确性标签
            updated = self.repository.update_accuracy_label(image_id, is_accurate)

            # 如果准确性标签是correct/incorrect，移动文件到对应文件夹
            if updated and is_accurate in ["correct", "incorrect"]:
                self._move_to_accuracy_folder(image_id, is_accurate)

            return updated

        except ImageRepositoryException as e:
            logger.error(f"更新准确性标签失败: {e}")
            raise ImageServiceException(f"更新准确性标签失败: {e}")
        except Exception as e:
            logger.error(f"更新准确性标签失败（未知错误）: {e}")
            raise ImageServiceException(f"更新准确性标签失败: {e}")

    def query_images(
        self,
        flower_genus: Optional[str] = None,
        is_accurate: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        查询图片元数据

        支持按花卉属、准确性、日期范围筛选

        Args:
            flower_genus: 花卉种属（可选）
            is_accurate: 准确性标签（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            List[Dict[str, Any]]: 图片元数据列表

        Raises:
            ImageServiceException: 查询失败

        使用示例：
        ```python
        # 查询玫瑰属的所有正确诊断图片
        images = service.query_images(flower_genus="Rosa", is_accurate="correct")
        for img in images:
            print(f"{img['image_id']}: {img['disease_name']}")

        # 查询某日期范围内的所有图片
        images = service.query_images(
            start_date=datetime(2025, 11, 1),
            end_date=datetime(2025, 11, 30)
        )
        ```
        """
        logger.info("查询图片元数据")

        try:
            images = self.repository.query(
                flower_genus=flower_genus,
                is_accurate=is_accurate,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(f"查询完成：找到 {len(images)} 条记录")
            return images

        except ImageRepositoryException as e:
            logger.error(f"查询失败: {e}")
            raise ImageServiceException(f"查询失败: {e}")

    def delete_image(self, image_id: str) -> bool:
        """
        删除图片（软删除）

        Args:
            image_id: 图片ID

        Returns:
            bool: True if deleted, False if not found

        Raises:
            ImageServiceException: 删除失败

        使用示例：
        ```python
        deleted = service.delete_image("img_20251113_001")
        if deleted:
            print("删除成功")
        else:
            print("图片不存在")
        ```
        """
        logger.info(f"删除图片: {image_id}")

        try:
            # 软删除数据库记录
            deleted = self.repository.soft_delete(image_id)

            # 注意：这里不删除物理文件，仅软删除数据库记录
            # 物理文件可以通过定期清理脚本删除

            if deleted:
                logger.info(f"图片删除成功: {image_id}")
            else:
                logger.warning(f"图片不存在或已删除: {image_id}")

            return deleted

        except ImageRepositoryException as e:
            logger.error(f"删除失败: {e}")
            raise ImageServiceException(f"删除失败: {e}")

    def _generate_image_id(self) -> str:
        """
        生成图片ID

        格式：img_YYYYMMDD_NNN

        Returns:
            str: 图片ID
        """
        from datetime import datetime
        import random

        today = datetime.now().strftime("%Y%m%d")
        seq = random.randint(0, 999)
        return f"img_{today}_{seq:03d}"

    def _move_to_accuracy_folder(
        self,
        image_id: str,
        is_accurate: str
    ) -> None:
        """
        将图片移动到准确性文件夹

        Args:
            image_id: 图片ID
            is_accurate: 准确性标签（'correct' / 'incorrect'）

        Raises:
            ImageServiceException: 移动失败
        """
        try:
            # 获取图片元数据
            image_data = self.repository.get_by_id(image_id)
            if not image_data:
                raise ImageServiceException(f"图片不存在: {image_id}")

            # 获取原文件路径
            original_path = Path(image_data["file_path"])
            original_full_path = self.storage.base_path / original_path

            if not original_full_path.exists():
                logger.warning(f"原文件不存在，跳过移动: {original_full_path}")
                return

            # 构建目标路径（相对于storage根目录）
            target_dir = original_path.parent / is_accurate
            target_path = target_dir / original_path.name

            # 确保目标目录存在
            target_full_dir = self.storage.base_path / target_dir
            target_full_dir.mkdir(parents=True, exist_ok=True)

            # 移动文件
            target_full_path = self.storage.base_path / target_path
            original_full_path.rename(target_full_path)

            logger.info(f"文件移动成功: {original_path} -> {target_path}")

            # 更新数据库中的文件路径
            # TODO: 实现update_file_path方法（可选）

        except Exception as e:
            logger.error(f"移动文件失败: {e}")
            # 不抛出异常，允许继续执行


def main():
    """
    ImageService 使用示例

    演示如何：
    1. 初始化 ImageService
    2. 保存图片和元数据
    3. 查询图片
    4. 更新准确性标签
    5. 删除图片
    """
    print("=" * 80)
    print("ImageService 使用示例")
    print("=" * 80)

    # 1. 初始化服务
    print("\n[示例1] 初始化 ImageService")
    project_root = Path(__file__).resolve().parent.parent
    storage_path = project_root / "uploads"
    db_path = project_root / "data" / "test_images.db"
    print(f"  存储路径: {storage_path}")
    print(f"  数据库路径: {db_path}")

    try:
        service = ImageService(storage_path, db_path)
        print("  [OK] ImageService 初始化完成")
    except ImageServiceException as e:
        print(f"  [ERROR] 初始化失败: {e}")
        return

    # 2. 保存图片（使用测试图片）
    print("\n[示例2] 保存图片和元数据")
    print("  提示: 需要真实图片文件进行测试")
    print("  [SKIP] 跳过实际保存（示例代码）")
    # 示例代码：
    # with open("rose.jpg", "rb") as f:
    #     image_bytes = f.read()
    # result = service.save_image(
    #     image_bytes=image_bytes,
    #     flower_genus="Rosa",
    #     diagnosis_id="diag_20251113_001",
    #     disease_id="rose_black_spot",
    #     disease_name="玫瑰黑斑病",
    #     confidence_level="confirmed"
    # )
    # print(f"  [OK] 保存成功: {result['image_id']}")

    # 3. 查询图片
    print("\n[示例3] 查询图片（按花卉种属）")
    try:
        images = service.query_images(flower_genus="Rosa")
        print(f"  [OK] 找到 {len(images)} 条记录")
        for img in images[:3]:  # 显示前3条
            print(f"    - {img['image_id']}: {img.get('disease_name', 'N/A')}")
    except ImageServiceException as e:
        print(f"  [INFO] 查询失败（可能无数据）: {e}")

    # 4. 更新准确性标签
    print("\n[示例4] 更新准确性标签")
    print("  提示: 需要实际图片ID进行测试")
    print("  [SKIP] 跳过实际更新（示例代码）")
    # 示例代码：
    # try:
    #     updated = service.update_accuracy_label("img_20251113_001", "correct")
    #     if updated:
    #         print("  [OK] 更新成功")
    #     else:
    #         print("  [INFO] 图片不存在")
    # except ImageServiceException as e:
    #     print(f"  [ERROR] 更新失败: {e}")

    # 5. 删除图片
    print("\n[示例5] 删除图片（软删除）")
    print("  提示: 需要实际图片ID进行测试")
    print("  [SKIP] 跳过实际删除（示例代码）")
    # 示例代码：
    # try:
    #     deleted = service.delete_image("img_20251113_001")
    #     if deleted:
    #         print("  [OK] 删除成功")
    #     else:
    #         print("  [INFO] 图片不存在")
    # except ImageServiceException as e:
    #     print(f"  [ERROR] 删除失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
