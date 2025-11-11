# 结构化输出框架对比分析

> 本文档对比主流的结构化输出框架（Outlines, Instructor, LangChain, 自研方案），帮助 PhytoOracle 选择最佳方案。

---

## 1. 问题定义：两个层次的"规范性"

### 层次1：提示词规范性（编写阶段）

**问题**：如何结构化地**编写**提示词？

**目标**：
- 所有提示词遵循统一结构（如 Purpose, Role, Observation, Options, Format）
- 便于版本控制和 A/B 测试
- 团队协作友好

**示例**：
```python
# 不规范的写法
prompt = "Identify the flower genus. Return JSON."

# 规范的写法（结构化）
prompt = PROOFPrompt(
    purpose=PromptPurpose(task="Identify the genus of this flower"),
    role=PromptRole(role="plant disease diagnosis assistant"),
    observation=PromptObservation(...),
    options=PromptOptions(...),
    format_spec=PromptFormat(...)
)
```

---

### 层次2：输出规范性（运行时）

**问题**：如何确保 VLM **返回**的数据符合预期格式？

**目标**：
- 100% 输出符合 JSON Schema 或 Pydantic 模型
- 减少解析错误和重试次数
- 自动验证和错误处理

**示例**：
```python
# 不规范的输出（VLM 可能返回）
"I think it's Rosa. Confidence: high"

# 规范的输出（期望）
{"choice": "Rosa", "confidence": 0.92, "reasoning": "..."}
```

---

## 2. 候选框架对比

### 2.1 Outlines (dottxt-ai)

**官网**：https://github.com/dottxt-ai/outlines

#### 核心特性

| 特性 | 说明 |
|------|------|
| **约束采样** | 在 token 生成阶段强制符合 JSON Schema |
| **100% 格式保证** | 通过 CFG/正则表达式约束，确保输出有效 |
| **Pydantic 支持** | 直接从 Pydantic 模型推断结构 |
| **性能优势** | 微秒级开销（vs 秒级重试） |
| **开源模型优先** | 主要用于 vLLM, TGI, Transformers |

#### 代码示例

```python
import outlines

model = outlines.models.transformers("qwen/Qwen-VL-Plus")

# 方法1: 使用 Pydantic 模型
from pydantic import BaseModel

class Q02Response(BaseModel):
    choice: str
    confidence: float

generator = outlines.generate.json(model, Q02Response)
response = generator(prompt, image)  # 100% 符合 Q02Response 格式

# 方法2: 使用 JSON Schema
schema = """{
    "type": "object",
    "properties": {
        "choice": {"type": "string"},
        "confidence": {"type": "number"}
    }
}"""
generator = outlines.generate.json(model, schema)
```

#### 适用性分析

| 维度 | PhytoOracle 需求 | Outlines 匹配度 | 说明 |
|------|-----------------|----------------|------|
| **提示词规范性** | ✅ 需要 | ❌ 不提供 | Outlines 不管提示词怎么写 |
| **输出规范性** | ✅ 需要 | ✅ 完美匹配 | 100% 格式保证 |
| **VLM 支持** | ✅ Qwen/ChatGPT/Claude | 🟡 部分支持 | 主要支持开源模型，闭源 API 需要集成 |
| **多提供商** | ✅ Fallback 机制 | ❌ 不支持 | 每个 Provider 需要单独配置 |
| **性能** | ✅ 需要快速响应 | ✅ 微秒级 | 比重试快得多 |
| **学习成本** | 🟡 希望较低 | 🟡 中等 | 需要理解约束采样原理 |

#### 优势

✅ **100% 格式保证**：不需要重试和异常处理
✅ **性能优秀**：约束采样只增加微秒级开销
✅ **Pydantic 原生支持**：直接用 PhytoOracle 的响应模型

#### 劣势

❌ **不解决提示词规范性**：只管输出，不管输入
❌ **闭源 API 集成复杂**：OpenAI/Anthropic 需要自己包装
❌ **不支持 Fallback**：无法直接实现 Qwen → ChatGPT → Claude 降级

---

### 2.2 Instructor (jxnl)

**官网**：https://github.com/jxnl/instructor

#### 核心特性

| 特性 | 说明 |
|------|------|
| **API 包装** | 简化 OpenAI/Anthropic/Qwen API 调用 |
| **Pydantic 验证** | 自动验证输出并重试 |
| **多提供商** | 支持 15+ 提供商 |
| **自动重试** | 验证失败时自动重试（最多3次） |
| **流式输出** | 支持流式 Pydantic 对象 |

#### 代码示例

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel

class Q02Response(BaseModel):
    choice: str
    confidence: float
    reasoning: str

# 包装 OpenAI 客户端
client = instructor.from_openai(OpenAI())

# 直接获取 Pydantic 对象
response = client.chat.completions.create(
    model="gpt-4o",
    response_model=Q02Response,  # 指定响应模型
    messages=[
        {"role": "system", "content": "You are a JSON API"},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": image_base64},
            {"type": "text", "text": prompt}
        ]}
    ]
)
# response 已经是 Q02Response 对象，无需解析
print(response.choice)  # "Rosa"
```

#### 适用性分析

| 维度 | PhytoOracle 需求 | Instructor 匹配度 | 说明 |
|------|-----------------|------------------|------|
| **提示词规范性** | ✅ 需要 | ❌ 不提供 | 只是 API 包装器 |
| **输出规范性** | ✅ 需要 | ✅ 很好 | 自动验证 + 重试 |
| **VLM 支持** | ✅ Qwen/ChatGPT/Claude | ✅ 完美支持 | 15+ 提供商 |
| **多提供商** | ✅ Fallback 机制 | 🟡 需要自己写 | 不提供内置 Fallback |
| **性能** | ✅ 需要快速响应 | 🟡 中等 | 重试会增加延迟 |
| **学习成本** | 🟡 希望较低 | ✅ 很低 | API 非常简单 |

#### 优势

✅ **API 简洁**：一行代码就能获取 Pydantic 对象
✅ **多提供商支持**：OpenAI, Anthropic, Qwen 等都支持
✅ **自动重试**：验证失败自动重试（最多3次）
✅ **学习成本低**：文档清晰，示例丰富

#### 劣势

❌ **不解决提示词规范性**：只是 API 包装器
❌ **重试增加延迟**：失败时需要重新调用 VLM（秒级开销）
❌ **不提供 Fallback**：需要自己实现 Provider 降级

---

### 2.3 LangChain PromptTemplate

**官网**：https://python.langchain.com/docs/modules/model_io/prompts/

#### 核心特性

| 特性 | 说明 |
|------|------|
| **模板引擎** | Jinja2 风格的变量替换 |
| **提示词组合** | 可以组合多个子模板 |
| **Few-shot 支持** | 提供 FewShotPromptTemplate |
| **with_structured_output** | 支持 Pydantic 输出 |

#### 代码示例

```python
from langchain.prompts import PromptTemplate

template = PromptTemplate.from_template("""
You are a {role}.

TASK: {task}

CHOICES:
{choices}

RESPONSE FORMAT:
{format}
""")

prompt = template.format(
    role="plant disease diagnosis assistant",
    task="Identify the genus of this flower",
    choices="- Rosa\n- Prunus",
    format='{"choice": "Rosa", "confidence": 0.85}'
)
```

#### 适用性分析

| 维度 | PhytoOracle 需求 | LangChain 匹配度 | 说明 |
|------|-----------------|-----------------|------|
| **提示词规范性** | ✅ 需要 | 🟡 部分支持 | 提供模板，但不强制结构 |
| **输出规范性** | ✅ 需要 | 🟡 部分支持 | `with_structured_output` |
| **VLM 支持** | ✅ Qwen/ChatGPT/Claude | ✅ 支持 | 通过 langchain-community |
| **多提供商** | ✅ Fallback 机制 | ❌ 需要自己写 | 不提供内置 Fallback |
| **性能** | ✅ 需要快速响应 | ✅ 无额外开销 | 只是字符串替换 |
| **学习成本** | 🟡 希望较低 | 🔴 较高 | LangChain 概念复杂 |

#### 优势

✅ **成熟生态**：大量第三方集成
✅ **模板组合**：可以组合多个子模板

#### 劣势

❌ **不强制结构**：提示词仍然是自由文本
❌ **PhytoOracle 不需要动态模板**：Q0-Q6 都是静态的
❌ **依赖地狱**：70+ 依赖包
❌ **过度设计**：功能太多，不符合 YAGNI 原则

---

### 2.4 自研 PROOF Framework

**位置**：`docs/prompt_framework_design.md`

#### 核心特性

| 特性 | 说明 |
|------|------|
| **5 大组件** | Purpose, Role, Observation, Options, Format |
| **参数化** | 可以单独修改某个维度（如 Few-shot 示例） |
| **版本控制** | 导出 JSON 配置，便于 Git diff |
| **A/B 测试** | 轻松生成变体 |
| **Pydantic 验证** | 内置响应验证器 |

#### 代码示例

```python
from infrastructure.llm.prompts.framework import PROOFPrompt

q0_2_prompt = PROOFPrompt(
    question_id="Q0.2",
    purpose=PromptPurpose(task="Identify the genus of this flower"),
    role=PromptRole(role="plant disease diagnosis assistant"),
    observation=PromptObservation(
        visual_method="Egg Yolk Metaphor",
        visual_clues={"Rosa": "Compound leaves with 5-7 leaflets"}
    ),
    options=PromptOptions(choices=[Choice("Rosa", "玫瑰/月季属")]),
    format_spec=PromptFormat(response_schema=Q02Response)
)

# 渲染成字符串
prompt_text = q0_2_prompt.render()

# 导出配置（版本控制）
config = q0_2_prompt.to_dict()
```

#### 适用性分析

| 维度 | PhytoOracle 需求 | PROOF 匹配度 | 说明 |
|------|-----------------|-------------|------|
| **提示词规范性** | ✅ 需要 | ✅ 完美匹配 | 强制 5 大组件结构 |
| **输出规范性** | ✅ 需要 | 🟡 需要配合 | 提供 ResponseValidator |
| **VLM 支持** | ✅ Qwen/ChatGPT/Claude | ✅ 支持 | 与 VLMClient 集成 |
| **多提供商** | ✅ Fallback 机制 | ✅ 支持 | 已有 VLMClient |
| **性能** | ✅ 需要快速响应 | ✅ 零开销 | 只是字符串拼接 |
| **学习成本** | 🟡 希望较低 | ✅ 很低 | 符合 PhytoOracle DDD 架构 |

#### 优势

✅ **专为 PhytoOracle 设计**：融入方法论 v5.0
✅ **强制结构化**：必须提供 5 大组件
✅ **零依赖**：纯 Python，无外部依赖
✅ **版本控制友好**：导出 JSON，便于 Git diff
✅ **A/B 测试友好**：参数化，易于生成变体

#### 劣势

❌ **输出规范性需要配合**：需要配合 ResponseValidator 或 Instructor
❌ **需要维护**：自研代码需要团队维护

---

## 3. 推荐方案

### 3.1 最佳实践：组合使用

**推荐：PROOF Framework（提示词规范性） + Instructor（输出规范性）**

```python
# 1. 使用 PROOF Framework 结构化编写提示词
q0_2_prompt = PROOFPrompt(
    purpose=PromptPurpose(task="Identify the genus of this flower"),
    role=PromptRole(role="plant disease diagnosis assistant"),
    observation=PromptObservation(...),
    options=PromptOptions(...),
    format_spec=PromptFormat(response_schema=Q02Response)
)

# 2. 渲染成字符串
prompt_text = q0_2_prompt.render()

# 3. 使用 Instructor 确保输出格式
import instructor
from openai import OpenAI

client = instructor.from_openai(OpenAI())

response = client.chat.completions.create(
    model="gpt-4o",
    response_model=Q02Response,  # 自动验证 + 重试
    messages=[
        {"role": "system", "content": "You are a JSON API"},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": image_base64},
            {"type": "text", "text": prompt_text}
        ]}
    ]
)
# response 已经是 Q02Response 对象，100% 符合格式
```

---

### 3.2 架构设计

```python
# infrastructure/llm/client.py
import instructor
from openai import OpenAI
from anthropic import Anthropic

class VLMClient:
    """VLM客户端 - 集成 Instructor"""

    def __init__(self):
        # 包装各Provider
        self.providers = [
            instructor.from_openai(OpenAI(base_url="https://qwen-api")),  # Qwen
            instructor.from_openai(OpenAI()),                              # ChatGPT
            instructor.from_anthropic(Anthropic())                         # Claude
        ]

    async def call_with_fallback(
        self,
        prompt: str,
        image: bytes,
        response_model: Type[BaseModel]
    ) -> BaseModel:
        """带降级的VLM调用 + 自动验证"""
        for provider in self.providers:
            try:
                response = provider.chat.completions.create(
                    model="auto-detect",
                    response_model=response_model,  # Instructor 自动验证
                    messages=[
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": image},
                            {"type": "text", "text": prompt}
                        ]}
                    ]
                )
                return response  # 已经是 Pydantic 对象
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue

        raise VLMError("All providers failed")


# 使用示例
class DiagnosisService:
    async def diagnose(self, image: bytes) -> DiagnosisResult:
        # 1. 使用 PROOF Framework 生成提示词
        q0_2_prompt = Q0_2_GENUS_PROMPT  # PROOFPrompt 对象

        # 2. 调用 VLMClient（集成 Instructor）
        response = await self.vlm_client.call_with_fallback(
            prompt=q0_2_prompt.render(),
            image=image,
            response_model=Q02Response  # 100% 符合格式
        )

        # 3. 直接使用 Pydantic 对象
        flower_genus = response.choice
        confidence = response.confidence
        reasoning = response.reasoning
```

---

### 3.3 为什么不用 Outlines？

| 原因 | 说明 |
|------|------|
| **闭源 API 集成复杂** | Qwen/ChatGPT/Claude API 需要自己包装 |
| **不支持 Fallback** | 无法直接实现多 Provider 降级 |
| **开源模型优先** | PhytoOracle 主要用闭源 API（成本可控） |

**何时考虑 Outlines**：
- 如果未来切换到自部署的开源 VLM（如 vLLM 部署 Qwen-VL）
- 如果需要极致性能（微秒级 vs 秒级重试）

---

## 4. 实施路线图

### Phase 1: PROOF Framework（提示词规范性）

**目标**：所有提示词结构化

- [ ] 实现 PROOF Framework 基类（`framework.py`）
- [ ] 迁移 Q0.0 - Q0.5 到 PROOF 框架
- [ ] 导出 JSON 配置到 `configs/` 目录
- [ ] 建立 CHANGELOG.md

**时间**：1-2 天

---

### Phase 2: Instructor 集成（输出规范性）

**目标**：100% 输出符合格式

- [ ] 安装 Instructor：`pip install instructor`
- [ ] 包装现有 VLMClient 的各 Provider
- [ ] 修改 `call_with_fallback` 方法，传入 `response_model`
- [ ] 移除现有的 `ResponseValidator`（Instructor 已提供）

**时间**：1 天

---

### Phase 3: 集成测试

**目标**：验证完整流程

- [ ] 编写集成测试（Q0-Q6 完整流程）
- [ ] 对比迁移前后的准确率
- [ ] 监控重试次数和响应时间

**时间**：0.5 天

---

## 5. 依赖管理

### 新增依赖

```toml
# pyproject.toml
[tool.poetry.dependencies]
instructor = "^1.7.0"  # 唯一新增依赖（25KB，无额外依赖）

# 已有依赖
pydantic = "^2.0"
fastapi = "^0.100"
```

**依赖对比**：

| 方案 | 新增依赖 | 依赖大小 |
|------|---------|---------|
| Outlines | `outlines` + `torch` + `transformers` | ~2GB |
| Instructor | `instructor` | ~25KB |
| LangChain | `langchain` + 70+ 依赖 | ~500MB |
| PROOF Framework | 无 | 0 |

**结论**：Instructor 是最轻量的选择。

---

## 6. 总结对比表

| 维度 | Outlines | Instructor | LangChain | PROOF Framework |
|------|----------|-----------|-----------|----------------|
| **提示词规范性** | ❌ | ❌ | 🟡 | ✅ |
| **输出规范性** | ✅ | ✅ | 🟡 | 🟡 |
| **VLM 支持** | 🟡 | ✅ | ✅ | ✅ |
| **Fallback 支持** | ❌ | 🟡 | 🟡 | ✅ |
| **性能** | ✅ | 🟡 | ✅ | ✅ |
| **学习成本** | 🟡 | ✅ | 🔴 | ✅ |
| **依赖大小** | 🔴 | ✅ | 🔴 | ✅ |
| **适合 PhytoOracle** | 🟡 | ✅ | ❌ | ✅ |

---

## 7. 最终推荐

### 推荐方案

**PROOF Framework（提示词） + Instructor（输出） = 完美组合**

✅ **提示词规范性**：PROOF Framework 强制结构化
✅ **输出规范性**：Instructor 自动验证 + 重试
✅ **轻量级**：只增加 25KB 依赖
✅ **学习成本低**：符合 PhytoOracle 的 DDD 架构
✅ **性能优秀**：Instructor 重试通常在 1-2 次内成功

### 不推荐

❌ **Outlines**：适合开源模型自部署，不适合闭源 API
❌ **LangChain**：过度设计，依赖地狱

---

**文档版本**：v1.0
**最后更新**：2025-11-11
**作者**：PhytoOracle 技术团队
