"""
Q0.4 完整性检查提示词

功能：
- 检查图像中植物器官的完整性
- 前置条件：Q0.3 已识别出器官类型
- 判断是完整器官、部分器官还是特写镜头
- 影响后续特征提取的细节程度

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
from .response_schema import Q04Response


# 定义 Q0.4 提示词
q0_4_prompt = PROOFPrompt(
    question_id="Q0.4",

    # P - Purpose（目的）
    purpose=PromptPurpose(
        task="Assess the completeness of the plant organ shown in the image",
        context="Image shows identified plant organ (flower or leaf, confirmed by Q0.3)",
        why_important="Completeness level affects which features can be reliably extracted for diagnosis"
    ),

    # R - Role（角色）
    role=PromptRole(
        role="image composition analyst",
        expertise=["image framing", "subject completeness assessment", "visual context evaluation"],
        constraints=["focus on organ visibility", "consider viewing angle and crop"]
    ),

    # O - Observation（观察指导）
    observation=PromptObservation(
        visual_method="Completeness Assessment Method",
        visual_clues={
            "complete": "Entire organ visible from base to tip (whole leaf or whole flower), can see overall shape and structure",
            "partial": "Only part of organ visible (e.g., half leaf, partial flower), edges are cut off by image boundaries",
            "close_up": "Extreme close-up/macro shot focusing on specific detail (e.g., leaf surface, petal texture), cannot see overall shape"
        },
        focus_areas=[
            "organ boundaries (are edges visible or cut off?)",
            "viewing distance (far enough to see whole organ?)",
            "crop framing (is organ centered and complete?)"
        ]
    ),

    # O - Options（选项）
    options=PromptOptions(
        choices=[
            Choice("complete", "完整器官（可看到器官的整体形态，从基部到顶端）"),
            Choice("partial", "部分器官（只能看到器官的一部分，边缘被裁剪）"),
            Choice("close_up", "特写镜头（极近距离拍摄，聚焦于某个细节，无法看到整体形态）")
        ],
        allow_unknown=False,
        allow_uncertain=False
    ),

    # F - Format（输出格式）
    format_spec=PromptFormat(
        response_schema=Q04Response,
        examples=[
            Example(
                input="Image shows an entire leaf from petiole to tip, all edges visible within frame",
                output=Q04Response(
                    choice="complete",
                    confidence=0.94,
                    reasoning="Entire leaf structure visible, can see full shape and proportions"
                )
            ),
            Example(
                input="Image shows leaf surface with visible spots, zoomed in so only 2-3 cm² area is visible",
                output=Q04Response(
                    choice="close_up",
                    confidence=0.92,
                    reasoning="Macro shot focusing on leaf surface details, overall leaf shape not visible"
                )
            ),
            Example(
                input="Image shows top half of a flower, bottom half is cut off by image border",
                output=Q04Response(
                    choice="partial",
                    confidence=0.88,
                    reasoning="Only partial flower visible, bottom portion cut off by framing"
                )
            )
        ],
        constraints=[
            "complete = can see ENTIRE organ within frame",
            "close_up = viewing distance < 5cm, cannot determine overall shape",
            "partial = edges cut off by image boundaries"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串常量
Q0_4_COMPLETENESS_PROMPT = q0_4_prompt.render()

# 导出配置
Q0_4_CONFIG = q0_4_prompt.to_dict()


if __name__ == "__main__":
    """Q0.4 提示词测试"""
    print("=" * 80)
    print("Q0.4 完整性检查提示词测试")
    print("=" * 80)

    print("\n[测试] 渲染提示词")
    print(f"  渲染后长度: {len(Q0_4_COMPLETENESS_PROMPT)} 字符")
    print(f"\n--- 提示词内容（前600字符） ---\n{Q0_4_COMPLETENESS_PROMPT[:600]}\n...")

    # 验证关键字段
    required_keywords = ["complete", "partial", "close_up", "completeness"]
    for keyword in required_keywords:
        if keyword in Q0_4_COMPLETENESS_PROMPT:
            print(f"  ✓ 包含: {keyword}")

    print("\n" + "=" * 80)
