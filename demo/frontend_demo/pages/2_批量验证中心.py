"""
批量验证中心页面

提供批量图片上传、批量推理、结果汇总、统计分析等功能。
"""
import streamlit as st
import tempfile
from pathlib import Path
from typing import List, Tuple

from services.batch_diagnosis_service import get_batch_diagnosis_service
from services.mock_knowledge_service import get_knowledge_service
from components.batch_components import (
    render_batch_upload,
    render_batch_results_table,
    render_batch_annotation_summary,
)
from components.statistics_charts import (
    render_statistics_cards,
    render_confidence_distribution,
    render_genus_distribution,
    render_confusion_matrix,
)
from models import BatchDiagnosisResult, Annotation

# 页面配置
st.set_page_config(
    page_title="批量验证中心 - PhytoOracle",
    page_icon="📦",
    layout="wide"
)

# 初始化服务
batch_service = get_batch_diagnosis_service()
kb_service = get_knowledge_service()

# 页面标题
st.title("📦 批量验证中心")
st.caption("批量上传图片、执行推理、查看统计分析")

st.markdown("---")

# ===== Session State 初始化 =====
if "batch_result" not in st.session_state:
    st.session_state.batch_result = None

if "batch_uploaded_files" not in st.session_state:
    st.session_state.batch_uploaded_files = None

# ===== 批量上传区域 =====
st.header("📤 步骤1: 批量上传图片")

uploaded_files = render_batch_upload()

if uploaded_files:
    st.session_state.batch_uploaded_files = uploaded_files

    # 显示上传成功提示
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("🚀 开始批量推理", type="primary", use_container_width=True):
            with st.spinner("正在执行批量推理，请稍候..."):
                # 保存上传的文件到临时目录
                temp_dir = tempfile.mkdtemp()
                image_files: List[Tuple[str, str]] = []

                for file in uploaded_files:
                    # 保存文件
                    file_path = Path(temp_dir) / file.name
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())

                    image_files.append((str(file_path), file.name))

                # 创建批次
                batch_result = batch_service.create_batch(image_files)

                # 进度条
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(current: int, total: int):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"推理进度: {current}/{total} ({progress*100:.1f}%)")

                # 执行批量推理
                batch_result = batch_service.process_batch(
                    batch_result,
                    image_files,
                    progress_callback=update_progress
                )

                # 保存到session state
                st.session_state.batch_result = batch_result

                st.success(f"✅ 批量推理完成！共处理 {batch_result.completed_count} 张图片")
                st.rerun()

# ===== 批量推理结果展示 =====
if st.session_state.batch_result:
    batch_result: BatchDiagnosisResult = st.session_state.batch_result

    st.markdown("---")
    st.header("📊 步骤2: 查看推理结果")

    # Tab布局
    tab1, tab2, tab3 = st.tabs(["📋 结果列表", "📈 统计分析", "✏️ 批量标注"])

    # ===== Tab 1: 结果列表 =====
    with tab1:
        render_batch_results_table(batch_result.items)

    # ===== Tab 2: 统计分析 =====
    with tab2:
        if batch_result.statistics:
            # 整体统计卡片
            render_statistics_cards(batch_result.statistics)

            st.markdown("---")

            # 置信度分布
            col1, col2 = st.columns(2)

            with col1:
                render_confidence_distribution(batch_result.statistics)

            with col2:
                render_genus_distribution(batch_result.statistics)

            st.markdown("---")

            # 混淆矩阵（如果有已标注样本）
            if batch_result.confusion_matrix:
                render_confusion_matrix(batch_result.confusion_matrix)
            else:
                st.info("💡 提示：完成标注后可查看混淆矩阵")

        else:
            st.info("暂无统计数据，请先完成批量推理")

    # ===== Tab 3: 批量标注 =====
    with tab3:
        st.subheader("✏️ 批量标注")

        # 显示标注进度
        render_batch_annotation_summary(batch_result.items)

        st.markdown("---")

        # 筛选未标注项
        unannotated_items = [item for item in batch_result.items if item.annotation_status is None]

        if unannotated_items:
            st.info(f"还有 {len(unannotated_items)} 张图片未标注")

            # 选择要标注的图片
            selected_item_name = st.selectbox(
                "选择图片进行标注",
                options=[item.image_name for item in unannotated_items],
                key="annotation_selector"
            )

            # 找到对应的item
            selected_item = next(
                (item for item in unannotated_items if item.image_name == selected_item_name),
                None
            )

            if selected_item:
                st.markdown("---")

                # 显示诊断结果
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("图片名称", selected_item.image_name)

                with col2:
                    st.metric("花卉属", selected_item.flower_genus)

                with col3:
                    st.metric("诊断疾病", selected_item.disease_name)

                with col4:
                    st.metric("置信度", f"{selected_item.confidence_score:.2f}")

                st.markdown("---")

                # 标注表单
                with st.form(key=f"annotation_form_{selected_item.image_id}"):
                    st.markdown("### 标注信息")

                    # 准确性选择
                    is_accurate = st.radio(
                        "诊断准确性",
                        options=["correct", "incorrect", "uncertain"],
                        format_func=lambda x: {
                            "correct": "✅ 正确",
                            "incorrect": "❌ 错误",
                            "uncertain": "❓ 不确定"
                        }[x],
                        horizontal=True,
                        key=f"accuracy_{selected_item.image_id}"
                    )

                    # 实际疾病（如果错误）
                    actual_disease_id = None
                    actual_disease_name = None
                    if is_accurate == "incorrect":
                        st.markdown("#### 实际疾病")
                        available_diseases = [
                            {"id": disease_id, "name": disease_data["disease_name"]}
                            for disease_id, disease_data in kb_service.diseases.items()
                        ]

                        disease_options = {d["name"]: d["id"] for d in available_diseases}
                        actual_disease_name = st.selectbox(
                            "选择实际疾病",
                            options=list(disease_options.keys()),
                            key=f"actual_disease_{selected_item.image_id}"
                        )
                        actual_disease_id = disease_options[actual_disease_name]

                    # 标注备注
                    notes = st.text_area(
                        "备注（可选）",
                        placeholder="记录标注理由或观察到的特征...",
                        key=f"notes_{selected_item.image_id}"
                    )

                    # 提交按钮
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        submitted = st.form_submit_button("💾 保存标注", use_container_width=True)

                    if submitted:
                        # 创建标注对象
                        annotation = Annotation(
                            is_accurate=is_accurate,
                            actual_disease_id=actual_disease_id,
                            actual_disease_name=actual_disease_name,
                            notes=notes if notes else None
                        )

                        # 更新批量结果
                        batch_result = batch_service.update_annotation(
                            batch_result,
                            selected_item.image_id,
                            annotation
                        )

                        # 更新session state
                        st.session_state.batch_result = batch_result

                        st.success("✅ 标注已保存！")
                        st.rerun()

        else:
            st.success("🎉 所有图片已完成标注！")

            # 显示标注汇总
            st.markdown("---")
            st.subheader("📊 标注汇总")

            col1, col2, col3 = st.columns(3)

            correct_count = sum(1 for item in batch_result.items if item.annotation_status == "correct")
            incorrect_count = sum(1 for item in batch_result.items if item.annotation_status == "incorrect")
            uncertain_count = sum(1 for item in batch_result.items if item.annotation_status == "uncertain")

            with col1:
                st.metric("✅ 正确", correct_count)

            with col2:
                st.metric("❌ 错误", incorrect_count)

            with col3:
                st.metric("❓ 不确定", uncertain_count)

            # 准确率
            if correct_count + incorrect_count > 0:
                accuracy = correct_count / (correct_count + incorrect_count)
                st.metric("准确率", f"{accuracy*100:.1f}%", help="正确数 / (正确数 + 错误数)")

else:
    st.info("👆 请先上传图片并执行批量推理")

# ===== 侧边栏：快速操作 =====
with st.sidebar:
    st.header("⚙️ 快速操作")

    if st.session_state.batch_result:
        batch_result = st.session_state.batch_result

        st.metric("批次ID", batch_result.batch_id)
        st.metric("总图片数", batch_result.total_images)
        st.metric("已完成", batch_result.completed_count)

        st.markdown("---")

        # 清空当前批次
        if st.button("🗑️ 清空当前批次", use_container_width=True):
            st.session_state.batch_result = None
            st.session_state.batch_uploaded_files = None
            st.rerun()

        # 导出完整结果
        if st.button("📥 导出完整结果", use_container_width=True):
            import json
            from datetime import datetime

            export_data = {
                "batch_id": batch_result.batch_id,
                "created_at": batch_result.created_at.isoformat(),
                "total_images": batch_result.total_images,
                "items": [
                    {
                        "image_name": item.image_name,
                        "flower_genus": item.flower_genus,
                        "disease_name": item.disease_name,
                        "confidence_score": item.confidence_score,
                        "confidence_level": item.confidence_level,
                        "annotation_status": item.annotation_status,
                        "actual_disease_name": item.actual_disease_name,
                        "notes": item.notes
                    }
                    for item in batch_result.items
                ]
            }

            if batch_result.statistics:
                export_data["statistics"] = {
                    "total_count": batch_result.statistics.total_count,
                    "annotated_count": batch_result.statistics.annotated_count,
                    "accuracy_rate": batch_result.statistics.accuracy_rate
                }

            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)

            st.download_button(
                label="💾 下载JSON",
                data=json_str.encode('utf-8'),
                file_name=f"batch_result_{batch_result.batch_id}.json",
                mime="application/json"
            )

    else:
        st.info("暂无批次数据")
