"""
推理过程可视化组件

完整展示推理链路的每个环节，包括本体追溯。
"""
import streamlit as st
import pandas as pd
from typing import Dict

from models import DiagnosisResult
from components.ontology_tracer import (
    render_ontology_reference,
    render_synonym_mapping,
    render_mismatch_explanation,
    render_match_type_badge,
    render_confidence_badge,
    render_confidence_level_badge,
)
from config import Q0_QUESTIONS


def render_diagnosis_result(diagnosis_result: DiagnosisResult) -> None:
    """
    渲染完整的推理结果

    Args:
        diagnosis_result: 推理结果对象
    """
    st.header("🔍 推理过程可视化")

    # 1. Q0序列
    render_q0_sequence(diagnosis_result)

    st.divider()

    # 2. Q1-Q6特征提取
    render_feature_extraction(diagnosis_result)

    st.divider()

    # 3. 候选疾病筛选
    render_candidate_diseases(diagnosis_result)

    st.divider()

    # 4. 加权评分
    render_scoring_results(diagnosis_result)

    st.divider()

    # 5. 最终诊断
    render_final_diagnosis(diagnosis_result)


def render_q0_sequence(diagnosis_result: DiagnosisResult) -> None:
    """渲染Q0序列结果"""
    st.subheader("1️⃣ Q0序列（6步分类问题）")

    for q_key, q_result in diagnosis_result.q0_sequence.items():
        q_config = Q0_QUESTIONS.get(q_key, {})
        label = q_config.get("label", q_key)

        with st.expander(f"**{label}** → {q_result.choice} {render_confidence_badge(q_result.confidence)}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**选择**: `{q_result.choice}`")
                st.markdown(f"**推理理由**: {q_result.reasoning}")

            with col2:
                st.metric("置信度", f"{q_result.confidence:.2f}")

            # 本体引用
            render_ontology_reference(q_result.ontology_reference)


def render_feature_extraction(diagnosis_result: DiagnosisResult) -> None:
    """渲染Q1-Q6特征提取结果"""
    st.subheader("2️⃣ Q1-Q6 动态特征提取（7个特征）")

    # 转换为表格数据
    table_data = []
    for feature_key, feature_result in diagnosis_result.feature_extraction.items():
        table_data.append({
            "特征": feature_key,
            "提取值": feature_result.choice,
            "置信度": f"{feature_result.confidence:.2f}",
            "推理理由": feature_result.reasoning
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 详细信息（可展开）
    with st.expander("🔬 查看特征提取详情（含本体引用）"):
        for feature_key, feature_result in diagnosis_result.feature_extraction.items():
            st.markdown(f"### {feature_key}")
            st.markdown(f"**提取值**: `{feature_result.choice}` {render_confidence_badge(feature_result.confidence)}")
            st.markdown(f"**推理理由**: {feature_result.reasoning}")

            # 本体引用
            render_ontology_reference(feature_result.ontology_reference, f"{feature_key} 特征定义")

            st.divider()


def render_candidate_diseases(diagnosis_result: DiagnosisResult) -> None:
    """渲染候选疾病筛选结果"""
    st.subheader("3️⃣ 候选疾病筛选")

    st.markdown(f"**筛选依据**: 基于 Q0.2 识别的花属 = `{diagnosis_result.q0_sequence['q0_2_flower_genus'].choice}`")
    st.markdown(f"**候选疾病数量**: {len(diagnosis_result.candidate_diseases)}")

    # 显示候选疾病列表
    for i, candidate in enumerate(diagnosis_result.candidate_diseases, 1):
        st.markdown(
            f"{i}. **{candidate.disease_name}** ({candidate.disease_name_en}) - "
            f"`{candidate.ontology_file}` (v{candidate.version})"
        )


def render_scoring_results(diagnosis_result: DiagnosisResult) -> None:
    """渲染加权评分结果"""
    st.subheader("4️⃣ 模糊匹配 + 加权评分")

    for i, scoring_result in enumerate(diagnosis_result.scoring_results, 1):
        # 卡片标题
        title = f"疾病 {i}: {scoring_result.disease_name} ({scoring_result.disease_id})"

        with st.expander(f"**{title}** - 总分: {scoring_result.total_score:.2f}", expanded=(i == 1)):
            # 基本信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总分", f"{scoring_result.total_score:.2f}")
            with col2:
                st.metric("置信度级别", scoring_result.confidence_level)
            with col3:
                st.metric("完整性修正系数", f"{scoring_result.completeness_modifier:.2f}")

            st.markdown(f"**疾病定义来源**: `{scoring_result.ontology_file}` (v{scoring_result.version})")

            # 分数细分
            st.markdown("#### 📊 分数细分")
            score_data = [
                {"重要性级别": "主要特征 (Major)", "分数": f"{scoring_result.major_score:.2f}", "权重": "60%"},
                {"重要性级别": "次要特征 (Minor)", "分数": f"{scoring_result.minor_score:.2f}", "权重": "30%"},
                {"重要性级别": "可选特征 (Optional)", "分数": f"{scoring_result.optional_score:.2f}", "权重": "10%"},
            ]
            st.table(pd.DataFrame(score_data))

            # 匹配详情
            st.markdown("#### 🔍 匹配详情（含本体引用）")

            for match_detail in scoring_result.match_details:
                st.markdown(f"**{match_detail.feature_key}** ({match_detail.importance_level})")

                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"VLM识别: `{match_detail.observed_value}`")
                with col2:
                    st.markdown(f"疾病期望: `{match_detail.expected_value}`")
                with col3:
                    st.markdown(render_match_type_badge(match_detail.match_type))

                st.markdown(f"**贡献分数**: {match_detail.contribution:.2f}")

                # 同义词映射或不匹配说明
                if match_detail.match_type == "fuzzy" and match_detail.synonym_mapping:
                    render_synonym_mapping(match_detail.synonym_mapping)
                elif match_detail.match_type == "no_match" and match_detail.mismatch_explanation:
                    render_mismatch_explanation(match_detail.mismatch_explanation)

                # 本体引用
                if match_detail.ontology_reference:
                    render_ontology_reference(match_detail.ontology_reference, f"{match_detail.feature_key} 本体定义")

                st.divider()


def render_final_diagnosis(diagnosis_result: DiagnosisResult) -> None:
    """渲染最终诊断结果"""
    st.subheader("5️⃣ 最终诊断结果")

    final = diagnosis_result.final_diagnosis

    # 突出显示
    st.markdown("### 🎯 诊断结果")
    st.markdown(f"## {final.disease_name} ({final.disease_name_en})")

    # 置信度级别
    render_confidence_level_badge(final.confidence_level, final.confidence_score)

    st.markdown(f"**病原体**: {final.pathogen}")
    st.markdown(f"**疾病定义**: `{final.ontology_file}` (v{final.version})")

    # 治疗建议
    st.markdown("### 💊 治疗建议")
    for i, suggestion in enumerate(final.treatment_suggestions, 1):
        st.markdown(f"{i}. {suggestion}")

    # 性能指标
    with st.expander("⏱️ 性能指标"):
        perf = diagnosis_result.performance
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总耗时", f"{perf.total_elapsed_time:.2f}s")
        with col2:
            st.metric("Q0耗时", f"{perf.q0_time:.2f}s")
        with col3:
            st.metric("Q1-Q6耗时", f"{perf.q1_q6_time:.2f}s")
        with col4:
            st.metric("匹配耗时", f"{perf.matching_time:.2f}s")

        st.markdown(f"**VLM提供商**: {perf.vlm_provider}")
