"""
知识库加载器自定义异常

功能：
- 定义知识库加载过程中的异常类型
- 提供清晰的错误信息和调试提示

异常清单：
- KnowledgeBaseError: 知识库基础异常
- KnowledgeBaseNotFoundError: 知识库文件或目录不存在
- KnowledgeBaseLoadError: 知识库加载失败
- KnowledgeBaseValidationError: 知识库数据验证失败
"""


class KnowledgeBaseError(Exception):
    """
    知识库基础异常

    所有知识库相关异常的基类
    """
    pass


class KnowledgeBaseNotFoundError(KnowledgeBaseError):
    """
    知识库文件或目录不存在异常

    使用场景：
    - 知识库根目录不存在
    - 疾病本体目录不存在
    - 特征本体文件不存在
    - 特定疾病文件不存在

    示例：
    ```python
    raise KnowledgeBaseNotFoundError(
        f"疾病知识库目录不存在: {diseases_path}"
    )
    ```
    """
    pass


class KnowledgeBaseLoadError(KnowledgeBaseError):
    """
    知识库加载失败异常

    使用场景：
    - JSON文件格式错误
    - JSON文件编码错误
    - 文件读取权限不足

    示例：
    ```python
    raise KnowledgeBaseLoadError(
        f"疾病文件加载失败: {json_file.name}, 原因: {e}"
    )
    ```
    """
    pass


class KnowledgeBaseValidationError(KnowledgeBaseError):
    """
    知识库数据验证失败异常

    使用场景：
    - Pydantic模型验证失败
    - 必填字段缺失
    - 字段类型不匹配
    - 字段值不符合约束

    示例：
    ```python
    raise KnowledgeBaseValidationError(
        f"疾病文件验证失败: {json_file.name}, 原因: {e}"
    )
    ```
    """
    pass


def main():
    """
    知识库异常使用示例

    演示如何：
    1. 抛出和捕获知识库异常
    2. 使用异常处理流程
    3. 提供清晰的错误信息
    """
    from pathlib import Path

    print("=" * 80)
    print("知识库异常使用示例")
    print("=" * 80)

    # 1. 捕获知识库不存在异常
    print("\n[示例1] 捕获知识库不存在异常")
    try:
        kb_path = Path("/non/exist/path")
        if not kb_path.exists():
            raise KnowledgeBaseNotFoundError(f"知识库目录不存在: {kb_path}")
    except KnowledgeBaseNotFoundError as e:
        print(f"  [捕获异常] {type(e).__name__}: {e}")

    # 2. 捕获知识库加载失败异常
    print("\n[示例2] 捕获知识库加载失败异常")
    try:
        json_file = "invalid.json"
        raise KnowledgeBaseLoadError(f"JSON文件格式错误: {json_file}")
    except KnowledgeBaseLoadError as e:
        print(f"  [捕获异常] {type(e).__name__}: {e}")

    # 3. 捕获知识库验证失败异常
    print("\n[示例3] 捕获知识库验证失败异常")
    try:
        raise KnowledgeBaseValidationError("必填字段 'disease_id' 缺失")
    except KnowledgeBaseValidationError as e:
        print(f"  [捕获异常] {type(e).__name__}: {e}")

    # 4. 使用基础异常捕获所有知识库异常
    print("\n[示例4] 使用基础异常捕获所有知识库异常")
    try:
        raise KnowledgeBaseNotFoundError("测试异常")
    except KnowledgeBaseError as e:
        print(f"  [捕获异常] {type(e).__name__}: {e}")
        print(f"  [异常类型] 是否为KnowledgeBaseError子类: {isinstance(e, KnowledgeBaseError)}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
