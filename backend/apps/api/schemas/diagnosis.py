"""
诊断API Schema模型 (P4.2 升级版)

功能：
- 定义诊断相关的API请求和响应模型
- 用于FastAPI的请求验证和响应序列化
- 遵循详细设计文档v2.0第6.2节的API协议定义

模型清单：
- DiagnosisRequest: 诊断请求（暂不使用，预留）
- QADetailSchema: VLM问答对详情Schema（P3.9新增）
- DiagnosisScoreSchema: 诊断评分详情Schema
- DiagnosisSchema: 诊断疾病信息Schema（level、confidence等）
- CandidateDiseaseSchema: 候选疾病Schema
- DiagnosisResponseSchema: 诊断响应Schema（扩展版，支持qa_details、feature_vector、scores等）
- DiseaseSchema: 疾病信息Schema（用于知识库查询）

实现阶段：P4.2
作者：AI Python Architect
日期：2025-11-15
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DiagnosisRequest(BaseModel):
    """
    诊断请求Schema（预留，暂不使用）

    说明：
    - 详细设计文档v2.0中，诊断接口使用multipart/form-data
    - FastAPI通过UploadFile处理图片上传，无需定义请求Schema
    - 此模型预留用于未来扩展（如：指定VLM提供商等参数）
    """
    pass


class QADetailSchema(BaseModel):
    """
    VLM问答对详情Schema

    用于记录Q0-Q6每个问题的VLM问答对详情

    字段说明：
    - question_id: 问题ID（如：Q0.0, Q0.1, Q1, Q2等）
    - question: 问题内容
    - answer: VLM回答
    - confidence: 置信度（0-1）
    - raw_response: VLM原始响应（JSON格式，可选）

    实现阶段：P3.9
    对应设计文档：详细设计文档v2.0 第6.2.1节
    """
    question_id: str = Field(..., description="问题ID（如：Q0.0, Q1等）")
    question: str = Field(..., description="问题内容")
    answer: str = Field(..., description="VLM回答")
    confidence: float = Field(..., ge=0, le=1, description="置信度（0-1）")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="VLM原始响应（JSON格式）")


class DiagnosisScoreSchema(BaseModel):
    """
    诊断评分详情Schema

    用于记录特征匹配的评分详情

    字段说明：
    - total_score: 总分（0-1）
    - major_features: 主要特征得分字典（特征名 -> 得分）
    - minor_features: 次要特征得分字典（特征名 -> 得分）
    - optional_features: 可选特征得分字典（特征名 -> 得分）
    - completeness_modifier: 完整性修正系数（0.5-1.0）
    - major_matched: 主要特征匹配数量
    - major_total: 主要特征总数量

    对应设计文档：详细设计文档v2.0 第6.2.1节 scores字段
    """
    total_score: float = Field(..., ge=0, le=1, description="总分（0-1）")
    major_features: Dict[str, float] = Field(
        default_factory=dict,
        description="主要特征得分字典（特征名 -> 得分）"
    )
    minor_features: Dict[str, float] = Field(
        default_factory=dict,
        description="次要特征得分字典（特征名 -> 得分）"
    )
    optional_features: Dict[str, float] = Field(
        default_factory=dict,
        description="可选特征得分字典（特征名 -> 得分）"
    )
    completeness_modifier: float = Field(
        ...,
        ge=0.5,
        le=1.0,
        description="完整性修正系数（0.5-1.0）"
    )
    major_matched: int = Field(..., ge=0, description="主要特征匹配数量")
    major_total: int = Field(..., ge=0, description="主要特征总数量")


class DiagnosisSchema(BaseModel):
    """
    诊断疾病信息Schema

    用于诊断响应中的确诊疾病信息

    字段说明：
    - disease_id: 疾病唯一标识符（如：cherry_powdery_mildew）
    - disease_name: 疾病中文名
    - common_name_en: 疾病英文名
    - pathogen: 病原体名称
    - level: 置信度级别（confirmed/suspected/unlikely）
    - confidence: 诊断置信度（0-1）

    对应设计文档：详细设计文档v2.0 第6.2.1节 diagnosis字段
    """
    disease_id: str = Field(..., description="疾病唯一标识符")
    disease_name: str = Field(..., description="疾病中文名")
    common_name_en: Optional[str] = Field(None, description="疾病英文名")
    pathogen: Optional[str] = Field(None, description="病原体名称")
    level: str = Field(
        ...,
        description="置信度级别（confirmed/suspected/unlikely）"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="诊断置信度（0-1）"
    )


class CandidateDiseaseSchema(BaseModel):
    """
    候选疾病Schema

    用于记录诊断候选疾病列表

    字段说明：
    - disease_id: 疾病唯一标识符
    - disease_name: 疾病中文名
    - score: 匹配得分（0-1）
    - level: 置信度级别（confirmed/suspected/unlikely）

    对应设计文档：详细设计文档v2.0 第6.2.1节 candidates字段
    """
    disease_id: str = Field(..., description="疾病唯一标识符")
    disease_name: str = Field(..., description="疾病中文名")
    score: float = Field(..., ge=0, le=1, description="匹配得分（0-1）")
    level: str = Field(
        ...,
        description="置信度级别（confirmed/suspected/unlikely）"
    )


class DiagnosisResponseSchema(BaseModel):
    """
    诊断响应Schema（完整版）

    用于诊断接口的响应数据

    字段说明：
    - diagnosis_id: 诊断唯一标识符（格式：diag_YYYYMMDD_NNN）
    - timestamp: 诊断时间戳（ISO 8601格式）
    - diagnosis: 诊断疾病信息（disease_id、disease_name、level、confidence等）
    - feature_vector: VLM提取的特征向量（Q0-Q6问诊结果）
    - scores: 特征匹配得分详情（可选，如果使用知识库匹配）
    - reasoning: 诊断推理过程（逐步推理链）
    - candidates: 所有候选疾病及其分数（Top N候选）
    - vlm_provider: 使用的VLM服务提供商
    - execution_time_ms: 诊断总耗时（毫秒）
    - metadata: 元数据（image_id、image_path、knowledge_base_version等）

    对应设计文档：详细设计文档v2.0 第6.2.1节
    """
    diagnosis_id: str = Field(
        ...,
        description="诊断唯一标识符（格式：diag_YYYYMMDD_NNN）",
        pattern=r"^diag_\d{8}_\d{3}$"
    )
    timestamp: datetime = Field(..., description="诊断时间戳")

    # 诊断结果
    diagnosis: DiagnosisSchema = Field(..., description="诊断疾病信息")

    # 特征向量（Dict格式，包含所有Q0-Q6提取的特征）
    feature_vector: Dict[str, Any] = Field(
        ...,
        description="VLM提取的特征向量（Q0-Q6问诊结果）"
    )

    # 评分详情（可选，知识库匹配时存在）
    scores: Optional[DiagnosisScoreSchema] = Field(
        None,
        description="特征匹配得分详情"
    )

    # 推理过程
    reasoning: List[str] = Field(
        default_factory=list,
        description="诊断推理过程（人类可读的逻辑链）"
    )

    # 候选疾病列表
    candidates: Optional[List[CandidateDiseaseSchema]] = Field(
        None,
        description="所有候选疾病及其分数（调试用）"
    )

    # 执行信息
    vlm_provider: str = Field(..., description="使用的VLM服务提供商")
    execution_time_ms: int = Field(
        ...,
        description="诊断总耗时（毫秒）"
    )

    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="元数据（image_id、image_path、knowledge_base_version等）"
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

    对应设计文档：详细设计文档v2.0 第6.3节
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


def main():
    """
    Schema模型使用示例

    演示如何：
    1. 创建诊断响应Schema
    2. 序列化为JSON
    3. 从JSON反序列化
    """
    from datetime import datetime

    print("=" * 80)
    print("诊断API Schema模型使用示例")
    print("=" * 80)

    # 1. 创建诊断响应Schema
    print("\n[示例1] 创建诊断响应Schema")
    diagnosis_response = DiagnosisResponseSchema(
        diagnosis_id="diag_20251115_001",
        timestamp=datetime.now(),
        diagnosis=DiagnosisSchema(
            disease_id="cherry_powdery_mildew",
            disease_name="樱花白粉病",
            common_name_en="Cherry Powdery Mildew",
            pathogen="Podosphaera clandestina",
            level="confirmed",
            confidence=0.92
        ),
        feature_vector={
            "content_type": "plant",
            "plant_category": "flower",
            "flower_genus": "Prunus",
            "organ": "leaf",
            "symptom_type": "powdery_coating"
        },
        scores=DiagnosisScoreSchema(
            total_score=0.92,
            major_features={"symptom_type": 0.5, "color_center": 0.3},
            minor_features={"location": 0.1},
            optional_features={},
            completeness_modifier=1.0,
            major_matched=2,
            major_total=2
        ),
        reasoning=[
            "Q0.0: 图片内容类型识别 → plant (置信度: 0.98)",
            "Layer2: 知识库匹配 → cherry_powdery_mildew (得分: 0.92)"
        ],
        candidates=[
            CandidateDiseaseSchema(
                disease_id="cherry_powdery_mildew",
                disease_name="樱花白粉病",
                score=0.92,
                level="confirmed"
            )
        ],
        vlm_provider="qwen-vl-plus",
        execution_time_ms=3245
    )

    print(f"  - diagnosis_id: {diagnosis_response.diagnosis_id}")
    print(f"  - disease_name: {diagnosis_response.diagnosis.disease_name}")
    print(f"  - level: {diagnosis_response.diagnosis.level}")
    print(f"  - confidence: {diagnosis_response.diagnosis.confidence}")

    # 2. 序列化为JSON
    print("\n[示例2] 序列化为JSON")
    json_str = diagnosis_response.model_dump_json(indent=2)
    print(f"  JSON长度: {len(json_str)} 字符")
    print(f"  JSON前200字符:\n{json_str[:200]}...")

    # 3. 从JSON反序列化
    print("\n[示例3] 从JSON反序列化")
    diagnosis_response_from_json = DiagnosisResponseSchema.model_validate_json(json_str)
    print(f"  - 反序列化成功: {diagnosis_response_from_json.diagnosis_id}")

    print("\n" + "=" * 80)
    print("✅ Schema模型演示完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
