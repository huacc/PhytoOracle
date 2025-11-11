#!/usr/bin/env python3
"""
PhytoOracle Mock 演示脚本
演示修复后的诊断逻辑（包含3种兜底场景）

运行方式：
pip install streamlit pillow
streamlit run demo_mock.py
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import random

# ==================== 数据模型 ====================

class ConfidenceLevel(str, Enum):
    """置信度级别（扩展版）"""
    CONFIRMED = "confirmed"
    SUSPECTED = "suspected"
    UNLIKELY = "unlikely"
    UNKNOWN = "unknown"
    VLM_FALLBACK = "vlm_fallback"
    SYSTEM_ERROR = "system_error"


# ==================== Mock 诊断逻辑 ====================

def mock_diagnose(scenario: str) -> Dict[str, Any]:
    """
    Mock 诊断函数 - 演示不同场景

    场景：
    1. confirmed: 确诊（玫瑰黑斑病）
    2. suspected: 疑似（樱花白粉病 vs 叶斑病）
    3. unknown: 知识库无数据（茉莉花未收录）
    4. vlm_fallback: VLM兜底（知识库外疾病）
    5. system_error: VLM完全失败
    """

    base_result = {
        "diagnosis_id": f"diag_{datetime.now().strftime('%Y%m%d')}_{random.randint(100, 999)}",
        "timestamp": datetime.now().isoformat(),
        "vlm_provider": "QwenVLPlus",
        "execution_time_ms": random.randint(1200, 3500)
    }

    if scenario == "confirmed":
        return {
            **base_result,
            "disease_name": "玫瑰黑斑病",
            "common_name_en": "Rose Black Spot",
            "pathogen": "Diplocarpon rosae (真菌)",
            "level": ConfidenceLevel.CONFIRMED.value,
            "confidence": 0.92,
            "feature_vector": {
                "flower_genus": "Rosa",
                "symptom_type": "necrosis",
                "color_center": "black",
                "color_border": "yellow",
                "size": "medium",
                "location": "leaf_edge"
            },
            "scores": {
                "total_score": 0.92,
                "major_matched": 2,
                "major_total": 2,
                "major_features_score": 0.80,
                "minor_features_score": 0.12
            },
            "message": None,
            "suggestion": "建议使用甲基托布津或代森锰锌进行防治",
            "vlm_suggestion": None,
            "error": None
        }

    elif scenario == "suspected":
        return {
            **base_result,
            "disease_name": "樱花白粉病",
            "common_name_en": "Cherry Powdery Mildew",
            "pathogen": "Podosphaera clandestina (真菌)",
            "level": ConfidenceLevel.SUSPECTED.value,
            "confidence": 0.72,
            "candidates": [
                {"disease_name": "樱花白粉病", "confidence": 0.72},
                {"disease_name": "樱花叶斑病", "confidence": 0.65},
                {"disease_name": "樱花褐斑病", "confidence": 0.58}
            ],
            "feature_vector": {
                "flower_genus": "Prunus",
                "symptom_type": "powdery_coating",
                "color_center": "white",
                "size": "medium"
            },
            "scores": {
                "total_score": 0.72,
                "major_matched": 1,
                "major_total": 2,
                "major_features_score": 0.50,
                "minor_features_score": 0.22
            },
            "message": None,
            "suggestion": "建议上传更多角度照片以提高诊断准确率",
            "vlm_suggestion": None,
            "error": None
        }

    elif scenario == "unknown":
        return {
            **base_result,
            "disease_name": None,
            "level": ConfidenceLevel.UNKNOWN.value,
            "confidence": 0.0,
            "message": "知识库中暂无 Jasminum（茉莉花属）的疾病数据",
            "suggestion": "请联系管理员添加该花卉的疾病知识库",
            "vlm_suggestion": None,
            "feature_vector": {
                "flower_genus": "Jasminum",  # 未收录的花卉
                "symptom_type": "necrosis"
            },
            "scores": None,
            "error": None
        }

    elif scenario == "vlm_fallback":
        return {
            **base_result,
            "disease_name": None,
            "level": ConfidenceLevel.VLM_FALLBACK.value,
            "confidence": 0.0,
            "message": "知识库未匹配到已知疾病",
            "suggestion": "可能是未收录疾病，建议上传更多角度图片或咨询专家",
            "vlm_suggestion": "观察到叶片边缘有不规则褐色斑点，可能是营养不良或真菌感染早期。建议：1) 检查土壤pH值；2) 增加钾肥施用；3) 如症状持续扩散，送样至实验室进行病原体鉴定。",
            "feature_vector": {
                "flower_genus": "Rosa",
                "symptom_type": "necrosis",
                "color_center": "brown",
                "size": "small"
            },
            "scores": {
                "total_score": 0.18,  # 低于0.30阈值
                "major_matched": 0,
                "major_total": 2,
                "major_features_score": 0.10,
                "minor_features_score": 0.08
            },
            "error": None
        }

    elif scenario == "system_error":
        return {
            **base_result,
            "disease_name": None,
            "level": ConfidenceLevel.SYSTEM_ERROR.value,
            "confidence": 0.0,
            "message": "诊断系统暂时不可用",
            "suggestion": "VLM服务异常: All VLM providers failed，请稍后重试",
            "vlm_suggestion": None,
            "feature_vector": {
                "flower_genus": "Rosa",
                "symptom_type": None
            },
            "scores": None,
            "error": "VLM服务异常"
        }

    else:
        raise ValueError(f"Unknown scenario: {scenario}")


# ==================== Streamlit UI ====================

def render_diagnosis_result(result: Dict[str, Any]):
    """渲染诊断结果"""

    # 1. 诊断ID和时间
    col1, col2 = st.columns(2)
    with col1:
        st.code(f"🆔 {result['diagnosis_id']}")
    with col2:
        st.code(f"⏱️ {result['execution_time_ms']}ms")

    # 2. 诊断级别（用颜色区分）
    level = result['level']
    level_colors = {
        "confirmed": "🟢",
        "suspected": "🟡",
        "unlikely": "🟠",
        "unknown": "⚪",
        "vlm_fallback": "🔵",
        "system_error": "🔴"
    }

    level_names = {
        "confirmed": "确诊",
        "suspected": "疑似",
        "unlikely": "不太可能",
        "unknown": "知识库无数据",
        "vlm_fallback": "VLM兜底诊断",
        "system_error": "系统错误"
    }

    st.subheader(f"{level_colors.get(level, '')} 诊断级别: {level_names.get(level, level)}")

    # 3. 主要诊断结果
    if result.get("disease_name"):
        st.success(f"**诊断结果**: {result['disease_name']}")
        if result.get("common_name_en"):
            st.caption(f"英文名: {result['common_name_en']}")
        if result.get("pathogen"):
            st.caption(f"病原体: {result['pathogen']}")
        st.metric("置信度", f"{result['confidence']:.1%}")

    # 4. 兜底逻辑特殊字段
    if result.get("message"):
        st.warning(f"**说明**: {result['message']}")

    if result.get("suggestion"):
        st.info(f"**建议**: {result['suggestion']}")

    if result.get("vlm_suggestion"):
        st.info(f"**VLM开放式诊断**:\n\n{result['vlm_suggestion']}")

    # 5. 候选疾病（疑似诊断）
    if result.get("candidates"):
        st.markdown("### 候选疾病列表")
        for idx, candidate in enumerate(result["candidates"], 1):
            st.write(f"{idx}. {candidate['disease_name']} - 置信度: {candidate['confidence']:.1%}")

    # 6. 诊断分数详情
    if result.get("scores"):
        st.markdown("### 诊断评分详情")
        scores = result["scores"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总分", f"{scores['total_score']:.2f}")
        with col2:
            st.metric("主要特征匹配", f"{scores['major_matched']}/{scores['major_total']}")
        with col3:
            st.metric("主要特征得分", f"{scores['major_features_score']:.2f}")

        # 医学诊断逻辑说明
        if scores["major_matched"] >= 2:
            st.success("✅ 主要特征匹配 ≥ 2/2（符合确诊条件）")
        elif scores["major_matched"] >= 1:
            st.warning("⚠️ 主要特征匹配 ≥ 1/2（符合疑似条件）")
        else:
            st.error("❌ 主要特征匹配 = 0（不符合诊断条件）")

    # 7. 特征向量
    if result.get("feature_vector"):
        with st.expander("🔬 提取的特征向量"):
            st.json(result["feature_vector"])

    # 8. 错误信息
    if result.get("error"):
        st.error(f"**错误**: {result['error']}")


def main():
    st.set_page_config(
        page_title="PhytoOracle Mock Demo",
        page_icon="🌸",
        layout="wide"
    )

    st.title("🌸 PhytoOracle - Mock 诊断演示")
    st.caption("演示修复后的3个核心缺陷：DiagnosisScore医学逻辑 + VLM响应协议 + 兜底逻辑")

    st.markdown("---")

    # 场景选择
    st.sidebar.header("📋 选择演示场景")

    scenario = st.sidebar.radio(
        "诊断场景",
        options=[
            ("confirmed", "🟢 确诊 - 玫瑰黑斑病"),
            ("suspected", "🟡 疑似 - 樱花白粉病"),
            ("unknown", "⚪ 知识库无数据 - 茉莉花未收录"),
            ("vlm_fallback", "🔵 VLM兜底 - 知识库外疾病"),
            ("system_error", "🔴 系统错误 - VLM完全失败")
        ],
        format_func=lambda x: x[1]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 修复说明

    **缺陷1: DiagnosisScore置信度逻辑**
    - ✅ 新增 `major_matched` / `major_total` 字段
    - ✅ 医学诊断逻辑：主要特征必须匹配 ≥2/2 才能确诊

    **缺陷2: VLM响应协议**
    - ✅ 定义完整 JSON Schema（Pydantic V2）
    - ✅ 添加 ResponseValidator 验证器
    - ✅ 完整 Q0-Q6 提示词模板（5.6节）

    **缺陷3: 兜底逻辑**
    - ✅ 知识库无数据（unknown）
    - ✅ VLM开放式诊断（vlm_fallback）
    - ✅ VLM完全失败（system_error）
    """)

    # 主界面
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 📷 上传图片")
        uploaded_file = st.file_uploader(
            "选择花卉图片",
            type=["jpg", "jpeg", "png"],
            help="真实场景中将调用VLM进行特征提取，此处使用Mock数据"
        )

        if uploaded_file:
            st.image(uploaded_file, caption="上传的图片", use_container_width=True)

    with col2:
        st.markdown("### 🔬 诊断结果")

        if st.button("🚀 开始诊断", type="primary", use_container_width=True):
            with st.spinner("诊断中..."):
                result = mock_diagnose(scenario[0])
                st.session_state["last_result"] = result

        if "last_result" in st.session_state:
            render_diagnosis_result(st.session_state["last_result"])


if __name__ == "__main__":
    main()
