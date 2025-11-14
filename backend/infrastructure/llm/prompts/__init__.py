"""
提示词模块 - 导出所有提示词和框架组件

功能：
- 导出 PROOF Framework 核心组件
- 导出所有 VLM 响应 Schema
- 导出 Q0.0-Q0.5 提示词常量
- 导出 Q1-Q6 动态特征提取构建器

使用示例：
```python
# 导入 Q0 系列提示词
from backend.infrastructure.llm.prompts import (
    Q0_0_CONTENT_TYPE_PROMPT,
    Q0_2_GENUS_PROMPT,
    Q0_5_ABNORMALITY_PROMPT
)

# 导入响应 Schema
from backend.infrastructure.llm.prompts import Q02Response, Q05Response

# 导入特征提取构建器
from backend.infrastructure.llm.prompts import feature_prompt_builder

# 使用动态构建器生成 Q1-Q6 提示词
q1_prompt = feature_prompt_builder.build_prompt("symptom_type")
```

作者：AI Python Architect
日期：2025-11-12
"""

# ==================== PROOF Framework 核心组件 ====================
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

# ==================== VLM 响应 Schema ====================
from .response_schema import (
    # 基类
    VLMResponse,
    # Q0 系列
    Q00Response,
    Q01Response,
    Q02Response,
    Q03Response,
    Q04Response,
    Q05Response,
    # Q1-Q6 动态特征提取
    FeatureResponse,
    # 特定特征维度的严格类型响应
    SymptomTypeResponse,
    ColorResponse,
    SizeResponse,
    LocationResponse,
    DistributionResponse,
)

# ==================== Q0 系列提示词常量 ====================
from .q0_0_content import Q0_0_CONTENT_TYPE_PROMPT, Q0_0_CONFIG, q0_0_prompt
from .q0_1_category import Q0_1_PLANT_CATEGORY_PROMPT, Q0_1_CONFIG, q0_1_prompt
from .q0_2_genus import Q0_2_GENUS_PROMPT, Q0_2_CONFIG, q0_2_prompt
from .q0_3_organ import Q0_3_ORGAN_PROMPT, Q0_3_CONFIG, q0_3_prompt
from .q0_4_completeness import Q0_4_COMPLETENESS_PROMPT, Q0_4_CONFIG, q0_4_prompt
from .q0_5_abnormality import Q0_5_ABNORMALITY_PROMPT, Q0_5_CONFIG, q0_5_prompt

# ==================== Q1-Q6 动态特征提取 ====================
from .q1_q6_features import FeaturePromptBuilder, feature_prompt_builder


# ==================== 导出所有公共接口 ====================
__all__ = [
    # PROOF Framework 核心组件
    "PROOFPrompt",
    "PromptPurpose",
    "PromptRole",
    "PromptObservation",
    "PromptOptions",
    "Choice",
    "PromptFormat",
    "Example",

    # VLM 响应 Schema
    "VLMResponse",
    "Q00Response",
    "Q01Response",
    "Q02Response",
    "Q03Response",
    "Q04Response",
    "Q05Response",
    "FeatureResponse",
    "SymptomTypeResponse",
    "ColorResponse",
    "SizeResponse",
    "LocationResponse",
    "DistributionResponse",

    # Q0 系列提示词常量（渲染后的字符串）
    "Q0_0_CONTENT_TYPE_PROMPT",
    "Q0_1_PLANT_CATEGORY_PROMPT",
    "Q0_2_GENUS_PROMPT",
    "Q0_3_ORGAN_PROMPT",
    "Q0_4_COMPLETENESS_PROMPT",
    "Q0_5_ABNORMALITY_PROMPT",

    # Q0 系列配置对象（用于版本控制）
    "Q0_0_CONFIG",
    "Q0_1_CONFIG",
    "Q0_2_CONFIG",
    "Q0_3_CONFIG",
    "Q0_4_CONFIG",
    "Q0_5_CONFIG",

    # Q0 系列原始 Prompt 对象
    "q0_0_prompt",
    "q0_1_prompt",
    "q0_2_prompt",
    "q0_3_prompt",
    "q0_4_prompt",
    "q0_5_prompt",

    # Q1-Q6 动态特征提取
    "FeaturePromptBuilder",
    "feature_prompt_builder",
]


# ==================== 模块级别的便捷函数 ====================

def get_all_q0_prompts():
    """
    获取所有 Q0 系列提示词（渲染后的字符串）

    Returns:
        dict: 键为问题ID（如 "Q0.0"），值为渲染后的提示词字符串

    使用示例：
    ```python
    from backend.infrastructure.llm.prompts import get_all_q0_prompts

    all_q0_prompts = get_all_q0_prompts()
    print(all_q0_prompts["Q0.0"])  # 打印 Q0.0 提示词
    ```
    """
    return {
        "Q0.0": Q0_0_CONTENT_TYPE_PROMPT,
        "Q0.1": Q0_1_PLANT_CATEGORY_PROMPT,
        "Q0.2": Q0_2_GENUS_PROMPT,
        "Q0.3": Q0_3_ORGAN_PROMPT,
        "Q0.4": Q0_4_COMPLETENESS_PROMPT,
        "Q0.5": Q0_5_ABNORMALITY_PROMPT,
    }


def get_feature_prompt(dimension: str) -> str:
    """
    获取特征维度的提示词（Q1-Q6）

    Args:
        dimension: 特征维度名称（如 "symptom_type", "color_center"）

    Returns:
        str: 渲染后的提示词字符串

    使用示例：
    ```python
    from backend.infrastructure.llm.prompts import get_feature_prompt

    q1_prompt = get_feature_prompt("symptom_type")
    q2_prompt = get_feature_prompt("color_center")
    ```
    """
    prompt_obj = feature_prompt_builder.build_prompt(dimension)
    return prompt_obj.render()


if __name__ == "__main__":
    """
    提示词模块测试

    验证：
    1. 所有导入正常
    2. 所有提示词可访问
    3. 便捷函数工作正常
    """
    print("=" * 80)
    print("提示词模块测试")
    print("=" * 80)

    # 1. 测试 Q0 系列提示词
    print("\n[测试1] Q0 系列提示词")
    q0_prompts = get_all_q0_prompts()
    for qid, prompt_text in q0_prompts.items():
        print(f"  ✓ {qid}: {len(prompt_text)} 字符")

    # 2. 测试响应 Schema
    print("\n[测试2] 响应 Schema")
    try:
        q00_resp = Q00Response(choice="plant", confidence=0.95, reasoning="test")
        q02_resp = Q02Response(choice="Rosa", confidence=0.88, reasoning="test")
        feature_resp = FeatureResponse(choice="necrosis_spot", confidence=0.90)
        print("  ✓ Q00Response 可实例化")
        print("  ✓ Q02Response 可实例化")
        print("  ✓ FeatureResponse 可实例化")
    except Exception as e:
        print(f"  ✗ Schema 实例化失败: {e}")

    # 3. 测试动态特征提取
    print("\n[测试3] 动态特征提取（Q1-Q6）")
    try:
        q1_prompt = get_feature_prompt("symptom_type")
        q2_prompt = get_feature_prompt("color_center")
        print(f"  ✓ Q1 (symptom_type): {len(q1_prompt)} 字符")
        print(f"  ✓ Q2 (color_center): {len(q2_prompt)} 字符")
    except Exception as e:
        print(f"  ✗ 动态提取失败: {e}")

    # 4. 测试 PROOF Framework 组件
    print("\n[测试4] PROOF Framework 组件")
    try:
        purpose = PromptPurpose(task="Test task")
        role = PromptRole(role="test role", expertise=["test"])
        observation = PromptObservation()
        options = PromptOptions(choices=[Choice("a", "test")])
        print("  ✓ 所有 PROOF 组件可实例化")
    except Exception as e:
        print(f"  ✗ PROOF 组件失败: {e}")

    print("\n" + "=" * 80)
    print("模块测试完成")
    print("=" * 80)
