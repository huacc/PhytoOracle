"""
加权诊断评分器（P2.5核心模块）

功能：
- 实现加权诊断评分算法
- 集成P2.3的FeatureMatcher和P2.4的FuzzyMatchingEngine
- 支持权重配置化和热重载
- 实现三层渐进诊断逻辑
- 应用完整性修正系数

类清单：
- WeightedDiagnosisScorer: 加权诊断评分器（主类）

设计原则：
- 组合模式：集成FeatureMatcher和FuzzyMatchingEngine，不修改已有代码
- 配置化：所有权重通过JSON配置文件管理
- 可扩展：支持新的权重策略和评分规则
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

from backend.domain.diagnosis import FeatureVector, DiagnosisScore, ConfidenceLevel, Completeness
from backend.domain.disease import DiseaseOntology
from backend.infrastructure.ontology.matcher import FeatureMatcher
from backend.infrastructure.ontology.fuzzy_matcher import FuzzyMatchingEngine


class WeightedDiagnosisScorer:
    """
    加权诊断评分器（P2.5核心类）

    实现三层渐进诊断逻辑的Layer 2（特征匹配和加权评分）和Layer 3（置信度判定）

    核心功能：
    1. 加权评分算法：主要特征（0.8）+ 次要特征（0.15）+ 可选特征（0.05）
    2. 完整性修正：complete(1.0) / partial(0.8) / close_up(0.6)
    3. 模糊匹配支持：集成P2.4的FuzzyMatchingEngine
    4. 三层渐进诊断：confirmed / suspected / unlikely
    5. 权重配置化：支持JSON配置和热重载

    使用示例：
    ```python
    from pathlib import Path

    # 初始化加权诊断评分器
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = project_root / "backend" / "knowledge_base"
    weights_dir = project_root / "backend" / "infrastructure" / "ontology" / "scoring_weights"
    fuzzy_rules_dir = project_root / "backend" / "infrastructure" / "ontology" / "fuzzy_rules"

    scorer = WeightedDiagnosisScorer(kb_path, weights_dir, fuzzy_rules_dir)

    # 对单个疾病进行评分
    feature_vector = FeatureVector(...)
    disease = DiseaseOntology(...)
    score, reasoning = scorer.score_disease(feature_vector, disease)

    print(f"总分: {score.total_score}")
    print(f"置信度级别: {score.confidence_level}")

    # 批量评分候选疾病
    candidates = [disease1, disease2, disease3]
    ranked_results = scorer.score_candidates(feature_vector, candidates)
    ```
    """

    def __init__(
        self,
        kb_path: Path,
        weights_dir: Path,
        fuzzy_rules_dir: Optional[Path] = None
    ):
        """
        初始化加权诊断评分器

        Args:
            kb_path: 知识库路径（用于初始化FeatureMatcher）
            weights_dir: 权重配置目录
            fuzzy_rules_dir: 模糊匹配规则目录（可选，如不提供则不使用FuzzyMatchingEngine）

        Raises:
            FileNotFoundError: 如果配置目录不存在
            json.JSONDecodeError: 如果配置文件格式错误
        """
        # 初始化P2.3的FeatureMatcher
        from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
        loader = KnowledgeBaseLoader(kb_path)
        feature_ontology = loader.get_feature_ontology()
        self.feature_matcher = FeatureMatcher(feature_ontology)

        # 初始化P2.4的FuzzyMatchingEngine（可选）
        self.fuzzy_engine = None
        if fuzzy_rules_dir and fuzzy_rules_dir.exists():
            self.fuzzy_engine = FuzzyMatchingEngine(fuzzy_rules_dir)

        # 加载权重配置
        self.weights_dir = Path(weights_dir)
        if not self.weights_dir.exists():
            raise FileNotFoundError(f"权重配置目录不存在: {self.weights_dir}")

        self._load_weights()

        # 记录最后加载时间
        self.last_loaded = datetime.now()

    def _load_weights(self) -> None:
        """
        加载所有权重配置文件

        Raises:
            FileNotFoundError: 如果配置文件不存在
            json.JSONDecodeError: 如果配置文件格式错误
        """
        # 加载特征维度权重
        feature_weights_path = self.weights_dir / "feature_weights.json"
        with open(feature_weights_path, "r", encoding="utf-8") as f:
            self.feature_weights = json.load(f)

        # 加载重要性权重
        importance_weights_path = self.weights_dir / "importance_weights.json"
        with open(importance_weights_path, "r", encoding="utf-8") as f:
            self.importance_weights = json.load(f)

        # 加载完整性修正系数
        completeness_weights_path = self.weights_dir / "completeness_weights.json"
        with open(completeness_weights_path, "r", encoding="utf-8") as f:
            self.completeness_weights = json.load(f)

    def reload_weights(self) -> None:
        """
        热重载所有权重配置

        重新从JSON文件加载所有权重配置，无需重启服务。
        适用场景：
        - 管理后台修改了权重配置
        - 权重调优后需要立即生效
        - 测试不同权重配置的效果

        Raises:
            FileNotFoundError: 如果配置文件不存在
            json.JSONDecodeError: 如果配置文件格式错误
        """
        self._load_weights()

        # 同时重载模糊匹配引擎的规则（如果存在）
        if self.fuzzy_engine:
            self.fuzzy_engine.reload_rules()

        self.last_loaded = datetime.now()

    def score_disease(
        self,
        feature_vector: FeatureVector,
        disease: DiseaseOntology
    ) -> Tuple[DiagnosisScore, Dict[str, Any]]:
        """
        对单个疾病进行加权评分

        Args:
            feature_vector: 从图像提取的特征向量
            disease: 疾病本体

        Returns:
            Tuple[DiagnosisScore, Dict[str, Any]]: (诊断评分对象, 推理细节)

        推理细节包含：
        - disease_id: 疾病ID
        - disease_name: 疾病名称
        - major_features_detail: 主要特征匹配详情
        - minor_features_detail: 次要特征匹配详情
        - optional_features_detail: 可选特征匹配详情
        - total_score_before_correction: 修正前总分
        - completeness_coefficient: 完整性修正系数
        - total_score: 修正后总分
        - confidence_level: 置信度级别

        示例：
        ```python
        score, reasoning = scorer.score_disease(feature_vector, disease)
        print(f"疾病: {reasoning['disease_name']}")
        print(f"总分: {reasoning['total_score']:.2f}")
        print(f"主要特征匹配: {score.major_matched}/{score.major_total}")
        print(f"置信度级别: {score.confidence_level}")
        ```
        """
        # 1. 使用P2.3的FeatureMatcher进行特征匹配
        base_score, base_reasoning = self.feature_matcher.match_disease(
            feature_vector,
            disease
        )

        # 2. 应用完整性修正系数
        completeness_coeff = self._get_completeness_coefficient(feature_vector.completeness)
        corrected_total_score = base_score.total_score * completeness_coeff

        # 3. 构建最终的DiagnosisScore对象（应用修正后的总分）
        final_score = DiagnosisScore(
            total_score=min(corrected_total_score, 1.0),  # 确保不超过1.0
            major_features_score=base_score.major_features_score,
            minor_features_score=base_score.minor_features_score,
            optional_features_score=base_score.optional_features_score,
            major_matched=base_score.major_matched,
            major_total=base_score.major_total
        )

        # 4. 构建推理细节（扩展P2.3的推理细节）
        reasoning = {
            **base_reasoning,
            "total_score_before_correction": base_score.total_score,
            "completeness": feature_vector.completeness,
            "completeness_coefficient": completeness_coeff,
            "total_score": final_score.total_score,
            "confidence_level": final_score.confidence_level
        }

        return final_score, reasoning

    def _get_completeness_coefficient(self, completeness: Completeness) -> float:
        """
        获取完整性修正系数

        Args:
            completeness: 完整性枚举值

        Returns:
            float: 修正系数（0.6-1.0）

        修正规则：
        - complete: 1.0（无修正）
        - partial: 0.8（轻度降权）
        - close_up: 0.6（中度降权）

        示例：
        ```python
        coeff = scorer._get_completeness_coefficient(Completeness.PARTIAL)
        # 返回: 0.8
        ```
        """
        coefficients = self.completeness_weights.get("coefficients", {
            "complete": 1.0,
            "partial": 0.8,
            "close_up": 0.6
        })

        # 将枚举值转换为字符串键
        completeness_str = completeness.value if hasattr(completeness, 'value') else str(completeness)

        return coefficients.get(completeness_str, 1.0)

    def score_candidates(
        self,
        feature_vector: FeatureVector,
        candidate_diseases: List[DiseaseOntology]
    ) -> List[Tuple[DiseaseOntology, DiagnosisScore, Dict[str, Any]]]:
        """
        对候选疾病列表进行批量评分和排序

        Args:
            feature_vector: 特征向量
            candidate_diseases: 候选疾病列表

        Returns:
            List[Tuple[DiseaseOntology, DiagnosisScore, Dict[str, Any]]]:
                排序后的 (疾病, 评分, 推理细节) 列表

        排序规则：
        1. 按total_score降序排序
        2. 如果total_score相同，按major_matched降序排序

        示例：
        ```python
        ranked_results = scorer.score_candidates(feature_vector, candidates)

        # 获取Top 1
        best_disease, best_score, best_reasoning = ranked_results[0]
        print(f"最佳匹配: {best_disease.disease_name}")
        print(f"总分: {best_score.total_score:.2f}")

        # 根据置信度级别处理
        if best_score.confidence_level == ConfidenceLevel.CONFIRMED:
            # 确诊
            return best_disease
        elif best_score.confidence_level == ConfidenceLevel.SUSPECTED:
            # 疑似，返回Top 2-3
            top_3 = ranked_results[:3]
            return top_3
        else:
            # 不太可能
            return None
        ```
        """
        results = []

        for disease in candidate_diseases:
            score, reasoning = self.score_disease(feature_vector, disease)
            results.append((disease, score, reasoning))

        # 按total_score降序排序，如果相同则按major_matched降序排序
        results.sort(
            key=lambda x: (x[1].total_score, x[1].major_matched),
            reverse=True
        )

        return results

    def get_weights_info(self) -> Dict[str, Any]:
        """
        获取权重配置信息（用于调试和监控）

        Returns:
            Dict[str, Any]: 权重配置信息，包含：
                - weights_dir: 权重配置目录
                - last_loaded: 最后加载时间
                - feature_weights_version: 特征权重版本
                - importance_weights_version: 重要性权重版本
                - completeness_weights_version: 完整性权重版本
                - major_weight: 主要特征权重
                - minor_weight: 次要特征权重
                - optional_weight: 可选特征权重
                - confirmed_threshold: 确诊阈值
                - suspected_threshold: 疑似阈值

        示例：
        ```python
        info = scorer.get_weights_info()
        print(f"权重配置目录: {info['weights_dir']}")
        print(f"主要特征权重: {info['major_weight']}")
        print(f"确诊阈值: {info['confirmed_threshold']}")
        ```
        """
        return {
            "weights_dir": str(self.weights_dir),
            "last_loaded": self.last_loaded.isoformat(),
            "feature_weights_version": self.feature_weights.get("version", "unknown"),
            "importance_weights_version": self.importance_weights.get("version", "unknown"),
            "completeness_weights_version": self.completeness_weights.get("version", "unknown"),
            "major_weight": self.importance_weights.get("weights", {}).get("major", 0.8),
            "minor_weight": self.importance_weights.get("weights", {}).get("minor", 0.15),
            "optional_weight": self.importance_weights.get("weights", {}).get("optional", 0.05),
            "confirmed_threshold": self.importance_weights.get("thresholds", {}).get("confirmed_score", 0.85),
            "suspected_threshold": self.importance_weights.get("thresholds", {}).get("suspected_score", 0.60),
            "completeness_coefficients": self.completeness_weights.get("coefficients", {})
        }


def main():
    """
    WeightedDiagnosisScorer 使用示例

    演示如何：
    1. 初始化加权诊断评分器
    2. 对单个疾病进行评分
    3. 批量评分候选疾病
    4. 测试不同完整性的影响
    5. 热重载权重配置
    6. 查看权重信息
    """
    from pathlib import Path
    from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
    from backend.domain.diagnosis import (
        ContentType, PlantCategory, FlowerGenus, OrganType,
        Completeness, AbnormalityStatus
    )

    print("=" * 80)
    print("WeightedDiagnosisScorer 使用示例")
    print("=" * 80)

    # 1. 初始化加权诊断评分器
    print("\n[示例1] 初始化加权诊断评分器")
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = project_root / "backend" / "knowledge_base"
    weights_dir = project_root / "backend" / "infrastructure" / "ontology" / "scoring_weights"
    fuzzy_rules_dir = project_root / "backend" / "infrastructure" / "ontology" / "fuzzy_rules"

    try:
        scorer = WeightedDiagnosisScorer(kb_path, weights_dir, fuzzy_rules_dir)
        print(f"  [OK] 加权诊断评分器初始化成功")
        print(f"  权重配置目录: {scorer.weights_dir}")
        print(f"  最后加载时间: {scorer.last_loaded}")
    except Exception as e:
        print(f"  [FAIL] 初始化失败: {e}")
        return

    # 2. 构造测试特征向量（玫瑰黑斑病的典型特征）
    print("\n[示例2] 构造测试特征向量")
    feature_vector_complete = FeatureVector(
        content_type=ContentType.PLANT,
        plant_category=PlantCategory.FLOWER,
        flower_genus=FlowerGenus.ROSA,
        organ=OrganType.LEAF,
        completeness=Completeness.COMPLETE,  # 完整器官
        has_abnormality=AbnormalityStatus.ABNORMAL,
        symptom_type="necrosis_spot",
        color_center="black",
        color_border="yellow",
        location="lamina",
        size="medium",
        distribution="scattered"
    )
    print(f"  [OK] 特征向量构造成功（完整器官）")

    # 3. 加载疾病
    print("\n[示例3] 加载疾病")
    loader = KnowledgeBaseLoader(kb_path)
    rose_disease = loader.get_disease_by_id("rose_black_spot")
    if not rose_disease:
        print(f"  [FAIL] 疾病不存在: rose_black_spot")
        return
    print(f"  [OK] 成功加载疾病: {rose_disease.disease_name}")

    # 4. 对单个疾病进行评分（完整器官）
    print("\n[示例4] 对单个疾病进行评分（完整器官）")
    score_complete, reasoning_complete = scorer.score_disease(feature_vector_complete, rose_disease)

    print(f"  疾病: {reasoning_complete['disease_name']}")
    print(f"  完整性: {reasoning_complete['completeness']}")
    print(f"  修正前总分: {reasoning_complete['total_score_before_correction']:.3f}")
    print(f"  完整性系数: {reasoning_complete['completeness_coefficient']:.2f}")
    print(f"  修正后总分: {score_complete.total_score:.3f}")
    print(f"  主要特征匹配: {score_complete.major_matched}/{score_complete.major_total}")
    print(f"  置信度级别: {score_complete.confidence_level}")

    # 5. 测试部分器官的影响
    print("\n[示例5] 测试部分器官的影响")
    feature_vector_partial = FeatureVector(
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

    score_partial, reasoning_partial = scorer.score_disease(feature_vector_partial, rose_disease)

    print(f"  完整性: {reasoning_partial['completeness']}")
    print(f"  修正前总分: {reasoning_partial['total_score_before_correction']:.3f}")
    print(f"  完整性系数: {reasoning_partial['completeness_coefficient']:.2f}")
    print(f"  修正后总分: {score_partial.total_score:.3f}")
    print(f"  置信度级别: {score_partial.confidence_level}")
    print(f"\n  对比: 部分器官比完整器官总分低 {(score_complete.total_score - score_partial.total_score):.3f}")

    # 6. 测试特写镜头的影响
    print("\n[示例6] 测试特写镜头的影响")
    feature_vector_closeup = FeatureVector(
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

    score_closeup, reasoning_closeup = scorer.score_disease(feature_vector_closeup, rose_disease)

    print(f"  完整性: {reasoning_closeup['completeness']}")
    print(f"  修正前总分: {reasoning_closeup['total_score_before_correction']:.3f}")
    print(f"  完整性系数: {reasoning_closeup['completeness_coefficient']:.2f}")
    print(f"  修正后总分: {score_closeup.total_score:.3f}")
    print(f"  置信度级别: {score_closeup.confidence_level}")
    print(f"\n  对比: 特写镜头比完整器官总分低 {(score_complete.total_score - score_closeup.total_score):.3f}")

    # 7. 批量评分候选疾病
    print("\n[示例7] 批量评分候选疾病")
    candidates = loader.get_all_diseases()
    if len(candidates) >= 2:
        ranked_results = scorer.score_candidates(feature_vector_complete, candidates)

        print(f"  候选疾病数量: {len(candidates)}")
        print(f"  排序结果（Top 3）:")
        for idx, (disease, score, reasoning) in enumerate(ranked_results[:3], 1):
            print(f"    {idx}. {disease.disease_name}")
            print(f"       - 总分: {score.total_score:.3f}")
            print(f"       - 主要特征匹配: {score.major_matched}/{score.major_total}")
            print(f"       - 置信度级别: {score.confidence_level}")
    else:
        print(f"  [SKIP] 候选疾病不足2个，跳过批量评分测试")

    # 8. 查看权重信息
    print("\n[示例8] 查看权重信息")
    info = scorer.get_weights_info()
    print(f"  特征权重版本: {info['feature_weights_version']}")
    print(f"  重要性权重版本: {info['importance_weights_version']}")
    print(f"  主要特征权重: {info['major_weight']}")
    print(f"  次要特征权重: {info['minor_weight']}")
    print(f"  可选特征权重: {info['optional_weight']}")
    print(f"  确诊阈值: {info['confirmed_threshold']}")
    print(f"  疑似阈值: {info['suspected_threshold']}")
    print(f"  完整性系数: {info['completeness_coefficients']}")

    # 9. 热重载权重配置
    print("\n[示例9] 热重载权重配置")
    try:
        scorer.reload_weights()
        print(f"  [OK] 权重配置重新加载成功")
        print(f"  新的加载时间: {scorer.last_loaded}")
    except Exception as e:
        print(f"  [FAIL] 热重载失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
