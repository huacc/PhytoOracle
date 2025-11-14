"""
Q1-Q6 动态特征提取提示词生成器

功能：
- 根据 symptom_type（症状类型）动态生成 Q1-Q6 提示词
- 每个特征维度使用独立的提示词模板
- 支持的特征维度：
  * Q1: symptom_type（症状类型）
  * Q2: color_center（症状中心颜色）
  * Q3: color_border（症状边缘颜色）
  * Q4: size（症状尺寸）
  * Q5: location（症状位置）
  * Q6: distribution（分布模式）

作者：AI Python Architect
日期：2025-11-12
"""

from typing import Dict, List
from .framework import (
    PROOFPrompt,
    PromptPurpose,
    PromptRole,
    PromptObservation,
    PromptOptions,
    Choice,
    PromptFormat,
    Example
)
from .response_schema import FeatureResponse


class FeaturePromptBuilder:
    """
    特征提取提示词构建器

    根据特征维度动态生成提示词

    使用示例：
    ```python
    builder = FeaturePromptBuilder()

    # 生成 Q1（symptom_type）提示词
    q1_prompt = builder.build_prompt("symptom_type")

    # 生成 Q2（color_center）提示词
    q2_prompt = builder.build_prompt("color_center")
    ```
    """

    def __init__(self):
        """初始化特征维度配置"""
        # 定义所有支持的特征维度及其配置
        self.dimension_configs = {
            "symptom_type": {
                "question_id": "Q1",
                "task": "Identify the symptom type (病征类型) of the abnormality",
                "visual_method": "Symptom Pattern Recognition",
                "visual_clues": {
                    "necrosis_spot": "Dark spots with dead tissue (black/brown), clearly defined borders, tissue death",
                    "powdery_coating": "White/gray powdery substance covering surface, looks like powder or flour",
                    "chlorosis": "Yellowing of tissue, loss of green pigment, but tissue still alive",
                    "wilting": "Drooping or sagging, loss of rigidity, tissue appears soft",
                    "deformation": "Abnormal shape or structure, twisted or distorted growth",
                    "rust_pustule": "Orange/rust-colored raised bumps, powdery when rubbed",
                    "mold": "Fuzzy or cottony growth, usually gray/black/green",
                    "other": "Symptoms that don't fit above categories"
                },
                "choices": [
                    Choice("necrosis_spot", "坏死斑点（组织死亡，黑色/褐色斑点）"),
                    Choice("powdery_coating", "白粉覆盖（白色/灰色粉末状覆盖物）"),
                    Choice("chlorosis", "黄化（组织变黄，但未死亡）"),
                    Choice("wilting", "枯萎（下垂、失去硬挺）"),
                    Choice("deformation", "畸形（形状异常、扭曲）"),
                    Choice("rust_pustule", "锈病脓疱（橙色/锈色凸起，粉末状）"),
                    Choice("mold", "霉层（模糊或棉絮状生长物）"),
                    Choice("other", "其他症状")
                ]
            },
            "color_center": {
                "question_id": "Q2",
                "task": "Identify the predominant color at the CENTER of the symptom spots/lesions",
                "visual_method": "Color Identification Method",
                "visual_clues": {
                    "black": "Pure black or very dark (almost black)",
                    "dark_brown": "Dark brown, chocolate color",
                    "brown": "Medium brown, like dried leaves",
                    "light_brown": "Light brown, tan, beige",
                    "yellow": "Yellow, golden",
                    "light_yellow": "Pale yellow, cream",
                    "white": "White or off-white",
                    "gray": "Gray, ash color",
                    "red": "Red, crimson",
                    "purple": "Purple, violet",
                    "green": "Green (abnormal green, different from healthy tissue)",
                    "other": "Other colors not listed"
                },
                "choices": [
                    Choice("black", "黑色"),
                    Choice("dark_brown", "深褐色"),
                    Choice("brown", "褐色"),
                    Choice("light_brown", "浅褐色"),
                    Choice("yellow", "黄色"),
                    Choice("light_yellow", "浅黄色"),
                    Choice("white", "白色"),
                    Choice("gray", "灰色"),
                    Choice("red", "红色"),
                    Choice("purple", "紫色"),
                    Choice("green", "绿色"),
                    Choice("other", "其他颜色")
                ]
            },
            "color_border": {
                "question_id": "Q3",
                "task": "Identify the color at the BORDER/EDGE (晕圈) of the symptom spots",
                "visual_method": "Border Color Recognition",
                "visual_clues": {
                    "yellow": "Yellow halo around spots (like egg white around yolk)",
                    "light_yellow": "Pale yellow, faint halo",
                    "brown": "Brown border or ring",
                    "white": "White or pale border",
                    "red": "Red or reddish border",
                    "green": "Green border (normal tissue color)",
                    "none": "No visible border, spot blends into healthy tissue",
                    "other": "Other border colors"
                },
                "choices": [
                    Choice("yellow", "黄色晕圈"),
                    Choice("light_yellow", "浅黄色晕圈"),
                    Choice("brown", "褐色边缘"),
                    Choice("white", "白色边缘"),
                    Choice("red", "红色边缘"),
                    Choice("green", "绿色（正常组织）"),
                    Choice("none", "无明显边缘"),
                    Choice("other", "其他颜色")
                ]
            },
            "size": {
                "question_id": "Q4",
                "task": "Estimate the typical SIZE (diameter) of individual symptom spots",
                "visual_method": "Size Estimation Method",
                "visual_clues": {
                    "very_small": "Pinpoint size, < 2mm, barely visible",
                    "small": "Small but clear, 2-5mm, like sesame seed",
                    "medium": "Medium size, 5-10mm, like pea or fingertip",
                    "large": "Large spots, 10-20mm, like coin",
                    "very_large": "Very large, > 20mm, multiple cm across"
                },
                "choices": [
                    Choice("very_small", "极小（<2mm，针尖大小）"),
                    Choice("small", "小（2-5mm，芝麻大小）"),
                    Choice("medium", "中等（5-10mm，豌豆大小）"),
                    Choice("large", "大（10-20mm，硬币大小）"),
                    Choice("very_large", "极大（>20mm，数厘米）")
                ]
            },
            "location": {
                "question_id": "Q5",
                "task": "Identify the PRIMARY LOCATION of symptoms on the plant organ",
                "visual_method": "Location Mapping Method",
                "visual_clues": {
                    "lamina": "On the leaf blade surface (main flat part)",
                    "lamina_center": "At the center of leaf blade",
                    "lamina_edge": "Along the edges of leaf",
                    "vein": "Along the veins/midrib",
                    "petiole": "On the leaf stalk",
                    "stem": "On the stem",
                    "petal": "On flower petals",
                    "sepal": "On sepals (green parts under petals)",
                    "whole": "Affects entire organ uniformly"
                },
                "choices": [
                    Choice("lamina", "叶肉（叶片主要部分）"),
                    Choice("lamina_center", "叶片中心"),
                    Choice("lamina_edge", "叶片边缘"),
                    Choice("vein", "叶脉"),
                    Choice("petiole", "叶柄"),
                    Choice("stem", "茎干"),
                    Choice("petal", "花瓣"),
                    Choice("sepal", "萼片"),
                    Choice("whole", "整体（均匀分布）")
                ]
            },
            "distribution": {
                "question_id": "Q6",
                "task": "Identify the DISTRIBUTION PATTERN of symptoms across the organ surface",
                "visual_method": "Pattern Recognition Method",
                "visual_clues": {
                    "scattered": "Randomly scattered, no clear pattern",
                    "clustered": "Grouped together in clusters",
                    "along_vein": "Arranged along veins or midrib",
                    "ring": "Circular or ring pattern",
                    "uniform": "Evenly distributed across surface",
                    "edge_concentrated": "Concentrated at edges",
                    "center_concentrated": "Concentrated at center"
                },
                "choices": [
                    Choice("scattered", "散发（随机分布）"),
                    Choice("clustered", "聚集（成簇分布）"),
                    Choice("along_vein", "沿叶脉分布"),
                    Choice("ring", "环状分布"),
                    Choice("uniform", "均匀分布"),
                    Choice("edge_concentrated", "边缘集中"),
                    Choice("center_concentrated", "中心集中")
                ]
            }
        }

    def build_prompt(self, dimension: str) -> PROOFPrompt:
        """
        根据特征维度构建提示词

        Args:
            dimension: 特征维度名称（如："symptom_type", "color_center"）

        Returns:
            PROOFPrompt: 构建好的提示词对象

        Raises:
            ValueError: 如果维度不支持

        使用示例：
        ```python
        builder = FeaturePromptBuilder()
        q1_prompt = builder.build_prompt("symptom_type")
        q1_text = q1_prompt.render()
        ```
        """
        if dimension not in self.dimension_configs:
            raise ValueError(
                f"Unsupported dimension: {dimension}. "
                f"Supported: {list(self.dimension_configs.keys())}"
            )

        config = self.dimension_configs[dimension]

        # 构建 PROOF 提示词
        prompt = PROOFPrompt(
            question_id=config["question_id"],

            # P - Purpose
            purpose=PromptPurpose(
                task=config["task"],
                context="Image shows abnormal plant organ (confirmed by Q0.5)",
                why_important=f"This feature ({dimension}) is critical for disease matching in knowledge base"
            ),

            # R - Role
            role=PromptRole(
                role="plant disease feature extractor",
                expertise=["disease symptomology", "visual feature recognition", "botanical pathology"],
                constraints=["focus on disease-related features", "ignore irrelevant details"]
            ),

            # O - Observation
            observation=PromptObservation(
                visual_method=config["visual_method"],
                visual_clues=config["visual_clues"],
                focus_areas=["symptom appearance", "color patterns", "spatial distribution"]
            ),

            # O - Options
            options=PromptOptions(
                choices=config["choices"],
                allow_unknown=True,
                allow_uncertain=True
            ),

            # F - Format
            format_spec=PromptFormat(
                response_schema=FeatureResponse,
                examples=None,  # 可根据需要添加示例
                constraints=[
                    "if multiple features present, choose the PREDOMINANT one",
                    "use 'unknown' if truly cannot determine",
                    "provide alternatives if uncertain"
                ]
            ),

            version="v1.0"
        )

        return prompt

    def build_all_prompts(self) -> Dict[str, str]:
        """
        构建所有特征维度的提示词

        Returns:
            Dict[str, str]: 维度名称 -> 渲染后的提示词字符串

        使用示例：
        ```python
        builder = FeaturePromptBuilder()
        all_prompts = builder.build_all_prompts()
        print(all_prompts["symptom_type"])
        ```
        """
        prompts = {}
        for dimension in self.dimension_configs.keys():
            prompt = self.build_prompt(dimension)
            prompts[dimension] = prompt.render()
        return prompts


# 创建全局实例
feature_prompt_builder = FeaturePromptBuilder()


if __name__ == "__main__":
    """
    Q1-Q6 特征提取提示词测试

    验证：
    1. 所有6个特征维度都能成功生成提示词
    2. 提示词包含必要的组件
    3. 选项数量正确
    """
    print("=" * 80)
    print("Q1-Q6 动态特征提取提示词测试")
    print("=" * 80)

    builder = FeaturePromptBuilder()

    # 1. 测试所有维度
    print("\n[测试1] 生成所有维度的提示词")
    dimensions = ["symptom_type", "color_center", "color_border", "size", "location", "distribution"]

    for dim in dimensions:
        try:
            prompt = builder.build_prompt(dim)
            rendered = prompt.render()
            config = prompt.to_dict()

            print(f"\n  ✓ {dim}:")
            print(f"    - 问题ID: {config['question_id']}")
            print(f"    - 选项数量: {len(config['options']['choices'])}")
            print(f"    - 渲染后长度: {len(rendered)} 字符")
        except Exception as e:
            print(f"\n  ✗ {dim}: {e}")

    # 2. 详细测试 symptom_type（Q1）
    print("\n\n[测试2] 详细测试 Q1 (symptom_type)")
    q1_prompt = builder.build_prompt("symptom_type")
    q1_text = q1_prompt.render()

    print(f"  渲染后长度: {len(q1_text)} 字符")
    print(f"\n--- Q1 提示词内容（前800字符） ---\n{q1_text[:800]}\n...")

    # 验证关键词
    required_keywords = ["necrosis_spot", "powdery_coating", "chlorosis", "VISUAL CLUES"]
    print("\n  验证关键词:")
    for keyword in required_keywords:
        if keyword in q1_text:
            print(f"    ✓ {keyword}")
        else:
            print(f"    ✗ 缺少: {keyword}")

    # 3. 测试批量生成
    print("\n\n[测试3] 批量生成所有提示词")
    all_prompts = builder.build_all_prompts()
    print(f"  生成提示词数量: {len(all_prompts)}")
    for dim, prompt_text in all_prompts.items():
        print(f"  - {dim}: {len(prompt_text)} 字符")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
