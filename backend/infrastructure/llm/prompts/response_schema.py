"""
VLM 响应格式协议 - Pydantic Models

功能：
- 定义所有 VLM Provider 必须遵守的响应格式
- 使用 Pydantic V2 + Literal 类型严格限制选项
- 确保 Instructor 能自动验证和重试
- 支持 Q0系列（Q0.0-Q0.5）和 Q1-Q6 动态特征提取

所有 VLM Provider 必须返回严格符合此协议的 JSON

作者：AI Python Architect
日期：2025-11-12
"""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class VLMResponse(BaseModel):
    """
    VLM 响应基类

    所有 VLM 响应模型的基类，定义通用字段

    字段说明：
    - choice: 选择的选项值（字符串）
    - confidence: VLM 对此答案的置信度（0.0-1.0）
    - reasoning: 推理过程（可选，用于调试和日志记录）

    使用示例：
    ```python
    # 不直接使用，而是使用子类
    response = Q00Response(
        choice="plant",
        confidence=0.95,
        reasoning="Image clearly shows green leaves and flowers"
    )
    ```
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    choice: str = Field(..., description="选择的选项值")
    confidence: float = Field(..., ge=0.0, le=1.0, description="VLM对此答案的置信度（0.0-1.0）")
    reasoning: Optional[str] = Field(default="", description="推理过程（可选，用于调试）")


# ==================== Q0 系列响应格式（逐级过滤） ====================


class Q00Response(VLMResponse):
    """
    Q0.0 内容类型识别响应

    识别图像的内容类型（植物、动物、人物、物体、风景等）

    可选项：
    - plant: 植物
    - animal: 动物
    - person: 人物
    - object: 物体
    - landscape: 风景
    - other: 其他

    使用示例：
    ```python
    response = Q00Response(
        choice="plant",
        confidence=0.98,
        reasoning="Image shows green leaves and flower structures"
    )
    ```
    """
    choice: Literal["plant", "animal", "person", "object", "landscape", "other"]


class Q01Response(VLMResponse):
    """
    Q0.1 植物类别识别响应

    识别植物的大类（花卉、蔬菜、树木、农作物、草本等）

    可选项：
    - flower: 花卉（观赏性花卉）
    - vegetable: 蔬菜
    - tree: 树木
    - crop: 农作物（粮食作物）
    - grass: 草本植物
    - other: 其他植物

    使用示例：
    ```python
    response = Q01Response(
        choice="flower",
        confidence=0.92,
        reasoning="Image shows ornamental flower with colorful petals"
    )
    ```
    """
    choice: Literal["flower", "vegetable", "tree", "crop", "grass", "other"]


class Q02Response(VLMResponse):
    """
    Q0.2 花卉种属识别响应

    识别花卉的属（Genus）

    可选项：
    - Rosa: 玫瑰/月季属
    - Prunus: 樱花/樱桃属
    - Tulipa: 郁金香属
    - Dianthus: 康乃馨属
    - Paeonia: 牡丹属
    - unknown: 未知种属

    使用示例：
    ```python
    response = Q02Response(
        choice="Rosa",
        confidence=0.88,
        reasoning="Compound leaves with 5 leaflets and thorny stems indicate Rosa genus"
    )
    ```
    """
    choice: Literal["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia", "unknown"]


class Q03Response(VLMResponse):
    """
    Q0.3 器官识别响应

    识别图像中展示的植物器官（花朵或叶片）

    可选项：
    - flower: 花朵
    - leaf: 叶片
    - both: 同时包含花朵和叶片

    使用示例：
    ```python
    response = Q03Response(
        choice="leaf",
        confidence=0.95,
        reasoning="Image primarily shows leaves with visible veins"
    )
    ```
    """
    choice: Literal["flower", "leaf", "both"]


class Q04Response(VLMResponse):
    """
    Q0.4 完整性检查响应

    检查图像中植物器官的完整性（是否为完整的器官或特写）

    可选项：
    - complete: 完整器官（可看到整体形态）
    - partial: 部分器官（只能看到一部分）
    - close_up: 特写镜头（聚焦于某个细节）

    使用示例：
    ```python
    response = Q04Response(
        choice="close_up",
        confidence=0.90,
        reasoning="Image shows zoomed-in view of leaf surface with visible spots"
    )
    ```
    """
    choice: Literal["complete", "partial", "close_up"]


class Q05Response(VLMResponse):
    """
    Q0.5 异常判断响应

    判断植物器官是否健康或存在异常

    可选项：
    - healthy: 健康（无明显异常）
    - abnormal: 异常（存在病症、虫害或其他异常）

    使用示例：
    ```python
    response = Q05Response(
        choice="abnormal",
        confidence=0.96,
        reasoning="Dark spots and yellow halos visible on leaf surface"
    )
    ```
    """
    choice: Literal["healthy", "abnormal"]


# ==================== Q1-Q6 动态特征提取响应格式 ====================


class FeatureResponse(VLMResponse):
    """
    Q1-Q6 动态特征提取响应

    用于提取疾病特征的各个维度（symptom_type、color_center、color_border 等）
    该模型的 choice 字段值取决于具体的特征维度

    字段说明：
    - choice: 选择的特征值（根据具体维度动态变化）
    - confidence: VLM 置信度（0.0-1.0）
    - reasoning: 推理过程（可选）
    - alternatives: 其他可能的选项（可选，用于不确定的情况）

    使用示例（以 symptom_type 为例）：
    ```python
    # Q1: symptom_type（症状类型）
    response = FeatureResponse(
        choice="necrosis_spot",
        confidence=0.91,
        reasoning="Dark necrotic spots visible on leaf surface",
        alternatives=["chlorosis_spot"]
    )

    # Q2: color_center（症状中心颜色）
    response = FeatureResponse(
        choice="black",
        confidence=0.88,
        reasoning="Center of spots is dark black/brown"
    )
    ```
    """
    choice: str  # 根据特征维度动态变化
    alternatives: Optional[List[str]] = Field(
        default=None,
        description="其他可能的选项（不确定时提供）"
    )


# ==================== 特定特征维度的严格类型响应（可选，用于更强的类型检查） ====================


class SymptomTypeResponse(VLMResponse):
    """
    症状类型识别响应（严格类型版本）

    识别疾病症状的类型

    可选项：
    - necrosis_spot: 坏死斑点
    - powdery_coating: 白粉覆盖
    - chlorosis: 黄化
    - wilting: 枯萎
    - deformation: 畸形
    - rust_pustule: 锈病脓疱
    - mold: 霉层
    - other: 其他症状

    使用示例：
    ```python
    response = SymptomTypeResponse(
        choice="necrosis_spot",
        confidence=0.93,
        reasoning="Dark necrotic spots with defined borders"
    )
    ```
    """
    choice: Literal[
        "necrosis_spot",
        "powdery_coating",
        "chlorosis",
        "wilting",
        "deformation",
        "rust_pustule",
        "mold",
        "other"
    ]


class ColorResponse(VLMResponse):
    """
    颜色识别响应（严格类型版本）

    识别症状的颜色（中心颜色或边缘颜色）

    可选项：
    - black: 黑色
    - dark_brown: 深棕色
    - brown: 棕色
    - light_brown: 浅棕色
    - yellow: 黄色
    - light_yellow: 浅黄色
    - white: 白色
    - gray: 灰色
    - red: 红色
    - purple: 紫色
    - green: 绿色
    - other: 其他颜色

    使用示例：
    ```python
    response = ColorResponse(
        choice="black",
        confidence=0.89,
        reasoning="Spot centers are predominantly black"
    )
    ```
    """
    choice: Literal[
        "black",
        "dark_brown",
        "brown",
        "light_brown",
        "yellow",
        "light_yellow",
        "white",
        "gray",
        "red",
        "purple",
        "green",
        "other"
    ]


class SizeResponse(VLMResponse):
    """
    尺寸识别响应（严格类型版本）

    识别症状的尺寸大小

    可选项：
    - very_small: 极小（<2mm）
    - small: 小（2-5mm）
    - medium: 中等（5-10mm）
    - large: 大（10-20mm）
    - very_large: 极大（>20mm）

    使用示例：
    ```python
    response = SizeResponse(
        choice="medium",
        confidence=0.85,
        reasoning="Spots are approximately 6-8mm in diameter"
    )
    ```
    """
    choice: Literal["very_small", "small", "medium", "large", "very_large"]


class LocationResponse(VLMResponse):
    """
    位置识别响应（严格类型版本）

    识别症状在器官上的位置

    可选项：
    - lamina: 叶片（叶肉）
    - lamina_center: 叶片中心
    - lamina_edge: 叶片边缘
    - vein: 叶脉
    - petiole: 叶柄
    - stem: 茎干
    - petal: 花瓣
    - sepal: 萼片
    - whole: 整体

    使用示例：
    ```python
    response = LocationResponse(
        choice="lamina",
        confidence=0.92,
        reasoning="Spots are located on leaf lamina, not on veins or edges"
    )
    ```
    """
    choice: Literal[
        "lamina",
        "lamina_center",
        "lamina_edge",
        "vein",
        "petiole",
        "stem",
        "petal",
        "sepal",
        "whole"
    ]


class DistributionResponse(VLMResponse):
    """
    分布模式识别响应（严格类型版本）

    识别症状在器官上的分布模式

    可选项：
    - scattered: 散发（零星分布）
    - clustered: 聚集（集中分布）
    - along_vein: 沿叶脉分布
    - ring: 环状分布
    - uniform: 均匀分布
    - edge_concentrated: 边缘集中
    - center_concentrated: 中心集中

    使用示例：
    ```python
    response = DistributionResponse(
        choice="scattered",
        confidence=0.88,
        reasoning="Spots are randomly scattered across leaf surface"
    )
    ```
    """
    choice: Literal[
        "scattered",
        "clustered",
        "along_vein",
        "ring",
        "uniform",
        "edge_concentrated",
        "center_concentrated"
    ]


# ==================== 导出所有响应模型 ====================

__all__ = [
    "VLMResponse",
    # Q0 系列
    "Q00Response",
    "Q01Response",
    "Q02Response",
    "Q03Response",
    "Q04Response",
    "Q05Response",
    # Q1-Q6 动态特征提取
    "FeatureResponse",
    # 特定特征维度的严格类型响应
    "SymptomTypeResponse",
    "ColorResponse",
    "SizeResponse",
    "LocationResponse",
    "DistributionResponse",
]


if __name__ == "__main__":
    """
    VLM 响应 Schema 使用示例

    演示如何：
    1. 创建各种响应对象
    2. 验证数据合法性（Literal 类型检查）
    3. 序列化为 JSON
    4. 从 JSON 反序列化
    """
    import json

    print("=" * 80)
    print("VLM 响应 Schema 使用示例")
    print("=" * 80)

    # 1. Q0.0 内容类型识别
    print("\n[示例1] Q0.0 内容类型识别")
    q00_response = Q00Response(
        choice="plant",
        confidence=0.98,
        reasoning="Image shows green leaves and flower structures"
    )
    print(f"  [OK] 创建 Q0.0 响应: {q00_response.choice}")
    print(f"  - 置信度: {q00_response.confidence}")
    print(f"  - JSON: {q00_response.model_dump_json(indent=2)}")

    # 2. Q0.2 花卉种属识别
    print("\n[示例2] Q0.2 花卉种属识别")
    q02_response = Q02Response(
        choice="Rosa",
        confidence=0.88,
        reasoning="Compound leaves with 5 leaflets and thorny stems"
    )
    print(f"  [OK] 创建 Q0.2 响应: {q02_response.choice}")
    print(f"  - JSON: {q02_response.model_dump_json(indent=2)}")

    # 3. Q0.5 异常判断
    print("\n[示例3] Q0.5 异常判断")
    q05_response = Q05Response(
        choice="abnormal",
        confidence=0.96,
        reasoning="Dark spots and yellow halos visible on leaf"
    )
    print(f"  [OK] 创建 Q0.5 响应: {q05_response.choice}")
    print(f"  - JSON: {q05_response.model_dump_json(indent=2)}")

    # 4. FeatureResponse 动态特征提取
    print("\n[示例4] FeatureResponse 动态特征提取（symptom_type）")
    feature_response = FeatureResponse(
        choice="necrosis_spot",
        confidence=0.91,
        reasoning="Dark necrotic spots with defined borders",
        alternatives=["chlorosis_spot"]
    )
    print(f"  [OK] 创建 FeatureResponse: {feature_response.choice}")
    print(f"  - 可选项: {feature_response.alternatives}")
    print(f"  - JSON: {feature_response.model_dump_json(indent=2)}")

    # 5. 严格类型检查（Literal）
    print("\n[示例5] 严格类型检查（Literal）")
    try:
        # 尝试创建无效的响应（choice 不在 Literal 列表中）
        invalid_response = Q00Response(
            choice="invalid_option",  # 无效选项
            confidence=0.5
        )
        print(f"  [FAIL] 不应该通过验证")
    except Exception as e:
        print(f"  [OK] 验证失败（符合预期）: {type(e).__name__}")
        print(f"     错误信息: {str(e)[:100]}...")

    # 6. 从 JSON 反序列化
    print("\n[示例6] 从 JSON 反序列化")
    json_str = '{"choice": "Rosa", "confidence": 0.92, "reasoning": "Test"}'
    try:
        parsed_response = Q02Response.model_validate_json(json_str)
        print(f"  [OK] 成功解析 JSON: {parsed_response.choice}")
        print(f"  - 对象类型: {type(parsed_response).__name__}")
    except Exception as e:
        print(f"  [FAIL] 解析失败: {e}")

    # 7. 验证置信度范围
    print("\n[示例7] 验证置信度范围（0.0-1.0）")
    try:
        # 尝试创建置信度超出范围的响应
        invalid_confidence = Q00Response(
            choice="plant",
            confidence=1.5  # 超出范围
        )
        print(f"  [FAIL] 不应该通过验证")
    except Exception as e:
        print(f"  [OK] 验证失败（符合预期）: {type(e).__name__}")
        print(f"     错误信息: {str(e)[:100]}...")

    # 8. 测试所有 Q0 系列响应
    print("\n[示例8] 测试所有 Q0 系列响应")
    q0_responses = [
        Q00Response(choice="plant", confidence=0.95),
        Q01Response(choice="flower", confidence=0.92),
        Q02Response(choice="Rosa", confidence=0.88),
        Q03Response(choice="leaf", confidence=0.90),
        Q04Response(choice="close_up", confidence=0.87),
        Q05Response(choice="abnormal", confidence=0.93),
    ]
    for idx, resp in enumerate(q0_responses):
        print(f"  Q0.{idx} - choice: {resp.choice}, confidence: {resp.confidence}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)
