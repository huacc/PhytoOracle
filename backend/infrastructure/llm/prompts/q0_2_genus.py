"""
Q0.2 花卉种属识别提示词

功能：
- 识别花卉的属（Genus）
- 前置条件：Q0.1 已确认为花卉
- 支持的种属：Rosa（玫瑰/月季）、Prunus（樱花/樱桃）、Tulipa（郁金香）、Dianthus（康乃馨）、Paeonia（牡丹）
- 融入方法论 v5.0 的复合特征描述法

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
from .response_schema import Q02Response


# 定义 Q0.2 提示词
q0_2_prompt = PROOFPrompt(
    question_id="Q0.2",

    # P - Purpose（目的）
    purpose=PromptPurpose(
        task="Identify the genus (属) of this ornamental flower",
        context="Image contains an ornamental flower (confirmed by Q0.1)",
        why_important="Accurate genus identification is critical for narrowing down disease candidates in knowledge base"
    ),

    # R - Role（角色）
    role=PromptRole(
        role="plant taxonomy specialist",
        expertise=[
            "plant morphology",
            "flower identification",
            "leaf pattern recognition",
            "stem structure analysis"
        ],
        constraints=[
            "focus only on the 5 supported genera",
            "use compound features (leaf + stem + flower) for identification"
        ]
    ),

    # O - Observation（观察指导）
    observation=PromptObservation(
        visual_method="Compound Feature Description (方法论v5.0)",
        visual_clues={
            "Rosa": "Compound leaves with 5-7 leaflets, thorny/prickly stems, layered petals arranged in spiral pattern, often pink/red/white colors",
            "Prunus": "Simple oval leaves with serrated edges, 5-petal flowers (usually white or pink), smooth bark, flowers often appear in clusters",
            "Tulipa": "Long narrow leaves emerging from base, cup-shaped flowers with 6 petals, smooth unbranched stem, single flower per stem",
            "Dianthus": "Narrow linear leaves growing in opposite pairs, fringed/serrated petal edges, swollen stem nodes, often fragrant flowers",
            "Paeonia": "Large compound leaves with broad leaflets, very large multi-layered flowers (8-10cm+), thick sturdy stems, glossy foliage"
        },
        focus_areas=[
            "leaf shape and arrangement (compound vs simple)",
            "stem texture (thorny vs smooth)",
            "petal arrangement and count",
            "flower size and structure",
            "overall plant habit"
        ]
    ),

    # O - Options（选项）
    options=PromptOptions(
        choices=[
            Choice("Rosa", "玫瑰/月季属（复叶、有刺茎、层叠花瓣）"),
            Choice("Prunus", "樱花/樱桃属（单叶锯齿边缘、5瓣花、光滑树皮）"),
            Choice("Tulipa", "郁金香属（狭长基生叶、杯状花、单花茎）"),
            Choice("Dianthus", "康乃馨属（线形对生叶、花瓣边缘锯齿、茎节膨大）"),
            Choice("Paeonia", "牡丹属（大型复叶、巨大多层花朵、粗壮茎）"),
            Choice("unknown", "未知种属（不在支持的5个属中，或无法识别）")
        ],
        allow_unknown=True,
        allow_uncertain=False
    ),

    # F - Format（输出格式）
    format_spec=PromptFormat(
        response_schema=Q02Response,
        examples=[
            Example(
                input="Image shows a flower with compound leaves (5 leaflets per leaf), visible thorns on stem, pink multi-layered petals",
                output=Q02Response(
                    choice="Rosa",
                    confidence=0.92,
                    reasoning="Compound leaves with 5 leaflets + thorny stem + layered petals = typical Rosa characteristics"
                )
            ),
            Example(
                input="Image shows simple oval leaves with serrated edges, 5-petal white flowers in clusters, smooth bark",
                output=Q02Response(
                    choice="Prunus",
                    confidence=0.88,
                    reasoning="Simple serrated leaves + 5-petal flowers + smooth bark = Prunus genus (cherry/sakura)"
                )
            ),
            Example(
                input="Image shows narrow leaves emerging from ground, cup-shaped flower with 6 petals, single stem without branches",
                output=Q02Response(
                    choice="Tulipa",
                    confidence=0.90,
                    reasoning="Long narrow basal leaves + cup-shaped flower + unbranched stem = Tulipa (tulip)"
                )
            )
        ],
        constraints=[
            "use ALL available clues (leaves + stem + flower)",
            "if only 1-2 features match, consider 'unknown'",
            "confidence should reflect match quality (3+ features matched = high confidence)"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串常量
Q0_2_GENUS_PROMPT = q0_2_prompt.render()

# 导出配置
Q0_2_CONFIG = q0_2_prompt.to_dict()


if __name__ == "__main__":
    """Q0.2 提示词测试"""
    print("=" * 80)
    print("Q0.2 花卉种属识别提示词测试")
    print("=" * 80)

    print("\n[测试] 渲染提示词")
    print(f"  渲染后长度: {len(Q0_2_GENUS_PROMPT)} 字符")

    # 验证关键字段（5种花卉的视觉线索）
    print("\n[验证] 包含5种花卉的视觉线索")
    required_genera = ["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia"]
    for genus in required_genera:
        if genus in Q0_2_GENUS_PROMPT:
            # 查找该种属的描述
            lines = Q0_2_GENUS_PROMPT.split('\n')
            for line in lines:
                if genus in line and ("Compound" in line or "Simple" in line or "Long" in line or "Narrow" in line or "Large" in line):
                    print(f"  ✓ {genus}: {line.strip()[:80]}...")
                    break
        else:
            print(f"  ✗ 缺少: {genus}")

    print("\n[验证] 包含复合特征描述")
    if "Compound Feature Description" in Q0_2_GENUS_PROMPT:
        print("  ✓ 包含方法论 v5.0 的复合特征描述法")
    else:
        print("  ✗ 缺少方法论引用")

    print("\n" + "=" * 80)
