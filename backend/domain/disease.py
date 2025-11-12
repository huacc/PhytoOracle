"""
疾病本体领域模型

功能：
- 定义疾病本体的领域模型
- 存储疾病的特征向量、诊断规则、特征重要性等信息
- 提供疾病匹配所需的辅助方法

模型清单：
- DiseaseOntology: 疾病本体模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List


class DiseaseOntology(BaseModel):
    """
    疾病本体模型

    存储疾病的完整知识信息，包括特征向量、诊断规则、特征重要性等

    字段说明：
    - version: 知识库版本号（格式：X.Y）
    - disease_id: 疾病唯一标识符（如：rosa_blackspot）
    - disease_name: 疾病名称（中文）
    - common_name_en: 英文常用名
    - pathogen: 病原体（真菌、细菌、病毒等）
    - feature_vector: 疾病特征向量（包含所有维度的期望值）
    - feature_importance: 特征重要性（主要特征、次要特征、可选特征）
    - diagnosis_rules: 诊断规则（确诊规则、疑似规则）
    - visual_descriptions: 视觉描述（VLM识别线索）
    - host_plants: 宿主植物列表
    - typical_symptoms: 典型症状描述

    使用示例：
    ```python
    disease = DiseaseOntology(
        version="4.1",
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Rose Black Spot",
        pathogen="Diplocarpon rosae (真菌)",
        feature_vector={...},
        feature_importance={...},
        diagnosis_rules={...}
    )

    # 获取主要特征
    major_features = disease.get_major_features()

    # 获取某维度的期望值
    expected_colors = disease.get_expected_values("color_center")
    ```
    """
    model_config = ConfigDict(validate_assignment=True)  # 启用赋值验证

    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+$",
        description="知识库版本号（格式：X.Y）"
    )
    disease_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="疾病唯一标识符（如：rosa_blackspot）"
    )
    disease_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="疾病名称（中文）"
    )
    common_name_en: str = Field(..., description="英文常用名")
    pathogen: str = Field(..., description="病原体（真菌、细菌、病毒等）")

    # 特征向量（包含所有维度的期望值）
    feature_vector: Dict[str, Any] = Field(
        ...,
        description="疾病特征向量（包含所有维度的期望值）"
    )

    # 特征重要性（主要特征、次要特征、可选特征）
    feature_importance: Dict[str, Dict] = Field(
        ...,
        description="特征重要性（major_features/minor_features/optional_features）"
    )

    # 诊断规则（确诊规则、疑似规则）
    diagnosis_rules: Dict[str, List[Dict]] = Field(
        ...,
        description="诊断规则（confirmed_rules/suspected_rules）"
    )

    # 视觉描述（VLM识别线索）
    visual_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="视觉描述（early_stage/advanced_stage等）"
    )

    # 宿主植物列表
    host_plants: List[str] = Field(
        default_factory=list,
        description="宿主植物列表（如：['Rosa', 'Prunus']）"
    )

    # 典型症状描述
    typical_symptoms: List[str] = Field(
        default_factory=list,
        description="典型症状描述（用于人工确认）"
    )

    def get_major_features(self) -> List[Dict]:
        """
        获取主要特征列表

        主要特征是诊断的核心依据，通常需要匹配≥2个才能确诊

        Returns:
            List[Dict]: 主要特征列表，每个元素包含：
                - dimension: 特征维度（如：color_center）
                - expected_values: 期望值列表
                - weight: 权重

        示例：
        ```python
        [
            {
                "dimension": "color_center",
                "expected_values": ["black", "dark_brown"],
                "weight": 0.5
            },
            {
                "dimension": "symptom_type",
                "expected_values": ["spot"],
                "weight": 0.5
            }
        ]
        ```
        """
        return self.feature_importance.get("major_features", {}).get("features", [])

    def get_expected_values(self, dimension: str) -> List[str]:
        """
        获取某维度的期望值

        Args:
            dimension: 特征维度（如：color_center、symptom_type等）

        Returns:
            List[str]: 期望值列表，如果维度不存在则返回空列表

        示例：
        ```python
        # 获取黑斑病的症状中心颜色期望值
        expected_colors = disease.get_expected_values("color_center")
        # 返回: ["black", "dark_brown"]
        ```
        """
        # 遍历所有特征组（主要、次要、可选）
        for feature_group in self.feature_importance.values():
            for feature in feature_group.get("features", []):
                if feature.get("dimension") == dimension:
                    return feature.get("expected_values", [])
        return []


def main():
    """
    DiseaseOntology模型使用示例

    演示如何：
    1. 从JSON文件加载疾病本体
    2. 访问疾病的基本信息
    3. 获取主要特征
    4. 获取特定维度的期望值
    """
    import json
    from pathlib import Path

    print("=" * 80)
    print("DiseaseOntology 模型使用示例")
    print("=" * 80)

    # 1. 从JSON文件加载疾病本体
    print("\n[示例1] 从JSON文件加载疾病本体")
    disease_file = Path(__file__).parent.parent / "knowledge_base/diseases/rose_black_spot.json"

    if disease_file.exists():
        disease_json = json.loads(disease_file.read_text(encoding="utf-8"))
        disease = DiseaseOntology(**disease_json)

        print(f"  [OK] 成功加载疾病: {disease.disease_name}")
        print(f"  - 疾病ID: {disease.disease_id}")
        print(f"  - 英文名: {disease.common_name_en}")
        print(f"  - 病原体: {disease.pathogen}")
        print(f"  - 版本: {disease.version}")
    else:
        print(f"  [FAIL] 文件不存在: {disease_file}")
        # 使用示例数据
        disease = DiseaseOntology(
            version="4.1",
            disease_id="rosa_blackspot",
            disease_name="玫瑰黑斑病",
            common_name_en="Rose Black Spot",
            pathogen="Diplocarpon rosae（真菌）",
            feature_vector={
                "symptom_type": "necrosis_spot",
                "color_center": ["black", "brown"],
                "color_border": ["yellow"]
            },
            feature_importance={
                "major_features": {
                    "_weight": 0.8,
                    "features": [
                        {
                            "dimension": "symptom_type",
                            "expected_values": ["necrosis_spot"],
                            "weight": 0.5
                        },
                        {
                            "dimension": "color_border",
                            "expected_values": ["yellow", "light_yellow"],
                            "weight": 0.3
                        }
                    ]
                }
            },
            diagnosis_rules={
                "confirmed": [
                    {
                        "rule_id": "R1",
                        "logic": "major_features >= 2/2",
                        "confidence": 0.95
                    }
                ],
                "suspected": []
            },
            host_plants=["Rosa"]
        )
        print(f"  [OK] 使用示例数据创建疾病: {disease.disease_name}")

    # 2. 访问疾病的基本信息
    print("\n[示例2] 访问疾病的基本信息")
    print(f"  - 宿主植物: {', '.join(disease.host_plants)}")
    print(f"  - 诊断规则数量: 确诊规则 {len(disease.diagnosis_rules.get('confirmed', []))} 个")
    print(f"  - 视觉描述数量: {len(disease.visual_descriptions)} 个")

    # 3. 获取主要特征
    print("\n[示例3] 获取主要特征")
    major_features = disease.get_major_features()
    print(f"  主要特征数量: {len(major_features)}")
    for idx, feature in enumerate(major_features, 1):
        print(f"  特征 {idx}:")
        print(f"    - 维度: {feature.get('dimension')}")
        print(f"    - 期望值: {feature.get('expected_values')}")
        print(f"    - 权重: {feature.get('weight')}")

    # 4. 获取特定维度的期望值
    print("\n[示例4] 获取特定维度的期望值")
    dimensions = ["symptom_type", "color_center", "color_border"]
    for dim in dimensions:
        expected_values = disease.get_expected_values(dim)
        if expected_values:
            print(f"  - {dim}: {expected_values}")
        else:
            print(f"  - {dim}: (无数据)")

    # 5. 访问特征向量
    print("\n[示例5] 访问特征向量")
    print(f"  特征向量维度数: {len(disease.feature_vector)}")
    for key, value in disease.feature_vector.items():
        print(f"  - {key}: {value}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
