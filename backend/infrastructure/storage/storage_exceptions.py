"""
存储异常（Storage Exceptions）

功能：
- 定义本地图片存储相关的自定义异常
- 提供详细的错误信息和上下文
- 便于异常处理和调试

异常清单：
- StorageException: 存储基础异常类
- StorageConfigError: 配置错误异常
- ImageSaveError: 图片保存失败异常
- ImageMoveError: 图片移动失败异常
- ImageDeleteError: 图片删除失败异常
- PathGenerationError: 路径生成错误异常
- InvalidImageFormat: 无效图片格式异常
- ImageTooLargeError: 图片过大异常
"""


class StorageException(Exception):
    """
    存储基础异常类

    所有存储相关的异常都继承自此类

    属性:
        message: 错误信息
        context: 错误上下文（可选）

    使用示例:
    ```python
    raise StorageException("存储操作失败", context={"operation": "save"})
    ```
    """

    def __init__(self, message: str, context: dict = None):
        """
        初始化存储异常

        Args:
            message: 错误信息
            context: 错误上下文，包含额外的调试信息
        """
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self):
        """返回详细的错误信息"""
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"{self.message} (Context: {context_str})"
        return self.message


class StorageConfigError(StorageException):
    """
    配置错误异常

    当存储配置文件缺失、格式错误或配置项无效时抛出

    使用示例:
    ```python
    raise StorageConfigError(
        "配置文件不存在",
        context={"config_path": "/path/to/config.json"}
    )
    ```
    """
    pass


class ImageSaveError(StorageException):
    """
    图片保存失败异常

    当图片保存到文件系统失败时抛出

    使用示例:
    ```python
    raise ImageSaveError(
        "无法保存图片文件",
        context={
            "file_path": "/path/to/image.jpg",
            "reason": "磁盘空间不足"
        }
    )
    ```
    """
    pass


class ImageMoveError(StorageException):
    """
    图片移动失败异常

    当图片从一个位置移动到另一个位置失败时抛出
    （例如：准确性标注时移动图片）

    使用示例:
    ```python
    raise ImageMoveError(
        "无法移动图片文件",
        context={
            "old_path": "/path/to/old.jpg",
            "new_path": "/path/to/new.jpg",
            "reason": "目标路径已存在"
        }
    )
    ```
    """
    pass


class ImageDeleteError(StorageException):
    """
    图片删除失败异常

    当图片删除操作失败时抛出

    使用示例:
    ```python
    raise ImageDeleteError(
        "无法删除图片文件",
        context={
            "file_path": "/path/to/image.jpg",
            "reason": "文件不存在"
        }
    )
    ```
    """
    pass


class PathGenerationError(StorageException):
    """
    路径生成错误异常

    当文件路径生成失败时抛出
    （例如：参数无效、路径格式错误等）

    使用示例:
    ```python
    raise PathGenerationError(
        "无法生成文件路径",
        context={
            "diagnosis_id": "invalid_id",
            "reason": "诊断ID格式不正确"
        }
    )
    ```
    """
    pass


class InvalidImageFormat(StorageException):
    """
    无效图片格式异常

    当图片格式不被支持时抛出
    （例如：不支持的文件扩展名、损坏的图片文件等）

    使用示例:
    ```python
    raise InvalidImageFormat(
        "不支持的图片格式",
        context={
            "format": "bmp",
            "allowed_formats": ["jpg", "jpeg", "png"]
        }
    )
    ```
    """
    pass


class ImageTooLargeError(StorageException):
    """
    图片过大异常

    当图片文件大小超过配置的最大限制时抛出

    使用示例:
    ```python
    raise ImageTooLargeError(
        "图片大小超过限制",
        context={
            "image_size": 15 * 1024 * 1024,  # 15MB
            "max_size": 10 * 1024 * 1024     # 10MB
        }
    )
    ```
    """
    pass


def main():
    """
    存储异常使用示例

    演示如何：
    1. 抛出不同类型的异常
    2. 捕获异常并获取上下文信息
    3. 在实际场景中使用异常
    """
    print("=" * 80)
    print("存储异常（Storage Exceptions）使用示例")
    print("=" * 80)

    # 示例1：基础异常
    print("\n[示例1] StorageException - 基础异常")
    try:
        raise StorageException(
            "存储操作失败",
            context={"operation": "save", "file": "test.jpg"}
        )
    except StorageException as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  错误信息: {e.message}")
        print(f"  错误上下文: {e.context}")
        print(f"  完整信息: {str(e)}")

    # 示例2：配置错误异常
    print("\n[示例2] StorageConfigError - 配置错误异常")
    try:
        raise StorageConfigError(
            "配置文件不存在",
            context={"config_path": "/path/to/config.json"}
        )
    except StorageConfigError as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  完整信息: {str(e)}")

    # 示例3：图片保存失败异常
    print("\n[示例3] ImageSaveError - 图片保存失败异常")
    try:
        raise ImageSaveError(
            "无法保存图片文件",
            context={
                "file_path": "/storage/images/unlabeled/rosa/2025-11/13/diag_20251113_001.jpg",
                "reason": "磁盘空间不足"
            }
        )
    except ImageSaveError as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  完整信息: {str(e)}")

    # 示例4：图片移动失败异常
    print("\n[示例4] ImageMoveError - 图片移动失败异常")
    try:
        raise ImageMoveError(
            "无法移动图片文件",
            context={
                "old_path": "/storage/images/unlabeled/rosa/2025-11/13/diag_20251113_001.jpg",
                "new_path": "/storage/images/correct/rosa/2025-11/13/diag_20251113_001.jpg",
                "reason": "目标路径已存在"
            }
        )
    except ImageMoveError as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  完整信息: {str(e)}")

    # 示例5：路径生成错误异常
    print("\n[示例5] PathGenerationError - 路径生成错误异常")
    try:
        raise PathGenerationError(
            "无法生成文件路径",
            context={
                "diagnosis_id": "invalid_id_format",
                "reason": "诊断ID格式不正确（应为diag_YYYYMMDD_NNN）"
            }
        )
    except PathGenerationError as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  完整信息: {str(e)}")

    # 示例6：无效图片格式异常
    print("\n[示例6] InvalidImageFormat - 无效图片格式异常")
    try:
        raise InvalidImageFormat(
            "不支持的图片格式",
            context={
                "format": "bmp",
                "allowed_formats": ["jpg", "jpeg", "png"]
            }
        )
    except InvalidImageFormat as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  完整信息: {str(e)}")

    # 示例7：图片过大异常
    print("\n[示例7] ImageTooLargeError - 图片过大异常")
    try:
        raise ImageTooLargeError(
            "图片大小超过限制",
            context={
                "image_size_mb": 15.5,
                "max_size_mb": 10.0
            }
        )
    except ImageTooLargeError as e:
        print(f"  捕获异常: {type(e).__name__}")
        print(f"  完整信息: {str(e)}")

    # 示例8：实际场景 - 图片保存流程中的异常处理
    print("\n[示例8] 实际场景 - 图片保存流程中的异常处理")

    def simulate_save_image(image_bytes: bytes, diagnosis_id: str):
        """模拟图片保存流程"""
        # 检查文件大小
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB
            raise ImageTooLargeError(
                "图片大小超过限制",
                context={
                    "image_size": len(image_bytes),
                    "max_size": 10 * 1024 * 1024
                }
            )

        # 检查诊断ID格式
        import re
        if not re.match(r"^diag_\d{8}_\d{3}$", diagnosis_id):
            raise PathGenerationError(
                "无法生成文件路径",
                context={
                    "diagnosis_id": diagnosis_id,
                    "reason": "诊断ID格式不正确"
                }
            )

        return f"/storage/images/unlabeled/rosa/2025-11/13/{diagnosis_id}.jpg"

    # 测试正常情况
    try:
        image_bytes = b"fake_image_data"
        diagnosis_id = "diag_20251113_001"
        saved_path = simulate_save_image(image_bytes, diagnosis_id)
        print(f"  [成功] 图片保存成功: {saved_path}")
    except StorageException as e:
        print(f"  [失败] {type(e).__name__}: {e}")

    # 测试图片过大
    try:
        large_image_bytes = b"x" * (11 * 1024 * 1024)  # 11MB
        diagnosis_id = "diag_20251113_001"
        saved_path = simulate_save_image(large_image_bytes, diagnosis_id)
        print(f"  [成功] 图片保存成功: {saved_path}")
    except StorageException as e:
        print(f"  [失败] {type(e).__name__}: {e}")

    # 测试诊断ID格式错误
    try:
        image_bytes = b"fake_image_data"
        diagnosis_id = "invalid_id"
        saved_path = simulate_save_image(image_bytes, diagnosis_id)
        print(f"  [成功] 图片保存成功: {saved_path}")
    except StorageException as e:
        print(f"  [失败] {type(e).__name__}: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
