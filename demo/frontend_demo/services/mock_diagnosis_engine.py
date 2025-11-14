"""
假数据推理引擎

根据图片文件名解析疾病类型，生成完整的推理链路数据。
"""
import re
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from models import (
    DiagnosisResult,
    OntologyReference,
    Q0StepResult,
    FeatureExtractionResult,
    SynonymMapping,
    MismatchExplanation,
    MatchDetail,
    CandidateDisease,
    ScoringResult,
    FinalDiagnosis,
    PerformanceMetrics,
    OntologyUsageSummary,
)
from services.mock_knowledge_service import get_knowledge_service
from config import (
    Q0_QUESTIONS,
    FEATURE_EXTRACTION_KEYS,
    CONFIDENCE_THRESHOLDS,
    CONFIDENCE_RANGES,
    FEATURE_IMPORTANCE_WEIGHTS,
    COMPLETENESS_MODIFIERS,
    FUZZY_MATCH_THRESHOLD,
    EXACT_MATCH_SCORE,
    FUZZY_MATCH_SCORE,
    VLM_PROVIDER,
    RANDOM_SEED,
    DISEASES_DIR,
    FEATURE_ONTOLOGY_FILE,
)


class MockDiagnosisEngine:
    """假数据推理引擎"""

    def __init__(self):
        """初始化推理引擎"""
        self.kb_service = get_knowledge_service()
        random.seed(RANDOM_SEED)  # 设置随机种子，保证一致性

    def diagnose(self, image_path: str, image_name: str) -> DiagnosisResult:
        """
        执行诊断推理（基于文件名解析）

        Args:
            image_path: 图片路径
            image_name: 图片文件名

        Returns:
            完整的推理结果
        """
        # 1. 解析文件名，获取疾病类型
        disease_type = self._parse_disease_from_filename(image_name)

        # 如果无法识别，随机选择一个疾病作为演示
        if not disease_type:
            available_diseases = list(self.kb_service.diseases.keys())
            if available_diseases:
                disease_type = random.choice(available_diseases)
                print(f"[Demo] 无法从文件名识别疾病，随机选择 '{disease_type}' 作为演示")

        # 2. 生成诊断ID和图片ID
        diagnosis_id = f"diag_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
        image_id = f"img_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"

        # 3. 生成Q0序列
        q0_sequence, flower_genus, completeness = self._generate_q0_sequence(disease_type)

        # 4. 生成Q1-Q6特征提取
        feature_extraction = self._generate_feature_extraction(disease_type)

        # 5. 筛选候选疾病
        candidate_diseases = self._filter_candidates(flower_genus)

        # 6. 计算加权评分
        scoring_results = self._calculate_scoring(
            feature_extraction,
            candidate_diseases,
            completeness,
            disease_type
        )

        # 7. 确定最终诊断
        final_diagnosis = self._determine_final_diagnosis(scoring_results[0])

        # 8. 生成本体使用总览
        ontology_usage_summary = self._generate_ontology_usage_summary(candidate_diseases)

        # 9. 生成性能指标
        performance = self._generate_performance_metrics()

        # 10. 组装完整结果
        return DiagnosisResult(
            diagnosis_id=diagnosis_id,
            image_id=image_id,
            timestamp=datetime.now(),
            ontology_usage_summary=ontology_usage_summary,
            q0_sequence=q0_sequence,
            feature_extraction=feature_extraction,
            candidate_diseases=candidate_diseases,
            scoring_results=scoring_results,
            final_diagnosis=final_diagnosis,
            performance=performance
        )

    def _parse_disease_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名解析疾病类型

        Args:
            filename: 文件名（如 "rose_black_spot_001.jpg"）

        Returns:
            疾病ID（如 "rose_black_spot"），如果无法解析返回None
        """
        # 移除文件扩展名
        name_without_ext = Path(filename).stem

        # 尝试匹配已知疾病ID模式
        for disease_id in self.kb_service.diseases.keys():
            if disease_id in name_without_ext.lower():
                return disease_id

        return None

    def _generate_q0_sequence(
        self,
        disease_type: Optional[str]
    ) -> Tuple[Dict[str, Q0StepResult], str, str]:
        """
        生成Q0序列结果

        Args:
            disease_type: 疾病类型

        Returns:
            (Q0序列结果字典, 花属, 完整性)
        """
        q0_results = {}

        # 获取疾病信息（如果有）
        disease_data = None
        if disease_type:
            disease_data = self.kb_service.get_disease(disease_type)

        # Q0.0: content_type
        q0_results["q0_0_content_type"] = Q0StepResult(
            choice="plant",
            confidence=self._random_confidence("correct_q0"),
            reasoning="Image shows plant tissue with disease symptoms",
            ontology_reference=OntologyReference(
                source="Q0.0 prompt definition",
                valid_choices=Q0_QUESTIONS["q0_0_content_type"]["choices"]
            )
        )

        # Q0.1: plant_category
        q0_results["q0_1_plant_category"] = Q0StepResult(
            choice="flower",
            confidence=self._random_confidence("correct_q0"),
            reasoning="Ornamental flowering plant visible",
            ontology_reference=OntologyReference(
                source="Q0.1 prompt definition",
                valid_choices=Q0_QUESTIONS["q0_1_plant_category"]["choices"]
            )
        )

        # Q0.2: flower_genus（关键：决定候选疾病）
        if disease_data:
            flower_genus = disease_data['host_plants'][0]
        else:
            flower_genus = "Unknown"

        q0_results["q0_2_flower_genus"] = Q0StepResult(
            choice=flower_genus,
            confidence=self._random_confidence("correct_q0"),
            reasoning=f"Identified as {flower_genus} based on leaf and flower morphology",
            ontology_reference=OntologyReference(
                source="knowledge_base disease definitions → host_plants field",
                valid_choices=self.kb_service.get_all_genera() + ["Unknown"]
            )
        )

        # Q0.3: organ_type
        q0_results["q0_3_organ_type"] = Q0StepResult(
            choice="leaf",
            confidence=self._random_confidence("correct_q0"),
            reasoning="Leaf structures visible with disease symptoms",
            ontology_reference=OntologyReference(
                source="Q0.3 prompt definition",
                valid_choices=Q0_QUESTIONS["q0_3_organ_type"]["choices"]
            )
        )

        # Q0.4: completeness（影响评分修正系数）
        completeness = "close_up"
        q0_results["q0_4_completeness"] = Q0StepResult(
            choice=completeness,
            confidence=self._random_confidence("correct_q0"),
            reasoning="Close-up view of affected area",
            ontology_reference=OntologyReference(
                source="Q0.4 prompt definition",
                valid_choices=Q0_QUESTIONS["q0_4_completeness"]["choices"]
            )
        )

        # Q0.5: abnormality
        q0_results["q0_5_abnormality"] = Q0StepResult(
            choice="abnormal",
            confidence=self._random_confidence("correct_q0"),
            reasoning="Clear disease symptoms observed",
            ontology_reference=OntologyReference(
                source="Q0.5 prompt definition",
                valid_choices=Q0_QUESTIONS["q0_5_abnormality"]["choices"]
            )
        )

        return q0_results, flower_genus, completeness

    def _generate_feature_extraction(
        self,
        disease_type: Optional[str]
    ) -> Dict[str, FeatureExtractionResult]:
        """
        生成Q1-Q6特征提取结果

        Args:
            disease_type: 疾病类型

        Returns:
            特征提取结果字典
        """
        results = {}

        disease_data = None
        if disease_type:
            disease_data = self.kb_service.get_disease(disease_type)

        if disease_data:
            # 根据疾病定义生成特征
            feature_vector = disease_data['feature_vector']
            all_features = {
                **feature_vector.get('major', {}),
                **feature_vector.get('minor', {}),
                **feature_vector.get('optional', {})
            }

            for feature_key in FEATURE_EXTRACTION_KEYS:
                if feature_key in all_features:
                    expected_value = all_features[feature_key]

                    # 可能使用同义词（模拟VLM识别的不确定性）
                    observed_value = expected_value
                    if random.random() < 0.3:  # 30%概率使用同义词
                        synonyms = self.kb_service.get_synonyms(feature_key, expected_value)
                        if synonyms:
                            observed_value = random.choice(synonyms)

                    feature_def = self.kb_service.get_feature_definition(feature_key)
                    results[feature_key] = FeatureExtractionResult(
                        choice=observed_value,
                        confidence=self._random_confidence("correct_q1_q6"),
                        reasoning=f"Observed {feature_key}: {observed_value}",
                        ontology_reference=OntologyReference(
                            source="feature_ontology.json",
                            feature_key=feature_key,
                            valid_choices=feature_def.get('values', []) if feature_def else [],
                            definition=feature_def.get('description', "") if feature_def else ""
                        )
                    )
                else:
                    # 特征不存在于疾病定义中，随机生成
                    feature_def = self.kb_service.get_feature_definition(feature_key)
                    if feature_def:
                        values = feature_def.get('values', [])
                        results[feature_key] = FeatureExtractionResult(
                            choice=random.choice(values) if values else "unknown",
                            confidence=self._random_confidence("correct_q1_q6") - 0.1,
                            reasoning=f"Uncertain {feature_key}",
                            ontology_reference=OntologyReference(
                                source="feature_ontology.json",
                                feature_key=feature_key,
                                valid_choices=values,
                                definition=feature_def.get('description', "")
                            )
                        )
        else:
            # 没有疾病信息，随机生成
            for feature_key in FEATURE_EXTRACTION_KEYS:
                feature_def = self.kb_service.get_feature_definition(feature_key)
                if feature_def:
                    values = feature_def.get('values', [])
                    results[feature_key] = FeatureExtractionResult(
                        choice=random.choice(values) if values else "unknown",
                        confidence=self._random_confidence("incorrect_q1_q6"),
                        reasoning=f"Detected {feature_key}",
                        ontology_reference=OntologyReference(
                            source="feature_ontology.json",
                            feature_key=feature_key,
                            valid_choices=values,
                            definition=feature_def.get('description', "")
                        )
                    )

        return results

    def _filter_candidates(self, flower_genus: str) -> List[CandidateDisease]:
        """
        筛选候选疾病

        Args:
            flower_genus: 花属

        Returns:
            候选疾病列表
        """
        candidates = []
        diseases = self.kb_service.get_diseases_by_genus(flower_genus)

        for disease_data in diseases:
            disease_file = DISEASES_DIR / f"{disease_data['disease_id']}_{disease_data['version']}.json"
            candidates.append(CandidateDisease(
                disease_id=disease_data['disease_id'],
                disease_name=disease_data['disease_name'],
                disease_name_en=disease_data['disease_name_en'],
                ontology_file=str(disease_file),
                version=disease_data['version']
            ))

        return candidates

    def _calculate_scoring(
        self,
        feature_extraction: Dict[str, FeatureExtractionResult],
        candidate_diseases: List[CandidateDisease],
        completeness: str,
        target_disease_type: Optional[str]
    ) -> List[ScoringResult]:
        """
        计算加权评分

        Args:
            feature_extraction: 特征提取结果
            candidate_diseases: 候选疾病列表
            completeness: 完整性
            target_disease_type: 目标疾病类型（用于确保正确疾病得分最高）

        Returns:
            评分结果列表（降序排列）
        """
        results = []

        for candidate in candidate_diseases:
            disease_data = self.kb_service.get_disease(candidate.disease_id)
            if not disease_data:
                continue

            # 计算匹配详情
            match_details = self._calculate_match_details(
                feature_extraction,
                disease_data
            )

            # 计算各级别分数
            major_score = self._calculate_importance_score(match_details, "major")
            minor_score = self._calculate_importance_score(match_details, "minor")
            optional_score = self._calculate_importance_score(match_details, "optional")

            # 应用完整性修正系数
            completeness_modifier = COMPLETENESS_MODIFIERS.get(completeness, 0.6)

            # 计算总分
            total_score = (
                major_score * FEATURE_IMPORTANCE_WEIGHTS["major"] +
                minor_score * FEATURE_IMPORTANCE_WEIGHTS["minor"] +
                optional_score * FEATURE_IMPORTANCE_WEIGHTS["optional"]
            ) * completeness_modifier

            # 如果是目标疾病，确保分数最高
            if target_disease_type and candidate.disease_id == target_disease_type:
                total_score = max(total_score, 0.88)  # 确保至少是confirmed级别

            # 确定置信度级别
            confidence_level = self._determine_confidence_level(total_score)

            # 统计匹配和未匹配特征
            matched_features = {"major": [], "minor": [], "optional": []}
            unmatched_features = {"major": [], "minor": [], "optional": []}

            for detail in match_details:
                if detail.match_type in ["exact", "fuzzy"]:
                    matched_features[detail.importance_level].append(detail.feature_key)
                else:
                    unmatched_features[detail.importance_level].append(detail.feature_key)

            results.append(ScoringResult(
                disease_id=candidate.disease_id,
                disease_name=candidate.disease_name,
                ontology_file=candidate.ontology_file,
                version=candidate.version,
                total_score=round(total_score, 2),
                confidence_level=confidence_level,
                major_score=round(major_score, 2),
                minor_score=round(minor_score, 2),
                optional_score=round(optional_score, 2),
                completeness_modifier=completeness_modifier,
                matched_features=matched_features,
                unmatched_features=unmatched_features,
                match_details=match_details
            ))

        # 按总分降序排列
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results

    def _calculate_match_details(
        self,
        feature_extraction: Dict[str, FeatureExtractionResult],
        disease_data: Dict
    ) -> List[MatchDetail]:
        """
        计算详细匹配信息

        Args:
            feature_extraction: 特征提取结果
            disease_data: 疾病定义数据

        Returns:
            匹配详情列表
        """
        details = []
        feature_vector = disease_data['feature_vector']

        for importance_level in ["major", "minor", "optional"]:
            expected_features = feature_vector.get(importance_level, {})

            for feature_key, expected_value in expected_features.items():
                if feature_key not in feature_extraction:
                    continue

                observed_value = feature_extraction[feature_key].choice

                # 查找标准值和匹配类型
                canonical_value, is_exact = self.kb_service.find_canonical_value(
                    feature_key,
                    observed_value
                )

                # 判断匹配类型
                if canonical_value == expected_value:
                    if is_exact:
                        match_type = "exact"
                        fuzzy_score = None
                        synonym_mapping = None
                    else:
                        match_type = "fuzzy"
                        fuzzy_score = FUZZY_MATCH_SCORE
                        synonym_mapping = SynonymMapping(
                            observed=observed_value,
                            canonical=canonical_value,
                            synonym_source=f"{FEATURE_ONTOLOGY_FILE.name} → {feature_key} → synonyms",
                            synonyms_list=self.kb_service.get_synonyms(feature_key, expected_value),
                            match_explanation=f"VLM识别的 '{observed_value}' 匹配到疾病定义中 '{expected_value}' 的同义词"
                        )
                else:
                    match_type = "no_match"
                    fuzzy_score = None
                    synonym_mapping = None

                # 计算贡献分数
                if match_type == "exact":
                    contribution_base = EXACT_MATCH_SCORE
                elif match_type == "fuzzy":
                    contribution_base = FUZZY_MATCH_SCORE
                else:
                    contribution_base = 0.0

                # 根据重要性级别调整贡献
                num_features = len(expected_features)
                contribution = contribution_base * FEATURE_IMPORTANCE_WEIGHTS[importance_level] / num_features if num_features > 0 else 0

                # 本体引用
                ontology_ref = OntologyReference(
                    source=f"{FEATURE_ONTOLOGY_FILE.name} → {feature_key}",
                    feature_key=feature_key
                )

                # 不匹配说明
                mismatch_explanation = None
                if match_type == "no_match":
                    expected_synonyms = [expected_value] + self.kb_service.get_synonyms(feature_key, expected_value)
                    mismatch_explanation = MismatchExplanation(
                        reason=f"VLM识别的 '{observed_value}' 不在 '{expected_value}' 的同义词列表中",
                        expected_synonyms=expected_synonyms,
                        ontology_reference=f"{FEATURE_ONTOLOGY_FILE.name} → {feature_key} → synonyms → {expected_value}"
                    )

                details.append(MatchDetail(
                    feature_key=feature_key,
                    importance_level=importance_level,
                    observed_value=observed_value,
                    expected_value=expected_value,
                    match_type=match_type,
                    fuzzy_score=fuzzy_score,
                    contribution=round(contribution, 2),
                    synonym_mapping=synonym_mapping,
                    mismatch_explanation=mismatch_explanation,
                    ontology_reference=ontology_ref
                ))

        return details

    def _calculate_importance_score(
        self,
        match_details: List[MatchDetail],
        importance_level: str
    ) -> float:
        """
        计算某个重要性级别的总分

        Args:
            match_details: 匹配详情列表
            importance_level: 重要性级别

        Returns:
            该级别的总分（0-1之间）
        """
        level_details = [d for d in match_details if d.importance_level == importance_level]
        if not level_details:
            return 0.0

        total_contribution = sum(d.contribution for d in level_details)
        max_contribution = FEATURE_IMPORTANCE_WEIGHTS[importance_level]

        return min(total_contribution / max_contribution, 1.0) if max_contribution > 0 else 0.0

    def _determine_confidence_level(self, total_score: float) -> str:
        """
        根据总分确定置信度级别

        Args:
            total_score: 总分

        Returns:
            置信度级别：confirmed/suspected/unlikely
        """
        for level, (min_score, max_score) in CONFIDENCE_THRESHOLDS.items():
            if min_score <= total_score <= max_score:
                return level
        return "unlikely"

    def _determine_final_diagnosis(self, top_scoring_result: ScoringResult) -> FinalDiagnosis:
        """
        确定最终诊断结果

        Args:
            top_scoring_result: 得分最高的疾病

        Returns:
            最终诊断结果
        """
        disease_data = self.kb_service.get_disease(top_scoring_result.disease_id)

        return FinalDiagnosis(
            disease_id=top_scoring_result.disease_id,
            disease_name=top_scoring_result.disease_name,
            disease_name_en=disease_data['disease_name_en'],
            confidence_level=top_scoring_result.confidence_level,
            confidence_score=top_scoring_result.total_score,
            pathogen=disease_data['pathogen']['scientific_name'],
            treatment_suggestions=disease_data['treatment_suggestions'],
            ontology_file=top_scoring_result.ontology_file,
            version=top_scoring_result.version,
            git_commit=disease_data.get('git_commit', 'unknown')
        )

    def _generate_ontology_usage_summary(
        self,
        candidate_diseases: List[CandidateDisease]
    ) -> OntologyUsageSummary:
        """
        生成本体使用总览

        Args:
            candidate_diseases: 候选疾病列表

        Returns:
            本体使用总览
        """
        version_info = self.kb_service.get_ontology_version_info()

        return OntologyUsageSummary(
            feature_ontology=OntologyUsageSummary.FeatureOntologyInfo(
                file_path=str(FEATURE_ONTOLOGY_FILE),
                version=version_info['version'],
                git_commit=version_info['git_commit']
            ),
            disease_ontologies_consulted=[
                OntologyUsageSummary.DiseaseOntologyInfo(
                    disease_id=candidate.disease_id,
                    file_path=candidate.ontology_file,
                    version=candidate.version
                )
                for candidate in candidate_diseases
            ]
        )

    def _generate_performance_metrics(self) -> PerformanceMetrics:
        """
        生成性能指标（假数据）

        Returns:
            性能指标
        """
        q0_time = round(random.uniform(1.0, 1.5), 2)
        q1_q6_time = round(random.uniform(1.8, 2.5), 2)
        matching_time = round(random.uniform(0.5, 1.0), 2)
        total_time = q0_time + q1_q6_time + matching_time

        return PerformanceMetrics(
            total_elapsed_time=round(total_time, 2),
            q0_time=q0_time,
            q1_q6_time=q1_q6_time,
            matching_time=matching_time,
            vlm_provider=VLM_PROVIDER
        )

    def _random_confidence(self, range_key: str) -> float:
        """
        生成随机置信度

        Args:
            range_key: 置信度范围键（如 "correct_q0"）

        Returns:
            置信度分数
        """
        min_val, max_val = CONFIDENCE_RANGES.get(range_key, (0.5, 0.9))
        return round(random.uniform(min_val, max_val), 2)


# 全局单例
def get_diagnosis_engine() -> MockDiagnosisEngine:
    """获取推理引擎单例"""
    return MockDiagnosisEngine()
