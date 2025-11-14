"""
Pydantic数据模型：本体使用

定义本体使用导出的数据结构。
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FuzzyMapping(BaseModel):
    """模糊匹配映射详情"""
    feature: str = Field(..., description="特征键名")
    vlm_value: str = Field(..., description="VLM识别值")
    ontology_value: str = Field(..., description="本体标准值")
    synonym_source: str = Field(..., description="同义词来源路径")
    fuzzy_score: float = Field(..., ge=0.0, le=1.0, description="模糊匹配分数")


class DiseaseOntologyUsage(BaseModel):
    """单个疾病本体使用信息"""
    disease_id: str = Field(..., description="疾病ID")
    file: str = Field(..., description="文件路径")
    version: str = Field(..., description="版本号")
    matched_features: Dict[str, List[str]] = Field(
        ..., description="匹配的特征（按重要性分组）"
    )
    fuzzy_mappings: List[FuzzyMapping] = Field(
        default_factory=list, description="模糊匹配列表"
    )


class FeatureOntologyUsage(BaseModel):
    """特征本体使用信息"""
    file: str = Field(..., description="文件路径")
    version: str = Field(..., description="版本号")
    git_commit: str = Field(..., description="Git提交哈希")
    used_features: List[str] = Field(..., description="使用的特征列表")


class OntologyUsage(BaseModel):
    """完整的本体使用信息"""
    feature_ontology: FeatureOntologyUsage = Field(..., description="特征本体使用")
    disease_ontologies: List[DiseaseOntologyUsage] = Field(
        ..., description="疾病本体使用列表"
    )


class OntologyUsageExport(BaseModel):
    """本体使用导出数据"""
    diagnosis_id: str = Field(..., description="诊断ID")
    ontology_usage: OntologyUsage = Field(..., description="本体使用信息")
    adjustment_notes: Optional[str] = Field(None, description="调整备注")
