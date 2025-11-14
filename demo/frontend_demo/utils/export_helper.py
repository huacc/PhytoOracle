"""
导出辅助工具

提供推理数据和本体使用导出功能。
"""
import json
from typing import Dict
from datetime import datetime

from models import (
    DiagnosisResult,
    OntologyUsageExport,
    OntologyUsage,
    FuzzyMapping,
    DiseaseOntologyUsage,
    FeatureOntologyUsage,
)


def export_diagnosis_result(diagnosis_result: DiagnosisResult) -> str:
    """
    导出推理结果为JSON字符串

    Args:
        diagnosis_result: 推理结果

    Returns:
        格式化的JSON字符串
    """
    # 使用Pydantic的model_dump方法转换为字典
    result_dict = diagnosis_result.model_dump(mode='json')
    return json.dumps(result_dict, ensure_ascii=False, indent=2)


def export_ontology_usage(
    diagnosis_result: DiagnosisResult,
    adjustment_notes: str = None
) -> str:
    """
    导出本体使用信息为JSON字符串

    Args:
        diagnosis_result: 推理结果
        adjustment_notes: 调整备注

    Returns:
        格式化的JSON字符串
    """
    # 提取模糊匹配信息
    fuzzy_mappings_dict: Dict[str, list] = {}

    for scoring_result in diagnosis_result.scoring_results:
        fuzzy_mappings = []

        for match_detail in scoring_result.match_details:
            if match_detail.match_type == "fuzzy" and match_detail.synonym_mapping:
                fuzzy_mappings.append(FuzzyMapping(
                    feature=match_detail.feature_key,
                    vlm_value=match_detail.synonym_mapping.observed,
                    ontology_value=match_detail.synonym_mapping.canonical,
                    synonym_source=match_detail.synonym_mapping.synonym_source,
                    fuzzy_score=match_detail.fuzzy_score or 0.85
                ))

        if fuzzy_mappings:
            fuzzy_mappings_dict[scoring_result.disease_id] = fuzzy_mappings

    # 构建疾病本体使用列表
    disease_ontologies = []
    for scoring_result in diagnosis_result.scoring_results:
        disease_ont_usage = DiseaseOntologyUsage(
            disease_id=scoring_result.disease_id,
            file=scoring_result.ontology_file,
            version=scoring_result.version,
            matched_features=scoring_result.matched_features,
            fuzzy_mappings=fuzzy_mappings_dict.get(scoring_result.disease_id, [])
        )
        disease_ontologies.append(disease_ont_usage)

    # 构建特征本体使用
    feature_ontology_usage = FeatureOntologyUsage(
        file=diagnosis_result.ontology_usage_summary.feature_ontology.file_path,
        version=diagnosis_result.ontology_usage_summary.feature_ontology.version,
        git_commit=diagnosis_result.ontology_usage_summary.feature_ontology.git_commit,
        used_features=list(diagnosis_result.feature_extraction.keys())
    )

    # 构建完整的本体使用数据
    ontology_usage = OntologyUsage(
        feature_ontology=feature_ontology_usage,
        disease_ontologies=disease_ontologies
    )

    ontology_usage_export = OntologyUsageExport(
        diagnosis_id=diagnosis_result.diagnosis_id,
        ontology_usage=ontology_usage,
        adjustment_notes=adjustment_notes
    )

    # 转换为JSON
    export_dict = ontology_usage_export.model_dump(mode='json')
    return json.dumps(export_dict, ensure_ascii=False, indent=2)


def generate_ontology_usage_summary_text(diagnosis_result: DiagnosisResult) -> str:
    """
    生成本体使用总结文本（用于界面展示）

    Args:
        diagnosis_result: 推理结果

    Returns:
        本体使用总结文本
    """
    lines = []
    lines.append("### 使用的本体文件\n")

    # 特征本体
    feature_ont = diagnosis_result.ontology_usage_summary.feature_ontology
    lines.append(f"**特征本体**: `{feature_ont.file_path}`")
    lines.append(f"- 版本: {feature_ont.version}")
    lines.append(f"- Git Commit: {feature_ont.git_commit}")
    lines.append(f"- 使用的特征: {', '.join(diagnosis_result.feature_extraction.keys())}\n")

    # 疾病本体
    lines.append("**疾病本体**:")
    for disease_ont in diagnosis_result.ontology_usage_summary.disease_ontologies_consulted:
        lines.append(f"- `{disease_ont.file_path}` (v{disease_ont.version})")

    # 关键同义词映射
    lines.append("\n### 关键同义词映射\n")
    has_fuzzy = False

    for scoring_result in diagnosis_result.scoring_results:
        for match_detail in scoring_result.match_details:
            if match_detail.match_type == "fuzzy" and match_detail.synonym_mapping:
                has_fuzzy = True
                sm = match_detail.synonym_mapping
                lines.append(
                    f"- **{match_detail.feature_key}**: \"{sm.observed}\" → \"{sm.canonical}\" "
                    f"(fuzzy match, score: {match_detail.fuzzy_score})"
                )
                lines.append(f"  - 同义词来源: `{sm.synonym_source}`")

    if not has_fuzzy:
        lines.append("*无模糊匹配*")

    return "\n".join(lines)
