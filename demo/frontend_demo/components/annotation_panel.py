"""
人工标注面板组件

提供准确性标注、实际疾病标注和备注输入功能。
"""
import streamlit as st
from typing import Optional, Dict, List

from models import Annotation, ImageAnnotation
from services import get_knowledge_service


def render_annotation_panel(
    diagnosis_id: str,
    image_id: str,
    diagnosed_disease_id: str
) -> Optional[ImageAnnotation]:
    """
    渲染人工标注面板

    Args:
        diagnosis_id: 诊断ID
        image_id: 图片ID
        diagnosed_disease_id: 诊断出的疾病ID

    Returns:
        如果用户点击保存，返回ImageAnnotation对象，否则返回None
    """
    st.header("✍️ 人工标注")

    st.markdown("请对诊断结果进行标注，帮助改进推理引擎和知识库。")

    # 准确性标注
    accuracy_options = {
        "correct": "✅ 正确",
        "incorrect": "❌ 错误",
        "uncertain": "❓ 不确定"
    }

    is_accurate = st.radio(
        "诊断准确性",
        options=list(accuracy_options.keys()),
        format_func=lambda x: accuracy_options[x],
        horizontal=True
    )

    # 如果标注为错误，显示实际疾病选择
    actual_disease_id = None
    actual_disease_name = None

    if is_accurate == "incorrect":
        st.markdown("#### 请选择实际疾病")

        kb_service = get_knowledge_service()
        all_diseases = kb_service.diseases

        disease_options = {
            disease_id: f"{data['disease_name']} ({data['disease_name_en']})"
            for disease_id, data in all_diseases.items()
        }

        actual_disease_id = st.selectbox(
            "实际疾病",
            options=list(disease_options.keys()),
            format_func=lambda x: disease_options.get(x, x),
            index=None,
            placeholder="请选择实际疾病..."
        )

        if actual_disease_id:
            actual_disease_name = all_diseases[actual_disease_id]['disease_name']

    # 标注备注
    notes = st.text_area(
        "标注备注（可选）",
        placeholder="可以记录：\n- 为什么诊断错误/正确\n- 本体定义需要如何调整\n- 其他观察和建议",
        height=150
    )

    # 保存按钮
    col1, col2 = st.columns([1, 5])
    with col1:
        save_button = st.button("💾 保存标注", type="primary", use_container_width=True)
    with col2:
        if save_button:
            st.success("✅ 标注已保存！")

    # 如果点击保存，返回标注数据
    if save_button:
        annotation = Annotation(
            is_accurate=is_accurate,
            actual_disease_id=actual_disease_id,
            actual_disease_name=actual_disease_name,
            notes=notes if notes.strip() else None
        )

        image_annotation = ImageAnnotation(
            image_id=image_id,
            diagnosis_id=diagnosis_id,
            annotation=annotation
        )

        return image_annotation

    return None


def display_annotation_summary(annotation: ImageAnnotation) -> None:
    """
    显示标注摘要

    Args:
        annotation: 标注数据
    """
    st.markdown("### 📋 标注摘要")

    # 准确性
    accuracy_icons = {
        "correct": "✅",
        "incorrect": "❌",
        "uncertain": "❓"
    }
    icon = accuracy_icons.get(annotation.annotation.is_accurate, "")

    st.markdown(f"**准确性**: {icon} {annotation.annotation.is_accurate}")

    # 实际疾病
    if annotation.annotation.actual_disease_id:
        st.markdown(f"**实际疾病**: {annotation.annotation.actual_disease_name} (`{annotation.annotation.actual_disease_id}`)")

    # 备注
    if annotation.annotation.notes:
        st.markdown(f"**备注**: {annotation.annotation.notes}")

    # 时间戳
    st.markdown(f"**标注时间**: {annotation.annotation.annotated_at.strftime('%Y-%m-%d %H:%M:%S')}")
