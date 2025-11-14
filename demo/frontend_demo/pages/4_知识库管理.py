"""
知识库管理页面

提供疾病列表浏览、疾病详情查看、特征本体浏览、疾病对比等功能。
"""
import streamlit as st

from components.knowledge_browser import (
    render_disease_list,
    render_disease_detail,
    render_feature_ontology_browser,
    render_knowledge_base_summary,
    render_ontology_comparison,
)

# 页面配置
st.set_page_config(
    page_title="知识库管理 - PhytoOracle",
    page_icon="📚",
    layout="wide"
)

# 页面标题
st.title("📚 知识库管理")
st.caption("浏览疾病定义、特征本体和知识库版本信息")

st.markdown("---")

# ===== Session State 初始化 =====
if "selected_disease_id" not in st.session_state:
    st.session_state.selected_disease_id = None

if "comparison_disease_1" not in st.session_state:
    st.session_state.comparison_disease_1 = None

if "comparison_disease_2" not in st.session_state:
    st.session_state.comparison_disease_2 = None

# ===== Tab布局 =====
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 疾病列表",
    "🔍 疾病详情",
    "🌳 特征本体",
    "🔄 疾病对比"
])

# ===== Tab 1: 疾病列表 =====
with tab1:
    st.header("📋 疾病列表")

    # 显示知识库摘要
    render_knowledge_base_summary()

    st.markdown("---")

    # 显示疾病列表
    selected_disease_id = render_disease_list()

    if selected_disease_id:
        st.session_state.selected_disease_id = selected_disease_id
        st.success(f"已选择疾病: {selected_disease_id}")
        st.info("💡 切换到「疾病详情」标签页查看完整信息")

# ===== Tab 2: 疾病详情 =====
with tab2:
    st.header("🔍 疾病详情")

    if st.session_state.selected_disease_id:
        render_disease_detail(st.session_state.selected_disease_id)

        st.markdown("---")

        # 快速导航
        col1, col2 = st.columns(2)

        with col1:
            if st.button("⬅️ 返回疾病列表", use_container_width=True):
                st.session_state.selected_disease_id = None
                st.rerun()

        with col2:
            if st.button("🔄 用于疾病对比", use_container_width=True):
                if not st.session_state.comparison_disease_1:
                    st.session_state.comparison_disease_1 = st.session_state.selected_disease_id
                    st.info("已设置为对比疾病1，请选择第二个疾病进行对比")
                elif not st.session_state.comparison_disease_2:
                    st.session_state.comparison_disease_2 = st.session_state.selected_disease_id
                    st.success("已设置为对比疾病2，切换到「疾病对比」标签页查看")
                else:
                    st.warning("已有两个对比疾病，请先清空对比列表")

    else:
        st.info("💡 请先在「疾病列表」标签页选择一个疾病")

        if st.button("➡️ 前往疾病列表", type="primary"):
            st.rerun()

# ===== Tab 3: 特征本体 =====
with tab3:
    st.header("🌳 特征本体浏览")

    render_feature_ontology_browser()

# ===== Tab 4: 疾病对比 =====
with tab4:
    st.header("🔄 疾病特征对比")

    st.info("""
    **功能说明**：

    对比两个疾病的特征向量，识别相同和不同的特征。
    这有助于理解疾病之间的区别，以及可能导致误诊的特征混淆。
    """)

    st.markdown("---")

    # 选择对比疾病
    from services.mock_knowledge_service import get_knowledge_service

    kb_service = get_knowledge_service()
    disease_options = {
        f"{data['disease_name']} ({disease_id})": disease_id
        for disease_id, data in kb_service.diseases.items()
    }

    col1, col2 = st.columns(2)

    with col1:
        disease_name_1 = st.selectbox(
            "选择疾病1",
            options=list(disease_options.keys()),
            index=0 if st.session_state.comparison_disease_1 is None else None,
            key="disease_select_1"
        )
        disease_id_1 = disease_options[disease_name_1]

    with col2:
        disease_name_2 = st.selectbox(
            "选择疾病2",
            options=[name for name in disease_options.keys() if disease_options[name] != disease_id_1],
            key="disease_select_2"
        )
        disease_id_2 = disease_options[disease_name_2]

    st.markdown("---")

    # 显示对比结果
    if disease_id_1 and disease_id_2:
        render_ontology_comparison(disease_id_1, disease_id_2)

        st.markdown("---")

        # 分析建议
        st.subheader("💡 优化建议")

        st.info("""
        **基于对比结果的优化方向**：

        1. **相同特征较多**：
           - 可能导致这两个疾病容易混淆
           - 需要增强区分性特征的权重
           - 考虑添加排除规则

        2. **不同特征较多**：
           - 疾病差异明显，不太可能误诊
           - 如果仍有误诊案例，需检查VLM特征提取准确性

        3. **关键特征差异**：
           - 识别哪些特征是区分这两个疾病的关键
           - 在评分算法中适当提高这些特征的权重

        4. **同义词问题**：
           - 检查是否存在同义词映射导致的特征值模糊
           - 优化同义词列表，减少歧义
        """)

    # 清空对比列表
    if st.button("🗑️ 清空对比列表", key="clear_comparison"):
        st.session_state.comparison_disease_1 = None
        st.session_state.comparison_disease_2 = None
        st.rerun()

# ===== 侧边栏：知识库信息 =====
with st.sidebar:
    st.header("📚 知识库信息")

    kb_service = get_knowledge_service()
    version_info = kb_service.get_ontology_version_info()

    st.markdown(f"**版本**: {version_info['version']}")
    st.markdown(f"**Git Commit**: `{version_info['git_commit']}`")

    st.markdown("---")

    st.subheader("📊 统计")

    disease_count = len(kb_service.diseases)
    feature_count = len(kb_service.feature_ontology)
    genera_count = len(kb_service.get_all_genera())

    st.metric("疾病数", disease_count)
    st.metric("特征类型数", feature_count)
    st.metric("宿主属种数", genera_count)

    st.markdown("---")

    st.subheader("💡 快速操作")

    if st.session_state.selected_disease_id:
        st.info(f"当前疾病: {st.session_state.selected_disease_id}")

        if st.button("清除选择", use_container_width=True):
            st.session_state.selected_disease_id = None
            st.rerun()

    st.markdown("---")

    # 说明信息
    with st.expander("ℹ️ 使用说明", expanded=False):
        st.markdown("""
        **知识库管理功能**：

        1. **疾病列表**：
           - 查看所有疾病定义
           - 按宿主植物筛选
           - 快速选择疾病查看详情

        2. **疾病详情**：
           - 查看完整的疾病定义JSON
           - 浏览特征向量（Major/Minor/Optional）
           - 查看治疗建议
           - 下载疾病定义文件

        3. **特征本体**：
           - 浏览所有特征类型
           - 查看可选值和同义词
           - 下载完整本体文件

        4. **疾病对比**：
           - 对比两个疾病的特征差异
           - 识别容易混淆的疾病对
           - 获取优化建议

        **注意**：
        - MVP版本为只读展示
        - 暂不支持直接编辑知识库
        - 需要修改时，请直接编辑JSON文件
        """)
