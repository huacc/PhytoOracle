"""
Q0.5 异常判断提示词

功能：
- 判断植物器官是否健康或存在异常
- 前置条件：Q0.4 已确认器官完整性
- 这是进入疾病诊断的最后一道关卡
- 只有异常（abnormal）才继续进行 Q1-Q6 特征提取

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
from .response_schema import Q05Response


# 定义 Q0.5 提示词
q0_5_prompt = PROOFPrompt(
    question_id="Q0.5",

    # P - Purpose（目的）
    purpose=PromptPurpose(
        task="Determine if the plant organ shows any signs of disease or abnormality",
        context="Image shows plant organ with assessed completeness (confirmed by Q0.4)",
        why_important="Only abnormal plants need disease diagnosis; healthy plants can skip Q1-Q6 feature extraction"
    ),

    # R - Role（角色）
    role=PromptRole(
        role="plant health inspector",
        expertise=[
            "plant pathology",
            "disease symptom recognition",
            "visual health assessment",
            "normal vs abnormal morphology"
        ],
        constraints=[
            "distinguish disease symptoms from natural variations",
            "consider environmental damage vs disease"
        ]
    ),

    # O - Observation（观察指导）
    observation=PromptObservation(
        visual_method="Binary Health Assessment",
        visual_clues={
            "healthy": "Uniform green color, no spots/discoloration, smooth texture, normal shape, vibrant appearance, no damage",
            "abnormal": "Spots (black/brown/yellow), discoloration, unusual texture (powdery/moldy), deformation, wilting, necrosis, chlorosis, lesions"
        },
        focus_areas=[
            "color uniformity (are there unusual spots or discoloration?)",
            "surface texture (is it smooth or covered with powder/mold?)",
            "structural integrity (any holes, tears, or deformation?)",
            "tissue health (any necrotic or chlorotic areas?)"
        ]
    ),

    # O - Options（选项）
    options=PromptOptions(
        choices=[
            Choice("healthy", "健康（无明显异常，颜色均匀，质地正常）"),
            Choice("abnormal", "异常（存在病症、虫害或其他异常，如斑点、变色、畸形等）")
        ],
        allow_unknown=False,
        allow_uncertain=False
    ),

    # F - Format（输出格式）
    format_spec=PromptFormat(
        response_schema=Q05Response,
        examples=[
            Example(
                input="Image shows green leaf with uniform color, smooth surface, no visible damage",
                output=Q05Response(
                    choice="healthy",
                    confidence=0.96,
                    reasoning="Leaf shows normal green color, smooth texture, no signs of disease or damage"
                )
            ),
            Example(
                input="Image shows leaf with multiple dark spots surrounded by yellow halos",
                output=Q05Response(
                    choice="abnormal",
                    confidence=0.98,
                    reasoning="Dark necrotic spots with yellow halos indicate disease symptoms (likely fungal infection)"
                )
            ),
            Example(
                input="Image shows leaf covered with white powdery coating",
                output=Q05Response(
                    choice="abnormal",
                    confidence=0.97,
                    reasoning="White powdery coating is characteristic of powdery mildew disease"
                )
            ),
            Example(
                input="Image shows leaf with irregular brown patches and some yellowing",
                output=Q05Response(
                    choice="abnormal",
                    confidence=0.93,
                    reasoning="Brown patches and yellowing indicate tissue damage or disease"
                )
            )
        ],
        constraints=[
            "be sensitive to subtle abnormalities - even small spots indicate 'abnormal'",
            "minor natural aging (slight yellowing at leaf tips) is still 'healthy'",
            "focus on disease-like patterns, not mechanical damage"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串常量
Q0_5_ABNORMALITY_PROMPT = q0_5_prompt.render()

# 导出配置
Q0_5_CONFIG = q0_5_prompt.to_dict()


if __name__ == "__main__":
    """Q0.5 提示词测试"""
    print("=" * 80)
    print("Q0.5 异常判断提示词测试")
    print("=" * 80)

    print("\n[测试] 渲染提示词")
    print(f"  渲染后长度: {len(Q0_5_ABNORMALITY_PROMPT)} 字符")
    print(f"\n--- 提示词内容（前800字符） ---\n{Q0_5_ABNORMALITY_PROMPT[:800]}\n...")

    # 验证关键字段
    required_keywords = ["healthy", "abnormal", "disease", "spots", "VISUAL CLUES"]
    for keyword in required_keywords:
        if keyword in Q0_5_ABNORMALITY_PROMPT:
            print(f"  ✓ 包含: {keyword}")

    # 验证 Few-shot 示例数量
    import re
    example_matches = re.findall(r"Example \d+:", Q0_5_ABNORMALITY_PROMPT)
    print(f"\n[验证] Few-shot 示例数量: {len(example_matches)}")
    if len(example_matches) >= 3:
        print("  ✓ 包含足够的示例（至少3个）")

    print("\n" + "=" * 80)
