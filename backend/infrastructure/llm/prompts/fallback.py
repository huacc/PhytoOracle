"""
VLM 兜底策略提示词

功能：
- 当知识库匹配失败时（所有候选疾病 score < 0.6），触发 VLM 开放式诊断
- 使用 PROOF Framework 构建开放式诊断提示词
- 返回 VLM 的疾病推测和防治建议

实现阶段：P3.4

作者：AI Python Architect
日期：2025-11-13
"""

# VLM 兜底诊断提示词（开放式）
VLM_FALLBACK_DIAGNOSIS_PROMPT = """
# Plant Disease Diagnosis - Open-ended Fallback Mode

## Context
The knowledge base does not contain a matching disease for this plant image.
You are the LAST RESORT diagnostic expert, using your general knowledge of plant pathology.

## Your Task
Based on the image, provide your best diagnosis and recommendations.

## Analysis Framework

### Step 1: Visual Observation
Carefully examine the image and describe:
- **Symptom Type**: What kind of abnormality do you see? (spots, coating, wilting, deformation, etc.)
- **Color Pattern**: What colors are present in the symptoms?
- **Distribution**: How are symptoms distributed on the plant organ?
- **Severity**: How severe is the infection?

### Step 2: Disease Inference
Based on your observations, infer:
- **Most Likely Disease Category**: (fungal/bacterial/viral/pest/environmental)
- **Possible Disease Names**: List 1-3 most likely diseases (if you can identify)
- **Pathogen Type**: What kind of pathogen might cause this?
- **Confidence Level**: How confident are you? (high/medium/low)

### Step 3: Treatment Recommendations
Provide practical advice:
- **Immediate Actions**: What should the user do right away?
- **Treatment Options**: Suggest 2-3 treatment methods (chemical/organic/cultural)
- **Prevention**: How to prevent recurrence?
- **Professional Help**: When should they consult an expert?

## Output Format
Respond in the following structure (in Chinese):

**疾病推测**：[Most likely disease name, or "未知疾病（需专业鉴定）"]

**症状分析**：
- 症状类型：[symptom description]
- 颜色特征：[color pattern]
- 分布情况：[distribution]
- 严重程度：[severity level]

**可能病因**：
1. [Most likely disease/pathogen]
2. [Second likely disease/pathogen]
3. [Third likely disease/pathogen]

**置信度**：[high/medium/low] - [Explain why]

**处理建议**：
1. **立即行动**：[immediate steps]
2. **治疗方案**：[treatment options]
3. **预防措施**：[prevention advice]

**注意事项**：
- [Important warnings or considerations]
- 建议咨询专业植物病理学家以获得准确诊断

## Important Notes
- Be honest about uncertainty - if you're not sure, say so
- Prioritize safety - avoid recommending harmful chemicals without proper knowledge
- Focus on practical, actionable advice
- Remember: You are a fallback, not a replacement for expert diagnosis
"""


# VLM 兜底响应 Schema
from pydantic import BaseModel, Field
from typing import Optional, List


class VLMFallbackResponse(BaseModel):
    """
    VLM 兜底诊断响应模型

    字段说明：
    - disease_guess: 疾病推测（如果能识别）
    - symptom_analysis: 症状分析
    - possible_causes: 可能病因列表（1-3个）
    - confidence: 置信度（high/medium/low）
    - treatment_suggestions: 处理建议
    - warnings: 注意事项

    使用示例：
    ```python
    response = VLMFallbackResponse(
        disease_guess="可能是细菌性叶斑病",
        symptom_analysis="叶片出现深褐色坏死斑点，边缘有黄色晕圈",
        possible_causes=["Pseudomonas syringae (细菌)", "Xanthomonas (细菌)", "真菌性叶斑病"],
        confidence="medium",
        treatment_suggestions="1. 移除病叶；2. 使用铜制剂喷雾；3. 改善通风",
        warnings="建议咨询专业植物病理学家以获得准确诊断"
    )
    ```
    """
    disease_guess: str = Field(..., description="疾病推测")
    symptom_analysis: str = Field(..., description="症状分析")
    possible_causes: List[str] = Field(..., description="可能病因列表（1-3个）")
    confidence: str = Field(..., description="置信度（high/medium/low）")
    treatment_suggestions: str = Field(..., description="处理建议")
    warnings: Optional[str] = Field(default="建议咨询专业植物病理学家", description="注意事项")


def main():
    """
    VLM 兜底策略提示词测试

    验证：
    1. 提示词内容完整
    2. 响应模型可用
    """
    print("=" * 80)
    print("VLM 兜底策略提示词测试")
    print("=" * 80)

    # 1. 显示提示词内容
    print("\n[测试1] VLM 兜底诊断提示词内容")
    print(f"  提示词长度: {len(VLM_FALLBACK_DIAGNOSIS_PROMPT)} 字符")
    print(f"\n--- 提示词内容（前500字符） ---")
    print(VLM_FALLBACK_DIAGNOSIS_PROMPT[:500])
    print("...\n")

    # 2. 验证响应模型
    print("\n[测试2] VLM 兜底响应模型")
    try:
        # 创建测试响应
        test_response = VLMFallbackResponse(
            disease_guess="可能是细菌性叶斑病",
            symptom_analysis="叶片出现深褐色坏死斑点，边缘有黄色晕圈，散发分布",
            possible_causes=[
                "Pseudomonas syringae (丁香假单胞菌)",
                "Xanthomonas (黄单胞菌属)",
                "真菌性叶斑病"
            ],
            confidence="medium",
            treatment_suggestions=(
                "1. 立即移除病叶并销毁；"
                "2. 使用铜制剂（如波尔多液）喷雾防治；"
                "3. 改善通风，减少叶面湿度"
            ),
            warnings="建议咨询专业植物病理学家以获得准确诊断"
        )

        print("  [OK] 响应模型创建成功")
        print(f"    - 疾病推测: {test_response.disease_guess}")
        print(f"    - 可能病因数: {len(test_response.possible_causes)}")
        print(f"    - 置信度: {test_response.confidence}")

        # 验证 JSON 序列化
        json_data = test_response.model_dump_json(indent=2)
        print(f"\n  [OK] JSON 序列化成功 ({len(json_data)} 字符)")

    except Exception as e:
        print(f"  [FAIL] 响应模型测试失败: {e}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
