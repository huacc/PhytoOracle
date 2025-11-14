"""
PROOF Framework - 提示词工程框架

功能：
- 提供 PROOF 框架（Purpose + Role + Observation + Options + Format）
- 结构化提示词编写，确保统一的5大组件
- 支持参数化和 A/B 测试
- 导出 JSON 配置，便于版本控制
- 融入方法论 v5.0 视觉化方法

PROOF 五要素：
- Purpose (P): 任务目的，明确告诉模型要完成什么任务
- Role (R): 角色设定，让模型扮演特定专家角色
- Observation (O): 观察指导，引导模型关注图像的关键区域
- Options (O): 可选输出，限制模型的输出范围
- Format (F): 输出格式，指定返回的数据结构

作者：AI Python Architect
日期：2025-11-12
"""

from pathlib import Path
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


@dataclass
class PromptPurpose:
    """
    提示词目的（Purpose）

    定义任务的核心目标、前置条件和重要性说明

    字段说明：
    - task: 任务描述（一句话，明确具体）
    - context: 前置条件（可选，说明任务的上下文）
    - why_important: 为什么重要（可选，强调任务的意义）

    使用示例：
    ```python
    purpose = PromptPurpose(
        task="Identify the genus (属) of this flower",
        context="The image contains an ornamental flower (confirmed by Q0.1)",
        why_important="Accurate genus identification is critical for disease diagnosis"
    )
    ```
    """
    task: str  # 任务描述
    context: Optional[str] = None  # 前置条件
    why_important: Optional[str] = None  # 为什么重要


@dataclass
class PromptRole:
    """
    提示词角色（Role）

    定义模型扮演的角色、专业知识领域和角色限制

    字段说明：
    - role: 角色名称（如："plant disease diagnosis assistant"）
    - expertise: 专业知识领域列表（如：["plant taxonomy", "visual morphology"]）
    - constraints: 角色限制（可选，如：["no medical advice for humans"]）

    使用示例：
    ```python
    role = PromptRole(
        role="plant disease diagnosis assistant",
        expertise=["plant taxonomy", "visual morphology analysis", "disease symptomology"],
        constraints=["focus only on ornamental flowers", "avoid making treatment recommendations"]
    )
    ```
    """
    role: str  # 角色名称
    expertise: List[str]  # 专业知识领域
    constraints: Optional[List[str]] = None  # 角色限制


@dataclass
class PromptObservation:
    """
    观察指导（Observation）

    引导模型关注图像的关键区域和视觉线索
    融入方法论 v5.0 的视觉化方法（如：Egg Yolk Metaphor, Compound Feature Description）

    字段说明：
    - visual_method: 视觉化方法名称（可选，如："Egg Yolk Metaphor"）
    - visual_clues: 视觉线索字典（可选，键为选项标签，值为视觉描述）
    - focus_areas: 重点关注区域（可选，如：["leaf shape", "stem texture"]）

    使用示例：
    ```python
    observation = PromptObservation(
        visual_method="Compound Feature Description (方法论v5.0)",
        visual_clues={
            "Rosa": "Compound leaves with 5-7 leaflets, thorny stems, layered petals",
            "Prunus": "Simple oval leaves with serrated edges, 5-petal flowers",
        },
        focus_areas=["leaf shape", "stem texture", "petal arrangement"]
    )
    ```
    """
    visual_method: Optional[str] = None  # 视觉化方法名称
    visual_clues: Optional[Dict[str, str]] = None  # 视觉线索字典
    focus_areas: Optional[List[str]] = None  # 重点关注区域


@dataclass
class Choice:
    """
    选项定义

    定义单个选项的标签和描述

    字段说明：
    - label: 选项标签（如："Rosa"）
    - description: 选项描述（如："玫瑰/月季属"）

    使用示例：
    ```python
    choice = Choice("Rosa", "玫瑰/月季属")
    ```
    """
    label: str  # 选项标签
    description: str  # 选项描述


@dataclass
class PromptOptions:
    """
    提示词选项（Options）

    限制模型的输出范围，提供可选的答案列表

    字段说明：
    - choices: 选项列表（List[Choice]）
    - allow_unknown: 是否允许 "unknown" 选项（默认True）
    - allow_uncertain: 是否允许 "unclear" 选项（默认False）

    使用示例：
    ```python
    options = PromptOptions(
        choices=[
            Choice("Rosa", "玫瑰/月季属"),
            Choice("Prunus", "樱花/樱桃属"),
        ],
        allow_unknown=True,
        allow_uncertain=False
    )
    ```
    """
    choices: List[Choice]  # 选项列表
    allow_unknown: bool = True  # 是否允许 "unknown"
    allow_uncertain: bool = False  # 是否允许 "unclear"


@dataclass
class Example:
    """
    Few-shot 示例

    提供输入-输出示例，帮助模型理解任务

    字段说明：
    - input: 输入描述（字符串）
    - output: 输出示例（Pydantic 对象）

    使用示例：
    ```python
    example = Example(
        input="Image shows a flower with compound leaves (5 leaflets), thorns",
        output=Q02Response(choice="Rosa", confidence=0.92, reasoning="...")
    )
    ```
    """
    input: str  # 输入描述
    output: BaseModel  # 输出（Pydantic 对象）


@dataclass
class PromptFormat:
    """
    输出格式（Format）

    定义输出的数据结构和约束条件

    字段说明：
    - response_schema: Pydantic 响应模型类（如：Q02Response）
    - examples: Few-shot 示例列表（可选）
    - constraints: 输出约束列表（可选，如：["Only return JSON", "No additional text"]）

    使用示例：
    ```python
    format_spec = PromptFormat(
        response_schema=Q02Response,
        examples=[...],
        constraints=["Only return valid JSON", "No explanations"]
    )
    ```
    """
    response_schema: Type[BaseModel]  # Pydantic 响应模型类
    examples: Optional[List[Example]] = None  # Few-shot 示例
    constraints: Optional[List[str]] = None  # 输出约束


class PROOFPrompt:
    """
    PROOF 框架提示词

    将 PROOF 五要素组合成完整的提示词，支持渲染、导出和版本管理

    字段说明：
    - question_id: 问题ID（如："Q0.2"）
    - purpose: 提示词目的（PromptPurpose）
    - role: 提示词角色（PromptRole）
    - observation: 观察指导（PromptObservation）
    - options: 提示词选项（PromptOptions）
    - format_spec: 输出格式（PromptFormat）
    - version: 提示词版本号（默认："v1.0"）

    使用示例：
    ```python
    prompt = PROOFPrompt(
        question_id="Q0.2",
        purpose=PromptPurpose(...),
        role=PromptRole(...),
        observation=PromptObservation(...),
        options=PromptOptions(...),
        format_spec=PromptFormat(...),
        version="v1.0"
    )

    # 渲染成完整的提示词字符串
    prompt_text = prompt.render()

    # 导出为字典（用于版本控制）
    config_dict = prompt.to_dict()
    ```
    """

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
        """
        初始化 PROOF 提示词

        Args:
            question_id: 问题ID（如："Q0.2"）
            purpose: 提示词目的
            role: 提示词角色
            observation: 观察指导
            options: 提示词选项
            format_spec: 输出格式
            version: 提示词版本号（默认："v1.0"）
        """
        self.question_id = question_id
        self.purpose = purpose
        self.role = role
        self.observation = observation
        self.options = options
        self.format_spec = format_spec
        self.version = version
        self.last_modified = datetime.now().isoformat()

    def render(self) -> str:
        """
        渲染成最终的提示词字符串

        流程：
        1. 渲染 Role 部分
        2. 渲染 Purpose 部分
        3. 渲染 Observation 部分（如果有）
        4. 渲染 Options 部分
        5. 渲染 Format 部分（Few-shot 示例 + 响应格式）
        6. 渲染 Constraints
        7. 返回完整提示词字符串

        Returns:
            str: 完整的提示词字符串

        使用示例：
        ```python
        prompt_text = prompt.render()
        print(prompt_text)
        ```
        """
        sections = []

        # 1. Role - 角色设定
        sections.append(f"You are a {self.role.role}.")
        if self.role.expertise:
            sections.append(f"Your expertise: {', '.join(self.role.expertise)}.")
        if self.role.constraints:
            sections.append(f"Constraints: {'; '.join(self.role.constraints)}.")
        sections.append("")

        # 2. Purpose - 任务目的
        sections.append(f"TASK: {self.purpose.task}")
        if self.purpose.context:
            sections.append(f"CONTEXT: {self.purpose.context}")
        if self.purpose.why_important:
            sections.append(f"WHY IMPORTANT: {self.purpose.why_important}")
        sections.append("")

        # 3. Observation - 观察指导（如果有）
        if self.observation.visual_method:
            sections.append(f"VISUAL METHOD: {self.observation.visual_method}")
            sections.append("")

        if self.observation.visual_clues:
            sections.append("VISUAL CLUES (识别线索):")
            for key, value in self.observation.visual_clues.items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

        if self.observation.focus_areas:
            sections.append(f"FOCUS AREAS: {', '.join(self.observation.focus_areas)}")
            sections.append("")

        # 4. Options - 可选输出
        sections.append("AVAILABLE CHOICES:")
        for choice in self.options.choices:
            sections.append(f"  - {choice.label}: {choice.description}")

        if self.options.allow_unknown:
            sections.append("  - unknown: 如果不在以上列表中或无法识别")
        if self.options.allow_uncertain:
            sections.append("  - unclear: 如果图像模糊或信息不足")
        sections.append("")

        # 5. Format - Few-shot 示例（如果有）
        if self.format_spec.examples:
            sections.append("FEW-SHOT EXAMPLES:")
            for idx, example in enumerate(self.format_spec.examples, 1):
                sections.append(f"\n  Example {idx}:")
                sections.append(f"  Input: {example.input}")
                sections.append(f"  Output: {example.output.model_dump_json(indent=4)}")
            sections.append("")

        # 6. Format - 响应格式
        sections.append("RESPONSE FORMAT (JSON only, no markdown code blocks):")
        sections.append(self._generate_example_json())
        sections.append("")

        # 7. Constraints - 输出约束
        sections.append("IMPORTANT CONSTRAINTS:")
        sections.append("  - Only return valid JSON (no markdown code blocks like ```json)")
        sections.append("  - No additional explanations or text outside JSON")
        sections.append("  - Ensure all required fields are present")
        if self.format_spec.constraints:
            for constraint in self.format_spec.constraints:
                sections.append(f"  - {constraint}")

        return "\n".join(sections)

    def _generate_example_json(self) -> str:
        """
        根据 response_schema 生成示例 JSON

        Returns:
            str: 示例 JSON 字符串（格式化后）
        """
        schema = self.format_spec.response_schema.model_json_schema()
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])
        example = {}

        # 遍历所有属性，生成示例值
        for key, prop in properties.items():
            prop_type = prop.get("type")

            if prop_type == "string":
                # 检查是否有枚举值
                if "enum" in prop:
                    example[key] = prop["enum"][0]  # 使用第一个枚举值
                else:
                    example[key] = "example_value"
            elif prop_type == "number":
                example[key] = 0.85
            elif prop_type == "integer":
                example[key] = 1
            elif prop_type == "boolean":
                example[key] = True
            elif prop_type == "array":
                example[key] = ["example1", "example2"]
            elif prop_type == "object":
                example[key] = {}

        return json.dumps(example, indent=2, ensure_ascii=False)

    def to_dict(self) -> Dict[str, Any]:
        """
        导出为字典（用于版本控制）

        Returns:
            Dict[str, Any]: 提示词配置字典

        使用示例：
        ```python
        config = prompt.to_dict()
        with open("q0_2_config.json", "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        ```
        """
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
                "choices": [
                    {"label": c.label, "description": c.description}
                    for c in self.options.choices
                ],
                "allow_unknown": self.options.allow_unknown,
                "allow_uncertain": self.options.allow_uncertain
            },
            "format": {
                "response_schema": self.format_spec.response_schema.__name__,
                "constraints": self.format_spec.constraints
            }
        }

    def save_config(self, output_path: Optional[Path] = None) -> Path:
        """
        保存配置到JSON文件

        Args:
            output_path: 输出路径（可选）。如果不指定，则保存到当前目录下的 configs/ 子目录

        Returns:
            Path: 保存的文件路径

        使用示例：
        ```python
        config_path = prompt.save_config()
        print(f"配置已保存到: {config_path}")
        ```
        """
        if output_path is None:
            # 默认保存到 configs/ 子目录
            config_dir = Path(__file__).parent / "configs"
            config_dir.mkdir(exist_ok=True)
            output_path = config_dir / f"{self.question_id.lower().replace('.', '_')}_config.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        return output_path


if __name__ == "__main__":
    """
    PROOFPrompt 使用示例

    演示如何：
    1. 创建 PROOF 提示词（以 Q0.2 为例）
    2. 渲染成完整的提示词字符串
    3. 导出为字典
    4. 保存为 JSON 配置文件
    """
    from pydantic import BaseModel, Field
    from typing import Literal

    print("=" * 80)
    print("PROOF Framework 使用示例")
    print("=" * 80)

    # 定义一个简单的响应模型（用于演示）
    class Q02Response(BaseModel):
        """Q0.2 花卉种属识别响应"""
        choice: Literal["Rosa", "Prunus", "Tulipa", "Dianthus", "Paeonia", "unknown"]
        confidence: float = Field(..., ge=0.0, le=1.0)
        reasoning: str = Field(default="", description="推理过程")

    # 1. 创建 PROOF 提示词（Q0.2 花卉种属识别）
    print("\n[示例1] 创建 PROOF 提示词（Q0.2 花卉种属识别）")

    q0_2_prompt = PROOFPrompt(
        question_id="Q0.2",

        # P - Purpose
        purpose=PromptPurpose(
            task="Identify the genus (属) of this flower",
            context="The image contains an ornamental flower (confirmed by Q0.1)",
            why_important="Accurate genus identification is critical for subsequent disease diagnosis"
        ),

        # R - Role
        role=PromptRole(
            role="plant disease diagnosis assistant",
            expertise=["plant taxonomy", "visual morphology analysis", "flower identification"],
            constraints=["focus only on ornamental flowers", "avoid wild plant identification"]
        ),

        # O - Observation
        observation=PromptObservation(
            visual_method="Compound Feature Description (方法论v5.0)",
            visual_clues={
                "Rosa": "Compound leaves with 5-7 leaflets, thorny stems, layered petals",
                "Prunus": "Simple oval leaves with serrated edges, 5-petal flowers, smooth bark",
                "Tulipa": "Long narrow leaves, cup-shaped flowers, smooth stem without branches",
                "Dianthus": "Narrow linear leaves, fringed petal edges, swollen stem nodes",
                "Paeonia": "Large compound leaves, large multi-layered flowers, thick stems"
            },
            focus_areas=["leaf shape and arrangement", "stem texture and thorns", "petal arrangement"]
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
                        reasoning="Compound leaves with 5 leaflets and thorny stems are typical features of Rosa genus"
                    )
                )
            ],
            constraints=["confidence must reflect actual certainty", "reasoning should be brief"]
        ),

        version="v1.0"
    )

    print(f"  [OK] 成功创建提示词: {q0_2_prompt.question_id}")
    print(f"  - 版本: {q0_2_prompt.version}")
    print(f"  - 任务: {q0_2_prompt.purpose.task}")
    print(f"  - 角色: {q0_2_prompt.role.role}")
    print(f"  - 选项数量: {len(q0_2_prompt.options.choices)}")

    # 2. 渲染成完整的提示词字符串
    print("\n[示例2] 渲染成完整的提示词字符串")
    rendered_prompt = q0_2_prompt.render()
    print(f"  渲染后的提示词长度: {len(rendered_prompt)} 字符")
    print(f"\n  --- 提示词内容（前500字符） ---")
    print(f"  {rendered_prompt[:500]}...")
    print(f"  --- （完整内容已省略） ---")

    # 3. 导出为字典
    print("\n[示例3] 导出为字典")
    config_dict = q0_2_prompt.to_dict()
    print(f"  配置字典键: {list(config_dict.keys())}")
    print(f"  - 问题ID: {config_dict['question_id']}")
    print(f"  - 版本: {config_dict['version']}")
    print(f"  - 最后修改: {config_dict['last_modified']}")

    # 4. 保存为 JSON 配置文件
    print("\n[示例4] 保存为 JSON 配置文件")
    try:
        config_path = q0_2_prompt.save_config()
        print(f"  [OK] 配置已保存到: {config_path}")

        # 验证文件内容
        with open(config_path, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        print(f"  [OK] 文件验证成功，问题ID: {saved_config['question_id']}")
    except Exception as e:
        print(f"  [FAIL] 保存失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)
