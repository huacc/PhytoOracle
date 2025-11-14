"""
图片Repository（图片元数据持久化）

功能：
- 实现图片元数据的CRUD操作
- 支持SQLite数据库持久化
- 提供按花卉属、准确性、日期范围的查询功能
- 实现软删除机制

实现阶段：P3.6

架构说明：
- 属于基础设施层（Infrastructure Layer）
- 遵循Repository模式
- 被ImageService调用

作者：AI Python Architect
日期：2025-11-13
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageRepositoryException(Exception):
    """
    图片Repository异常基类
    """
    pass


class ImageRepository:
    """
    图片Repository类

    核心功能：
    1. 保存图片元数据（save方法）
    2. 查询图片元数据（query方法）
    3. 更新准确性标签（update_accuracy_label方法）
    4. 软删除图片（soft_delete方法）
    5. 按ID查询单个图片（get_by_id方法）

    数据库表结构（P3.9更新）：
    ```sql
    CREATE TABLE images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id TEXT UNIQUE NOT NULL,
        file_path TEXT NOT NULL,
        flower_genus TEXT,
        diagnosis_id TEXT,
        disease_id TEXT,
        disease_name TEXT,
        confidence_level TEXT,
        is_accurate TEXT,  -- 'correct' / 'incorrect' / 'unknown'
        user_feedback TEXT,  -- P3.9新增：用户反馈文本（可选）
        uploaded_at TEXT NOT NULL,
        is_deleted INTEGER DEFAULT 0,
        deleted_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ```

    使用示例：
    ```python
    # 初始化Repository
    db_path = Path("data/images.db")
    repo = ImageRepository(db_path)

    # 保存图片元数据
    image_data = {
        "image_id": "img_20251113_001",
        "file_path": "/uploads/2025-11-13/rose_001.jpg",
        "flower_genus": "Rosa",
        "diagnosis_id": "diag_20251113_001",
        "disease_id": "rose_black_spot",
        "disease_name": "玫瑰黑斑病",
        "confidence_level": "confirmed"
    }
    repo.save(image_data)

    # 查询图片
    images = repo.query(flower_genus="Rosa", is_accurate="correct")
    ```
    """

    def __init__(self, db_path: Path):
        """
        初始化ImageRepository

        Args:
            db_path: SQLite数据库文件路径

        Raises:
            ImageRepositoryException: 数据库初始化失败
        """
        self.db_path = db_path

        # 确保数据库目录存在
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建数据库目录: {db_dir}")

        # 初始化数据库表
        self._init_database()

        logger.info(f"ImageRepository 初始化完成，数据库路径: {self.db_path}")

    def _init_database(self) -> None:
        """
        初始化数据库表

        创建 images 表（如果不存在）
        如果表已存在，自动添加P3.9新增的user_feedback列（如果尚未添加）

        Raises:
            ImageRepositoryException: 数据库初始化失败
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 创建images表（如果不存在）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_id TEXT UNIQUE NOT NULL,
                        file_path TEXT NOT NULL,
                        flower_genus TEXT,
                        diagnosis_id TEXT,
                        disease_id TEXT,
                        disease_name TEXT,
                        confidence_level TEXT,
                        is_accurate TEXT DEFAULT 'unknown',
                        user_feedback TEXT,
                        uploaded_at TEXT NOT NULL,
                        is_deleted INTEGER DEFAULT 0,
                        deleted_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # P3.9 Migration: 如果表已存在但没有user_feedback列，则添加该列
                # 检查列是否存在
                cursor.execute("PRAGMA table_info(images)")
                columns = [column[1] for column in cursor.fetchall()]

                if "user_feedback" not in columns:
                    logger.info("检测到旧版本数据库，正在添加user_feedback列...")
                    cursor.execute("""
                        ALTER TABLE images ADD COLUMN user_feedback TEXT
                    """)
                    logger.info("user_feedback列添加成功")

                conn.commit()
                logger.info("数据库表初始化完成")

        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise ImageRepositoryException(f"数据库初始化失败: {e}")

    @contextmanager
    def _get_connection(self):
        """
        获取数据库连接（上下文管理器）

        Yields:
            sqlite3.Connection: 数据库连接

        Raises:
            ImageRepositoryException: 数据库连接失败
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # 支持字典式访问
            yield conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise ImageRepositoryException(f"数据库连接失败: {e}")
        finally:
            conn.close()

    def save(self, image_data: Dict[str, Any]) -> str:
        """
        保存图片元数据

        Args:
            image_data: 图片元数据字典
            ```python
            {
                "image_id": "img_20251113_001",
                "file_path": "/uploads/2025-11-13/rose_001.jpg",
                "flower_genus": "Rosa",
                "diagnosis_id": "diag_20251113_001",
                "disease_id": "rose_black_spot",
                "disease_name": "玫瑰黑斑病",
                "confidence_level": "confirmed"
            }
            ```

        Returns:
            str: 图片ID

        Raises:
            ImageRepositoryException: 保存失败
        """
        try:
            now = datetime.now().isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO images (
                        image_id, file_path, flower_genus, diagnosis_id,
                        disease_id, disease_name, confidence_level,
                        uploaded_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    image_data["image_id"],
                    image_data["file_path"],
                    image_data.get("flower_genus"),
                    image_data.get("diagnosis_id"),
                    image_data.get("disease_id"),
                    image_data.get("disease_name"),
                    image_data.get("confidence_level"),
                    now,
                    now,
                    now
                ))
                conn.commit()

            logger.info(f"保存图片元数据成功: {image_data['image_id']}")
            return image_data["image_id"]

        except sqlite3.IntegrityError as e:
            logger.error(f"保存失败（唯一约束冲突）: {e}")
            raise ImageRepositoryException(f"图片ID已存在: {image_data['image_id']}")
        except sqlite3.Error as e:
            logger.error(f"保存失败: {e}")
            raise ImageRepositoryException(f"保存失败: {e}")

    def query(
        self,
        flower_genus: Optional[str] = None,
        is_accurate: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        查询图片元数据

        支持多条件组合查询

        Args:
            flower_genus: 花卉种属（可选）
            is_accurate: 准确性标签（'correct' / 'incorrect' / 'unknown'，可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            include_deleted: 是否包含已删除的图片（默认 False）

        Returns:
            List[Dict[str, Any]]: 图片元数据列表

        Raises:
            ImageRepositoryException: 查询失败

        使用示例：
        ```python
        # 查询玫瑰属的所有正确诊断图片
        images = repo.query(flower_genus="Rosa", is_accurate="correct")

        # 查询某日期范围内的所有图片
        images = repo.query(
            start_date=datetime(2025, 11, 1),
            end_date=datetime(2025, 11, 30)
        )
        ```
        """
        try:
            # 构建SQL查询
            sql = "SELECT * FROM images WHERE 1=1"
            params = []

            if not include_deleted:
                sql += " AND is_deleted = 0"

            if flower_genus:
                sql += " AND flower_genus = ?"
                params.append(flower_genus)

            if is_accurate:
                sql += " AND is_accurate = ?"
                params.append(is_accurate)

            if start_date:
                sql += " AND uploaded_at >= ?"
                params.append(start_date.isoformat())

            if end_date:
                sql += " AND uploaded_at <= ?"
                params.append(end_date.isoformat())

            sql += " ORDER BY uploaded_at DESC"

            # 执行查询
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            # 转换为字典列表
            results = [dict(row) for row in rows]
            logger.info(f"查询图片元数据：找到 {len(results)} 条记录")

            return results

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}")
            raise ImageRepositoryException(f"查询失败: {e}")

    def get_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        按ID查询单个图片元数据

        Args:
            image_id: 图片ID

        Returns:
            Dict[str, Any]: 图片元数据（如果找到）
            None: 如果图片不存在

        Raises:
            ImageRepositoryException: 查询失败
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM images
                    WHERE image_id = ? AND is_deleted = 0
                """, (image_id,))
                row = cursor.fetchone()

            if row:
                result = dict(row)
                logger.info(f"查询图片 {image_id}：找到")
                return result
            else:
                logger.info(f"查询图片 {image_id}：未找到")
                return None

        except sqlite3.Error as e:
            logger.error(f"查询失败: {e}")
            raise ImageRepositoryException(f"查询失败: {e}")

    def update_accuracy_label(
        self,
        image_id: str,
        is_accurate: str,
        user_feedback: Optional[str] = None
    ) -> bool:
        """
        更新准确性标签（P3.9扩展：支持用户反馈）

        Args:
            image_id: 图片ID
            is_accurate: 准确性标签（'correct' / 'incorrect' / 'unknown'）
            user_feedback: 用户反馈文本（可选，P3.9新增）

        Returns:
            bool: True if updated, False if not found

        Raises:
            ImageRepositoryException: 更新失败
        """
        try:
            now = datetime.now().isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # P3.9: 如果提供了user_feedback，则同时更新
                if user_feedback is not None:
                    cursor.execute("""
                        UPDATE images
                        SET is_accurate = ?, user_feedback = ?, updated_at = ?
                        WHERE image_id = ? AND is_deleted = 0
                    """, (is_accurate, user_feedback, now, image_id))
                else:
                    cursor.execute("""
                        UPDATE images
                        SET is_accurate = ?, updated_at = ?
                        WHERE image_id = ? AND is_deleted = 0
                    """, (is_accurate, now, image_id))

                conn.commit()

                updated = cursor.rowcount > 0

            if updated:
                feedback_info = f" (反馈: {user_feedback[:20]}...)" if user_feedback else ""
                logger.info(f"更新准确性标签成功: {image_id} -> {is_accurate}{feedback_info}")
            else:
                logger.warning(f"更新失败：图片 {image_id} 不存在或已删除")

            return updated

        except sqlite3.Error as e:
            logger.error(f"更新失败: {e}")
            raise ImageRepositoryException(f"更新失败: {e}")

    def soft_delete(self, image_id: str) -> bool:
        """
        软删除图片

        Args:
            image_id: 图片ID

        Returns:
            bool: True if deleted, False if not found

        Raises:
            ImageRepositoryException: 删除失败
        """
        try:
            now = datetime.now().isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE images
                    SET is_deleted = 1, deleted_at = ?, updated_at = ?
                    WHERE image_id = ? AND is_deleted = 0
                """, (now, now, image_id))
                conn.commit()

                deleted = cursor.rowcount > 0

            if deleted:
                logger.info(f"软删除图片成功: {image_id}")
            else:
                logger.warning(f"删除失败：图片 {image_id} 不存在或已删除")

            return deleted

        except sqlite3.Error as e:
            logger.error(f"删除失败: {e}")
            raise ImageRepositoryException(f"删除失败: {e}")


def main():
    """
    ImageRepository 使用示例

    演示如何：
    1. 初始化Repository
    2. 保存图片元数据
    3. 查询图片
    4. 更新准确性标签
    5. 软删除图片
    """
    print("=" * 80)
    print("ImageRepository 使用示例")
    print("=" * 80)

    # 1. 初始化Repository
    print("\n[示例1] 初始化ImageRepository")
    db_path = Path("data/test_images.db")
    print(f"  数据库路径: {db_path}")

    try:
        repo = ImageRepository(db_path)
        print("  [OK] ImageRepository 初始化完成")
    except ImageRepositoryException as e:
        print(f"  [ERROR] 初始化失败: {e}")
        return

    # 2. 保存图片元数据
    print("\n[示例2] 保存图片元数据")
    image_data = {
        "image_id": "img_20251113_001",
        "file_path": "/uploads/2025-11-13/rose_001.jpg",
        "flower_genus": "Rosa",
        "diagnosis_id": "diag_20251113_001",
        "disease_id": "rose_black_spot",
        "disease_name": "玫瑰黑斑病",
        "confidence_level": "confirmed"
    }

    try:
        image_id = repo.save(image_data)
        print(f"  [OK] 保存成功，图片ID: {image_id}")
    except ImageRepositoryException as e:
        print(f"  [INFO] 保存失败（可能已存在）: {e}")

    # 3. 查询图片
    print("\n[示例3] 查询图片（按花卉种属）")
    try:
        images = repo.query(flower_genus="Rosa")
        print(f"  [OK] 找到 {len(images)} 条记录")
        for img in images[:3]:  # 显示前3条
            print(f"    - {img['image_id']}: {img['disease_name']}")
    except ImageRepositoryException as e:
        print(f"  [ERROR] 查询失败: {e}")

    # 4. 按ID查询单个图片
    print("\n[示例4] 按ID查询单个图片")
    try:
        img = repo.get_by_id("img_20251113_001")
        if img:
            print(f"  [OK] 找到图片")
            print(f"    - 图片ID: {img['image_id']}")
            print(f"    - 文件路径: {img['file_path']}")
            print(f"    - 种属: {img['flower_genus']}")
            print(f"    - 疾病: {img['disease_name']}")
        else:
            print("  [INFO] 图片不存在")
    except ImageRepositoryException as e:
        print(f"  [ERROR] 查询失败: {e}")

    # 5. 更新准确性标签
    print("\n[示例5] 更新准确性标签")
    try:
        updated = repo.update_accuracy_label("img_20251113_001", "correct")
        if updated:
            print("  [OK] 更新成功")
        else:
            print("  [INFO] 图片不存在或已删除")
    except ImageRepositoryException as e:
        print(f"  [ERROR] 更新失败: {e}")

    # 6. 软删除图片
    print("\n[示例6] 软删除图片")
    try:
        deleted = repo.soft_delete("img_20251113_001")
        if deleted:
            print("  [OK] 删除成功")
        else:
            print("  [INFO] 图片不存在或已删除")
    except ImageRepositoryException as e:
        print(f"  [ERROR] 删除失败: {e}")

    # 7. 验证删除（默认查询不应包含已删除的记录）
    print("\n[示例7] 验证删除（查询不包含已删除记录）")
    try:
        img = repo.get_by_id("img_20251113_001")
        if img:
            print("  [FAIL] 软删除失败：仍能查询到记录")
        else:
            print("  [OK] 软删除成功：无法查询到记录")
    except ImageRepositoryException as e:
        print(f"  [ERROR] 查询失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
