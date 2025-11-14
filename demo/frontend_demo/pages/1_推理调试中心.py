"""
推理调试中心 - 单张调试、批量验证、图片对比

核心功能：图片上传、推理、可视化、标注、导出、批量验证、图片对比
"""
import streamlit as st
from PIL import Image
import io

from services import get_diagnosis_engine
from services.history_manager import get_history_manager
from components import (
    render_diagnosis_result,
    render_annotation_panel,
    render_image_comparison_selector,
    render_side_by_side_comparison,
    render_difference_analysis,
)
from utils import (
    export_diagnosis_result,
    export_ontology_usage,
    generate_ontology_usage_summary_text,
)
from config import SUPPORTED_IMAGE_FORMATS, PAGE_ICON


def main():
    """主函数"""
    st.set_page_config(
        page_title="推理调试中心 - PhytoOracle",
        page_icon=PAGE_ICON,
        layout="wide"
    )

    st.title("🔬 推理调试中心")

    # 初始化session state
    init_session_state()

    # Tab布局：三个模式
    tab1, tab2, tab3 = st.tabs([
        "📋 Tab 1: 单张调试",
        "📊 Tab 2: 批量验证",
        "🔍 Tab 3: 图片对比"
    ])

    # Tab 1: 单张调试模式
    with tab1:
        render_single_diagnosis_mode()

    # Tab 2: 批量验证模式
    with tab2:
        st.info("💡 批量验证功能已移至「批量验证中心」页面")
        if st.button("➡️ 前往批量验证中心", type="primary", key="goto_batch_from_tab2"):
            st.switch_page("pages/2_批量验证中心.py")

    # Tab 3: 图片对比模式
    with tab3:
        render_comparison_mode()


def init_session_state():
    """初始化Session State"""
    if "current_diagnosis" not in st.session_state:
        st.session_state.current_diagnosis = None

    if "current_annotation" not in st.session_state:
        st.session_state.current_annotation = None

    if "current_image_name" not in st.session_state:
        st.session_state.current_image_name = None

    if "current_image_bytes" not in st.session_state:
        st.session_state.current_image_bytes = None

    if "show_diagnosis" not in st.session_state:
        st.session_state.show_diagnosis = False

    # 初始化历史管理器
    HistoryManager = get_history_manager()
    HistoryManager.initialize_session_state()


def render_single_diagnosis_mode():
    """渲染单张调试模式"""
    st.header("📤 单张调试模式")
    st.caption("上传单张图片进行详细推理和分析")

    # 1. 图片上传模块
    render_image_upload_section()

    # 2. 如果有推理结果，显示推理过程和其他模块
    if st.session_state.show_diagnosis and st.session_state.current_diagnosis:
        st.divider()

        # 推理过程可视化
        render_diagnosis_result(st.session_state.current_diagnosis)

        st.divider()

        # 本体使用总结
        render_ontology_usage_summary()

        st.divider()

        # 人工标注
        render_annotation_section()

        st.divider()

        # 导出功能
        render_export_section()


def render_image_upload_section():
    """渲染图片上传模块"""
    st.subheader("📤 图片上传与推理")

    col1, col2 = st.columns([2, 1])

    with col1:
        # 文件上传器
        uploaded_file = st.file_uploader(
            "上传植物病害图片",
            type=SUPPORTED_IMAGE_FORMATS,
            help="支持拖拽上传或点击选择。文件名应包含疾病信息，如：rose_black_spot_001.jpg"
        )

        if uploaded_file is not None:
            # 保存图片信息
            st.session_state.current_image_name = uploaded_file.name
            st.session_state.current_image_bytes = uploaded_file.getvalue()

            # 显示图片预览
            st.markdown("#### 图片预览")
            image = Image.open(io.BytesIO(st.session_state.current_image_bytes))
            st.image(image, caption=uploaded_file.name, use_container_width=True)

            # 显示图片信息
            st.markdown(f"**文件名**: `{uploaded_file.name}`")
            st.markdown(f"**尺寸**: {image.size[0]} x {image.size[1]} px")
            st.markdown(f"**大小**: {len(st.session_state.current_image_bytes) / 1024:.2f} KB")

    with col2:
        if uploaded_file is not None:
            st.markdown("#### 执行推理")

            if st.button("🚀 开始推理", type="primary", use_container_width=True):
                # 执行推理
                with st.spinner("正在执行推理..."):
                    try:
                        engine = get_diagnosis_engine()
                        diagnosis_result = engine.diagnose(
                            image_path="uploaded",  # 假数据不需要真实路径
                            image_name=uploaded_file.name
                        )

                        # 保存结果
                        st.session_state.current_diagnosis = diagnosis_result
                        st.session_state.show_diagnosis = True

                        # 添加到历史记录
                        HistoryManager = get_history_manager()
                        HistoryManager.add_diagnosis_record(
                            diagnosis_result=diagnosis_result,
                            image_name=uploaded_file.name
                        )

                        st.success("✅ 推理完成！")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 推理失败: {str(e)}")

            # 重置按钮
            if st.session_state.show_diagnosis:
                if st.button("🔄 重新上传", use_container_width=True):
                    # 重置状态
                    st.session_state.current_diagnosis = None
                    st.session_state.current_annotation = None
                    st.session_state.current_image_name = None
                    st.session_state.current_image_bytes = None
                    st.session_state.show_diagnosis = False
                    st.rerun()

        else:
            st.info("👆 请先上传图片")


def render_ontology_usage_summary():
    """渲染本体使用总结"""
    st.header("📚 本体使用总结")

    diagnosis = st.session_state.current_diagnosis

    # 生成总结文本
    summary_text = generate_ontology_usage_summary_text(diagnosis)
    st.markdown(summary_text)


def render_annotation_section():
    """渲染人工标注模块"""
    diagnosis = st.session_state.current_diagnosis

    annotation = render_annotation_panel(
        diagnosis_id=diagnosis.diagnosis_id,
        image_id=diagnosis.image_id,
        diagnosed_disease_id=diagnosis.final_diagnosis.disease_id
    )

    if annotation:
        st.session_state.current_annotation = annotation

        # 更新历史记录
        HistoryManager = get_history_manager()
        HistoryManager.update_annotation(
            image_id=diagnosis.image_id,
            annotation_status=annotation.annotation.accuracy,
            actual_disease_id=annotation.annotation.actual_disease_id,
            actual_disease_name=annotation.annotation.actual_disease_name,
            notes=annotation.annotation.notes
        )


def render_export_section():
    """渲染导出功能模块"""
    st.header("💾 数据导出")

    diagnosis = st.session_state.current_diagnosis

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 推理全链路JSON")
        st.markdown("包含完整的推理过程、本体引用、匹配详情等所有信息。")

        # 导出推理结果
        diagnosis_json = export_diagnosis_result(diagnosis)

        st.download_button(
            label="⬇️ 下载推理结果 JSON",
            data=diagnosis_json,
            file_name=f"diagnosis_{diagnosis.diagnosis_id}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        st.markdown("### 📋 本体使用清单JSON")
        st.markdown("提取的本体使用信息，便于使用Claude进行代码级调整。")

        # 获取标注备注（如果有）
        adjustment_notes = None
        if st.session_state.current_annotation:
            adjustment_notes = st.session_state.current_annotation.annotation.notes

        # 导出本体使用
        ontology_json = export_ontology_usage(diagnosis, adjustment_notes)

        st.download_button(
            label="⬇️ 下载本体使用清单 JSON",
            data=ontology_json,
            file_name=f"ontology_usage_{diagnosis.diagnosis_id}.json",
            mime="application/json",
            use_container_width=True
        )

    # 预览JSON（可选）
    with st.expander("👁️ 预览本体使用清单"):
        st.json(ontology_json, expanded=False)


def render_comparison_mode():
    """渲染图片对比模式（Tab 3）"""
    st.header("🔍 图片对比模式")
    st.caption("对比多张图片的推理结果，分析特征差异")

    HistoryManager = get_history_manager()

    # 获取历史数据
    history_items = HistoryManager.get_all_history_items()
    diagnosis_results = HistoryManager.get_all_diagnosis_results()

    if not history_items:
        st.warning("⚠️ 暂无历史推理数据")
        st.info("💡 请先在「单张调试」模式下完成推理，或在「批量验证中心」完成批量推理后再使用对比功能")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➡️ 前往单张调试", type="primary", key="goto_single_from_comparison"):
                # 切换到Tab 1
                st.info("请点击上方「Tab 1: 单张调试」标签页")
        with col2:
            if st.button("➡️ 前往批量验证中心", type="primary", key="goto_batch_from_comparison"):
                st.switch_page("pages/2_批量验证中心.py")

        return

    # 显示历史统计
    stats = HistoryManager.get_history_statistics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("历史记录数", stats["total"])
    with col2:
        st.metric("已标注", stats["annotated"])
    with col3:
        if stats["accuracy_rate"] is not None:
            st.metric("准确率", f"{stats['accuracy_rate']*100:.1f}%")
        else:
            st.metric("准确率", "N/A")
    with col4:
        st.metric("误诊案例", stats["incorrect"])

    st.markdown("---")

    # 1. 图片选择模块
    selected_image_ids = render_image_comparison_selector(history_items)

    # 如果选择了2-4张图片，显示对比
    if selected_image_ids and 2 <= len(selected_image_ids) <= 4:
        st.markdown("---")

        # 获取选中的items和诊断结果
        selected_items = [
            item for item in history_items
            if item.image_id in selected_image_ids
        ]

        # 按选择顺序排序
        selected_items_sorted = []
        for image_id in selected_image_ids:
            for item in selected_items:
                if item.image_id == image_id:
                    selected_items_sorted.append(item)
                    break

        # 2. 并排展示
        render_side_by_side_comparison(selected_items_sorted, diagnosis_results)

        st.markdown("---")

        # 3. 差异分析报告
        render_difference_analysis(selected_items_sorted, diagnosis_results)


if __name__ == "__main__":
    main()
