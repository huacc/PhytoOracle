"""
特征匹配器

功能：
- 将提取的特征向量与疾病知识库进行匹配
- 计算加权相似度评分（主要特征、次要特征、可选特征）
- 支持模糊匹配（颜色别名、尺寸容差）
- 遵循医学诊断逻辑（主要特征≥2/2确诊）

类清单：
- FeatureMatcher: 特征匹配器（主类）
"""

from typing import Dict, Any, Tuple, List, Set
from backend.domain.diagnosis import FeatureVector, DiagnosisScore
from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology


class FeatureMatcher:
    """
    特征匹配器

    负责将提取的特征向量与疾病知识库进行匹配，计算相似度评分

    匹配逻辑：
    1. 主要特征匹配（权重：0.8，通常需要≥2/2才能确诊）
    2. 次要特征匹配（权重：0.15）
    3. 可选特征匹配（权重：0.05）
    4. 模糊匹配支持（颜色别名、尺寸容差）

    使用示例：
    ```python
    from backend.infrastructure.ontology.loader import KnowledgeBaseLoader

    # 初始化
    loader = KnowledgeBaseLoader(kb_path)
    feature_ontology = loader.get_feature_ontology()
    matcher = FeatureMatcher(feature_ontology)

    # 匹配疾病
    feature_vector = FeatureVector(...)
    disease = loader.get_disease_by_id("rose_black_spot")
    score, reasoning = matcher.match_disease(feature_vector, disease)

    print(f"匹配评分: {score.total_score:.2f}")
    print(f"主要特征匹配: {score.major_matched}/{score.major_total}")
    print(f"置信度级别: {score.confidence_level}")
    ```
    """

    def __init__(self, feature_ontology: FeatureOntology):
        """
        初始化特征匹配器

        Args:
            feature_ontology: 特征本体对象（包含模糊匹配规则）
        """
        self.feature_ontology = feature_ontology
        self.fuzzy_rules = feature_ontology.fuzzy_matching

        # 解析模糊匹配规则
        self.color_aliases = self.fuzzy_rules.get("color_aliases", {})
        self.size_order = self.fuzzy_rules.get("size_order", {}).get("order", [])
        self.size_tolerance = self.fuzzy_rules.get("size_tolerance", {}).get("value", 1)
        self.synonym_mapping = self.fuzzy_rules.get("synonym_mapping", {})

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

        推理细节包含：
        - disease_id: 疾病ID
        - disease_name: 疾病名称
        - major_features_detail: 主要特征匹配详情
        - minor_features_detail: 次要特征匹配详情
        - optional_features_detail: 可选特征匹配详情
        - total_score: 总分
        - confidence_level: 置信度级别

        示例：
        ```python
        score, reasoning = matcher.match_disease(feature_vector, disease)
        print(f"疾病: {reasoning['disease_name']}")
        print(f"总分: {reasoning['total_score']:.2f}")
        print(f"主要特征匹配: {score.major_matched}/{score.major_total}")
        ```
        """
        # 获取疾病的特征重要性配置
        feature_importance = disease.feature_importance

        # 1. 匹配主要特征（权重：0.8，通常需要≥2/2才能确诊）
        major_score, major_matched, major_total, major_detail = self._match_feature_group(
            feature_vector,
            feature_importance.get("major_features", {})
        )

        # 2. 匹配次要特征（权重：0.15）
        minor_score, _, _, minor_detail = self._match_feature_group(
            feature_vector,
            feature_importance.get("minor_features", {})
        )

        # 3. 匹配可选特征（权重：0.05）
        optional_score, _, _, optional_detail = self._match_feature_group(
            feature_vector,
            feature_importance.get("optional_features", {})
        )

        # 4. 计算总分（加权平均）
        weight_major = feature_importance.get("major_features", {}).get("_weight", 0.8)
        weight_minor = feature_importance.get("minor_features", {}).get("_weight", 0.15)
        weight_optional = feature_importance.get("optional_features", {}).get("_weight", 0.05)

        total_score = (
            major_score * weight_major +
            minor_score * weight_minor +
            optional_score * weight_optional
        )

        # 5. 构建诊断评分对象
        diagnosis_score = DiagnosisScore(
            total_score=min(total_score, 1.0),  # 确保不超过1.0
            major_features_score=major_score,
            minor_features_score=minor_score,
            optional_features_score=optional_score,
            major_matched=major_matched,
            major_total=major_total
        )

        # 6. 构建推理细节
        reasoning = {
            "disease_id": disease.disease_id,
            "disease_name": disease.disease_name,
            "major_features_detail": major_detail,
            "minor_features_detail": minor_detail,
            "optional_features_detail": optional_detail,
            "total_score": diagnosis_score.total_score,
            "confidence_level": diagnosis_score.confidence_level
        }

        return diagnosis_score, reasoning

    def _match_feature_group(
        self,
        feature_vector: FeatureVector,
        feature_group: Dict[str, Any]
    ) -> Tuple[float, int, int, List[Dict]]:
        """
        匹配特征组（主要/次要/可选）

        Args:
            feature_vector: 提取的特征向量
            feature_group: 特征组配置（从疾病本体的feature_importance中获取）

        Returns:
            Tuple[float, int, int, List[Dict]]: (平均得分, 匹配数量, 总数量, 详情列表)

        示例：
        ```python
        major_features = disease.feature_importance["major_features"]
        score, matched, total, detail = self._match_feature_group(
            feature_vector,
            major_features
        )
        ```
        """
        features = feature_group.get("features", [])
        if not features:
            return 0.0, 0, 0, []

        total_count = len(features)
        matched_count = 0
        total_score = 0.0
        details = []

        for feature_config in features:
            dimension = feature_config.get("dimension")
            expected_values = feature_config.get("expected_values", [])
            weight = feature_config.get("weight", 1.0 / total_count)  # 默认均分权重

            # 从特征向量中获取实际值
            actual_value = getattr(feature_vector, dimension, None)

            # 匹配特征
            is_matched, match_score = self._match_single_feature(
                dimension,
                actual_value,
                expected_values
            )

            # 计算加权得分
            weighted_score = match_score * weight

            if is_matched:
                matched_count += 1

            total_score += weighted_score

            # 记录详情
            details.append({
                "dimension": dimension,
                "expected_values": expected_values,
                "actual_value": actual_value,
                "is_matched": is_matched,
                "match_score": match_score,
                "weight": weight,
                "weighted_score": weighted_score
            })

        # 计算平均得分（归一化到0-1）
        avg_score = total_score if total_count > 0 else 0.0

        return avg_score, matched_count, total_count, details

    def _match_single_feature(
        self,
        dimension: str,
        actual_value: Any,
        expected_values: List[str]
    ) -> Tuple[bool, float]:
        """
        匹配单个特征

        Args:
            dimension: 特征维度（如 "symptom_type", "color_center"）
            actual_value: 实际值（从特征向量中提取）
            expected_values: 期望值列表（从疾病本体中获取）

        Returns:
            Tuple[bool, float]: (是否匹配, 匹配得分0-1)

        匹配逻辑：
        1. 如果实际值为None，返回(False, 0.0)
        2. 如果维度为颜色，使用颜色模糊匹配
        3. 如果维度为尺寸，使用尺寸容差匹配
        4. 如果维度为症状类型，使用同义词匹配
        5. 否则，使用精确匹配

        示例：
        ```python
        is_matched, score = self._match_single_feature(
            "color_center",
            "deep_black",
            ["black", "dark_brown"]
        )
        ```
        """
        if actual_value is None:
            return False, 0.0

        # 1. 颜色匹配（支持模糊匹配）
        if "color" in dimension:
            return self._match_color(actual_value, expected_values)

        # 2. 尺寸匹配（允许±1级容差）
        elif dimension == "size":
            return self._match_size(actual_value, expected_values)

        # 3. 症状类型匹配（支持同义词）
        elif dimension == "symptom_type":
            return self._match_symptom_type(actual_value, expected_values)

        # 4. 精确匹配（其他维度）
        else:
            return self._match_exact(actual_value, expected_values)

    def _match_color(
        self,
        actual_color: str,
        expected_colors: List[str]
    ) -> Tuple[bool, float]:
        """
        颜色匹配（支持模糊匹配）

        Args:
            actual_color: 实际颜色（如 "deep_black"）
            expected_colors: 期望颜色列表（如 ["black", "dark_brown"]）

        Returns:
            Tuple[bool, float]: (是否匹配, 匹配得分)

        匹配逻辑：
        1. 精确匹配：1.0分
        2. 颜色别名匹配：0.9分（例如："deep_black" 匹配 "black"）
        3. 不匹配：0.0分

        示例：
        ```python
        # 精确匹配
        is_matched, score = self._match_color("black", ["black", "brown"])
        # 返回: (True, 1.0)

        # 颜色别名匹配
        is_matched, score = self._match_color("deep_black", ["black"])
        # 返回: (True, 0.9)
        ```
        """
        # 1. 精确匹配
        if actual_color in expected_colors:
            return True, 1.0

        # 2. 颜色别名匹配
        # 展开实际颜色的所有别名
        actual_aliases = self._expand_color_aliases(actual_color)

        # 展开期望颜色的所有别名
        expected_aliases_set = set()
        for expected_color in expected_colors:
            expected_aliases_set.update(self._expand_color_aliases(expected_color))

        # 检查是否有交集
        if actual_aliases & expected_aliases_set:
            return True, 0.9  # 模糊匹配得分略低

        return False, 0.0

    def _expand_color_aliases(self, color: str) -> Set[str]:
        """
        展开颜色别名

        Args:
            color: 颜色值（如 "deep_black"）

        Returns:
            Set[str]: 颜色及其所有别名（如 {"deep_black", "black", "dark_brown"}）

        示例：
        ```python
        aliases = self._expand_color_aliases("deep_black")
        # 返回: {"deep_black", "black", "dark_brown"}
        ```
        """
        aliases = {color}  # 包含自身

        # 从color_aliases中查找
        for alias_group, colors in self.color_aliases.items():
            if color in colors or alias_group == color:
                aliases.add(alias_group)
                aliases.update(colors)

        return aliases

    def _match_size(
        self,
        actual_size: str,
        expected_sizes: List[str]
    ) -> Tuple[bool, float]:
        """
        尺寸匹配（允许±1级容差）

        Args:
            actual_size: 实际尺寸（如 "medium"）
            expected_sizes: 期望尺寸列表（如 ["small", "medium"]）

        Returns:
            Tuple[bool, float]: (是否匹配, 匹配得分)

        匹配逻辑：
        1. 精确匹配：1.0分
        2. 相邻级别匹配（±1级容差）：0.8分
        3. 不匹配：0.0分

        尺寸顺序：["pinpoint", "small", "medium_small", "medium", "medium_large", "large"]

        示例：
        ```python
        # 精确匹配
        is_matched, score = self._match_size("medium", ["medium"])
        # 返回: (True, 1.0)

        # 相邻级别匹配
        is_matched, score = self._match_size("medium", ["small"])
        # 返回: (True, 0.8)
        ```
        """
        # 1. 精确匹配
        if actual_size in expected_sizes:
            return True, 1.0

        # 2. 相邻级别匹配（±1级容差）
        if not self.size_order:
            return False, 0.0

        try:
            actual_idx = self.size_order.index(actual_size)

            for expected_size in expected_sizes:
                expected_idx = self.size_order.index(expected_size)
                diff = abs(actual_idx - expected_idx)

                if diff <= self.size_tolerance:
                    return True, 0.8  # 相邻级别匹配得分略低

        except ValueError:
            # 尺寸不在size_order中，回退到精确匹配
            return actual_size in expected_sizes, 1.0 if actual_size in expected_sizes else 0.0

        return False, 0.0

    def _match_symptom_type(
        self,
        actual_symptom: str,
        expected_symptoms: List[str]
    ) -> Tuple[bool, float]:
        """
        症状类型匹配（支持同义词）

        Args:
            actual_symptom: 实际症状类型（如 "necrosis_spot"）
            expected_symptoms: 期望症状类型列表（如 ["necrosis_spot", "bacterial_spot"]）

        Returns:
            Tuple[bool, float]: (是否匹配, 匹配得分)

        匹配逻辑：
        1. 精确匹配：1.0分
        2. 同义词匹配：0.9分
        3. 不匹配：0.0分

        示例：
        ```python
        # 精确匹配
        is_matched, score = self._match_symptom_type("necrosis_spot", ["necrosis_spot"])
        # 返回: (True, 1.0)

        # 同义词匹配（"necrosis_spot" 和 "bacterial_spot" 都是 "spot" 的同义词）
        is_matched, score = self._match_symptom_type("necrosis_spot", ["bacterial_spot"])
        # 返回: (True, 0.9)
        ```
        """
        # 1. 精确匹配
        if actual_symptom in expected_symptoms:
            return True, 1.0

        # 2. 同义词匹配
        for synonym_group, symptoms in self.synonym_mapping.items():
            if actual_symptom in symptoms:
                # 检查期望症状是否也在同一同义词组
                for expected in expected_symptoms:
                    if expected in symptoms:
                        return True, 0.9

        return False, 0.0

    def _match_exact(
        self,
        actual_value: str,
        expected_values: List[str]
    ) -> Tuple[bool, float]:
        """
        精确匹配

        Args:
            actual_value: 实际值
            expected_values: 期望值列表

        Returns:
            Tuple[bool, float]: (是否匹配, 匹配得分)

        示例：
        ```python
        is_matched, score = self._match_exact("lamina", ["lamina", "vein"])
        # 返回: (True, 1.0)
        ```
        """
        if actual_value in expected_values:
            return True, 1.0
        return False, 0.0


def main():
    """
    FeatureMatcher 使用示例

    演示如何：
    1. 初始化特征匹配器
    2. 匹配单个疾病
    3. 查看匹配详情
    4. 测试模糊匹配
    """
    from pathlib import Path
    from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
    from backend.domain.diagnosis import FeatureVector, ContentType, PlantCategory, FlowerGenus, OrganType, Completeness, AbnormalityStatus

    print("=" * 80)
    print("FeatureMatcher 使用示例")
    print("=" * 80)

    # 1. 初始化知识库加载器和特征匹配器
    print("\n[示例1] 初始化特征匹配器")
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = project_root / "backend" / "knowledge_base"

    try:
        loader = KnowledgeBaseLoader(kb_path)
        feature_ontology = loader.get_feature_ontology()
        matcher = FeatureMatcher(feature_ontology)
        print(f"  [OK] 特征匹配器初始化成功")
    except Exception as e:
        print(f"  [FAIL] 特征匹配器初始化失败: {e}")
        return

    # 2. 构造测试特征向量（玫瑰黑斑病的典型特征）
    print("\n[示例2] 构造测试特征向量")
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
    print(f"    - 症状类型: {feature_vector.symptom_type}")
    print(f"    - 中心颜色: {feature_vector.color_center}")
    print(f"    - 边缘颜色: {feature_vector.color_border}")

    # 3. 匹配玫瑰黑斑病
    print("\n[示例3] 匹配玫瑰黑斑病")
    disease = loader.get_disease_by_id("rose_black_spot")
    if disease:
        score, reasoning = matcher.match_disease(feature_vector, disease)

        print(f"  疾病: {reasoning['disease_name']}")
        print(f"  总分: {score.total_score:.3f}")
        print(f"  主要特征匹配: {score.major_matched}/{score.major_total}")
        print(f"  主要特征得分: {score.major_features_score:.3f}")
        print(f"  次要特征得分: {score.minor_features_score:.3f}")
        print(f"  可选特征得分: {score.optional_features_score:.3f}")
        print(f"  置信度级别: {score.confidence_level}")

        # 显示主要特征匹配详情
        print(f"\n  主要特征匹配详情:")
        for detail in reasoning['major_features_detail']:
            print(f"    - {detail['dimension']}:")
            print(f"      期望值: {detail['expected_values']}")
            print(f"      实际值: {detail['actual_value']}")
            print(f"      匹配: {detail['is_matched']} (得分: {detail['match_score']:.2f})")
    else:
        print(f"  [FAIL] 疾病不存在: rose_black_spot")

    # 4. 测试模糊匹配（颜色别名）
    print("\n[示例4] 测试模糊匹配（颜色别名）")
    feature_vector_fuzzy = FeatureVector(
        content_type=ContentType.PLANT,
        plant_category=PlantCategory.FLOWER,
        flower_genus=FlowerGenus.ROSA,
        organ=OrganType.LEAF,
        completeness=Completeness.COMPLETE,
        has_abnormality=AbnormalityStatus.ABNORMAL,
        symptom_type="necrosis_spot",
        color_center="deep_black",  # 使用颜色别名
        color_border="light_yellow",  # 使用颜色别名
        location="lamina",
        size="medium_small",  # 使用相邻尺寸
        distribution="scattered"
    )

    if disease:
        score_fuzzy, reasoning_fuzzy = matcher.match_disease(feature_vector_fuzzy, disease)

        print(f"  疾病: {reasoning_fuzzy['disease_name']}")
        print(f"  总分: {score_fuzzy.total_score:.3f}")
        print(f"  主要特征匹配: {score_fuzzy.major_matched}/{score_fuzzy.major_total}")
        print(f"  置信度级别: {score_fuzzy.confidence_level}")
        print(f"\n  注意: 模糊匹配得分略低于精确匹配")

    # 5. 测试不匹配的疾病
    print("\n[示例5] 测试不匹配的疾病（樱花白粉病）")
    cherry_disease = loader.get_disease_by_id("cherry_powdery_mildew")
    if cherry_disease:
        score_mismatch, reasoning_mismatch = matcher.match_disease(feature_vector, cherry_disease)

        print(f"  疾病: {reasoning_mismatch['disease_name']}")
        print(f"  总分: {score_mismatch.total_score:.3f}")
        print(f"  主要特征匹配: {score_mismatch.major_matched}/{score_mismatch.major_total}")
        print(f"  置信度级别: {score_mismatch.confidence_level}")
        print(f"\n  注意: 特征不匹配，总分很低")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
