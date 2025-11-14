"""
批量验证相关UI组件

包含批量上传、结果表格、快速标注等组件。
"""
import streamlit as st
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime

from models import BatchDiagnosisItem, Annotation


def render_batch_upload() -> Optional[List]:
    """
    渲染批量上传组件

    Returns:
        上传的文件列表，如果没有上传则返回None
    """
    st.subheader("📤 批量上传图片")

    with st.container():
        uploaded_files = st.file_uploader(
            "选择多张图片进行批量推理",
            type=["jpg", "jpeg", "png", "bmp"],
            accept_multiple_files=True,
            help="支持一次上传 5-50 张图片，推荐 10-20 张以获得最佳体验"
        )

        if uploaded_files:
            st.info(f"已上传 {len(uploaded_files)} 张图片")

            # 显示缩略图预览
            with st.expander("📷 查看缩略图", expanded=False):
                cols = st.columns(5)
                for idx, file in enumerate(uploaded_files):
                    with cols[idx % 5]:
                        st.image(file, caption=file.name, use_container_width=True)

            return uploaded_files

    return None


def render_batch_results_table(
    items: List[BatchDiagnosisItem],
    show_annotation_column: bool = True
) -> Optional[str]:
    """
    渲染批量推理结果表格

    Args:
        items: 批量推理结果项列表
        show_annotation_column: 是否显示标注列

    Returns:
        选中的image_id（用于查看详情），如果没有选中则返回None
    """
    if not items:
        st.warning("暂无推理结果")
        return None

    st.subheader("📊 批量推理结果")

    # 转换为DataFrame
    df_data = []
    for item in items:
        # 标注状态显示
        if show_annotation_column:
            if item.annotation_status == "correct":
                annotation_display = "✅ 正确"
            elif item.annotation_status == "incorrect":
                annotation_display = f"❌ 错误 (实际: {item.actual_disease_name})"
            elif item.annotation_status == "uncertain":
                annotation_display = "❓ 不确定"
            else:
                annotation_display = "⚪ 未标注"
        else:
            annotation_display = "-"

        # 置信度显示
        confidence_display = f"{item.confidence_score:.2f} ({item.confidence_level})"

        df_data.append({
            "图片名称": item.image_name,
            "花卉属": item.flower_genus,
            "诊断结果": item.disease_name,
            "置信度": confidence_display,
            "标注状态": annotation_display,
            "诊断时间": item.diagnosed_at.strftime("%H:%M:%S"),
            "image_id": item.image_id,  # 用于详情查看
        })

    df = pd.DataFrame(df_data)

    # 使用Streamlit的data_editor实现交互式表格
    st.dataframe(
        df.drop(columns=["image_id"]),  # 隐藏内部ID列
        use_container_width=True,
        height=400
    )

    # 筛选功能
    with st.expander("🔍 筛选选项", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_genus = st.multiselect(
                "按花卉属筛选",
                options=sorted(df["花卉属"].unique()),
                default=None
            )

        with col2:
            filter_confidence = st.multiselect(
                "按置信度级别筛选",
                options=["confirmed", "suspected", "unlikely"],
                default=None,
                format_func=lambda x: {"confirmed": "确诊", "suspected": "疑似", "unlikely": "不太可能"}[x]
            )

        with col3:
            if show_annotation_column:
                filter_annotation = st.multiselect(
                    "按标注状态筛选",
                    options=["correct", "incorrect", "uncertain", None],
                    default=None,
                    format_func=lambda x: {
                        "correct": "✅ 正确",
                        "incorrect": "❌ 错误",
                        "uncertain": "❓ 不确定",
                        None: "⚪ 未标注"
                    }[x]
                )
            else:
                filter_annotation = None

    # 应用筛选
    filtered_items = items
    if filter_genus:
        filtered_items = [item for item in filtered_items if item.flower_genus in filter_genus]
    if filter_confidence:
        filtered_items = [item for item in filtered_items if item.confidence_level in filter_confidence]
    if filter_annotation is not None:
        filtered_items = [item for item in filtered_items if item.annotation_status in filter_annotation]

    if filtered_items != items:
        st.info(f"筛选后显示 {len(filtered_items)}/{len(items)} 条结果")

        # 重新显示筛选后的表格
        filtered_df_data = [d for d in df_data if any(
            item.image_id == d["image_id"] for item in filtered_items
        )]

        if filtered_df_data:
            filtered_df = pd.DataFrame(filtered_df_data)
            # 只在列存在时删除
            display_df = filtered_df.drop(columns=["image_id"]) if "image_id" in filtered_df.columns else filtered_df
            st.dataframe(
                display_df,
                use_container_width=True,
                height=300
            )
        else:
            st.warning("没有符合筛选条件的结果")

    # 快速操作按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 导出CSV", use_container_width=True):
            # 只在列存在时删除
            export_df = df.drop(columns=["image_id"]) if "image_id" in df.columns else df
            csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载CSV文件",
                data=csv_data,
                file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col2:
        # 导出误诊案例
        incorrect_items = [item for item in items if item.annotation_status == "incorrect"]
        if incorrect_items:
            if st.button(f"⚠️ 导出误诊案例 ({len(incorrect_items)})", use_container_width=True):
                incorrect_df = pd.DataFrame([
                    {
                        "图片名称": item.image_name,
                        "诊断结果": item.disease_name,
                        "实际疾病": item.actual_disease_name,
                        "置信度": f"{item.confidence_score:.2f}",
                        "备注": item.notes or ""
                    }
                    for item in incorrect_items
                ])
                csv_data = incorrect_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="下载误诊案例CSV",
                    data=csv_data,
                    file_name=f"incorrect_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

    with col3:
        # 显示未标注数量
        unannotated_count = sum(1 for item in items if item.annotation_status is None)
        if unannotated_count > 0:
            st.metric("待标注", f"{unannotated_count} 张")

    return None


def render_quick_annotation_panel(
    item: BatchDiagnosisItem,
    available_diseases: List[Dict[str, str]]
) -> Optional[Annotation]:
    """
    渲染快速标注面板

    Args:
        item: 批量推理结果项
        available_diseases: 可选疾病列表 [{"id": ..., "name": ...}, ...]

    Returns:
        标注数据，如果未提交则返回None
    """
    st.subheader(f"✏️ 标注: {item.image_name}")

    with st.form(key=f"annotation_form_{item.image_id}"):
        # 诊断结果展示
        col1, col2 = st.columns(2)
        with col1:
            st.metric("诊断疾病", item.disease_name)
        with col2:
            st.metric("置信度", f"{item.confidence_score:.2f} ({item.confidence_level})")

        # 标注准确性
        is_accurate = st.radio(
            "诊断准确性",
            options=["correct", "incorrect", "uncertain"],
            format_func=lambda x: {"correct": "✅ 正确", "incorrect": "❌ 错误", "uncertain": "❓ 不确定"}[x],
            horizontal=True,
            key=f"accuracy_{item.image_id}"
        )

        # 实际疾病（如果错误）
        actual_disease_id = None
        actual_disease_name = None
        if is_accurate == "incorrect":
            disease_options = {d["name"]: d["id"] for d in available_diseases}
            actual_disease_name = st.selectbox(
                "实际疾病",
                options=list(disease_options.keys()),
                key=f"actual_disease_{item.image_id}"
            )
            actual_disease_id = disease_options[actual_disease_name]

        # 标注备注
        notes = st.text_area(
            "备注（可选）",
            placeholder="记录标注理由或观察到的特征...",
            key=f"notes_{item.image_id}"
        )

        # 提交按钮
        submitted = st.form_submit_button("💾 保存标注", use_container_width=True)

        if submitted:
            annotation = Annotation(
                is_accurate=is_accurate,
                actual_disease_id=actual_disease_id,
                actual_disease_name=actual_disease_name,
                notes=notes if notes else None
            )
            st.success("标注已保存！")
            return annotation

    return None


def render_batch_annotation_summary(items: List[BatchDiagnosisItem]) -> None:
    """
    渲染批量标注进度摘要

    Args:
        items: 批量推理结果项列表
    """
    annotated_count = sum(1 for item in items if item.annotation_status is not None)
    total_count = len(items)
    progress = annotated_count / total_count if total_count > 0 else 0

    st.progress(progress, text=f"标注进度: {annotated_count}/{total_count} ({progress*100:.1f}%)")

    # 显示标注分布
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        correct_count = sum(1 for item in items if item.annotation_status == "correct")
        st.metric("✅ 正确", correct_count)

    with col2:
        incorrect_count = sum(1 for item in items if item.annotation_status == "incorrect")
        st.metric("❌ 错误", incorrect_count)

    with col3:
        uncertain_count = sum(1 for item in items if item.annotation_status == "uncertain")
        st.metric("❓ 不确定", uncertain_count)

    with col4:
        unannotated_count = total_count - annotated_count
        st.metric("⚪ 未标注", unannotated_count)
