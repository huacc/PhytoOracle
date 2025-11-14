"""
P2.5 加权诊断评分器 - 单元测试

测试范围：
1. WeightedDiagnosisScorer初始化
2. 单个疾病评分
3. 完整性修正系数
4. 批量评分和排序
5. 权重热重载
6. 权重信息查询
7. 集成测试（完整诊断流程）
8. 边界条件测试

测试原则：
- 使用真实数据（backend/knowledge_base/下的JSON文件）
- 不使用mock返回结果
- 验证三层渐进诊断逻辑
- 验证权重配置化功能
"""

import pytest
from pathlib import Path
from backend.infrastructure.ontology import WeightedDiagnosisScorer
from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
from backend.domain.diagnosis import (
    FeatureVector, ConfidenceLevel, ContentType, PlantCategory,
    FlowerGenus, OrganType, Completeness, AbnormalityStatus
)


@pytest.fixture
def project_root():
    """
    获取项目根目录

    Returns:
        Path: 项目根目录路径
    """
    return Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def kb_path(project_root):
    """
    获取知识库路径

    Returns:
        Path: 知识库路径
    """
    return project_root / "backend" / "knowledge_base"


@pytest.fixture
def weights_dir(project_root):
    """
    获取权重配置目录

    Returns:
        Path: 权重配置目录
    """
    return project_root / "backend" / "infrastructure" / "ontology" / "scoring_weights"


@pytest.fixture
def fuzzy_rules_dir(project_root):
    """
    获取模糊匹配规则目录

    Returns:
        Path: 模糊匹配规则目录
    """
    return project_root / "backend" / "infrastructure" / "ontology" / "fuzzy_rules"


@pytest.fixture
def scorer(kb_path, weights_dir, fuzzy_rules_dir):
    """
    初始化WeightedDiagnosisScorer

    Returns:
        WeightedDiagnosisScorer: 加权诊断评分器实例
    """
    return WeightedDiagnosisScorer(kb_path, weights_dir, fuzzy_rules_dir)


@pytest.fixture
def loader(kb_path):
    """
    初始化KnowledgeBaseLoader

    Returns:
        KnowledgeBaseLoader: 知识库加载器实例
    """
    return KnowledgeBaseLoader(kb_path)


@pytest.fixture
def rose_feature_vector():
    """
    构造玫瑰黑斑病的典型特征向量（完整器官）

    Returns:
        FeatureVector: 特征向量
    """
    return FeatureVector(
        content_type=ContentType.PLANT,
        plant_category=PlantCategory.FLOWER,
        flower_genus=FlowerGenus.ROSA,
        organ=OrganType.LEAF,
        completeness=Completeness.COMPLETE,
        has_abnormality=AbnormalityStatus.ABNORMAL,
        symptom_type="necrosis_spot",
        color_center="black",
        color_border="yellow",
        location="lamina",
        size="medium",
        distribution="scattered"
    )


@pytest.fixture
def rose_disease(loader):
    """
    加载玫瑰黑斑病

    Returns:
        DiseaseOntology: 玫瑰黑斑病本体
    """
    disease = loader.get_disease_by_id("rose_black_spot")
    assert disease is not None, "玫瑰黑斑病不存在"
    return disease


class TestWeightedDiagnosisScorerInitialization:
    """测试WeightedDiagnosisScorer的初始化"""

    def test_scorer_initialization_success(self, scorer):
        """测试正常初始化"""
        assert scorer is not None
        assert scorer.feature_matcher is not None
        assert scorer.fuzzy_engine is not None
        assert scorer.weights_dir.exists()
        assert scorer.feature_weights is not None
        assert scorer.importance_weights is not None
        assert scorer.completeness_weights is not None

    def test_scorer_initialization_without_fuzzy_engine(self, kb_path, weights_dir):
        """测试不使用FuzzyMatchingEngine的初始化"""
        scorer = WeightedDiagnosisScorer(kb_path, weights_dir, None)
        assert scorer is not None
        assert scorer.fuzzy_engine is None

    def test_scorer_initialization_with_invalid_weights_dir(self, kb_path):
        """测试无效的权重配置目录"""
        with pytest.raises(FileNotFoundError):
            invalid_weights_dir = Path("/nonexistent/weights")
            WeightedDiagnosisScorer(kb_path, invalid_weights_dir, None)


class TestSingleDiseaseScoring:
    """测试单个疾病评分"""

    def test_score_rose_disease_complete_organ(self, scorer, rose_feature_vector, rose_disease):
        """测试玫瑰黑斑病评分（完整器官）"""
        score, reasoning = scorer.score_disease(rose_feature_vector, rose_disease)

        # 验证返回结果
        assert score is not None
        assert reasoning is not None

        # 验证DiagnosisScore对象
        assert 0 <= score.total_score <= 1.0
        assert score.major_matched >= 0
        assert score.major_total >= 0
        assert score.confidence_level in [
            ConfidenceLevel.CONFIRMED,
            ConfidenceLevel.SUSPECTED,
            ConfidenceLevel.UNLIKELY
        ]

        # 验证推理细节
        assert reasoning["disease_id"] == "rose_black_spot"
        assert reasoning["disease_name"] == "玫瑰黑斑病"
        assert "total_score_before_correction" in reasoning
        assert "completeness_coefficient" in reasoning
        assert reasoning["completeness_coefficient"] == 1.0  # 完整器官无修正

        # 验证主要特征匹配（应该匹配2/2）
        assert score.major_matched == 2
        assert score.major_total == 2

    def test_score_rose_disease_partial_organ(self, scorer, rose_disease):
        """测试玫瑰黑斑病评分（部分器官）"""
        # 构造部分器官的特征向量
        partial_feature_vector = FeatureVector(
            content_type=ContentType.PLANT,
            plant_category=PlantCategory.FLOWER,
            flower_genus=FlowerGenus.ROSA,
            organ=OrganType.LEAF,
            completeness=Completeness.PARTIAL,  # 部分器官
            has_abnormality=AbnormalityStatus.ABNORMAL,
            symptom_type="necrosis_spot",
            color_center="black",
            color_border="yellow",
            location="lamina",
            size="medium",
            distribution="scattered"
        )

        score, reasoning = scorer.score_disease(partial_feature_vector, rose_disease)

        # 验证完整性修正系数
        assert reasoning["completeness_coefficient"] == 0.8

        # 验证修正后的总分低于修正前
        assert score.total_score < reasoning["total_score_before_correction"]

    def test_score_rose_disease_closeup(self, scorer, rose_disease):
        """测试玫瑰黑斑病评分（特写镜头）"""
        # 构造特写镜头的特征向量
        closeup_feature_vector = FeatureVector(
            content_type=ContentType.PLANT,
            plant_category=PlantCategory.FLOWER,
            flower_genus=FlowerGenus.ROSA,
            organ=OrganType.LEAF,
            completeness=Completeness.CLOSE_UP,  # 特写镜头
            has_abnormality=AbnormalityStatus.ABNORMAL,
            symptom_type="necrosis_spot",
            color_center="black",
            color_border="yellow",
            location="lamina",
            size="medium",
            distribution="scattered"
        )

        score, reasoning = scorer.score_disease(closeup_feature_vector, rose_disease)

        # 验证完整性修正系数
        assert reasoning["completeness_coefficient"] == 0.6

        # 验证修正后的总分低于修正前
        assert score.total_score < reasoning["total_score_before_correction"]


class TestCompletenessCorrection:
    """测试完整性修正系数"""

    def test_completeness_complete(self, scorer):
        """测试完整器官的修正系数"""
        coeff = scorer._get_completeness_coefficient(Completeness.COMPLETE)
        assert coeff == 1.0

    def test_completeness_partial(self, scorer):
        """测试部分器官的修正系数"""
        coeff = scorer._get_completeness_coefficient(Completeness.PARTIAL)
        assert coeff == 0.8

    def test_completeness_closeup(self, scorer):
        """测试特写镜头的修正系数"""
        coeff = scorer._get_completeness_coefficient(Completeness.CLOSE_UP)
        assert coeff == 0.6


class TestBatchScoring:
    """测试批量评分和排序"""

    def test_score_candidates(self, scorer, rose_feature_vector, loader):
        """测试批量评分候选疾病"""
        candidates = loader.get_all_diseases()
        assert len(candidates) >= 2

        ranked_results = scorer.score_candidates(rose_feature_vector, candidates)

        # 验证返回结果
        assert len(ranked_results) == len(candidates)

        # 验证排序（按total_score降序）
        for i in range(len(ranked_results) - 1):
            current_score = ranked_results[i][1].total_score
            next_score = ranked_results[i + 1][1].total_score
            assert current_score >= next_score

        # 验证Top1应该是玫瑰黑斑病
        top1_disease, top1_score, top1_reasoning = ranked_results[0]
        assert top1_disease.disease_id == "rose_black_spot"
        assert top1_score.total_score > 0.5


class TestWeightsReload:
    """测试权重热重载"""

    def test_reload_weights(self, scorer):
        """测试热重载权重配置"""
        # 记录初始加载时间
        initial_loaded_time = scorer.last_loaded

        # 等待一小段时间
        import time
        time.sleep(0.1)

        # 重载权重
        scorer.reload_weights()

        # 验证加载时间已更新
        assert scorer.last_loaded > initial_loaded_time


class TestWeightsInfo:
    """测试权重信息查询"""

    def test_get_weights_info(self, scorer):
        """测试获取权重配置信息"""
        info = scorer.get_weights_info()

        # 验证返回结果包含所有必要字段
        assert "weights_dir" in info
        assert "last_loaded" in info
        assert "feature_weights_version" in info
        assert "importance_weights_version" in info
        assert "completeness_weights_version" in info
        assert "major_weight" in info
        assert "minor_weight" in info
        assert "optional_weight" in info
        assert "confirmed_threshold" in info
        assert "suspected_threshold" in info
        assert "completeness_coefficients" in info

        # 验证权重值
        assert info["major_weight"] == 0.8
        assert info["minor_weight"] == 0.15
        assert info["optional_weight"] == 0.05

        # 验证阈值
        assert info["confirmed_threshold"] == 0.85
        assert info["suspected_threshold"] == 0.6

        # 验证完整性系数
        completeness_coeffs = info["completeness_coefficients"]
        assert completeness_coeffs["complete"] == 1.0
        assert completeness_coeffs["partial"] == 0.8
        assert completeness_coeffs["close_up"] == 0.6


class TestThreeLayerDiagnosisLogic:
    """测试三层渐进诊断逻辑"""

    def test_confirmed_diagnosis(self, scorer, rose_feature_vector, rose_disease):
        """测试确诊逻辑（total_score ≥ 0.85 且 major_matched ≥ 2/2）"""
        score, reasoning = scorer.score_disease(rose_feature_vector, rose_disease)

        # 根据实际评分判断
        if score.total_score >= 0.85 and score.major_matched >= score.major_total:
            assert score.confidence_level == ConfidenceLevel.CONFIRMED
        elif score.total_score >= 0.6 and score.major_matched >= score.major_total / 2:
            assert score.confidence_level == ConfidenceLevel.SUSPECTED
        else:
            assert score.confidence_level == ConfidenceLevel.UNLIKELY

    def test_suspected_diagnosis(self, scorer, rose_disease):
        """测试疑似诊断逻辑（0.60 ≤ total_score < 0.85 且 major_matched ≥ 1/2）"""
        # 构造部分匹配的特征向量（主要特征只匹配1/2）
        suspected_feature_vector = FeatureVector(
            content_type=ContentType.PLANT,
            plant_category=PlantCategory.FLOWER,
            flower_genus=FlowerGenus.ROSA,
            organ=OrganType.LEAF,
            completeness=Completeness.COMPLETE,
            has_abnormality=AbnormalityStatus.ABNORMAL,
            symptom_type="necrosis_spot",  # 匹配
            color_center="brown",  # 不完全匹配
            color_border="brown",  # 不匹配
            location="lamina",
            size="small",
            distribution="scattered"
        )

        score, reasoning = scorer.score_disease(suspected_feature_vector, rose_disease)

        # 验证置信度级别
        if score.total_score >= 0.85 and score.major_matched >= score.major_total:
            assert score.confidence_level == ConfidenceLevel.CONFIRMED
        elif score.total_score >= 0.6 and score.major_matched >= score.major_total / 2:
            assert score.confidence_level == ConfidenceLevel.SUSPECTED
        else:
            assert score.confidence_level == ConfidenceLevel.UNLIKELY

    def test_unlikely_diagnosis(self, scorer, rose_disease):
        """测试不太可能诊断逻辑（total_score < 0.60 或 major_matched < 1/2）"""
        # 构造完全不匹配的特征向量
        unlikely_feature_vector = FeatureVector(
            content_type=ContentType.PLANT,
            plant_category=PlantCategory.FLOWER,
            flower_genus=FlowerGenus.ROSA,
            organ=OrganType.LEAF,
            completeness=Completeness.COMPLETE,
            has_abnormality=AbnormalityStatus.ABNORMAL,
            symptom_type="powdery_coating",  # 不匹配
            color_center="white",  # 不匹配
            color_border="white",  # 不匹配
            location="lamina",
            size="small",
            distribution="scattered"
        )

        score, reasoning = scorer.score_disease(unlikely_feature_vector, rose_disease)

        # 应该是不太可能
        assert score.confidence_level == ConfidenceLevel.UNLIKELY


class TestIntegration:
    """集成测试（完整诊断流程）"""

    def test_full_diagnosis_workflow(self, scorer, rose_feature_vector, loader):
        """测试完整的诊断流程"""
        # 1. 获取候选疾病（模拟Q0.2剪枝）
        candidate_ids = loader.get_diseases_by_host("Rosa")
        assert len(candidate_ids) >= 1

        # 将疾病ID转换为疾病对象
        candidates = [loader.get_disease_by_id(disease_id) for disease_id in candidate_ids]
        candidates = [d for d in candidates if d is not None]  # 过滤None

        # 2. 批量评分候选疾病
        ranked_results = scorer.score_candidates(rose_feature_vector, candidates)

        # 3. 获取最佳匹配
        best_disease, best_score, best_reasoning = ranked_results[0]

        # 验证最佳匹配
        assert best_disease.disease_id == "rose_black_spot"
        assert best_score.total_score > 0.5

        # 4. 根据置信度级别处理
        if best_score.confidence_level == ConfidenceLevel.CONFIRMED:
            # 确诊
            assert best_score.total_score >= 0.85
            assert best_score.major_matched >= best_score.major_total
        elif best_score.confidence_level == ConfidenceLevel.SUSPECTED:
            # 疑似，返回Top 2-3
            top_3 = ranked_results[:min(3, len(ranked_results))]
            assert len(top_3) >= 1
        else:
            # 不太可能
            assert best_score.total_score < 0.6 or best_score.major_matched < best_score.major_total / 2


def main():
    """
    运行测试

    使用pytest运行所有测试用例
    """
    import sys
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    main()
