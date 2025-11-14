"""
知识库管理器

功能：
- 提供全局唯一的知识库访问接口（单例模式）
- 统一管理知识库加载器、索引器、匹配器
- 支持热重载（管理后台调用 reload() 方法）
- 为诊断引擎提供高层次的知识库查询API

类清单：
- KnowledgeBaseManager: 知识库管理器（单例）
"""

from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology
from backend.domain.plant import PlantOntology
from backend.domain.diagnosis import FeatureVector, DiagnosisScore

from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
from backend.infrastructure.ontology.indexer import DiseaseIndexer
from backend.infrastructure.ontology.matcher import FeatureMatcher
from backend.infrastructure.ontology.exceptions import KnowledgeBaseError


class KnowledgeBaseManager:
    """
    知识库管理器（单例模式）

    提供全局唯一的知识库访问接口，统一管理：
    1. 知识库加载器（KnowledgeBaseLoader）
    2. 疾病索引器（DiseaseIndexer）
    3. 特征匹配器（FeatureMatcher）

    使用示例（推荐方式）：
    ```python
    # 方式1：使用 get_instance() 获取单例
    manager = KnowledgeBaseManager.get_instance()

    # 方式2：直接实例化（自动返回单例）
    manager = KnowledgeBaseManager()

    # 查询候选疾病
    candidates = manager.get_diseases_by_host("Rosa")

    # 匹配疾病
    score, reasoning = manager.match_disease(feature_vector, disease)

    # 热重载知识库
    manager.reload()
    ```

    注意事项：
    - 单例模式确保全局只有一个知识库实例
    - 避免重复加载知识库，节省内存
    - 支持热重载，无需重启服务
    """

    _instance: Optional['KnowledgeBaseManager'] = None
    _lock = False  # 简单的锁机制，避免重复初始化

    def __new__(cls):
        """
        单例模式实现

        确保全局只有一个 KnowledgeBaseManager 实例

        Returns:
            KnowledgeBaseManager: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, kb_path: Optional[Path] = None):
        """
        初始化知识库管理器

        Args:
            kb_path: 知识库根目录路径（可选，默认使用项目根目录下的 backend/knowledge_base）

        注意：
        - 如果已经初始化过，再次调用 __init__ 不会重新初始化
        - 如果需要重新加载知识库，请调用 reload() 方法
        """
        # 避免重复初始化
        if self._initialized:
            return

        # 确定知识库路径
        if kb_path is None:
            # 使用相对路径（推荐）
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            kb_path = project_root / "backend" / "knowledge_base"

        self.kb_path = kb_path

        # 初始化加载器
        self.loader = KnowledgeBaseLoader(kb_path)

        # 初始化索引器
        diseases = self.loader.get_all_diseases()
        self.indexer = DiseaseIndexer(diseases)

        # 初始化匹配器
        feature_ontology = self.loader.get_feature_ontology()
        if feature_ontology:
            self.matcher = FeatureMatcher(feature_ontology)
        else:
            raise KnowledgeBaseError("特征本体加载失败，无法初始化匹配器")

        # 标记为已初始化
        self._initialized = True

    @classmethod
    def get_instance(cls, kb_path: Optional[Path] = None) -> 'KnowledgeBaseManager':
        """
        获取知识库管理器实例（单例）

        Args:
            kb_path: 知识库根目录路径（可选，仅在首次调用时有效）

        Returns:
            KnowledgeBaseManager: 知识库管理器实例

        示例：
        ```python
        # 方式1：使用默认路径
        manager = KnowledgeBaseManager.get_instance()

        # 方式2：指定自定义路径（仅在首次调用时有效）
        custom_path = Path("/custom/knowledge_base")
        manager = KnowledgeBaseManager.get_instance(custom_path)
        ```
        """
        if cls._instance is None or not cls._instance._initialized:
            instance = cls.__new__(cls)
            instance.__init__(kb_path)
            cls._instance = instance
        return cls._instance

    # ========== 知识库查询API ==========

    def get_disease_by_id(self, disease_id: str) -> Optional[DiseaseOntology]:
        """
        根据疾病ID获取疾病本体

        Args:
            disease_id: 疾病ID（如 "rose_black_spot"）

        Returns:
            Optional[DiseaseOntology]: 疾病本体对象，如果不存在则返回None

        示例：
        ```python
        disease = manager.get_disease_by_id("rose_black_spot")
        if disease:
            print(f"疾病名称: {disease.disease_name}")
        ```
        """
        return self.indexer.get_by_id(disease_id)

    def get_all_diseases(self) -> List[DiseaseOntology]:
        """
        获取所有疾病本体

        Returns:
            List[DiseaseOntology]: 疾病本体列表
        """
        return self.indexer.get_all_diseases()

    def get_diseases_by_host(self, genus: str) -> List[DiseaseOntology]:
        """
        根据宿主植物获取候选疾病

        Args:
            genus: 植物属名（如 "Rosa"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表

        示例：
        ```python
        candidates = manager.get_diseases_by_host("Rosa")
        print(f"Rosa属候选疾病数: {len(candidates)}")
        ```
        """
        return self.indexer.get_by_host(genus)

    def get_diseases_by_hosts(self, genera: List[str]) -> List[DiseaseOntology]:
        """
        根据多个宿主植物获取候选疾病（并集）

        Args:
            genera: 植物属名列表（如 ["Rosa", "Prunus"]）

        Returns:
            List[DiseaseOntology]: 候选疾病列表（去重）
        """
        return self.indexer.get_by_hosts(genera)

    def get_diseases_by_symptom_type(self, symptom_type: str) -> List[DiseaseOntology]:
        """
        根据症状类型获取候选疾病

        Args:
            symptom_type: 症状类型（如 "necrosis_spot"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表
        """
        return self.indexer.get_by_symptom_type(symptom_type)

    def get_feature_ontology(self) -> Optional[FeatureOntology]:
        """
        获取特征本体

        Returns:
            Optional[FeatureOntology]: 特征本体对象
        """
        return self.loader.get_feature_ontology()

    def get_all_plants(self) -> List[PlantOntology]:
        """
        获取所有植物本体

        Returns:
            List[PlantOntology]: 植物本体列表
        """
        return self.loader.get_all_plants()

    def get_all_hosts(self) -> List[str]:
        """
        获取所有宿主植物属名

        Returns:
            List[str]: 宿主植物属名列表
        """
        return self.indexer.get_all_hosts()

    # ========== 特征匹配API ==========

    def match_disease(
        self,
        feature_vector: FeatureVector,
        disease: DiseaseOntology
    ) -> Tuple[DiagnosisScore, Dict[str, Any]]:
        """
        匹配疾病，返回综合评分和推理细节

        Args:
            feature_vector: 提取的特征向量
            disease: 疾病本体

        Returns:
            Tuple[DiagnosisScore, Dict[str, Any]]: (诊断评分, 推理细节)

        示例：
        ```python
        disease = manager.get_disease_by_id("rose_black_spot")
        score, reasoning = manager.match_disease(feature_vector, disease)

        print(f"疾病: {reasoning['disease_name']}")
        print(f"总分: {score.total_score:.2f}")
        print(f"主要特征匹配: {score.major_matched}/{score.major_total}")
        print(f"置信度级别: {score.confidence_level}")
        ```
        """
        return self.matcher.match_disease(feature_vector, disease)

    def match_all_candidates(
        self,
        feature_vector: FeatureVector,
        candidates: List[DiseaseOntology]
    ) -> List[Tuple[DiseaseOntology, DiagnosisScore, Dict[str, Any]]]:
        """
        批量匹配候选疾病，返回排序后的结果

        Args:
            feature_vector: 提取的特征向量
            candidates: 候选疾病列表

        Returns:
            List[Tuple[DiseaseOntology, DiagnosisScore, Dict[str, Any]]]:
                排序后的匹配结果列表，每个元素为 (疾病, 评分, 推理细节)
                按总分从高到低排序

        示例：
        ```python
        candidates = manager.get_diseases_by_host("Rosa")
        results = manager.match_all_candidates(feature_vector, candidates)

        for disease, score, reasoning in results:
            print(f"{disease.disease_name}: {score.total_score:.2f} ({score.confidence_level})")
        ```
        """
        results = []
        for disease in candidates:
            score, reasoning = self.matcher.match_disease(feature_vector, disease)
            results.append((disease, score, reasoning))

        # 按总分从高到低排序
        results.sort(key=lambda x: x[1].total_score, reverse=True)

        return results

    # ========== 热重载API ==========

    def reload(self) -> None:
        """
        热重载知识库

        重新加载所有知识库文件，更新索引和匹配器

        使用场景：
        - 管理后台修改了疾病本体JSON文件
        - 管理后台添加了新的疾病
        - 需要立即生效，不重启服务

        示例：
        ```python
        # 管理后台调用
        manager.reload()
        print("知识库已重新加载")
        ```
        """
        # 重新加载知识库
        self.loader.reload()

        # 重建索引
        diseases = self.loader.get_all_diseases()
        self.indexer = DiseaseIndexer(diseases)

        # 重建匹配器
        feature_ontology = self.loader.get_feature_ontology()
        if feature_ontology:
            self.matcher = FeatureMatcher(feature_ontology)
        else:
            raise KnowledgeBaseError("特征本体加载失败，无法重建匹配器")

    # ========== 统计API ==========

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Returns:
            Dict[str, Any]: 统计信息字典

        示例：
        ```python
        stats = manager.get_statistics()
        print(f"疾病总数: {stats['total_diseases']}")
        print(f"宿主植物数: {stats['total_hosts']}")
        ```
        """
        indexer_stats = self.indexer.get_statistics()

        return {
            "total_diseases": indexer_stats["total_diseases"],
            "total_hosts": indexer_stats["total_hosts"],
            "total_plants": len(self.loader.get_all_plants()),
            "feature_ontology_version": self.loader.get_feature_ontology().version if self.loader.get_feature_ontology() else "Unknown",
            "kb_path": str(self.kb_path),
            "indexer_stats": indexer_stats
        }


def main():
    """
    KnowledgeBaseManager 使用示例

    演示如何：
    1. 获取单例实例
    2. 查询疾病
    3. 匹配疾病
    4. 批量匹配候选疾病
    5. 热重载知识库
    6. 获取统计信息
    """
    from backend.domain.diagnosis import FeatureVector, ContentType, PlantCategory, FlowerGenus, OrganType, Completeness, AbnormalityStatus

    print("=" * 80)
    print("KnowledgeBaseManager 使用示例")
    print("=" * 80)

    # 1. 获取单例实例
    print("\n[示例1] 获取知识库管理器单例实例")
    manager = KnowledgeBaseManager.get_instance()
    print(f"  [OK] 单例实例获取成功")

    # 验证单例模式
    manager2 = KnowledgeBaseManager.get_instance()
    print(f"  [验证] 两次获取的实例是否相同: {manager is manager2}")

    # 2. 查询疾病
    print("\n[示例2] 查询疾病")
    disease = manager.get_disease_by_id("rose_black_spot")
    if disease:
        print(f"  [OK] 找到疾病: {disease.disease_name}")
        print(f"    - ID: {disease.disease_id}")
        print(f"    - 病原体: {disease.pathogen}")
        print(f"    - 宿主植物: {', '.join(disease.host_plants)}")

    # 3. 根据宿主植物查询候选疾病
    print("\n[示例3] 根据宿主植物查询候选疾病")
    candidates = manager.get_diseases_by_host("Rosa")
    print(f"  宿主植物: Rosa")
    print(f"  候选疾病数: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name}")

    # 4. 构造测试特征向量
    print("\n[示例4] 构造测试特征向量")
    feature_vector = FeatureVector(
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
    print(f"  [OK] 特征向量构造成功")

    # 5. 匹配单个疾病
    print("\n[示例5] 匹配单个疾病（玫瑰黑斑病）")
    if disease:
        score, reasoning = manager.match_disease(feature_vector, disease)
        print(f"  疾病: {reasoning['disease_name']}")
        print(f"  总分: {score.total_score:.3f}")
        print(f"  主要特征匹配: {score.major_matched}/{score.major_total}")
        print(f"  置信度级别: {score.confidence_level}")

    # 6. 批量匹配候选疾病
    print("\n[示例6] 批量匹配候选疾病")
    results = manager.match_all_candidates(feature_vector, candidates)
    print(f"  候选疾病数: {len(results)}")
    print(f"  匹配结果（按得分排序）:")
    for disease, score, reasoning in results:
        print(f"    - {disease.disease_name}: {score.total_score:.3f} ({score.confidence_level})")

    # 7. 获取所有宿主植物
    print("\n[示例7] 获取所有宿主植物")
    hosts = manager.get_all_hosts()
    print(f"  宿主植物数: {len(hosts)}")
    print(f"  宿主植物列表: {', '.join(hosts)}")

    # 8. 获取统计信息
    print("\n[示例8] 获取知识库统计信息")
    stats = manager.get_statistics()
    print(f"  疾病总数: {stats['total_diseases']}")
    print(f"  宿主植物数: {stats['total_hosts']}")
    print(f"  植物本体数: {stats['total_plants']}")
    print(f"  特征本体版本: {stats['feature_ontology_version']}")
    print(f"  知识库路径: {stats['kb_path']}")

    # 9. 热重载知识库（模拟）
    print("\n[示例9] 热重载知识库")
    print(f"  重载前疾病数: {len(manager.get_all_diseases())}")
    try:
        manager.reload()
        print(f"  [OK] 知识库重载成功")
        print(f"  重载后疾病数: {len(manager.get_all_diseases())}")
    except Exception as e:
        print(f"  [FAIL] 知识库重载失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
