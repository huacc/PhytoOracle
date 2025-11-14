"""
本体追溯组件

展示推理过程中使用的本体定义和同义词映射。
"""
import streamlit as st
from typing import Optional, Dict, Any

from models import (
    OntologyReference,
    SynonymMapping,
    MismatchExplanation,
)


def render_ontology_reference(
    ontology_ref: OntologyReference,
    label: str = "本体定义"
) -> None:
    """
    渲染本体引用信息

    Args:
        ontology_ref: 本体引用对象
        label: 展开器标签
    """
    with st.expander(f"📖 查看{label}"):
        st.markdown(f"**来源**: `{ontology_ref.source}`")

        if ontology_ref.feature_key:
            st.markdown(f"**特征键**: `{ontology_ref.feature_key}`")

        if ontology_ref.definition:
            st.markdown(f"**定义**: {ontology_ref.definition}")

        if ontology_ref.valid_choices:
            st.markdown("**有效选项**:")
            st.code(", ".join(ontology_ref.valid_choices))


def render_synonym_mapping(synonym_mapping: SynonymMapping) -> None:
    """
    渲染同义词映射详情

    Args:
        synonym_mapping: 同义词映射对象
    """
    st.info("🔄 **模糊匹配 - 同义词映射**")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**VLM识别值**: `{synonym_mapping.observed}`")
    with col2:
        st.markdown(f"**本体标准值**: `{synonym_mapping.canonical}`")

    st.markdown(f"**同义词来源**: `{synonym_mapping.synonym_source}`")
    st.markdown(f"**同义词列表**: {', '.join([f'`{s}`' for s in synonym_mapping.synonyms_list])}")
    st.markdown(f"**匹配说明**: {synonym_mapping.match_explanation}")


def render_mismatch_explanation(mismatch_exp: MismatchExplanation) -> None:
    """
    渲染不匹配说明

    Args:
        mismatch_exp: 不匹配说明对象
    """
    st.error("❌ **不匹配**")
    st.markdown(f"**原因**: {mismatch_exp.reason}")
    st.markdown(f"**期望的同义词列表**: {', '.join([f'`{s}`' for s in mismatch_exp.expected_synonyms])}")
    st.markdown(f"**本体引用**: `{mismatch_exp.ontology_reference}`")


def render_match_type_badge(match_type: str) -> str:
    """
    生成匹配类型徽章HTML

    Args:
        match_type: 匹配类型（exact/fuzzy/no_match）

    Returns:
        HTML字符串
    """
    badges = {
        "exact": "🟢 精确匹配",
        "fuzzy": "🟡 模糊匹配",
        "no_match": "🔴 不匹配"
    }
    return badges.get(match_type, match_type)


def render_confidence_badge(confidence: float) -> str:
    """
    生成置信度徽章

    Args:
        confidence: 置信度分数

    Returns:
        带颜色的置信度文本
    """
    if confidence >= 0.85:
        return f"🟢 {confidence:.2f}"
    elif confidence >= 0.70:
        return f"🟡 {confidence:.2f}"
    else:
        return f"🔴 {confidence:.2f}"


def render_confidence_level_badge(confidence_level: str, score: float) -> None:
    """
    渲染置信度级别徽章

    Args:
        confidence_level: 置信度级别
        score: 分数
    """
    level_config = {
        "confirmed": ("🟢", "确诊", "green"),
        "suspected": ("🟡", "疑似", "orange"),
        "unlikely": ("🔴", "不太可能", "red")
    }

    icon, label, color = level_config.get(confidence_level, ("⚪", "未知", "gray"))

    st.markdown(
        f"<div style='padding: 10px; border-radius: 5px; background-color: var(--{color}-background); "
        f"border-left: 4px solid var(--{color});'>"
        f"<b>{icon} {label}</b> - 分数: {score:.2f}"
        f"</div>",
        unsafe_allow_html=True
    )
