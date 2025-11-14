"""
P2.3 知识库加载器单元测试

测试范围：
- KnowledgeBaseLoader: 知识库加载器
- DiseaseIndexer: 疾病索引器
- FeatureMatcher: 特征匹配器
- KnowledgeBaseManager: 知识库管理器（单例）

测试策略：
- 使用真实数据（backend/knowledge_base/下的JSON文件）
- 不使用mock（验收要求）
- 测试成功和失败场景
- 验证数据完整性和一致性
"""

import pytest
from pathlib import Path

from backend.infrastructure.ontology import (
    KnowledgeBaseManager,
    KnowledgeBaseLoader,
    DiseaseIndexer,
    FeatureMatcher,
    KnowledgeBaseNotFoundError,
    KnowledgeBaseLoadError,
    KnowledgeBaseValidationError
)
from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology
from backend.domain.plant import PlantOntology
from backend.domain.diagnosis import (
    FeatureVector,
    ContentType,
    PlantCategory,
    FlowerGenus,
    OrganType,
    Completeness,
    AbnormalityStatus,
    ConfidenceLevel
)


# ========== Fixtures ==========

@pytest.fixture(scope="module")
def kb_path():
    """知识库路径（使用相对路径）"""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    return project_root / "backend" / "knowledge_base"


@pytest.fixture(scope="module")
def loader(kb_path):
    """知识库加载器（module级别，避免重复加载）"""
    return KnowledgeBaseLoader(kb_path)


@pytest.fixture(scope="module")
def indexer(loader):
    """疾病索引器"""
    diseases = loader.get_all_diseases()
    return DiseaseIndexer(diseases)


@pytest.fixture(scope="module")
def matcher(loader):
    """特征匹配器"""
    feature_ontology = loader.get_feature_ontology()
    return FeatureMatcher(feature_ontology)


@pytest.fixture
def rose_black_spot_feature_vector():
    """玫瑰黑斑病的典型特征向量"""
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


# ========== 测试：KnowledgeBaseLoader ==========

class TestKnowledgeBaseLoader:
    """知识库加载器测试"""

    def test_loader_initialization(self, kb_path):
        """测试加载器初始化"""
        loader = KnowledgeBaseLoader(kb_path)
        assert loader is not None
        assert loader.kb_path == kb_path

    def test_load_all_diseases(self, loader):
        """测试加载所有疾病本体"""
        diseases = loader.load_all_diseases()

        # 验收标准：至少加载2种疾病（Rose Black Spot + Cherry Powdery Mildew）
        assert len(diseases) >= 2

        # 验证疾病本体类型
        for disease in diseases:
            assert isinstance(disease, DiseaseOntology)
            assert disease.disease_id
            assert disease.disease_name
            assert disease.pathogen

    def test_load_specific_disease(self, loader):
        """测试加载特定疾病（rose_black_spot）"""
        disease = loader.get_disease_by_id("rose_black_spot")

        # 验收标准：可通过 get_disease_by_id() 查询
        assert disease is not None
        assert disease.disease_id == "rose_black_spot"
        assert disease.disease_name == "玫瑰黑斑病"
        assert disease.common_name_en == "Rose Black Spot"
        assert "Rosa" in disease.host_plants

    def test_load_feature_ontology(self, loader):
        """测试加载特征本体"""
        feature_ontology = loader.load_feature_ontology()

        assert feature_ontology is not None
        assert isinstance(feature_ontology, FeatureOntology)
        assert feature_ontology.version
        assert len(feature_ontology.dimensions) > 0
        assert len(feature_ontology.fuzzy_matching) > 0

    def test_load_plants(self, loader):
        """测试加载植物本体"""
        plants = loader.load_all_plants()

        # 至少应该有Rosa和Prunus（从疾病中提取或从JSON加载）
        assert len(plants) >= 2

        # 验证植物本体类型
        for plant in plants:
            assert isinstance(plant, PlantOntology)
            assert plant.genus

    def test_get_diseases_by_host(self, loader):
        """测试根据宿主植物查询候选疾病"""
        disease_ids = loader.get_diseases_by_host("Rosa")

        # Rosa属至少应该有1种疾病（rose_black_spot）
        assert len(disease_ids) >= 1
        assert "rose_black_spot" in disease_ids

    def test_reload(self, loader):
        """测试热重载"""
        # 记录重载前的疾病数量
        diseases_before = loader.get_all_diseases()
        count_before = len(diseases_before)

        # 执行重载
        loader.reload()

        # 验证重载后疾病数量一致
        diseases_after = loader.get_all_diseases()
        count_after = len(diseases_after)

        # 验收标准：热更新机制验证（reload()生效）
        assert count_after == count_before

    def test_loader_invalid_path(self):
        """测试加载器初始化失败（路径不存在）"""
        with pytest.raises(KnowledgeBaseNotFoundError):
            KnowledgeBaseLoader(Path("/non/exist/path"))


# ========== 测试：DiseaseIndexer ==========

class TestDiseaseIndexer:
    """疾病索引器测试"""

    def test_indexer_initialization(self, indexer):
        """测试索引器初始化"""
        assert indexer is not None
        assert len(indexer.diseases) >= 2

    def test_get_by_host(self, indexer):
        """测试按宿主植物索引"""
        candidates = indexer.get_by_host("Rosa")

        # Rosa属至少应该有1种疾病
        assert len(candidates) >= 1

        # 验证所有候选疾病都包含Rosa宿主
        for disease in candidates:
            assert "Rosa" in disease.host_plants

    def test_get_by_symptom_type(self, indexer):
        """测试按症状类型索引"""
        candidates = indexer.get_by_symptom_type("necrosis_spot")

        # 至少应该有1种具有坏死斑点症状的疾病
        assert len(candidates) >= 1

    def test_get_by_color_center(self, indexer):
        """测试按中心颜色索引"""
        candidates = indexer.get_by_color_center("black")

        # 至少应该有1种症状中心为黑色的疾病
        assert len(candidates) >= 1

    def test_get_by_color_border(self, indexer):
        """测试按边缘颜色索引"""
        candidates = indexer.get_by_color_border("yellow")

        # 至少应该有1种症状边缘为黄色的疾病（rose_black_spot）
        assert len(candidates) >= 1

    def test_get_by_symptom(self, indexer):
        """测试按症状特征组合索引"""
        candidates = indexer.get_by_symptom("necrosis_spot", "black")

        # 至少应该有1种疾病同时满足两个条件
        assert len(candidates) >= 1

    def test_get_by_id(self, indexer):
        """测试按疾病ID索引"""
        disease = indexer.get_by_id("rose_black_spot")

        assert disease is not None
        assert disease.disease_id == "rose_black_spot"

    def test_get_all_hosts(self, indexer):
        """测试获取所有宿主植物"""
        hosts = indexer.get_all_hosts()

        # 至少应该有2个宿主植物（Rosa, Prunus）
        assert len(hosts) >= 2
        assert "Rosa" in hosts

    def test_get_statistics(self, indexer):
        """测试获取统计信息"""
        stats = indexer.get_statistics()

        assert stats["total_diseases"] >= 2
        assert stats["total_hosts"] >= 2
        assert stats["total_symptom_keys"] > 0


# ========== 测试：FeatureMatcher ==========

class TestFeatureMatcher:
    """特征匹配器测试"""

    def test_matcher_initialization(self, matcher):
        """测试匹配器初始化"""
        assert matcher is not None
        assert matcher.feature_ontology is not None

    def test_match_disease_perfect(self, matcher, loader, rose_black_spot_feature_vector):
        """测试完美匹配（玫瑰黑斑病）"""
        disease = loader.get_disease_by_id("rose_black_spot")
        score, reasoning = matcher.match_disease(rose_black_spot_feature_vector, disease)

        # 验证评分对象
        assert score.total_score > 0.6  # 合理的匹配分数（注意：实际知识库主要特征匹配可能不是满分）
        assert score.major_matched >= 1  # 至少匹配1个主要特征
        assert score.confidence_level in [ConfidenceLevel.CONFIRMED, ConfidenceLevel.SUSPECTED]  # 确诊或疑似

        # 验证推理细节
        assert reasoning["disease_id"] == "rose_black_spot"
        assert reasoning["disease_name"] == "玫瑰黑斑病"
        assert "major_features_detail" in reasoning

    def test_match_disease_mismatch(self, matcher, loader, rose_black_spot_feature_vector):
        """测试不匹配（樱花白粉病 vs 玫瑰黑斑病特征）"""
        disease = loader.get_disease_by_id("cherry_powdery_mildew")
        if disease:
            score, reasoning = matcher.match_disease(rose_black_spot_feature_vector, disease)

            # 验证评分对象（不匹配应该得分很低）
            assert score.total_score < 0.6  # 低分
            assert score.confidence_level != ConfidenceLevel.CONFIRMED  # 非确诊

    def test_match_color_exact(self, matcher):
        """测试颜色精确匹配"""
        is_matched, score = matcher._match_color("black", ["black", "brown"])
        assert is_matched is True
        assert score == 1.0

    def test_match_color_fuzzy(self, matcher):
        """测试颜色模糊匹配（颜色别名）"""
        is_matched, score = matcher._match_color("deep_black", ["black"])

        # 应该通过颜色别名匹配
        assert is_matched is True
        assert score < 1.0  # 模糊匹配得分略低

    def test_match_size_exact(self, matcher):
        """测试尺寸精确匹配"""
        is_matched, score = matcher._match_size("medium", ["medium"])
        assert is_matched is True
        assert score == 1.0

    def test_match_size_tolerance(self, matcher):
        """测试尺寸容差匹配（±1级）"""
        is_matched, score = matcher._match_size("medium", ["medium_small"])

        # 应该通过相邻级别匹配
        assert is_matched is True
        assert score < 1.0  # 容差匹配得分略低


# ========== 测试：KnowledgeBaseManager ==========

class TestKnowledgeBaseManager:
    """知识库管理器测试（单例模式）"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = KnowledgeBaseManager.get_instance()
        manager2 = KnowledgeBaseManager.get_instance()

        # 验证两次获取的实例是否相同
        assert manager1 is manager2

    def test_manager_get_disease_by_id(self):
        """测试通过管理器查询疾病"""
        manager = KnowledgeBaseManager.get_instance()
        disease = manager.get_disease_by_id("rose_black_spot")

        # 验收标准：可通过 knowledge_base.get_disease_by_id() 查询
        assert disease is not None
        assert disease.disease_id == "rose_black_spot"

    def test_manager_get_diseases_by_host(self):
        """测试通过管理器按宿主植物查询"""
        manager = KnowledgeBaseManager.get_instance()
        candidates = manager.get_diseases_by_host("Rosa")

        assert len(candidates) >= 1

    def test_manager_match_disease(self, rose_black_spot_feature_vector):
        """测试通过管理器匹配疾病"""
        manager = KnowledgeBaseManager.get_instance()
        disease = manager.get_disease_by_id("rose_black_spot")

        score, reasoning = manager.match_disease(rose_black_spot_feature_vector, disease)

        assert score.total_score > 0.6  # 合理的匹配分数
        assert score.confidence_level in [ConfidenceLevel.CONFIRMED, ConfidenceLevel.SUSPECTED]

    def test_manager_match_all_candidates(self, rose_black_spot_feature_vector):
        """测试通过管理器批量匹配候选疾病"""
        manager = KnowledgeBaseManager.get_instance()
        candidates = manager.get_diseases_by_host("Rosa")

        results = manager.match_all_candidates(rose_black_spot_feature_vector, candidates)

        # 验证结果排序（按得分从高到低）
        assert len(results) >= 1
        for i in range(len(results) - 1):
            assert results[i][1].total_score >= results[i + 1][1].total_score

    def test_manager_reload(self):
        """测试通过管理器热重载"""
        manager = KnowledgeBaseManager.get_instance()

        # 记录重载前的疾病数量
        count_before = len(manager.get_all_diseases())

        # 执行重载
        manager.reload()

        # 验证重载后疾病数量一致
        count_after = len(manager.get_all_diseases())

        # 验收标准：热更新机制验证（修改JSON文件后调用reload()生效）
        assert count_after == count_before

    def test_manager_get_statistics(self):
        """测试获取统计信息"""
        manager = KnowledgeBaseManager.get_instance()
        stats = manager.get_statistics()

        assert stats["total_diseases"] >= 2
        assert stats["total_hosts"] >= 2
        assert "feature_ontology_version" in stats


# ========== 集成测试 ==========

class TestIntegration:
    """集成测试：完整的知识库查询和匹配流程"""

    def test_full_workflow(self, rose_black_spot_feature_vector):
        """测试完整的诊断流程"""
        # 1. 获取知识库管理器
        manager = KnowledgeBaseManager.get_instance()

        # 2. 根据宿主植物获取候选疾病
        candidates = manager.get_diseases_by_host("Rosa")
        assert len(candidates) >= 1

        # 3. 批量匹配候选疾病
        results = manager.match_all_candidates(rose_black_spot_feature_vector, candidates)
        assert len(results) >= 1

        # 4. 获取最佳匹配
        best_disease, best_score, best_reasoning = results[0]

        # 5. 验证最佳匹配是玫瑰黑斑病（最高分）
        assert best_disease.disease_id == "rose_black_spot"
        assert best_score.total_score > 0.5  # 合理的匹配分数
        assert best_score.confidence_level in [ConfidenceLevel.CONFIRMED, ConfidenceLevel.SUSPECTED, ConfidenceLevel.UNLIKELY]


if __name__ == "__main__":
    """
    运行测试：
    pytest backend/tests/unit/test_p2_3_knowledge_base.py -v
    """
    pytest.main([__file__, "-v", "-s"])
