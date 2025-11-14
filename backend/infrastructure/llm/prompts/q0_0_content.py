"""
Q0.0 内容类型识别提示词

功能：
- 识别图像的内容类型（植物、动物、人物、物体、风景等）
- 这是诊断流程的第一道关卡
- 如果不是植物，直接拒绝后续诊断

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
from .response_schema import Q00Response


# 定义 Q0.0 提示词
q0_0_prompt = PROOFPrompt(
    question_id="Q0.0",

    # P - Purpose（目的）
    purpose=PromptPurpose(
        task="Identify the content type of this image",
        context="This is the first step in plant disease diagnosis workflow",
        why_important="Only plant images should proceed to further diagnosis steps"
    ),

    # R - Role（角色）
    role=PromptRole(
        role="image content classifier",
        expertise=["computer vision", "object recognition", "content categorization"],
        constraints=["focus on primary subject", "ignore background elements"]
    ),

    # O - Observation（观察指导）
    observation=PromptObservation(
        visual_method="Primary Subject Identification",
        visual_clues={
            "plant": "Green leaves, stems, flowers, roots, or other botanical structures",
            "animal": "Living creatures with eyes, fur, feathers, or scales",
            "person": "Human body parts (face, hands, clothing)",
            "object": "Man-made items (tools, furniture, devices)",
            "landscape": "Natural scenery (mountains, rivers, sky)",
            "other": "Anything that doesn't fit above categories"
        },
        focus_areas=["primary subject", "dominant features", "overall composition"]
    ),

    # O - Options（选项）
    options=PromptOptions(
        choices=[
            Choice("plant", "植物（绿叶、茎、花、根等植物结构）"),
            Choice("animal", "动物（有眼睛、毛发、羽毛或鳞片的生物）"),
            Choice("person", "人物（人体部位、面部、手部）"),
            Choice("object", "物体（人造物品，如工具、家具）"),
            Choice("landscape", "风景（自然景观，如山、河、天空）"),
            Choice("other", "其他（不属于以上任何类别）")
        ],
        allow_unknown=False,  # 必须选择一个类别
        allow_uncertain=False
    ),

    # F - Format（输出格式）
    format_spec=PromptFormat(
        response_schema=Q00Response,
        examples=[
            Example(
                input="Image shows green leaves with visible veins and some flowers",
                output=Q00Response(
                    choice="plant",
                    confidence=0.98,
                    reasoning="Clear botanical structures (leaves and flowers) visible"
                )
            ),
            Example(
                input="Image shows a smartphone on a desk",
                output=Q00Response(
                    choice="object",
                    confidence=0.95,
                    reasoning="Man-made electronic device, not a living organism"
                )
            )
        ],
        constraints=[
            "confidence should be high (>0.8) for clear images",
            "use 'other' only when truly unclear"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串常量（供 VLM 客户端使用）
Q0_0_CONTENT_TYPE_PROMPT = q0_0_prompt.render()

# 导出配置（用于版本控制）
Q0_0_CONFIG = q0_0_prompt.to_dict()


if __name__ == "__main__":
    """
    Q0.0 提示词测试

    验证：
    1. 提示词能成功渲染
    2. 包含所有必要组件
    3. 输出格式正确
    """
    print("=" * 80)
    print("Q0.0 内容类型识别提示词测试")
    print("=" * 80)

    # 1. 渲染提示词
    print("\n[测试1] 渲染提示词")
    print(f"  渲染后长度: {len(Q0_0_CONTENT_TYPE_PROMPT)} 字符")
    print(f"\n--- 提示词内容 ---\n{Q0_0_CONTENT_TYPE_PROMPT}\n--- 结束 ---")

    # 2. 验证关键字段
    print("\n[测试2] 验证关键字段")
    required_keywords = ["TASK", "CHOICES", "plant", "animal", "RESPONSE FORMAT"]
    for keyword in required_keywords:
        if keyword in Q0_0_CONTENT_TYPE_PROMPT:
            print(f"  ✓ 包含关键字: {keyword}")
        else:
            print(f"  ✗ 缺少关键字: {keyword}")

    # 3. 验证配置导出
    print("\n[测试3] 验证配置导出")
    print(f"  问题ID: {Q0_0_CONFIG['question_id']}")
    print(f"  版本: {Q0_0_CONFIG['version']}")
    print(f"  选项数量: {len(Q0_0_CONFIG['options']['choices'])}")

    print("\n" + "=" * 80)
