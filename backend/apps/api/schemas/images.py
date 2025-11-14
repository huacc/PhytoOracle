"""
图片管理API Schema模型 (P4.6 实现)

功能：
- 定义图片管理相关的API请求和响应模型
- 用于FastAPI的请求验证和响应序列化
- 遵循详细设计文档v2.0第6.7节的API协议定义

模型清单：
- ImageListRequest: 图片列表查询请求
- ImageDiagnosisInfo: 关联的诊断信息Schema
- ImageItemSchema: 单个图片信息Schema
- ImageListResponse: 图片列表分页响应
- AccuracyUpdateRequest: 准确性标注请求
- AccuracyUpdateResponse: 准确性标注响应

实现阶段：P4.6
对应设计文档：详细设计文档v2.0 第6.7节
作者：AI Python Architect
日期：2025-11-15
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ImageListRequest(BaseModel):
    """
    图片列表查询请求Schema

    用于GET /api/v1/images接口的查询参数

    字段说明：
    - start_date: 开始日期（ISO 8601格式，可选）
    - end_date: 结束日期（ISO 8601格式，可选）
    - flower_genus: 花卉种属筛选（可选）
    - has_diagnosis: 是否已诊断（true/false，可选）
    - accuracy_status: 准确性标注状态（accurate/inaccurate/not_marked，可选）
    - page: 页码（默认1）
    - page_size: 每页条数（默认50，最大100）

    对应设计文档：详细设计文档v2.0 第6.7.1节
    """
    start_date: Optional[str] = Field(
        None,
        description="开始日期（ISO 8601格式）",
        example="2025-01-01T00:00:00Z"
    )
    end_date: Optional[str] = Field(
        None,
        description="结束日期（ISO 8601格式）",
        example="2025-01-31T23:59:59Z"
    )
    flower_genus: Optional[str] = Field(
        None,
        description="花卉种属筛选",
        example="Rosa"
    )
    has_diagnosis: Optional[bool] = Field(
        None,
        description="是否已诊断（true/false）"
    )
    accuracy_status: Optional[str] = Field(
        None,
        description="准确性标注状态（accurate/inaccurate/not_marked）",
        example="accurate"
    )
    page: int = Field(
        1,
        ge=1,
        description="页码（默认1）"
    )
    page_size: int = Field(
        50,
        ge=1,
        le=100,
        description="每页条数（默认50，最大100）"
    )


class ImageDiagnosisInfo(BaseModel):
    """
    关联的诊断信息Schema

    用于ImageItemSchema中的diagnosis字段

    字段说明：
    - diagnosis_id: 诊断ID
    - disease_id: 疾病ID
    - disease_name: 疾病名称
    - level: 置信度级别（confirmed/suspected/unlikely）
    - confidence: 置信度（0-1）
    - diagnosed_at: 诊断时间（ISO 8601格式）

    对应设计文档：详细设计文档v2.0 第6.7.1节 diagnosis字段
    """
    diagnosis_id: str = Field(..., description="诊断ID")
    disease_id: str = Field(..., description="疾病ID")
    disease_name: str = Field(..., description="疾病名称")
    level: str = Field(..., description="置信度级别（confirmed/suspected/unlikely）")
    confidence: float = Field(..., ge=0, le=1, description="置信度（0-1）")
    diagnosed_at: str = Field(..., description="诊断时间（ISO 8601格式）")


class ImageItemSchema(BaseModel):
    """
    单个图片信息Schema

    用于ImageListResponse中的images数组

    字段说明：
    - image_id: 图片ID
    - image_filename: 图片文件名
    - image_path: 图片存储路径（相对路径）
    - uploaded_at: 上传时间（ISO 8601格式）
    - file_size_bytes: 文件大小（字节）
    - width: 图片宽度（像素，可选）
    - height: 图片高度（像素，可选）
    - format: 图片格式（jpg/png/heic，可选）
    - diagnosis: 关联的诊断信息（可选，如果没有诊断则为null）
    - accuracy_status: 准确性标注状态（accurate/inaccurate/not_marked）
    - accuracy_marked_at: 标注时间（ISO 8601格式，可选）
    - accuracy_marked_by: 标注人（可选）

    对应设计文档：详细设计文档v2.0 第6.7.1节 images数组元素
    """
    image_id: str = Field(..., description="图片ID")
    image_filename: str = Field(..., description="图片文件名")
    image_path: str = Field(..., description="图片存储路径（相对路径）")
    uploaded_at: str = Field(..., description="上传时间（ISO 8601格式）")
    file_size_bytes: Optional[int] = Field(None, description="文件大小（字节）")
    width: Optional[int] = Field(None, description="图片宽度（像素）")
    height: Optional[int] = Field(None, description="图片高度（像素）")
    format: Optional[str] = Field(None, description="图片格式（jpg/png/heic）")

    # 关联的诊断信息（可选）
    diagnosis: Optional[ImageDiagnosisInfo] = Field(
        None,
        description="关联的诊断信息（如果没有诊断则为null）"
    )

    # 准确性标注信息
    accuracy_status: str = Field(
        ...,
        description="准确性标注状态（accurate/inaccurate/not_marked）"
    )
    accuracy_marked_at: Optional[str] = Field(
        None,
        description="标注时间（ISO 8601格式）"
    )
    accuracy_marked_by: Optional[str] = Field(
        None,
        description="标注人"
    )


class ImageListResponse(BaseModel):
    """
    图片列表分页响应Schema

    用于GET /api/v1/images接口的响应

    字段说明：
    - total: 总记录数
    - page: 当前页码
    - page_size: 每页条数
    - images: 图片信息列表

    对应设计文档：详细设计文档v2.0 第6.7.1节
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    images: List[ImageItemSchema] = Field(
        default_factory=list,
        description="图片信息列表"
    )


class AccuracyUpdateRequest(BaseModel):
    """
    准确性标注请求Schema

    用于PATCH /api/v1/images/{image_id}/accuracy接口的请求

    字段说明：
    - accuracy_status: 准确性状态（accurate/inaccurate）
    - comment: 标注备注（可选）
    - marked_by: 标注人（可选）

    对应设计文档：详细设计文档v2.0 第6.7.2节
    """
    accuracy_status: str = Field(
        ...,
        description="准确性状态（accurate/inaccurate）",
        example="accurate"
    )
    comment: Optional[str] = Field(
        None,
        description="标注备注",
        example="诊断结果准确，症状特征识别正确"
    )
    marked_by: Optional[str] = Field(
        None,
        description="标注人",
        example="expert@example.com"
    )


class AccuracyUpdateResponse(BaseModel):
    """
    准确性标注响应Schema

    用于PATCH /api/v1/images/{image_id}/accuracy接口的响应

    字段说明：
    - image_id: 图片ID
    - accuracy_status: 准确性状态（accurate/inaccurate）
    - comment: 标注备注
    - marked_at: 标注时间（ISO 8601格式）
    - marked_by: 标注人
    - diagnosis_id: 关联的诊断ID（可选）
    - message: 提示消息

    对应设计文档：详细设计文档v2.0 第6.7.2节
    """
    image_id: str = Field(..., description="图片ID")
    accuracy_status: str = Field(..., description="准确性状态（accurate/inaccurate）")
    comment: Optional[str] = Field(None, description="标注备注")
    marked_at: str = Field(..., description="标注时间（ISO 8601格式）")
    marked_by: Optional[str] = Field(None, description="标注人")
    diagnosis_id: Optional[str] = Field(None, description="关联的诊断ID")
    message: str = Field(..., description="提示消息")


def main():
    """
    图片管理API Schema模型使用示例

    演示如何：
    1. 创建图片列表查询请求
    2. 创建图片信息Schema
    3. 创建图片列表响应
    4. 创建准确性标注请求
    5. 序列化为JSON
    """
    from datetime import datetime

    print("=" * 80)
    print("图片管理API Schema模型使用示例")
    print("=" * 80)

    # 1. 创建图片列表查询请求
    print("\n[示例1] 创建图片列表查询请求")
    list_request = ImageListRequest(
        start_date="2025-01-01T00:00:00Z",
        end_date="2025-01-31T23:59:59Z",
        flower_genus="Rosa",
        has_diagnosis=True,
        accuracy_status="accurate",
        page=1,
        page_size=50
    )
    print(f"  - start_date: {list_request.start_date}")
    print(f"  - flower_genus: {list_request.flower_genus}")
    print(f"  - page: {list_request.page}, page_size: {list_request.page_size}")

    # 2. 创建图片信息Schema
    print("\n[示例2] 创建图片信息Schema")
    image_item = ImageItemSchema(
        image_id="img_20250114_001",
        image_filename="rose_leaf_001.jpg",
        image_path="storage/images/unlabeled/rosa/2025-01/14/img_20250114_001.jpg",
        uploaded_at="2025-01-14T10:30:45Z",
        file_size_bytes=524288,
        width=1920,
        height=1080,
        format="jpg",
        diagnosis=ImageDiagnosisInfo(
            diagnosis_id="diag_20250114_001",
            disease_id="rose_black_spot",
            disease_name="玫瑰黑斑病",
            level="confirmed",
            confidence=0.92,
            diagnosed_at="2025-01-14T10:30:50Z"
        ),
        accuracy_status="accurate",
        accuracy_marked_at="2025-01-14T11:00:00Z",
        accuracy_marked_by="admin@example.com"
    )
    print(f"  - image_id: {image_item.image_id}")
    print(f"  - diagnosis: {image_item.diagnosis.disease_name if image_item.diagnosis else 'None'}")
    print(f"  - accuracy_status: {image_item.accuracy_status}")

    # 3. 创建图片列表响应
    print("\n[示例3] 创建图片列表响应")
    list_response = ImageListResponse(
        total=250,
        page=1,
        page_size=50,
        images=[image_item]
    )
    print(f"  - total: {list_response.total}")
    print(f"  - page: {list_response.page}, page_size: {list_response.page_size}")
    print(f"  - images count: {len(list_response.images)}")

    # 4. 创建准确性标注请求
    print("\n[示例4] 创建准确性标注请求")
    accuracy_request = AccuracyUpdateRequest(
        accuracy_status="accurate",
        comment="诊断结果准确，症状特征识别正确",
        marked_by="expert@example.com"
    )
    print(f"  - accuracy_status: {accuracy_request.accuracy_status}")
    print(f"  - comment: {accuracy_request.comment}")
    print(f"  - marked_by: {accuracy_request.marked_by}")

    # 5. 序列化为JSON
    print("\n[示例5] 序列化为JSON")
    json_str = list_response.model_dump_json(indent=2)
    print(f"  JSON长度: {len(json_str)} 字符")
    print(f"  JSON前200字符:\n{json_str[:200]}...")

    print("\n" + "=" * 80)
    print("✅ Schema模型演示完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
