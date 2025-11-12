"""
特征本体领域模型

功能：
- 定义特征本体的领域模型
- 存储特征维度定义、模糊匹配规则等
- 用于特征提取和匹配

模型清单：
- FeatureOntology: 特征本体模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List


class FeatureOntology(BaseModel):
    """
    特征本体模型

    存储特征维度定义、模糊匹配规则、症状类型、颜色、尺寸、分布模式等

    字段说明：
    - version: 特征本体版本号（格式：X.Y）
    - dimensions: 特征维度定义（如：color_center、symptom_type等）
    - fuzzy_matching: 模糊匹配规则（如：近似颜色映射）
    - symptom_types: 症状类型定义（斑点、溃疡、霉层等）
    - colors: 颜色定义（标准颜色及其变体）
    - sizes: 尺寸定义（小、中、大等）
    - distribution_patterns: 分布模式定义（散发、聚集、环状等）

    使用示例：
    ```python
    feature_ontology = FeatureOntology(
        version="1.0",
        dimensions={
            "color_center": {
                "type": "enum",
                "values": ["black", "brown", "yellow", "white"],
                "description": "症状中心颜色"
            }
        },
        fuzzy_matching={
            "color_aliases": {
                "deep_black": ["black", "dark_brown"],
                "yellowish": ["yellow", "light_brown"]
            }
        },
        symptom_types=[
            {"value": "spot", "label": "斑点"},
            {"value": "blight", "label": "溃疡"}
        ]
    )
    ```
    """
    model_config = ConfigDict(validate_assignment=True)  # 启用赋值验证

    version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="特征本体版本号（格式：X.Y）"
    )

    # 特征维度定义
    dimensions: Dict[str, Dict] = Field(
        ...,
        description="特征维度定义，每个维度包含type、values、description等"
    )

    # 模糊匹配规则
    fuzzy_matching: Dict[str, Any] = Field(
        ...,
        description="模糊匹配规则，如：近似颜色映射、同义词映射等"
    )

    # 症状类型定义
    symptom_types: List[Dict[str, str]] = Field(
        default_factory=list,
        description="症状类型定义，每个元素包含value和label"
    )

    # 颜色定义
    colors: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="颜色定义，标准颜色及其变体，如：{'black': ['deep_black', 'dark_brown']}"
    )

    # 尺寸定义
    sizes: List[str] = Field(
        default_factory=list,
        description="尺寸定义，如：['small', 'medium', 'large']"
    )

    # 分布模式定义
    distribution_patterns: List[str] = Field(
        default_factory=list,
        description="分布模式定义，如：['scattered', 'clustered', 'ring']"
    )


def main():
    """
    FeatureOntology模型使用示例

    演示如何：
    1. 从JSON文件加载特征本体
    2. 访问特征维度定义
    3. 访问模糊匹配规则
    4. 使用模糊匹配查找颜色别名
    """
    import json
    from pathlib import Path

    print("=" * 80)
    print("FeatureOntology 模型使用示例")
    print("=" * 80)

    # 1. 从JSON文件加载特征本体
    print("\n[示例1] 从JSON文件加载特征本体")
    feature_file = Path(__file__).parent.parent / "knowledge_base/features/feature_ontology.json"

    if feature_file.exists():
        feature_json = json.loads(feature_file.read_text(encoding="utf-8"))
        feature_ontology = FeatureOntology(**feature_json)

        print(f"  [OK] 成功加载特征本体")
        print(f"  - 版本: {feature_ontology.version}")
        print(f"  - 特征维度数: {len(feature_ontology.dimensions)}")
    else:
        print(f"  [FAIL] 文件不存在: {feature_file}")
        # 使用示例数据
        feature_ontology = FeatureOntology(
            version="1.0",
            dimensions={
                "symptom_type": {
                    "type": "enum",
                    "values": ["necrosis_spot", "powdery_coating", "chlorosis"],
                    "description": "症状类型"
                },
                "color_center": {
                    "type": "enum",
                    "values": ["black", "brown", "yellow", "white"],
                    "description": "症状中心颜色"
                },
                "size": {
                    "type": "enum",
                    "values": ["small", "medium", "large"],
                    "description": "症状尺寸"
                }
            },
            fuzzy_matching={
                "color_aliases": {
                    "deep_black": ["black", "dark_brown"],
                    "yellowish": ["yellow", "light_yellow"],
                    "whitish": ["white", "grayish_white"]
                },
                "size_order": ["small", "medium", "large"],
                "size_tolerance": 1
            },
            symptom_types=[
                {"value": "necrosis_spot", "label": "坏死斑点"},
                {"value": "powdery_coating", "label": "白粉覆盖"},
                {"value": "chlorosis", "label": "黄化"}
            ],
            colors={
                "black": ["deep_black", "dark_brown"],
                "yellow": ["yellowish", "light_yellow"],
                "white": ["whitish", "grayish_white"]
            },
            sizes=["small", "medium", "large"],
            distribution_patterns=["scattered", "clustered", "along_vein"]
        )
        print(f"  [OK] 使用示例数据创建特征本体")

    # 2. 访问特征维度定义
    print("\n[示例2] 访问特征维度定义")
    print(f"  特征维度数量: {len(feature_ontology.dimensions)}")
    for dim_name, dim_info in list(feature_ontology.dimensions.items())[:3]:
        print(f"  - {dim_name}:")
        print(f"    类型: {dim_info.get('type')}")
        print(f"    描述: {dim_info.get('description')}")
        values = dim_info.get('values', [])
        if values:
            print(f"    可选值数量: {len(values)}")

    # 3. 访问模糊匹配规则
    print("\n[示例3] 访问模糊匹配规则")
    fuzzy = feature_ontology.fuzzy_matching
    print(f"  模糊匹配规则类型数: {len(fuzzy)}")

    if "color_aliases" in fuzzy:
        color_aliases = fuzzy["color_aliases"]
        print(f"  - 颜色别名组数: {len(color_aliases)}")
        for alias_group, colors in list(color_aliases.items())[:3]:
            print(f"    • {alias_group} → {colors}")

    if "size_tolerance" in fuzzy:
        print(f"  - 尺寸容差: ±{fuzzy['size_tolerance']} 级")

    # 4. 使用模糊匹配查找颜色别名
    print("\n[示例4] 使用模糊匹配查找颜色别名")

    def find_color_matches(color_input: str, feature_ontology: FeatureOntology) -> list:
        """根据输入颜色查找所有匹配的颜色（包括别名）"""
        color_aliases = feature_ontology.fuzzy_matching.get("color_aliases", {})

        # 直接匹配
        matches = [color_input]

        # 查找别名组
        for alias_group, colors in color_aliases.items():
            if color_input in colors or alias_group == color_input:
                matches.extend([c for c in colors if c not in matches])

        return matches

    test_colors = ["deep_black", "yellowish", "white"]
    for color in test_colors:
        matches = find_color_matches(color, feature_ontology)
        print(f"  输入颜色: {color}")
        print(f"    匹配结果: {matches}")

    # 5. 访问症状类型定义
    print("\n[示例5] 访问症状类型定义")
    print(f"  症状类型数量: {len(feature_ontology.symptom_types)}")
    for symptom in feature_ontology.symptom_types:
        print(f"  - {symptom.get('value')}: {symptom.get('label')}")

    # 6. 访问尺寸和分布模式定义
    print("\n[示例6] 访问尺寸和分布模式定义")
    print(f"  尺寸定义: {feature_ontology.sizes}")
    print(f"  分布模式: {feature_ontology.distribution_patterns}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
