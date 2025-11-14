"""
Pydantic数据模型：推理结果

定义完整的推理结果数据结构，严格符合需求文档4.1节的定义。
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class OntologyReference(BaseModel):
    """本体引用信息"""
    source: str = Field(..., description="本体来源（文件路径或定义名称）")
    valid_choices: Optional[List[str]] = Field(None, description="有效选项列表")
    feature_key: Optional[str] = Field(None, description="特征键名")
    definition: Optional[str] = Field(None, description="特征定义描述")


class Q0StepResult(BaseModel):
    """Q0序列单步结果"""
    choice: str = Field(..., description="选择的值")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    reasoning: str = Field(..., description="推理理由")
    ontology_reference: OntologyReference = Field(..., description="本体引用")


class FeatureExtractionResult(BaseModel):
    """特征提取单个结果"""
    choice: str = Field(..., description="提取的特征值")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    reasoning: str = Field(..., description="推理理由")
    alternatives: Optional[List[str]] = Field(None, description="备选值")
    ontology_reference: OntologyReference = Field(..., description="本体引用")


class SynonymMapping(BaseModel):
    """同义词映射详情"""
    observed: str = Field(..., description="VLM识别的值")
    canonical: str = Field(..., description="本体标准值")
    synonym_source: str = Field(..., description="同义词来源路径")
    synonyms_list: List[str] = Field(..., description="同义词列表")
    match_explanation: str = Field(..., description="匹配说明")


class MismatchExplanation(BaseModel):
    """不匹配说明"""
    reason: str = Field(..., description="不匹配原因")
    expected_synonyms: List[str] = Field(..., description="期望的同义词列表")
    ontology_reference: str = Field(..., description="本体引用路径")


class MatchDetail(BaseModel):
    """单个特征匹配详情"""
    feature_key: str = Field(..., description="特征键名")
    importance_level: str = Field(..., description="重要性级别：major/minor/optional")
    observed_value: str = Field(..., description="观测值")
    expected_value: str = Field(..., description="期望值")
    match_type: str = Field(..., description="匹配类型：exact/fuzzy/no_match")
    fuzzy_score: Optional[float] = Field(None, description="模糊匹配分数")
    contribution: float = Field(..., description="对总分的贡献")
    synonym_mapping: Optional[SynonymMapping] = Field(None, description="同义词映射（如有）")
    mismatch_explanation: Optional[MismatchExplanation] = Field(None, description="不匹配说明（如有）")
    ontology_reference: Optional[OntologyReference] = Field(None, description="本体引用")


class CandidateDisease(BaseModel):
    """候选疾病信息"""
    disease_id: str = Field(..., description="疾病ID")
    disease_name: str = Field(..., description="疾病中文名")
    disease_name_en: str = Field(..., description="疾病英文名")
    ontology_file: str = Field(..., description="疾病定义文件路径")
    version: str = Field(..., description="版本号")


class ScoringResult(BaseModel):
    """单个疾病的评分结果"""
    disease_id: str = Field(..., description="疾病ID")
    disease_name: str = Field(..., description="疾病中文名")
    ontology_file: str = Field(..., description="疾病定义文件路径")
    version: str = Field(..., description="版本号")
    total_score: float = Field(..., ge=0.0, le=1.0, description="总分")
    confidence_level: str = Field(..., description="置信度级别：confirmed/suspected/unlikely")
    major_score: float = Field(..., description="主要特征分数")
    minor_score: float = Field(..., description="次要特征分数")
    optional_score: float = Field(..., description="可选特征分数")
    completeness_modifier: float = Field(..., description="完整性修正系数")
    matched_features: Dict[str, List[str]] = Field(..., description="匹配的特征（按重要性分组）")
    unmatched_features: Dict[str, List[str]] = Field(..., description="未匹配的特征（按重要性分组）")
    match_details: List[MatchDetail] = Field(..., description="详细匹配信息")


class FinalDiagnosis(BaseModel):
    """最终诊断结果"""
    disease_id: str = Field(..., description="疾病ID")
    disease_name: str = Field(..., description="疾病中文名")
    disease_name_en: str = Field(..., description="疾病英文名")
    confidence_level: str = Field(..., description="置信度级别")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="置信度分数")
    pathogen: str = Field(..., description="病原体")
    treatment_suggestions: List[str] = Field(..., description="治疗建议")
    ontology_file: str = Field(..., description="疾病定义文件路径")
    version: str = Field(..., description="版本号")
    git_commit: Optional[str] = Field(None, description="Git提交哈希")


class PerformanceMetrics(BaseModel):
    """性能指标"""
    total_elapsed_time: float = Field(..., description="总耗时（秒）")
    q0_time: float = Field(..., description="Q0序列耗时（秒）")
    q1_q6_time: float = Field(..., description="Q1-Q6特征提取耗时（秒）")
    matching_time: float = Field(..., description="匹配评分耗时（秒）")
    vlm_provider: str = Field(..., description="VLM提供商")


class OntologyUsageSummary(BaseModel):
    """本体使用总览"""

    class FeatureOntologyInfo(BaseModel):
        """特征本体信息"""
        file_path: str = Field(..., description="文件路径")
        version: str = Field(..., description="版本号")
        git_commit: str = Field(..., description="Git提交哈希")

    class DiseaseOntologyInfo(BaseModel):
        """疾病本体信息"""
        disease_id: str = Field(..., description="疾病ID")
        file_path: str = Field(..., description="文件路径")
        version: str = Field(..., description="版本号")

    feature_ontology: FeatureOntologyInfo = Field(..., description="特征本体信息")
    disease_ontologies_consulted: List[DiseaseOntologyInfo] = Field(
        ..., description="查询的疾病本体列表"
    )


class DiagnosisResult(BaseModel):
    """完整推理结果"""
    diagnosis_id: str = Field(..., description="诊断ID")
    image_id: str = Field(..., description="图片ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    ontology_usage_summary: OntologyUsageSummary = Field(..., description="本体使用总览")

    q0_sequence: Dict[str, Q0StepResult] = Field(..., description="Q0序列结果")

    feature_extraction: Dict[str, FeatureExtractionResult] = Field(
        ..., description="Q1-Q6特征提取结果"
    )

    candidate_diseases: List[CandidateDisease] = Field(..., description="候选疾病列表")

    scoring_results: List[ScoringResult] = Field(..., description="评分结果列表（降序排列）")

    final_diagnosis: FinalDiagnosis = Field(..., description="最终诊断结果")

    performance: PerformanceMetrics = Field(..., description="性能指标")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
