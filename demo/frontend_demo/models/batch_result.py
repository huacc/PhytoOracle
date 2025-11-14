"""
批量推理结果数据模型

定义批量推理的数据结构，包括批次信息、汇总统计等。
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class BatchDiagnosisItem(BaseModel):
    """批量推理中的单个图片结果"""

    image_name: str = Field(..., description="图片文件名")
    image_id: str = Field(..., description="图片ID")
    diagnosis_id: str = Field(..., description="诊断ID")
    flower_genus: str = Field(..., description="花卉属名")
    disease_id: str = Field(..., description="诊断疾病ID")
    disease_name: str = Field(..., description="诊断疾病名称")
    confidence_level: str = Field(..., description="置信度级别 (confirmed/suspected/unlikely)")
    confidence_score: float = Field(..., description="置信度分数 (0-1)")
    annotation_status: Optional[str] = Field(None, description="标注状态 (correct/incorrect/uncertain/null)")
    actual_disease_id: Optional[str] = Field(None, description="实际疾病ID（如果标注为错误）")
    actual_disease_name: Optional[str] = Field(None, description="实际疾病名称（如果标注为错误）")
    notes: Optional[str] = Field(None, description="标注备注")
    diagnosed_at: datetime = Field(..., description="诊断时间")


class BatchStatistics(BaseModel):
    """批量推理统计数据"""

    total_count: int = Field(..., description="总诊断量")
    annotated_count: int = Field(0, description="已标注数量")
    unannotated_count: int = Field(0, description="未标注数量")
    correct_count: int = Field(0, description="标注为正确的数量")
    incorrect_count: int = Field(0, description="标注为错误的数量")
    uncertain_count: int = Field(0, description="标注为不确定的数量")
    accuracy_rate: Optional[float] = Field(None, description="准确率 (correct/annotated)")

    # 按置信度级别统计
    by_confidence: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="按置信度级别统计 {level: {total, correct, accuracy}}"
    )

    # 按花卉属统计
    by_genus: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="按花卉属统计 {genus: {total, correct, accuracy}}"
    )


class ConfusionMatrixData(BaseModel):
    """混淆矩阵数据"""

    labels: List[str] = Field(..., description="疾病标签列表")
    matrix: List[List[int]] = Field(..., description="混淆矩阵 (actual x predicted)")
    total_samples: int = Field(..., description="总样本数（已标注）")


class BatchDiagnosisResult(BaseModel):
    """批量推理完整结果"""

    batch_id: str = Field(..., description="批次ID")
    created_at: datetime = Field(..., description="创建时间")
    total_images: int = Field(..., description="总图片数")
    completed_count: int = Field(0, description="已完成数量")
    failed_count: int = Field(0, description="失败数量")
    status: str = Field("processing", description="批次状态 (processing/completed/failed)")

    items: List[BatchDiagnosisItem] = Field(default_factory=list, description="推理结果列表")
    statistics: Optional[BatchStatistics] = Field(None, description="统计数据")
    confusion_matrix: Optional[ConfusionMatrixData] = Field(None, description="混淆矩阵")
