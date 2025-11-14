"""
Q0.3 器官识别提示词

功能：
- 识别图像中展示的植物器官（花朵、叶片或同时包含两者）
- 前置条件：Q0.2 已识别出花卉种属
- 用于确定后续特征提取的焦点区域

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
from .response_schema import Q03Response


# 定义 Q0.3 提示词
q0_3_prompt = PROOFPrompt(
    question_id="Q0.3",

    # P - Purpose（目的）
    purpose=PromptPurpose(
        task="Identify which plant organ (flower or leaf) is prominently shown in the image",
        context="Image contains an identified flower genus (confirmed by Q0.2)",
        why_important="Different organs require different feature extraction strategies for disease diagnosis"
    ),

    # R - Role（角色）
    role=PromptRole(
        role="plant anatomy specialist",
        expertise=["plant organ recognition", "botanical morphology", "image composition analysis"],
        constraints=["focus on primary organ", "ignore minor background organs"]
    ),

    # O - Observation（观察指导）
    observation=PromptObservation(
        visual_method="Primary Organ Identification",
        visual_clues={
            "flower": "Colorful petals, reproductive structures (stamens, pistils), flower buds - takes up majority of image",
            "leaf": "Green lamina (leaf blade), visible veins, petiole (leaf stalk) - leaf is the main subject",
            "both": "Both flower and leaf are clearly visible and occupy significant portions of the image"
        },
        focus_areas=["image composition", "subject proportions", "dominant features"]
    ),

    # O - Options（选项）
    options=PromptOptions(
        choices=[
            Choice("flower", "花朵（图像主要展示花瓣、花蕊等花器官）"),
            Choice("leaf", "叶片（图像主要展示叶片、叶脉等叶器官）"),
            Choice("both", "同时包含（花朵和叶片都清晰可见且占据显著比例）")
        ],
        allow_unknown=False,
        allow_uncertain=False
    ),

    # F - Format（输出格式）
    format_spec=PromptFormat(
        response_schema=Q03Response,
        examples=[
            Example(
                input="Image shows close-up of green leaves with visible veins, no flowers visible",
                output=Q03Response(
                    choice="leaf",
                    confidence=0.95,
                    reasoning="Image primarily shows leaf structures, no flower organs present"
                )
            ),
            Example(
                input="Image shows pink flower petals with yellow center, some leaves in background",
                output=Q03Response(
                    choice="flower",
                    confidence=0.92,
                    reasoning="Flower occupies majority of image, leaves are minor background elements"
                )
            ),
            Example(
                input="Image shows rose flower with multiple leaves clearly visible around it",
                output=Q03Response(
                    choice="both",
                    confidence=0.88,
                    reasoning="Both flower and leaves are prominent and occupy significant portions"
                )
            )
        ],
        constraints=[
            "choose 'both' only if BOTH organs are prominent",
            "background elements don't count - focus on main subject"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串常量
Q0_3_ORGAN_PROMPT = q0_3_prompt.render()

# 导出配置
Q0_3_CONFIG = q0_3_prompt.to_dict()


if __name__ == "__main__":
    """Q0.3 提示词测试"""
    print("=" * 80)
    print("Q0.3 器官识别提示词测试")
    print("=" * 80)

    print("\n[测试] 渲染提示词")
    print(f"  渲染后长度: {len(Q0_3_ORGAN_PROMPT)} 字符")
    print(f"\n--- 提示词内容（前600字符） ---\n{Q0_3_ORGAN_PROMPT[:600]}\n...")

    # 验证关键字段
    required_keywords = ["flower", "leaf", "both", "organ"]
    for keyword in required_keywords:
        if keyword in Q0_3_ORGAN_PROMPT:
            print(f"  ✓ 包含: {keyword}")

    print("\n" + "=" * 80)
