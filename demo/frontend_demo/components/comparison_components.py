"""
图片对比组件

提供图片对比、差异高亮、差异分析等功能。
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
import sys
from pathlib import Path

# 添加父目录到 sys.path 以支持导入
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from models import BatchDiagnosisItem, DiagnosisResult
import pandas as pd


def render_image_comparison_selector(
    available_items: List[BatchDiagnosisItem],
) -> List[str]:
    """
    渲染图片选择器（从历史记录中选择2-4张图片进行对比）

    Args:
        available_items: 可用的批量推理结果列表

    Returns:
        选中的图片ID列表
    """
    st.subheader("📋 选择图片进行对比")
    st.caption("从历史推理记录中选择 2-4 张图片进行详细对比分析")

    if not available_items:
        st.warning("⚠️ 暂无历史推理数据")
        st.info("💡 请先在「单张调试」或「批量验证」中完成推理后再使用对比功能")
        return []

    # 创建筛选器
    col1, col2, col3 = st.columns(3)

    with col1:
        # 按花卉属筛选
        all_genera = sorted(list(set(item.flower_genus for item in available_items)))
        selected_genera = st.multiselect(
            "按花卉属筛选",
            options=all_genera,
            default=all_genera,
            help="选择要显示的花卉属"
        )

    with col2:
        # 按置信度级别筛选
        all_confidence_levels = ["confirmed", "suspected", "unlikely"]
        level_name_map = {
            "confirmed": "确诊",
            "suspected": "疑似",
            "unlikely": "不太可能"
        }
        selected_levels = st.multiselect(
            "按置信度级别筛选",
            options=all_confidence_levels,
            format_func=lambda x: level_name_map.get(x, x),
            default=all_confidence_levels,
            help="选择要显示的置信度级别"
        )

    with col3:
        # 按准确性筛选
        all_annotation_statuses = ["correct", "incorrect", "uncertain", None]
        status_name_map = {
            "correct": "✅ 正确",
            "incorrect": "❌ 错误",
            "uncertain": "❓ 不确定",
            None: "⏸️ 未标注"
        }
        selected_statuses = st.multiselect(
            "按准确性筛选",
            options=all_annotation_statuses,
            format_func=lambda x: status_name_map.get(x, str(x)),
            default=all_annotation_statuses,
            help="选择要显示的标注状态"
        )

    # 应用筛选
    filtered_items = [
        item for item in available_items
        if item.flower_genus in selected_genera
        and item.confidence_level in selected_levels
        and item.annotation_status in selected_statuses
    ]

    if not filtered_items:
        st.info("🔍 没有符合筛选条件的图片")
        return []

    st.markdown(f"**筛选结果**: 找到 {len(filtered_items)} 张图片")

    # 创建选择器
    st.markdown("---")
    st.markdown("### 选择要对比的图片（2-4张）")

    # 准备选项数据
    options = []
    for item in filtered_items:
        status_icon = status_name_map.get(item.annotation_status, "⏸️ 未标注")
        label = f"{item.image_name} | {item.flower_genus} | {item.disease_name} | {status_icon}"
        options.append((item.image_id, label))

    # 使用multiselect
    selected_image_ids = st.multiselect(
        "选择图片",
        options=[opt[0] for opt in options],
        format_func=lambda x: next(opt[1] for opt in options if opt[0] == x),
        max_selections=4,
        help="最少选择2张，最多选择4张图片进行对比"
    )

    # 显示选择提示
    if len(selected_image_ids) < 2:
        st.info("💡 请至少选择 2 张图片进行对比")
    elif len(selected_image_ids) > 4:
        st.warning("⚠️ 最多只能选择 4 张图片进行对比")
    else:
        st.success(f"✅ 已选择 {len(selected_image_ids)} 张图片")

    return selected_image_ids


def render_side_by_side_comparison(
    items: List[BatchDiagnosisItem],
    diagnosis_results: Dict[str, DiagnosisResult]
) -> None:
    """
    并排展示选中的图片及其推理结果，并高亮差异

    Args:
        items: 要对比的批量推理结果项列表
        diagnosis_results: 诊断结果字典，键为image_id
    """
    if not items or len(items) < 2:
        return

    st.subheader("🔍 并排对比分析")
    st.caption(f"对比 {len(items)} 张图片的推理结果和关键特征")

    # 创建列布局
    cols = st.columns(len(items))

    # 收集所有特征用于差异检测
    all_features: Dict[str, List[Any]] = {
        "flower_genus": [],
        "abnormality": [],
        "symptom_type": [],
        "color_center": [],
        "color_border": [],
        "diagnosis": [],
        "confidence_level": [],
        "annotation_status": []
    }

    # 收集数据
    for item in items:
        all_features["flower_genus"].append(item.flower_genus)
        all_features["diagnosis"].append(item.disease_name)
        all_features["confidence_level"].append(item.confidence_level)
        all_features["annotation_status"].append(item.annotation_status)

        # 从诊断结果中提取特征
        diagnosis = diagnosis_results.get(item.image_id)
        if diagnosis:
            all_features["abnormality"].append(diagnosis.q0_sequence.get("q0_5_abnormality", {}).get("choice", "N/A"))
            features = diagnosis.feature_extraction
            all_features["symptom_type"].append(features.get("symptom_type", {}).get("choice", "N/A"))
            all_features["color_center"].append(features.get("color_center", {}).get("choice", "N/A"))
            all_features["color_border"].append(features.get("color_border", {}).get("choice", "N/A"))
        else:
            all_features["abnormality"].append("N/A")
            all_features["symptom_type"].append("N/A")
            all_features["color_center"].append("N/A")
            all_features["color_border"].append("N/A")

    # 检测差异
    differences = detect_differences(all_features)

    # 并排展示
    for idx, (col, item) in enumerate(zip(cols, items)):
        with col:
            # 图片预览
            st.markdown(f"#### 图片 {idx + 1}")
            st.markdown(f"**{item.image_name}**")

            # 显示图片占位符
            st.info(f"📷 {item.image_name}")

            # Q0.2 花属
            render_comparison_field(
                label="Q0.2 花卉属",
                value=item.flower_genus,
                is_different="flower_genus" in differences,
                idx=idx,
                all_values=all_features["flower_genus"]
            )

            # Q0.5 异常判断
            render_comparison_field(
                label="Q0.5 异常判断",
                value=all_features["abnormality"][idx],
                is_different="abnormality" in differences,
                idx=idx,
                all_values=all_features["abnormality"]
            )

            st.markdown("---")

            # Q1-Q6 关键特征
            st.markdown("**关键特征**")
            render_comparison_field(
                label="症状类型",
                value=all_features["symptom_type"][idx],
                is_different="symptom_type" in differences,
                idx=idx,
                all_values=all_features["symptom_type"],
                compact=True
            )
            render_comparison_field(
                label="中心颜色",
                value=all_features["color_center"][idx],
                is_different="color_center" in differences,
                idx=idx,
                all_values=all_features["color_center"],
                compact=True
            )
            render_comparison_field(
                label="边缘颜色",
                value=all_features["color_border"][idx],
                is_different="color_border" in differences,
                idx=idx,
                all_values=all_features["color_border"],
                compact=True
            )

            st.markdown("---")

            # 诊断结果
            render_comparison_field(
                label="诊断结果",
                value=item.disease_name,
                is_different="diagnosis" in differences,
                idx=idx,
                all_values=all_features["diagnosis"]
            )

            # 置信度
            confidence_text = f"{item.confidence_score:.3f} ({item.confidence_level})"
            render_comparison_field(
                label="置信度",
                value=confidence_text,
                is_different="confidence_level" in differences,
                idx=idx,
                all_values=[f"{items[i].confidence_score:.3f} ({items[i].confidence_level})" for i in range(len(items))]
            )

            # 准确性标注
            status_map = {
                "correct": "✅ 正确",
                "incorrect": "❌ 错误",
                "uncertain": "❓ 不确定",
                None: "⏸️ 未标注"
            }
            status_text = status_map.get(item.annotation_status, "⏸️ 未标注")
            render_comparison_field(
                label="准确性",
                value=status_text,
                is_different="annotation_status" in differences,
                idx=idx,
                all_values=[status_map.get(items[i].annotation_status, "⏸️ 未标注") for i in range(len(items))]
            )


def render_comparison_field(
    label: str,
    value: Any,
    is_different: bool,
    idx: int,
    all_values: List[Any],
    compact: bool = False
) -> None:
    """
    渲染对比字段，并根据差异状态显示不同样式

    Args:
        label: 字段标签
        value: 字段值
        is_different: 是否有差异
        idx: 当前索引
        all_values: 所有值列表（用于确定当前值是否为少数）
        compact: 是否使用紧凑样式
    """
    if not is_different:
        # 无差异：普通样式
        if compact:
            st.markdown(f"- **{label}**: `{value}`")
        else:
            st.markdown(f"**{label}**: `{value}`")
    else:
        # 有差异：高亮显示
        # 判断当前值是否为少数（不同于多数值）
        from collections import Counter
        value_counts = Counter(all_values)
        most_common_value = value_counts.most_common(1)[0][0] if value_counts else None

        if value != most_common_value:
            # 当前值与多数不同：红色高亮
            color = "#ff4444"
            icon = "⚠️"
        else:
            # 当前值与多数相同：绿色高亮
            color = "#44ff44"
            icon = "✓"

        if compact:
            st.markdown(
                f"- **{label}**: <span style='background-color: {color}; padding: 2px 6px; border-radius: 3px;'>"
                f"{icon} {value}</span>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"**{label}**: <span style='background-color: {color}; padding: 4px 8px; border-radius: 4px; "
                f"font-weight: bold;'>{icon} {value}</span>",
                unsafe_allow_html=True
            )


def detect_differences(all_features: Dict[str, List[Any]]) -> List[str]:
    """
    检测哪些特征有差异

    Args:
        all_features: 所有特征的字典，键为特征名，值为所有图片的该特征值列表

    Returns:
        有差异的特征名列表
    """
    differences = []
    for feature_key, values in all_features.items():
        # 如果值不全相同，则认为有差异
        if len(set(values)) > 1:
            differences.append(feature_key)
    return differences


def render_difference_analysis(
    items: List[BatchDiagnosisItem],
    diagnosis_results: Dict[str, DiagnosisResult]
) -> None:
    """
    渲染差异分析报告

    Args:
        items: 要对比的批量推理结果项列表
        diagnosis_results: 诊断结果字典
    """
    if not items or len(items) < 2:
        return

    st.subheader("📊 差异分析报告")

    # 收集特征数据
    all_features: Dict[str, List[Any]] = {
        "flower_genus": [],
        "abnormality": [],
        "symptom_type": [],
        "color_center": [],
        "color_border": [],
        "diagnosis": [],
        "confidence_level": [],
        "annotation_status": []
    }

    for item in items:
        all_features["flower_genus"].append(item.flower_genus)
        all_features["diagnosis"].append(item.disease_name)
        all_features["confidence_level"].append(item.confidence_level)
        all_features["annotation_status"].append(item.annotation_status)

        diagnosis = diagnosis_results.get(item.image_id)
        if diagnosis:
            all_features["abnormality"].append(diagnosis.q0_sequence.get("q0_5_abnormality", {}).get("choice", "N/A"))
            features = diagnosis.feature_extraction
            all_features["symptom_type"].append(features.get("symptom_type", {}).get("choice", "N/A"))
            all_features["color_center"].append(features.get("color_center", {}).get("choice", "N/A"))
            all_features["color_border"].append(features.get("color_border", {}).get("choice", "N/A"))
        else:
            all_features["abnormality"].append("N/A")
            all_features["symptom_type"].append("N/A")
            all_features["color_center"].append("N/A")
            all_features["color_border"].append("N/A")

    # 检测差异
    differences = detect_differences(all_features)

    # 生成差异表格
    st.markdown("### 🔍 特征差异统计")

    diff_data = []
    for feature_key, values in all_features.items():
        unique_values = set(values)
        if len(unique_values) > 1:
            feature_name_map = {
                "flower_genus": "花卉属",
                "abnormality": "异常判断",
                "symptom_type": "症状类型",
                "color_center": "中心颜色",
                "color_border": "边缘颜色",
                "diagnosis": "诊断结果",
                "confidence_level": "置信度级别",
                "annotation_status": "准确性"
            }
            diff_data.append({
                "特征": feature_name_map.get(feature_key, feature_key),
                "不同值数量": len(unique_values),
                "具体值": ", ".join(str(v) for v in unique_values)
            })

    if diff_data:
        df = pd.DataFrame(diff_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ 所有图片的特征完全一致！")

    st.markdown("---")

    # 相同点和差异点分析
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ 相同点")
        same_features = [k for k in all_features.keys() if k not in differences]
        if same_features:
            feature_name_map = {
                "flower_genus": "花卉属",
                "abnormality": "异常判断",
                "symptom_type": "症状类型",
                "color_center": "中心颜色",
                "color_border": "边缘颜色",
                "diagnosis": "诊断结果",
                "confidence_level": "置信度级别",
                "annotation_status": "准确性"
            }
            for feature_key in same_features:
                feature_name = feature_name_map.get(feature_key, feature_key)
                value = all_features[feature_key][0]
                st.markdown(f"- **{feature_name}**: `{value}`")
        else:
            st.info("所有特征都存在差异")

    with col2:
        st.markdown("### ⚠️ 差异点")
        if differences:
            feature_name_map = {
                "flower_genus": "花卉属",
                "abnormality": "异常判断",
                "symptom_type": "症状类型",
                "color_center": "中心颜色",
                "color_border": "边缘颜色",
                "diagnosis": "诊断结果",
                "confidence_level": "置信度级别",
                "annotation_status": "准确性"
            }
            for feature_key in differences:
                feature_name = feature_name_map.get(feature_key, feature_key)
                unique_values = list(set(all_features[feature_key]))
                st.markdown(f"- **{feature_name}**: {len(unique_values)} 个不同值")
        else:
            st.success("无差异")

    st.markdown("---")

    # 可能原因和优化建议
    st.markdown("### 💡 差异原因分析与优化建议")

    if not differences:
        st.info("""
        **完全一致的结果表明**：
        - VLM 特征提取稳定
        - 推理算法一致性高
        - 疾病特征明显易识别

        **建议**：继续保持当前配置。
        """)
    else:
        # 根据差异类型提供建议
        suggestions = []

        if "flower_genus" in differences:
            suggestions.append("""
            **花卉属识别差异**：
            - 可能原因：图片质量不同、拍摄角度差异、植物生长阶段不同
            - 优化建议：增强 Q0.2 提示词描述，添加更多植物形态特征识别
            """)

        if "symptom_type" in differences or "color_center" in differences or "color_border" in differences:
            suggestions.append("""
            **症状特征识别差异**：
            - 可能原因：光照条件影响颜色识别、病害发展阶段不同、图片质量差异
            - 优化建议：
              - 提供更详细的颜色描述和对比示例
              - 增加特征提取的 few-shot 示例
              - 考虑引入图像预处理（色彩归一化）
            """)

        if "diagnosis" in differences:
            suggestions.append("""
            **诊断结果差异**：
            - 可能原因：特征识别差异导致评分不同、疾病特征相似度高
            - 优化建议：
              - 检查知识库中相似疾病的区分性特征
              - 调整加权评分函数的权重分配
              - 增加排除规则减少混淆
            """)

        if "annotation_status" in differences:
            suggestions.append("""
            **标注结果不一致**：
            - 可能原因：部分图片诊断正确、部分错误，或部分未标注
            - 优化建议：
              - 优先分析错误案例的特征差异
              - 对比正确和错误案例的置信度分布
              - 考虑引入主动学习机制
            """)

        for suggestion in suggestions:
            st.info(suggestion)
