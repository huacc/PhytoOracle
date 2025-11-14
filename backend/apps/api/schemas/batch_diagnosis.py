"""
批量诊断API Schema模型 (P4.5 实现)

功能：
- 定义批量诊断相关的API请求和响应模型
- 用于FastAPI的请求验证和响应序列化
- 遵循详细设计文档v2.0第6.6节的API协议定义

模型清单：
- BatchUploadRequest: 批量上传请求（multipart/form-data）
- BatchCreateResponse: 批量任务创建响应
- BatchDiagnosisResultItem: 单个诊断结果项
- BatchSummary: 批量诊断汇总统计
- BatchResultResponse: 批量诊断结果响应（完成状态）
- BatchProgressResponse: 批量诊断进度响应（处理中状态）
- CurrentImageInfo: 当前处理中的图片信息

实现阶段：P4.5
对应设计文档：详细设计文档v2.0 第6.6节
作者：AI Python Architect
日期：2025-11-15
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BatchCreateResponse(BaseModel):
    """
    批量任务创建响应Schema

    用于POST /api/v1/diagnose/batch接口的响应

    字段说明：
    - batch_id: 批量诊断任务ID（格式：batch_YYYYMMDD_HHmmss）
    - total_images: 总图片数量
    - status: 任务状态（processing）
    - created_at: 创建时间（ISO 8601格式）
    - estimated_completion_time: 预计完成时间（ISO 8601格式）
    - message: 提示消息

    对应设计文档：详细设计文档v2.0 第6.6.1节
    """
    batch_id: str = Field(..., description="批量诊断任务ID（格式：batch_YYYYMMDD_HHmmss）")
    total_images: int = Field(..., description="总图片数量")
    status: str = Field(..., description="任务状态（processing）")
    created_at: str = Field(..., description="创建时间（ISO 8601格式）")
    estimated_completion_time: str = Field(..., description="预计完成时间（ISO 8601格式）")
    message: str = Field(..., description="提示消息")


class BatchDiagnosisResultItem(BaseModel):
    """
    单个批量诊断结果项Schema

    用于BatchResultResponse的results数组

    字段说明：
    - image_id: 图片ID
    - image_filename: 图片文件名
    - diagnosis_id: 诊断ID（可选，诊断成功时有值）
    - disease_id: 疾病ID（可选）
    - disease_name: 疾病名称
    - level: 置信度等级（confirmed | suspected | unlikely）
    - confidence: 置信度分数（0-1）
    - vlm_provider: VLM提供商（如：qwen-vl-plus）
    - execution_time_ms: 执行耗时（毫秒）
    - error: 错误信息（可选，诊断失败时有值）

    对应设计文档：详细设计文档v2.0 第6.6.2节
    """
    image_id: str = Field(..., description="图片ID")
    image_filename: str = Field(..., description="图片文件名")
    diagnosis_id: Optional[str] = Field(None, description="诊断ID（诊断成功时有值）")
    disease_id: Optional[str] = Field(None, description="疾病ID")
    disease_name: str = Field(..., description="疾病名称")
    level: str = Field(..., description="置信度等级（confirmed | suspected | unlikely）")
    confidence: float = Field(..., description="置信度分数（0-1）")
    vlm_provider: str = Field(..., description="VLM提供商（如：qwen-vl-plus）")
    execution_time_ms: int = Field(..., description="执行耗时（毫秒）")
    error: Optional[str] = Field(None, description="错误信息（诊断失败时有值）")


class BatchSummary(BaseModel):
    """
    批量诊断汇总统计Schema

    用于BatchResultResponse的summary字段

    字段说明：
    - confirmed_count: 确诊数量（level=confirmed）
    - suspected_count: 疑似数量（level=suspected）
    - unlikely_count: 不太可能数量（level=unlikely）
    - error_count: 错误数量
    - average_confidence: 平均置信度
    - average_execution_time_ms: 平均执行耗时（毫秒）

    对应设计文档：详细设计文档v2.0 第6.6.2节
    """
    confirmed_count: int = Field(..., description="确诊数量（level=confirmed）")
    suspected_count: int = Field(..., description="疑似数量（level=suspected）")
    unlikely_count: int = Field(..., description="不太可能数量（level=unlikely）")
    error_count: int = Field(..., description="错误数量")
    average_confidence: float = Field(..., description="平均置信度")
    average_execution_time_ms: int = Field(..., description="平均执行耗时（毫秒）")


class BatchResultResponse(BaseModel):
    """
    批量诊断结果响应Schema（完成状态）

    用于GET /api/v1/diagnose/batch/{batch_id}接口的响应

    字段说明：
    - batch_id: 批量诊断任务ID
    - status: 任务状态（completed | failed | processing）
    - total_images: 总图片数量
    - completed_images: 已完成图片数量
    - failed_images: 失败图片数量
    - created_at: 创建时间（ISO 8601格式）
    - completed_at: 完成时间（ISO 8601格式，可选）
    - execution_time_ms: 总执行耗时（毫秒，可选）
    - results: 诊断结果列表（可选，completed状态时有值）
    - summary: 汇总统计（可选，completed状态时有值）
    - message: 提示消息（可选，processing/failed状态时有值）
    - estimated_completion_time: 预计完成时间（可选，processing状态时有值）

    对应设计文档：详细设计文档v2.0 第6.6.2节
    """
    batch_id: str = Field(..., description="批量诊断任务ID")
    status: str = Field(..., description="任务状态（completed | failed | processing）")
    total_images: int = Field(..., description="总图片数量")
    completed_images: int = Field(..., description="已完成图片数量")
    failed_images: int = Field(..., description="失败图片数量")
    created_at: str = Field(..., description="创建时间（ISO 8601格式）")
    completed_at: Optional[str] = Field(None, description="完成时间（ISO 8601格式）")
    execution_time_ms: Optional[int] = Field(None, description="总执行耗时（毫秒）")
    results: Optional[List[BatchDiagnosisResultItem]] = Field(None, description="诊断结果列表（completed状态时有值）")
    summary: Optional[BatchSummary] = Field(None, description="汇总统计（completed状态时有值）")
    message: Optional[str] = Field(None, description="提示消息（processing/failed状态时有值）")
    estimated_completion_time: Optional[str] = Field(None, description="预计完成时间（processing状态时有值）")


class CurrentImageInfo(BaseModel):
    """
    当前处理中的图片信息Schema

    用于BatchProgressResponse的current_image字段

    字段说明：
    - image_id: 图片ID
    - image_filename: 图片文件名
    - started_at: 开始处理时间（ISO 8601格式）

    对应设计文档：详细设计文档v2.0 第6.6.3节
    """
    image_id: str = Field(..., description="图片ID")
    image_filename: str = Field(..., description="图片文件名")
    started_at: str = Field(..., description="开始处理时间（ISO 8601格式）")


class BatchProgressResponse(BaseModel):
    """
    批量诊断进度响应Schema

    用于GET /api/v1/diagnose/batch/{batch_id}/progress接口的响应

    字段说明：
    - batch_id: 批量诊断任务ID
    - status: 任务状态（processing | completed | failed）
    - total_images: 总图片数量
    - completed_images: 已完成图片数量
    - failed_images: 失败图片数量
    - progress_percentage: 进度百分比（0-100）
    - current_image: 当前处理中的图片信息（可选，processing状态时有值）
    - created_at: 创建时间（ISO 8601格式）
    - estimated_completion_time: 预计完成时间（可选，processing状态时有值）
    - average_time_per_image_ms: 单张图片平均耗时（毫秒，可选）
    - completed_at: 完成时间（可选，completed/failed状态时有值）
    - message: 提示消息（可选）

    对应设计文档：详细设计文档v2.0 第6.6.3节
    """
    batch_id: str = Field(..., description="批量诊断任务ID")
    status: str = Field(..., description="任务状态（processing | completed | failed）")
    total_images: int = Field(..., description="总图片数量")
    completed_images: int = Field(..., description="已完成图片数量")
    failed_images: int = Field(..., description="失败图片数量")
    progress_percentage: int = Field(..., description="进度百分比（0-100）")
    current_image: Optional[CurrentImageInfo] = Field(None, description="当前处理中的图片信息（processing状态时有值）")
    created_at: str = Field(..., description="创建时间（ISO 8601格式）")
    estimated_completion_time: Optional[str] = Field(None, description="预计完成时间（processing状态时有值）")
    average_time_per_image_ms: Optional[int] = Field(None, description="单张图片平均耗时（毫秒）")
    completed_at: Optional[str] = Field(None, description="完成时间（completed/failed状态时有值）")
    message: Optional[str] = Field(None, description="提示消息")


# ==================== 主函数 ====================

def main():
    """
    Schema模型使用示例

    演示如何构造批量诊断API的响应对象
    """
    print("\n" + "=" * 60)
    print("批量诊断API Schema模型使用示例")
    print("=" * 60 + "\n")

    # 1. 批量任务创建响应示例
    print("1️⃣ 批量任务创建响应（BatchCreateResponse）")
    create_response = BatchCreateResponse(
        batch_id="batch_20251115_143000",
        total_images=50,
        status="processing",
        created_at="2025-11-15T14:30:00Z",
        estimated_completion_time="2025-11-15T14:35:00Z",
        message="批量诊断任务已创建，请使用batch_id查询进度"
    )
    print(f"   batch_id: {create_response.batch_id}")
    print(f"   total_images: {create_response.total_images}")
    print(f"   status: {create_response.status}")
    print(f"   message: {create_response.message}")

    # 2. 批量进度响应示例（处理中）
    print("\n2️⃣ 批量进度响应（BatchProgressResponse - 处理中）")
    progress_response = BatchProgressResponse(
        batch_id="batch_20251115_143000",
        status="processing",
        total_images=50,
        completed_images=23,
        failed_images=0,
        progress_percentage=46,
        current_image=CurrentImageInfo(
            image_id="img_20251115_024",
            image_filename="rose_leaf_024.jpg",
            started_at="2025-11-15T14:33:12Z"
        ),
        created_at="2025-11-15T14:30:00Z",
        estimated_completion_time="2025-11-15T14:35:00Z",
        average_time_per_image_ms=3200,
        message="批量诊断进行中，请稍后刷新查询"
    )
    print(f"   batch_id: {progress_response.batch_id}")
    print(f"   progress: {progress_response.completed_images}/{progress_response.total_images} ({progress_response.progress_percentage}%)")
    print(f"   current_image: {progress_response.current_image.image_filename}")

    # 3. 批量结果响应示例（已完成）
    print("\n3️⃣ 批量结果响应（BatchResultResponse - 已完成）")
    result_response = BatchResultResponse(
        batch_id="batch_20251115_143000",
        status="completed",
        total_images=50,
        completed_images=50,
        failed_images=0,
        created_at="2025-11-15T14:30:00Z",
        completed_at="2025-11-15T14:35:12Z",
        execution_time_ms=267000,
        results=[
            BatchDiagnosisResultItem(
                image_id="img_20251115_001",
                image_filename="rose_leaf_001.jpg",
                diagnosis_id="diag_20251115_001",
                disease_id="rose_black_spot",
                disease_name="玫瑰黑斑病",
                level="confirmed",
                confidence=0.92,
                vlm_provider="qwen-vl-plus",
                execution_time_ms=3245
            ),
            BatchDiagnosisResultItem(
                image_id="img_20251115_002",
                image_filename="rose_leaf_002.jpg",
                diagnosis_id="diag_20251115_002",
                disease_id="rose_powdery_mildew",
                disease_name="玫瑰白粉病",
                level="suspected",
                confidence=0.75,
                vlm_provider="qwen-vl-plus",
                execution_time_ms=2987
            )
        ],
        summary=BatchSummary(
            confirmed_count=35,
            suspected_count=12,
            unlikely_count=3,
            error_count=0,
            average_confidence=0.86,
            average_execution_time_ms=3120
        )
    )
    print(f"   batch_id: {result_response.batch_id}")
    print(f"   status: {result_response.status}")
    print(f"   execution_time: {result_response.execution_time_ms}ms")
    print(f"   summary: confirmed={result_response.summary.confirmed_count}, suspected={result_response.summary.suspected_count}")
    print(f"   results count: {len(result_response.results)}")

    print("\n" + "=" * 60)
    print("✅ Schema模型示例完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
