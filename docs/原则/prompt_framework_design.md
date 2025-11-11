# PhytoOracle 提示词结构化框架 (PROOF Framework)

> 本文档定义了 PhytoOracle 项目的提示词标准框架，确保所有 VLM 提示词的规范性、一致性和可维护性。

---

## 1. 为什么需要提示词框架？

### 1.1 当前痛点

❌ **缺乏一致性**：不同开发者写的提示词风格不同
❌ **难以维护**：提示词是大段文本，修改时容易遗漏关键部分
❌ **难以 A/B 测试**：无法只改变某个维度（如 Few-shot 示例）而保持其他部分不变
❌ **缺乏可追溯性**：不清楚每个提示词包含哪些元素

### 1.2 框架化的好处

✅ **规范化**：所有提示词遵循统一结构
✅ **参数化**：可以只修改某个维度（如 Tone、Examples）
✅ **版本控制友好**：参数变化一目了然
✅ **团队协作**：新成员可以快速上手
✅ **A/B 测试**：可以生成多个变体（只改变某个参数）

---

## 2. PROOF 框架定义

**PROOF** = **P**urpose + **R**ole + **O**bservation + **O**ptions + **F**ormat

### 2.1 框架结构

```python
class PromptFramework:
    """提示词框架基类"""

    # P - Purpose（目的）
    purpose: str           # 这个问题要回答什么？
    context: Optional[str] # 前置条件（如"The image contains a plant"）

    # R - Role（角色）
    role: str              # VLM 扮演的角色
    expertise: List[str]   # 需要的专业知识（如["plant pathology", "visual analysis"]）

    # O - Observation（观察指导）
    visual_method: Optional[str]  # 视觉化方法（如"Egg Yolk Metaphor"）
    visual_clues: Optional[dict]  # 视觉线索（如各花卉的特征描述）

    # O - Options（选项）
    choices: List[Choice]         # 可选答案
    allow_unknown: bool = True    # 是否允许"unknown"选项

    # F - Format（格式）
    response_schema: Type[BaseModel]  # Pydantic 响应模型
    examples: Optional[List[Example]] # Few-shot 示例

    # 元数据
    question_id: str       # 问题ID（如"Q0.2"）
    version: str           # 版本号（如"v1.0"）
    last_modified: str     # 最后修改日期
```

---

## 3. PROOF 框架详细说明

### 3.1 P - Purpose（目的）

**定义**：明确告诉 VLM 这个问题的目标是什么。

**包含元素**：
- `task`：一句话描述任务（如"Identify the genus of this flower"）
- `context`：前置条件（如"The image contains an ornamental flower"）
- `why_important`：为什么需要回答这个问题（可选，用于复杂任务）

**示例**：

```python
purpose = PromptPurpose(
    task="Identify the genus (属) of this flower",
    context="The image contains an ornamental flower (confirmed by Q0.1)",
    why_important="This helps narrow down candidate diseases in the knowledge base"
)
```

---

### 3.2 R - Role（角色）

**定义**：明确 VLM 的角色和专业知识领域。

**包含元素**：
- `role`：角色名称（如"plant disease diagnosis assistant"）
- `expertise`：需要的专业知识列表
- `constraints`：角色的限制（如"不能诊断人类疾病"）

**示例**：

```python
role = PromptRole(
    role="plant disease diagnosis assistant",
    expertise=["plant taxonomy", "visual morphology analysis"],
    constraints=["Only diagnose ornamental flowers", "No medical advice for humans"]
)
```

---

### 3.3 O - Observation（观察指导）

**定义**：指导 VLM 如何观察图片，融入视觉化方法。

**包含元素**：
- `visual_method`：视觉化方法名称（如"Egg Yolk Metaphor"）
- `visual_clues`：具体的视觉线索（如各花卉的特征）
- `focus_areas`：重点关注的区域（如"leaf edges", "spot center"）

**示例**：

```python
observation = PromptObservation(
    visual_method="Compound Feature Description",
    visual_clues={
        "Rosa": "Compound leaves with 5-7 leaflets, thorny stems, layered petals",
        "Prunus": "Simple oval leaves with serrated edges, 5-petal flowers, smooth bark"
    },
    focus_areas=["leaf shape", "stem texture", "petal arrangement"]
)
```

---

### 3.4 O - Options（选项）

**定义**：明确列出所有可选答案，以及如何处理不确定性。

**包含元素**：
- `choices`：选项列表（每个选项包含 label + description）
- `allow_unknown`：是否允许"unknown"选项
- `allow_uncertain`：是否允许"unclear"选项
- `multi_select`：是否允许多选（默认 False）

**示例**：

```python
options = PromptOptions(
    choices=[
        Choice(label="Rosa", description="玫瑰/月季属"),
        Choice(label="Prunus", description="樱花/樱桃属"),
        Choice(label="Tulipa", description="郁金香属"),
        Choice(label="Dianthus", description="康乃馨属"),
        Choice(label="Paeonia", description="牡丹属")
    ],
    allow_unknown=True,
    allow_uncertain=False,
    multi_select=False
)
```

---

### 3.5 F - Format（格式）

**定义**：明确输出格式和 Few-shot 示例。

**包含元素**：
- `response_schema`：Pydantic 响应模型（用于验证）
- `examples`：Few-shot 示例列表
- `constraints`：输出约束（如"Only return JSON, no additional text"）

**示例**：

```python
format_spec = PromptFormat(
    response_schema=Q02Response,
    examples=[
        Example(
            input="Image shows a flower with compound leaves (5 leaflets), thorns on stem, pink layered petals",
            output=Q02Response(
                choice="Rosa",
                confidence=0.92,
                reasoning="Compound leaves with 5 leaflets and thorny stems are典型特征 of Rosa genus"
            )
        )
    ],
    constraints=[
        "Only return JSON",
        "No additional text outside JSON structure",
        "Confidence must be between 0.0 and 1.0"
    ]
)
```

---

## 4. 代码实现

### 4.1 框架基类

```python
# infrastructure/llm/prompts/framework.py
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PromptPurpose:
    """提示词目的"""
    task: str                          # 任务描述（一句话）
    context: Optional[str] = None      # 前置条件
    why_important: Optional[str] = None  # 为什么重要

@dataclass
class PromptRole:
    """提示词角色"""
    role: str                     # 角色名称
    expertise: List[str]          # 专业知识领域
    constraints: List[str] = None # 角色限制

@dataclass
class PromptObservation:
    """观察指导"""
    visual_method: Optional[str] = None      # 视觉化方法名称
    visual_clues: Optional[Dict[str, str]] = None  # 视觉线索
    focus_areas: Optional[List[str]] = None  # 重点关注区域

@dataclass
class Choice:
    """选项"""
    label: str           # 选项标签
    description: str     # 选项描述

@dataclass
class PromptOptions:
    """提示词选项"""
    choices: List[Choice]           # 选项列表
    allow_unknown: bool = True      # 是否允许"unknown"
    allow_uncertain: bool = False   # 是否允许"unclear"
    multi_select: bool = False      # 是否允许多选

@dataclass
class Example:
    """Few-shot 示例"""
    input: str                      # 输入描述
    output: BaseModel               # 输出（Pydantic 对象）

@dataclass
class PromptFormat:
    """输出格式"""
    response_schema: Type[BaseModel]  # Pydantic 响应模型
    examples: Optional[List[Example]] = None  # Few-shot 示例
    constraints: List[str] = None     # 输出约束

class PROOFPrompt:
    """PROOF 框架提示词"""

    def __init__(
        self,
        question_id: str,
        purpose: PromptPurpose,
        role: PromptRole,
        observation: PromptObservation,
        options: PromptOptions,
        format_spec: PromptFormat,
        version: str = "v1.0"
    ):
        self.question_id = question_id
        self.purpose = purpose
        self.role = role
        self.observation = observation
        self.options = options
        self.format_spec = format_spec
        self.version = version
        self.last_modified = datetime.now().isoformat()

    def render(self) -> str:
        """渲染成最终的提示词字符串"""
        sections = []

        # 1. Role
        sections.append(f"You are a {self.role.role}.")
        if self.role.expertise:
            sections.append(f"Your expertise: {', '.join(self.role.expertise)}.")
        if self.role.constraints:
            sections.append(f"Constraints: {' '.join(self.role.constraints)}.")

        sections.append("")  # 空行

        # 2. Purpose
        sections.append(f"TASK: {self.purpose.task}")
        if self.purpose.context:
            sections.append(f"CONTEXT: {self.purpose.context}")

        sections.append("")

        # 3. Observation（如果有）
        if self.observation.visual_method:
            sections.append(f"VISUAL METHOD ({self.observation.visual_method}):")

        if self.observation.visual_clues:
            sections.append("VISUAL CLUES:")
            for key, value in self.observation.visual_clues.items():
                sections.append(f"- {key}: {value}")
            sections.append("")

        if self.observation.focus_areas:
            sections.append(f"FOCUS ON: {', '.join(self.observation.focus_areas)}")
            sections.append("")

        # 4. Options
        sections.append("CHOICES:")
        for choice in self.options.choices:
            sections.append(f"- {choice.label}: {choice.description}")

        if self.options.allow_unknown:
            sections.append("- unknown (如果不在以上列表中)")
        if self.options.allow_uncertain:
            sections.append("- unclear (如果图像质量不足以判断)")

        sections.append("")

        # 5. Format（Few-shot 示例）
        if self.format_spec.examples:
            sections.append("FEW-SHOT EXAMPLE:")
            for example in self.format_spec.examples:
                sections.append(f"Input: {example.input}")
                sections.append(f"Output: {example.output.model_dump_json(indent=2)}")
            sections.append("")

        # 6. Format（响应格式）
        sections.append("RESPONSE FORMAT (JSON only):")
        schema_example = self.format_spec.response_schema.model_json_schema()
        sections.append("```json")
        sections.append(self._generate_example_json(schema_example))
        sections.append("```")
        sections.append("")

        # 7. Constraints
        if self.format_spec.constraints:
            sections.append("IMPORTANT:")
            for constraint in self.format_spec.constraints:
                sections.append(f"- {constraint}")

        return "\n".join(sections)

    def _generate_example_json(self, schema: dict) -> str:
        """根据 JSON Schema 生成示例 JSON"""
        properties = schema.get("properties", {})
        example = {}

        for key, prop in properties.items():
            if prop.get("type") == "string":
                if "enum" in prop:
                    example[key] = prop["enum"][0]
                else:
                    example[key] = prop.get("default", "example_value")
            elif prop.get("type") == "number":
                example[key] = prop.get("default", 0.85)

        import json
        return json.dumps(example, indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        """导出为字典（用于版本控制）"""
        return {
            "question_id": self.question_id,
            "version": self.version,
            "last_modified": self.last_modified,
            "purpose": {
                "task": self.purpose.task,
                "context": self.purpose.context,
                "why_important": self.purpose.why_important
            },
            "role": {
                "role": self.role.role,
                "expertise": self.role.expertise,
                "constraints": self.role.constraints
            },
            "observation": {
                "visual_method": self.observation.visual_method,
                "visual_clues": self.observation.visual_clues,
                "focus_areas": self.observation.focus_areas
            },
            "options": {
                "choices": [{"label": c.label, "description": c.description} for c in self.options.choices],
                "allow_unknown": self.options.allow_unknown,
                "allow_uncertain": self.options.allow_uncertain
            },
            "format": {
                "response_schema": self.format_spec.response_schema.__name__,
                "num_examples": len(self.format_spec.examples) if self.format_spec.examples else 0,
                "constraints": self.format_spec.constraints
            }
        }
```

---

### 4.2 使用示例：Q0.2 花卉种属识别

```python
# infrastructure/llm/prompts/q0_2_genus.py
from .framework import *
from ..response_schema import Q02Response

# 定义提示词参数
q0_2_prompt = PROOFPrompt(
    question_id="Q0.2",

    # P - Purpose
    purpose=PromptPurpose(
        task="Identify the genus (属) of this flower",
        context="The image contains an ornamental flower (confirmed by Q0.1)",
        why_important="This helps narrow down candidate diseases in the knowledge base"
    ),

    # R - Role
    role=PromptRole(
        role="plant disease diagnosis assistant",
        expertise=["plant taxonomy", "visual morphology analysis"],
        constraints=["Only diagnose ornamental flowers listed in the knowledge base"]
    ),

    # O - Observation
    observation=PromptObservation(
        visual_method="Compound Feature Description (方法论v5.0)",
        visual_clues={
            "Rosa": "Compound leaves with 5-7 leaflets, thorny stems, layered petals",
            "Prunus": "Simple oval leaves with serrated edges, 5-petal flowers, smooth bark",
            "Tulipa": "Long narrow leaves, cup-shaped flowers, smooth stem",
            "Dianthus": "Narrow linear leaves, fringed petal edges, swollen stem nodes",
            "Paeonia": "Large compound leaves, large multi-layered flowers, thick stems"
        },
        focus_areas=["leaf shape", "stem texture", "petal arrangement"]
    ),

    # O - Options
    options=PromptOptions(
        choices=[
            Choice("Rosa", "玫瑰/月季属"),
            Choice("Prunus", "樱花/樱桃属"),
            Choice("Tulipa", "郁金香属"),
            Choice("Dianthus", "康乃馨属"),
            Choice("Paeonia", "牡丹属")
        ],
        allow_unknown=True,
        allow_uncertain=False
    ),

    # F - Format
    format_spec=PromptFormat(
        response_schema=Q02Response,
        examples=[
            Example(
                input="Image shows a flower with compound leaves (5 leaflets), thorns on stem, pink layered petals",
                output=Q02Response(
                    choice="Rosa",
                    confidence=0.92,
                    reasoning="Compound leaves with 5 leaflets and thorny stems are典型特征 of Rosa genus"
                )
            )
        ],
        constraints=[
            "Only return JSON, no additional text",
            "Confidence must be between 0.0 and 1.0"
        ]
    ),

    version="v1.0"
)

# 渲染成字符串
Q0_2_GENUS_PROMPT = q0_2_prompt.render()

# 导出为字典（用于版本控制）
Q0_2_GENUS_CONFIG = q0_2_prompt.to_dict()
```

---

### 4.3 A/B 测试：只改变某个维度

```python
# 测试1: 改变 Few-shot 示例
q0_2_variant_a = PROOFPrompt(
    question_id="Q0.2",
    purpose=q0_2_prompt.purpose,
    role=q0_2_prompt.role,
    observation=q0_2_prompt.observation,
    options=q0_2_prompt.options,
    format_spec=PromptFormat(
        response_schema=Q02Response,
        examples=[  # 替换为新的示例
            Example(
                input="Image shows simple oval leaves with serrated edges, and 5-petal pink flowers",
                output=Q02Response(
                    choice="Prunus",
                    confidence=0.88,
                    reasoning="Simple oval leaves with serrated edges are典型特征 of Prunus genus"
                )
            )
        ],
        constraints=q0_2_prompt.format_spec.constraints
    ),
    version="v1.1_variant_a"
)

# 测试2: 改变视觉化方法
q0_2_variant_b = PROOFPrompt(
    question_id="Q0.2",
    purpose=q0_2_prompt.purpose,
    role=q0_2_prompt.role,
    observation=PromptObservation(
        visual_method="3-Zone Comparison (新方法)",  # 替换为新方法
        visual_clues=q0_2_prompt.observation.visual_clues,
        focus_areas=q0_2_prompt.observation.focus_areas
    ),
    options=q0_2_prompt.options,
    format_spec=q0_2_prompt.format_spec,
    version="v1.1_variant_b"
)

# A/B 测试
async def ab_test():
    test_images = load_test_images()

    accuracy_original = await test_prompts(test_images, q0_2_prompt.render())
    accuracy_variant_a = await test_prompts(test_images, q0_2_variant_a.render())
    accuracy_variant_b = await test_prompts(test_images, q0_2_variant_b.render())

    print(f"Original: {accuracy_original}")
    print(f"Variant A (new example): {accuracy_variant_a}")
    print(f"Variant B (new visual method): {accuracy_variant_b}")
```

---

## 5. 版本控制策略

### 5.1 提示词配置文件

每个提示词导出为 JSON 配置文件，纳入 Git 版本控制：

```json
// infrastructure/llm/prompts/configs/q0_2_genus_v1.0.json
{
  "question_id": "Q0.2",
  "version": "v1.0",
  "last_modified": "2025-11-11T10:30:00",
  "purpose": {
    "task": "Identify the genus (属) of this flower",
    "context": "The image contains an ornamental flower"
  },
  "role": {
    "role": "plant disease diagnosis assistant",
    "expertise": ["plant taxonomy", "visual morphology analysis"]
  },
  "observation": {
    "visual_method": "Compound Feature Description",
    "visual_clues": {
      "Rosa": "Compound leaves with 5-7 leaflets, thorny stems",
      "Prunus": "Simple oval leaves with serrated edges"
    }
  },
  "options": {
    "choices": [
      {"label": "Rosa", "description": "玫瑰/月季属"},
      {"label": "Prunus", "description": "樱花/樱桃属"}
    ],
    "allow_unknown": true
  },
  "format": {
    "response_schema": "Q02Response",
    "num_examples": 1,
    "constraints": ["Only return JSON"]
  }
}
```

### 5.2 CHANGELOG.md

记录每次参数变更：

```markdown
# Prompt Engineering CHANGELOG

## Q0.2 花卉种属识别

### v1.1 (2025-11-15)
- **改动**: 更新 Few-shot 示例（从 Rosa 改为 Prunus）
- **原因**: 测试发现 VLM 对 Prunus 的识别准确率较低
- **A/B 测试结果**: 准确率从 82% 提升到 88%
- **审批人**: @expert_botanist

### v1.0 (2025-11-11)
- 初始版本
- 采用 Compound Feature Description 视觉化方法
```

---

## 6. 与 LangChain PromptTemplate 的对比

| 维度 | LangChain PromptTemplate | PROOF Framework |
|------|-------------------------|-----------------|
| **变量替换** | ✅ 支持 Jinja2 模板 | ❌ 不需要（提示词是静态的） |
| **结构化** | ❌ 自由文本，无强制结构 | ✅ 强制 5 大组件 |
| **领域特定** | ❌ 通用框架 | ✅ 融入方法论 v5.0 |
| **版本控制** | ❌ 无标准方案 | ✅ JSON 配置 + CHANGELOG |
| **A/B 测试** | ❌ 需要手工管理 | ✅ 参数化，易于生成变体 |
| **Pydantic 集成** | ✅ 支持 | ✅ 原生支持 |
| **依赖** | 需要整个 LangChain | 零依赖（纯 Python） |

**结论**：PROOF Framework 更适合 PhytoOracle 的需求。

---

## 7. 实施计划

### 7.1 短期（v1.0）

- [ ] 实现 PROOF Framework 基类（`framework.py`）
- [ ] 将现有 Q0.0 - Q0.5 提示词迁移到 PROOF 框架
- [ ] 导出配置文件到 `infrastructure/llm/prompts/configs/`
- [ ] 建立 CHANGELOG.md

### 7.2 中期（v1.5）

- [ ] 将 Q1-Q6 提示词迁移到 PROOF 框架
- [ ] 实现 A/B 测试脚本（`ab_test.py`）
- [ ] 建立提示词审批流程（需要专家签字）

### 7.3 长期（v2.0）

- [ ] 实现提示词可视化编辑器（Web UI）
- [ ] 自动化 A/B 测试（CI/CD 集成）
- [ ] 提示词推荐系统（根据历史准确率推荐最佳参数组合）

---

## 8. 总结

### 核心价值

✅ **规范化**：所有提示词遵循 PROOF 框架（Purpose, Role, Observation, Options, Format）
✅ **参数化**：可以单独修改某个维度（如 Few-shot 示例、视觉化方法）
✅ **版本控制**：配置文件 + CHANGELOG，便于追溯和回滚
✅ **A/B 测试友好**：轻松生成变体，对比准确率
✅ **领域特定**：融入方法论 v5.0 的视觉化方法

### 与行业框架的关系

- **借鉴** CO-STAR、RISEN 等经典框架的思想
- **定制** 针对 VLM 视觉诊断任务的特点
- **超越** 提供代码实现 + 版本控制 + A/B 测试

---

**文档版本**：v1.0
**最后更新**：2025-11-11
**作者**：PhytoOracle 技术团队
