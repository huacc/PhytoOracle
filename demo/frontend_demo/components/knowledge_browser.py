"""
知识库浏览组件

提供疾病列表、疾病详情、特征本体浏览等功能。
"""
import streamlit as st
import json
from typing import Dict, List, Optional

from services.mock_knowledge_service import get_knowledge_service


def render_disease_list() -> Optional[str]:
    """
    渲染疾病列表

    Returns:
        选中的疾病ID，如果没有选中则返回None
    """
    st.subheader("🦠 疾病列表")

    kb_service = get_knowledge_service()
    diseases = kb_service.diseases

    if not diseases:
        st.warning("知识库中暂无疾病定义")
        return None

    # 创建疾病表格数据
    table_data = []
    for disease_id, disease_data in diseases.items():
        table_data.append({
            "疾病ID": disease_id,
            "疾病名称": disease_data["disease_name"],
            "英文名称": disease_data["disease_name_en"],
            "宿主植物": ", ".join(disease_data["host_plants"]),
            "版本": disease_data["version"],
            "病原体": disease_data["pathogen"]["scientific_name"]
        })

    # 显示表格
    import pandas as pd
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 选择疾病查看详情
    st.markdown("---")
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_disease_name = st.selectbox(
            "选择疾病查看详情",
            options=[d["disease_name"] for d in diseases.values()],
            key="disease_selector"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📖 查看详情", use_container_width=True):
            # 找到对应的disease_id
            for disease_id, disease_data in diseases.items():
                if disease_data["disease_name"] == selected_disease_name:
                    return disease_id

    return None


def render_disease_detail(disease_id: str) -> None:
    """
    渲染疾病详情

    Args:
        disease_id: 疾病ID
    """
    kb_service = get_knowledge_service()
    disease_data = kb_service.get_disease(disease_id)

    if not disease_data:
        st.error(f"未找到疾病: {disease_id}")
        return

    st.subheader(f"🔍 疾病详情: {disease_data['disease_name']}")

    # 基本信息
    with st.expander("📋 基本信息", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**疾病ID**: `{disease_id}`")
            st.markdown(f"**中文名称**: {disease_data['disease_name']}")
            st.markdown(f"**英文名称**: {disease_data['disease_name_en']}")
            st.markdown(f"**版本**: {disease_data['version']}")

        with col2:
            st.markdown(f"**宿主植物**: {', '.join(disease_data['host_plants'])}")
            st.markdown(f"**病原体**: {disease_data['pathogen']['scientific_name']}")
            # 显示病原体俗名（如果存在）
            if 'common_name' in disease_data['pathogen']:
                st.markdown(f"**病原俗名**: {disease_data['pathogen']['common_name']}")

    # 特征向量
    with st.expander("🧬 特征向量", expanded=True):
        feature_vector = disease_data["feature_vector"]

        st.markdown("#### 主要特征 (Major Features)")
        major_features = feature_vector.get("major", {})
        if major_features:
            for feature_key, feature_value in major_features.items():
                st.markdown(f"- **{feature_key}**: `{feature_value}`")
        else:
            st.info("无主要特征")

        st.markdown("#### 次要特征 (Minor Features)")
        minor_features = feature_vector.get("minor", {})
        if minor_features:
            for feature_key, feature_value in minor_features.items():
                st.markdown(f"- **{feature_key}**: `{feature_value}`")
        else:
            st.info("无次要特征")

        st.markdown("#### 可选特征 (Optional Features)")
        optional_features = feature_vector.get("optional", {})
        if optional_features:
            for feature_key, feature_value in optional_features.items():
                st.markdown(f"- **{feature_key}**: `{feature_value}`")
        else:
            st.info("无可选特征")

    # 治疗建议
    with st.expander("💊 治疗建议", expanded=True):
        treatment_suggestions = disease_data.get("treatment_suggestions", [])
        if treatment_suggestions:
            for idx, suggestion in enumerate(treatment_suggestions, 1):
                st.markdown(f"{idx}. {suggestion}")
        else:
            st.info("暂无治疗建议")

    # 完整JSON
    with st.expander("📄 完整JSON定义", expanded=False):
        st.json(disease_data)

        # 提供下载按钮
        json_str = json.dumps(disease_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 下载JSON",
            data=json_str.encode('utf-8'),
            file_name=f"{disease_id}_{disease_data['version']}.json",
            mime="application/json"
        )


def render_feature_ontology_browser() -> None:
    """渲染特征本体浏览器"""
    st.subheader("🌳 特征本体浏览")

    kb_service = get_knowledge_service()

    if not kb_service.feature_ontology:
        st.warning("特征本体未加载")
        return

    # 显示版本信息
    version_info = kb_service.get_ontology_version_info()
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📦 版本: {version_info['version']}")
    with col2:
        st.info(f"🔖 Git Commit: `{version_info['git_commit']}`")

    st.markdown("---")

    # 获取features字典
    features_dict = kb_service.feature_ontology.get('features', {})

    if not features_dict:
        st.warning("特征本体中没有定义任何特征")
        return

    # 遍历所有特征类型
    for feature_key, feature_data in features_dict.items():
        with st.expander(f"🔹 {feature_key}", expanded=False):
            # 特征描述
            if "description" in feature_data:
                st.markdown(f"**描述**: {feature_data['description']}")

            # 可选值
            st.markdown("**可选值**:")
            values = feature_data.get("values", [])
            if values:
                for value in values:
                    st.markdown(f"- `{value}`")
            else:
                st.info("无预定义值")

            # 同义词
            synonyms = feature_data.get("synonyms", {})
            if synonyms:
                st.markdown("**同义词映射**:")
                for canonical_value, synonym_list in synonyms.items():
                    st.markdown(f"- **{canonical_value}**: {', '.join([f'`{s}`' for s in synonym_list])}")
            else:
                st.info("无同义词定义")

    # 完整JSON下载
    st.markdown("---")
    st.subheader("📥 导出完整本体")

    json_str = json.dumps(kb_service.feature_ontology, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 下载 Feature Ontology JSON",
        data=json_str.encode('utf-8'),
        file_name="feature_ontology.json",
        mime="application/json"
    )


def render_knowledge_base_summary() -> None:
    """渲染知识库摘要统计"""
    st.subheader("📊 知识库摘要")

    kb_service = get_knowledge_service()

    col1, col2, col3 = st.columns(3)

    with col1:
        disease_count = len(kb_service.diseases)
        st.metric("疾病总数", disease_count)

    with col2:
        genera_count = len(kb_service.get_all_genera())
        st.metric("宿主属种数", genera_count)

    with col3:
        feature_count = len(kb_service.feature_ontology)
        st.metric("特征类型数", feature_count)

    # 按属种分布
    st.markdown("---")
    st.markdown("### 按宿主植物分布")

    genus_distribution = {}
    for disease_data in kb_service.diseases.values():
        for genus in disease_data["host_plants"]:
            genus_distribution[genus] = genus_distribution.get(genus, 0) + 1

    import pandas as pd
    df = pd.DataFrame([
        {"宿主属": genus, "疾病数量": count}
        for genus, count in sorted(genus_distribution.items(), key=lambda x: x[1], reverse=True)
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_ontology_comparison(disease_id_1: str, disease_id_2: str) -> None:
    """
    渲染两个疾病的特征对比

    Args:
        disease_id_1: 疾病1的ID
        disease_id_2: 疾病2的ID
    """
    st.subheader("🔄 疾病特征对比")

    kb_service = get_knowledge_service()

    disease_1 = kb_service.get_disease(disease_id_1)
    disease_2 = kb_service.get_disease(disease_id_2)

    if not disease_1 or not disease_2:
        st.error("无法加载疾病数据")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {disease_1['disease_name']}")
        st.markdown(f"**版本**: {disease_1['version']}")

    with col2:
        st.markdown(f"### {disease_2['disease_name']}")
        st.markdown(f"**版本**: {disease_2['version']}")

    st.markdown("---")

    # 对比特征向量
    feature_vector_1 = disease_1["feature_vector"]
    feature_vector_2 = disease_2["feature_vector"]

    all_features_1 = {
        **feature_vector_1.get("major", {}),
        **feature_vector_1.get("minor", {}),
        **feature_vector_1.get("optional", {})
    }

    all_features_2 = {
        **feature_vector_2.get("major", {}),
        **feature_vector_2.get("minor", {}),
        **feature_vector_2.get("optional", {})
    }

    # 获取所有特征键
    all_keys = set(all_features_1.keys()) | set(all_features_2.keys())

    # 创建对比表格
    comparison_data = []
    for feature_key in sorted(all_keys):
        value_1 = all_features_1.get(feature_key, "-")
        value_2 = all_features_2.get(feature_key, "-")

        # 标记差异
        if value_1 == value_2:
            difference = "✅ 相同"
        else:
            difference = "❌ 不同"

        comparison_data.append({
            "特征": feature_key,
            disease_1['disease_name']: value_1,
            disease_2['disease_name']: value_2,
            "差异": difference
        })

    import pandas as pd
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 统计差异
    different_count = sum(1 for row in comparison_data if row["差异"] == "❌ 不同")
    same_count = len(comparison_data) - different_count

    col1, col2 = st.columns(2)
    with col1:
        st.metric("相同特征", same_count)
    with col2:
        st.metric("不同特征", different_count)
