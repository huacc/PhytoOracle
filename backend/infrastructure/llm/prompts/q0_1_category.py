"""
Q0.1 植物类别识别提示词

功能：
- 识别植物的大类（花卉、蔬菜、树木、农作物、草本等）
- 前置条件：Q0.0 已确认为植物
- 只有花卉才能继续进行疾病诊断

作者：AI Python Architect
日期：2025-11-12
"""

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
from .response_schema import Q01Response


# 定义 Q0.1 提示词
q0_1_prompt = PROOFPrompt(
    question_id="Q0.1",

    # P - Purpose（目的）
    purpose=PromptPurpose(
        task="Identify the plant category (flower, vegetable, tree, crop, grass, or other)",
        context="Image contains a plant (confirmed by Q0.0)",
        why_important="Only ornamental flowers are supported for disease diagnosis in current version"
    ),

    # R - Role（角色）
    role=PromptRole(
        role="plant category specialist",
        expertise=["botany", "plant taxonomy", "agricultural classification"],
        constraints=["distinguish ornamental plants from edible plants", "focus on plant function and use"]
    ),

    # O - Observation（观察指导）
    observation=PromptObservation(
        visual_method="Functional Classification Method",
        visual_clues={
            "flower": "Ornamental plant with colorful petals, grown for beauty (roses, tulips, carnations)",
            "vegetable": "Edible plant grown for food (tomatoes, lettuce, cabbage)",
            "tree": "Woody plant with trunk and branches (oak, pine, cherry tree)",
            "crop": "Agricultural plant grown for grains (wheat, corn, rice)",
            "grass": "Herbaceous plant with narrow leaves (lawn grass, wild grass)",
            "other": "Plants that don't fit above categories (ferns, mosses, succulents)"
        },
        focus_areas=["flower presence", "leaf type", "growth habit", "plant size"]
    ),

    # O - Options（选项）
    options=PromptOptions(
        choices=[
            Choice("flower", "花卉（观赏性花卉植物，如玫瑰、郁金香、康乃馨）"),
            Choice("vegetable", "蔬菜（可食用蔬菜，如番茄、生菜、白菜）"),
            Choice("tree", "树木（木本植物，有主干和分枝）"),
            Choice("crop", "农作物（粮食作物，如小麦、玉米、水稻）"),
            Choice("grass", "草本植物（狭叶草类，如草坪草、野草）"),
            Choice("other", "其他植物（不属于以上类别，如蕨类、苔藓、多肉）")
        ],
        allow_unknown=False,
        allow_uncertain=False
    ),

    # F - Format（输出格式）
    format_spec=PromptFormat(
        response_schema=Q01Response,
        examples=[
            Example(
                input="Image shows a plant with colorful pink petals arranged in layers, thorny stem",
                output=Q01Response(
                    choice="flower",
                    confidence=0.96,
                    reasoning="Colorful petals indicate ornamental flower, likely a rose"
                )
            ),
            Example(
                input="Image shows green leaves with serrated edges, red fruits visible",
                output=Q01Response(
                    choice="vegetable",
                    confidence=0.88,
                    reasoning="Red fruits and leaf structure suggest tomato plant"
                )
            )
        ],
        constraints=[
            "prioritize flower identification for ornamental plants",
            "consider both flower presence and plant structure"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串常量
Q0_1_PLANT_CATEGORY_PROMPT = q0_1_prompt.render()

# 导出配置
Q0_1_CONFIG = q0_1_prompt.to_dict()


if __name__ == "__main__":
    """Q0.1 提示词测试"""
    print("=" * 80)
    print("Q0.1 植物类别识别提示词测试")
    print("=" * 80)

    print("\n[测试] 渲染提示词")
    print(f"  渲染后长度: {len(Q0_1_PLANT_CATEGORY_PROMPT)} 字符")
    print(f"\n--- 提示词内容（前800字符） ---\n{Q0_1_PLANT_CATEGORY_PROMPT[:800]}\n...")

    # 验证关键字段
    required_keywords = ["flower", "vegetable", "tree", "VISUAL CLUES"]
    for keyword in required_keywords:
        if keyword in Q0_1_PLANT_CATEGORY_PROMPT:
            print(f"  ✓ 包含: {keyword}")

    print("\n" + "=" * 80)
