"""
诊断API Schema模型

功能：
- 定义诊断相关的API请求和响应模型
- 用于FastAPI的请求验证和响应序列化
- 遵循P1.1的OpenAPI规范定义

模型清单：
- DiagnosisRequest: 诊断请求（暂不使用，预留）
- DiagnosedDiseaseSchema: 诊断疾病信息Schema
- DiagnosisResponseSchema: 诊断响应Schema
- DiseaseSchema: 疾病信息Schema（用于知识库查询）
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DiagnosisRequest(BaseModel):
    """
    诊断请求Schema（预留，暂不使用）

    说明：
    - P1.1的OpenAPI定义中，诊断接口使用multipart/form-data
    - FastAPI通过UploadFile处理图片上传，无需定义请求Schema
    - 此模型预留用于未来扩展（如：指定VLM提供商等参数）
    """
    pass


class DiagnosedDiseaseSchema(BaseModel):
    """
    诊断疾病信息Schema

    用于诊断响应中的确诊疾病或疑似疾病列表

    字段说明：
    - disease_id: 疾病唯一标识符（如：rose_black_spot）
    - disease_name: 疾病中文名
    - common_name_en: 疾病英文名
    - pathogen: 病原体名称
    - confidence: 诊断置信度（0-1）

    对应OpenAPI: components/schemas/DiagnosedDisease
    """
    disease_id: str = Field(..., description="疾病唯一标识符")
    disease_name: str = Field(..., description="疾病中文名")
    common_name_en: Optional[str] = Field(None, description="疾病英文名")
    pathogen: Optional[str] = Field(None, description="病原体名称")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="诊断置信度（0-1）"
    )


class DiagnosisResponseSchema(BaseModel):
    """
    诊断响应Schema

    用于诊断接口的响应数据

    字段说明：
    - diagnosis_id: 诊断唯一标识符（格式：diag_YYYYMMDD_NNN）
    - timestamp: 诊断时间戳（ISO 8601格式）
    - status: 诊断状态（confirmed/suspected/unlikely）
    - confirmed_disease: 确诊疾病信息（status=confirmed时存在）
    - suspected_diseases: 疑似疾病列表（status=suspected时存在，Top 2-3候选）
    - feature_vector: VLM提取的特征向量（Q0-Q6问诊结果）
    - scores: 特征匹配得分详情
    - reasoning: 诊断推理过程
    - candidates: 所有候选疾病及其分数（调试用）
    - vlm_provider: 使用的VLM服务提供商
    - execution_time_ms: 诊断总耗时（毫秒）

    对应OpenAPI: components/schemas/DiagnosisResponse
    """
    diagnosis_id: str = Field(
        ...,
        description="诊断唯一标识符（格式：diag_YYYYMMDD_NNN）",
        pattern=r"^diag_\d{8}_\d{3}$"
    )
    timestamp: datetime = Field(..., description="诊断时间戳")
    status: str = Field(
        ...,
        description="诊断状态（confirmed/suspected/unlikely）"
    )
    confirmed_disease: Optional[DiagnosedDiseaseSchema] = Field(
        None,
        description="确诊疾病信息（status=confirmed时存在）"
    )
    suspected_diseases: Optional[List[DiagnosedDiseaseSchema]] = Field(
        None,
        description="疑似疾病列表（status=suspected时存在，Top 2-3候选）"
    )
    feature_vector: Dict[str, Any] = Field(
        ...,
        description="VLM提取的特征向量（Q0-Q6问诊结果）"
    )
    scores: Optional[Dict[str, Any]] = Field(
        None,
        description="特征匹配得分详情"
    )
    reasoning: List[str] = Field(
        default_factory=list,
        description="诊断推理过程（人类可读的逻辑链）"
    )
    candidates: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="所有候选疾病及其分数（调试用）"
    )
    vlm_provider: str = Field(..., description="使用的VLM服务提供商")
    execution_time_ms: int = Field(
        ...,
        description="诊断总耗时（毫秒）"
    )


class DiseaseSchema(BaseModel):
    """
    疾病信息Schema

    用于知识库查询接口的响应数据

    字段说明：
    - disease_id: 疾病唯一标识符
    - disease_name: 疾病中文名
    - common_name_en: 疾病英文名
    - pathogen: 病原体名称
    - pathogen_type: 病原体类型（fungal/bacterial/viral）
    - affected_plants: 受影响的植物列表
    - typical_symptoms: 典型症状列表

    对应OpenAPI: components/schemas/Disease
    """
    disease_id: str = Field(..., description="疾病唯一标识符")
    disease_name: str = Field(..., description="疾病中文名")
    common_name_en: Optional[str] = Field(None, description="疾病英文名")
    pathogen: str = Field(..., description="病原体名称")
    pathogen_type: str = Field(..., description="病原体类型（fungal/bacterial/viral）")
    affected_plants: List[str] = Field(
        default_factory=list,
        description="受影响的植物列表"
    )
    typical_symptoms: List[str] = Field(
        default_factory=list,
        description="典型症状列表"
    )
