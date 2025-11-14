"""
Pydantic数据模型：人工标注

定义人工标注的数据结构。
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Annotation(BaseModel):
    """人工标注信息"""
    is_accurate: str = Field(
        ...,
        description="准确性标注：correct/incorrect/uncertain"
    )
    actual_disease_id: Optional[str] = Field(
        None,
        description="实际疾病ID（如果错误）"
    )
    actual_disease_name: Optional[str] = Field(
        None,
        description="实际疾病名称（如果错误）"
    )
    notes: Optional[str] = Field(
        None,
        description="标注备注"
    )
    annotated_by: str = Field(
        default="user",
        description="标注人"
    )
    annotated_at: datetime = Field(
        default_factory=datetime.now,
        description="标注时间"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ImageAnnotation(BaseModel):
    """图片标注（包含图片ID和诊断ID）"""
    image_id: str = Field(..., description="图片ID")
    diagnosis_id: str = Field(..., description="诊断ID")
    annotation: Annotation = Field(..., description="标注信息")
