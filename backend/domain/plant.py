"""
植物本体领域模型

功能：
- 定义植物本体的领域模型
- 存储植物的分类学信息、器官解剖、视觉线索等
- 用于Q0.2花卉种属识别和候选疾病剪枝

模型清单：
- PlantOntology: 植物本体模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List


class PlantOntology(BaseModel):
    """
    植物本体模型

    存储植物的分类学信息、器官解剖、视觉线索等，用于花卉识别和疾病剪枝

    字段说明：
    - kingdom: 界（默认：Plantae，植物界）
    - family: 科（如：Rosaceae，蔷薇科）
    - genus: 属（如：Rosa，蔷薇属）
    - species: 种列表（如：['Rosa chinensis', 'Rosa rugosa']）
    - common_names: 常用名（多语言）
    - organ_anatomy: 器官解剖信息
    - visual_cues: VLM识别线索
    - susceptible_diseases: 易感疾病列表

    使用示例：
    ```python
    plant = PlantOntology(
        kingdom="Plantae",
        family="Rosaceae",
        genus="Rosa",
        species=["Rosa chinensis", "Rosa rugosa"],
        common_names={"zh": "玫瑰", "en": "Rose"},
        organ_anatomy={
            "leaf": ["pinnate", "serrated_margin"],
            "flower": ["5_petals", "multiple_stamens"]
        },
        visual_cues={
            "leaf_shape": "羽状复叶，边缘有锯齿",
            "flower_shape": "花瓣5枚或多重瓣，雄蕊众多"
        },
        susceptible_diseases=["rosa_blackspot", "rosa_powdery_mildew"]
    )
    ```
    """
    model_config = ConfigDict(validate_assignment=True)  # 启用赋值验证

    # 分类学信息
    kingdom: str = Field(
        default="Plantae",
        description="界（默认：Plantae，植物界）"
    )
    family: str = Field(..., description="科（如：Rosaceae，蔷薇科）")
    genus: str = Field(..., description="属（如：Rosa，蔷薇属）")
    species: List[str] = Field(
        default_factory=list,
        description="种列表（如：['Rosa chinensis', 'Rosa rugosa']）"
    )
    common_names: Dict[str, str] = Field(
        default_factory=dict,
        description="常用名（多语言），格式：{'zh': '玫瑰', 'en': 'Rose'}"
    )

    # 器官解剖信息
    organ_anatomy: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="器官解剖信息，格式：{'leaf': ['特征1', '特征2'], 'flower': ['特征1', '特征2']}"
    )

    # VLM识别线索
    visual_cues: Dict[str, str] = Field(
        default_factory=dict,
        description="VLM识别线索，用于Q0.2花卉种属识别"
    )

    # 易感疾病列表
    susceptible_diseases: List[str] = Field(
        default_factory=list,
        description="易感疾病列表（疾病ID），用于候选疾病剪枝"
    )


def main():
    """
    PlantOntology模型使用示例

    演示如何：
    1. 创建植物本体对象
    2. 访问分类学信息
    3. 访问器官解剖信息
    4. 获取易感疾病列表
    """
    print("=" * 80)
    print("PlantOntology 模型使用示例")
    print("=" * 80)

    # 1. 创建玫瑰植物本体对象
    print("\n[示例1] 创建玫瑰植物本体对象")
    rosa_plant = PlantOntology(
        kingdom="Plantae",
        family="Rosaceae",
        genus="Rosa",
        species=["Rosa chinensis", "Rosa rugosa", "Rosa multiflora"],
        common_names={
            "zh": "玫瑰",
            "en": "Rose",
            "zh_tw": "玫瑰"
        },
        organ_anatomy={
            "leaf": ["pinnate", "serrated_margin", "3-7_leaflets"],
            "flower": ["5_petals", "multiple_stamens", "fragrant"],
            "stem": ["thorny", "woody"]
        },
        visual_cues={
            "leaf_shape": "羽状复叶，边缘有锯齿，小叶3-7枚",
            "flower_shape": "花瓣5枚或多重瓣，雄蕊众多，有芳香",
            "stem_feature": "茎有刺，木质化"
        },
        susceptible_diseases=[
            "rose_black_spot",
            "rose_powdery_mildew",
            "rose_rust",
            "rose_downy_mildew"
        ]
    )

    print(f"  [OK] 成功创建植物: {rosa_plant.common_names.get('zh')}")
    print(f"  - 学名: {rosa_plant.genus}")
    print(f"  - 科: {rosa_plant.family}")

    # 2. 访问分类学信息
    print("\n[示例2] 访问分类学信息")
    print(f"  - 界: {rosa_plant.kingdom}")
    print(f"  - 科: {rosa_plant.family}")
    print(f"  - 属: {rosa_plant.genus}")
    print(f"  - 种列表:")
    for species in rosa_plant.species:
        print(f"    • {species}")
    print(f"  - 常用名:")
    for lang, name in rosa_plant.common_names.items():
        print(f"    • {lang}: {name}")

    # 3. 访问器官解剖信息
    print("\n[示例3] 访问器官解剖信息")
    print(f"  器官数量: {len(rosa_plant.organ_anatomy)}")
    for organ, features in rosa_plant.organ_anatomy.items():
        print(f"  - {organ}: {', '.join(features)}")

    # 4. 访问VLM识别线索
    print("\n[示例4] 访问VLM识别线索")
    for key, value in rosa_plant.visual_cues.items():
        print(f"  - {key}: {value}")

    # 5. 获取易感疾病列表
    print("\n[示例5] 获取易感疾病列表")
    print(f"  易感疾病数量: {len(rosa_plant.susceptible_diseases)}")
    for disease_id in rosa_plant.susceptible_diseases:
        print(f"  • {disease_id}")

    # 6. 创建樱花植物本体对象
    print("\n[示例6] 创建樱花植物本体对象")
    prunus_plant = PlantOntology(
        family="Rosaceae",
        genus="Prunus",
        species=["Prunus serrulata", "Prunus avium"],
        common_names={
            "zh": "樱花",
            "en": "Cherry"
        },
        organ_anatomy={
            "leaf": ["simple", "serrated_margin", "alternate"],
            "flower": ["5_petals", "umbel_inflorescence"]
        },
        visual_cues={
            "leaf_shape": "单叶，边缘有锯齿，互生",
            "flower_shape": "花瓣5枚，伞形花序"
        },
        susceptible_diseases=[
            "cherry_powdery_mildew",
            "cherry_brown_rot",
            "cherry_leaf_spot"
        ]
    )

    print(f"  [OK] 成功创建植物: {prunus_plant.common_names.get('zh')}")
    print(f"  - 学名: {prunus_plant.genus}")
    print(f"  - 易感疾病: {len(prunus_plant.susceptible_diseases)} 种")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
