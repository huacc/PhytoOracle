"""
统计分析页面（增强版）

提供全局统计、图表可视化、误诊分析、准确率趋势图、数据导出等功能。
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

from components.statistics_charts import (
    render_statistics_cards,
    render_confidence_distribution,
    render_genus_distribution,
    render_confusion_matrix,
    render_confidence_score_histogram,
    render_disease_distribution_pie,
)
from models import BatchDiagnosisResult
from services.history_manager import get_history_manager

# 页面配置
st.set_page_config(
    page_title="统计分析 - PhytoOracle",
    page_icon="📊",
    layout="wide"
)

# 页面标题
st.title("📊 统计分析")
st.caption("查看批量推理的全局统计、可视化分析和准确率趋势")

st.markdown("---")

# 初始化历史管理器
HistoryManager = get_history_manager()
HistoryManager.initialize_session_state()

# 检查是否有批量推理数据或历史数据
batch_result = st.session_state.get("batch_result")
history_items = HistoryManager.get_all_history_items()

# 数据源选择
data_source = None
if batch_result and history_items:
    data_source = st.radio(
        "选择数据源",
        options=["batch", "history", "combined"],
        format_func=lambda x: {
            "batch": "当前批量推理结果",
            "history": "历史推理记录",
            "combined": "合并所有数据"
        }[x],
        horizontal=True
    )
elif batch_result:
    data_source = "batch"
    st.info("💡 当前显示：批量推理结果")
elif history_items:
    data_source = "history"
    st.info("💡 当前显示：历史推理记录")
else:
    data_source = None

if data_source is None:
    st.warning("⚠️ 暂无推理数据")
    st.info("💡 请先访问「推理调试中心」或「批量验证中心」页面，完成推理后再查看统计分析")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ 前往推理调试中心", type="primary"):
            st.switch_page("pages/1_推理调试中心.py")
    with col2:
        if st.button("➡️ 前往批量验证中心", type="primary"):
            st.switch_page("pages/2_批量验证中心.py")

else:
    # 准备数据
    if data_source == "batch":
        items = batch_result.items
        statistics = batch_result.statistics
        confusion_matrix = batch_result.confusion_matrix
    elif data_source == "history":
        items = history_items
        statistics = None  # 需要重新计算
        confusion_matrix = None
    else:  # combined
        # 合并批量和历史数据
        items = list(batch_result.items) if batch_result else []
        items.extend(history_items)
        # 去重（基于image_id）
        seen_ids = set()
        unique_items = []
        for item in items:
            if item.image_id not in seen_ids:
                unique_items.append(item)
                seen_ids.add(item.image_id)
        items = unique_items
        statistics = None
        confusion_matrix = None

    # 如果statistics为None，重新计算
    if statistics is None:
        from services.batch_diagnosis_service import BatchDiagnosisService
        service = BatchDiagnosisService()
        statistics = service.calculate_statistics(items)
        confusion_matrix = service.calculate_confusion_matrix(items)

    # ===== 全局统计卡片 =====
    if statistics:
        render_statistics_cards(statistics)
    else:
        st.info("暂无统计数据")

    st.markdown("---")

    # ===== Tab布局：多种分析视图 =====
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 分布分析",
        "🔥 混淆矩阵",
        "📉 置信度分析",
        "⚠️ 误诊分析",
        "📈 准确率趋势"
    ])

    # ===== Tab 1: 分布分析 =====
    with tab1:
        st.subheader("📊 数据分布分析")

        col1, col2 = st.columns(2)

        with col1:
            # 按置信度级别统计
            if statistics:
                render_confidence_distribution(statistics)
            else:
                st.info("暂无数据")

        with col2:
            # 按花卉属统计
            if statistics:
                render_genus_distribution(statistics)
            else:
                st.info("暂无数据")

        st.markdown("---")

        # 诊断疾病分布饼图
        render_disease_distribution_pie(items)

    # ===== Tab 2: 混淆矩阵 =====
    with tab2:
        st.subheader("🔥 混淆矩阵分析")

        if confusion_matrix:
            render_confusion_matrix(confusion_matrix)

            st.markdown("---")

            # 显示混淆矩阵解读
            st.info("""
            **混淆矩阵解读**：

            - **对角线元素**：表示预测正确的样本数（实际疾病 = 预测疾病）
            - **非对角线元素**：表示预测错误的样本数
            - **行（纵轴）**：实际疾病
            - **列（横轴）**：预测疾病

            例如：如果矩阵中 (玫瑰黑斑病, 玫瑰白粉病) 位置的值为 2，
            表示有 2 个实际为玫瑰黑斑病的样本被误诊为玫瑰白粉病。
            """)

        else:
            st.warning("⚠️ 暂无混淆矩阵数据")
            st.info("💡 提示：需要至少完成部分图片的标注后才能生成混淆矩阵")

    # ===== Tab 3: 置信度分析 =====
    with tab3:
        st.subheader("📉 置信度分数分析")

        render_confidence_score_histogram(items)

        st.markdown("---")

        # 置信度阈值分析
        st.markdown("### 🎯 置信度阈值分析")

        st.info("""
        **当前阈值设定**：

        - **确诊 (Confirmed)**: ≥ 0.85
        - **疑似 (Suspected)**: 0.65 ~ 0.85
        - **不太可能 (Unlikely)**: < 0.65

        **优化建议**：
        - 观察不同置信度级别的准确率分布
        - 如果 "疑似" 级别的准确率较高，可以考虑降低 "确诊" 阈值
        - 如果 "不太可能" 级别中仍有正确诊断，需要优化特征提取或评分算法
        """)

    # ===== Tab 4: 误诊分析 =====
    with tab4:
        st.subheader("⚠️ 误诊案例分析")

        # 筛选误诊案例
        incorrect_items = [
            item for item in items
            if item.annotation_status == "incorrect"
        ]

        if incorrect_items:
            st.metric("误诊案例数", len(incorrect_items))

            st.markdown("---")

            # 显示误诊案例表格
            st.markdown("### 误诊案例列表")

            misdiagnosis_data = []
            for item in incorrect_items:
                misdiagnosis_data.append({
                    "图片名称": item.image_name,
                    "花卉属": item.flower_genus,
                    "预测疾病": item.disease_name,
                    "实际疾病": item.actual_disease_name,
                    "置信度": f"{item.confidence_score:.2f} ({item.confidence_level})",
                    "备注": item.notes or "-"
                })

            df = pd.DataFrame(misdiagnosis_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # 误诊模式分析
            st.markdown("### 🔍 误诊模式分析")

            # 统计高频误诊模式
            misdiagnosis_patterns = {}
            for item in incorrect_items:
                pattern_key = f"{item.actual_disease_name} → {item.disease_name}"
                misdiagnosis_patterns[pattern_key] = misdiagnosis_patterns.get(pattern_key, 0) + 1

            if misdiagnosis_patterns:
                st.markdown("**高频误诊模式**：")

                pattern_df = pd.DataFrame([
                    {
                        "误诊模式": pattern,
                        "出现次数": count,
                        "占比": f"{count/len(incorrect_items)*100:.1f}%"
                    }
                    for pattern, count in sorted(
                        misdiagnosis_patterns.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                ])

                st.dataframe(pattern_df, use_container_width=True, hide_index=True)

                st.markdown("---")

                # 优化建议
                st.markdown("### 💡 优化建议")

                st.info("""
                **针对高频误诊模式的优化方向**：

                1. **特征对比分析**：
                   - 对比误诊疾病对（如 A → B）的特征向量差异
                   - 识别容易混淆的特征（如颜色、形状、质地）

                2. **知识库调整**：
                   - 增强区分性特征的权重
                   - 添加排除规则（如果特征X=值Y，则排除疾病Z）
                   - 补充同义词映射，减少模糊匹配误差

                3. **VLM提示词优化**：
                   - 针对易混淆特征，优化Q1-Q6的提示词描述
                   - 添加对比性描述（如 "区分黑色和深褐色"）

                4. **置信度校准**：
                   - 如果高置信度误诊较多，需要重新校准评分函数
                   - 考虑引入不确定性量化机制
                """)

            # 导出误诊案例
            col1, col2, col3 = st.columns(3)
            with col1:
                csv_data = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 导出误诊案例CSV",
                    data=csv_data,
                    file_name=f"misdiagnosis_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                json_data = df.to_json(orient="records", force_ascii=False, indent=2)
                st.download_button(
                    label="📥 导出误诊案例JSON",
                    data=json_data,
                    file_name=f"misdiagnosis_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

        else:
            st.success("🎉 没有误诊案例！")

            if statistics and statistics.annotated_count > 0:
                st.balloons()
                st.markdown("""
                **恭喜！所有已标注的样本都诊断正确！**

                这说明：
                - 推理算法性能优秀
                - 知识库质量高
                - VLM特征提取准确

                继续保持！
                """)
            else:
                st.info("💡 提示：完成标注后可查看误诊分析")

    # ===== Tab 5: 准确率趋势 =====
    with tab5:
        st.subheader("📈 准确率趋势分析")

        # 生成模拟的历史趋势数据
        st.info("💡 以下为模拟数据，展示准确率随时间变化的趋势分析")

        # 生成过去30天的模拟数据
        trend_data = generate_accuracy_trend_data(days=30, current_accuracy=statistics.accuracy_rate if statistics and statistics.accuracy_rate else 0.8)

        # 绘制趋势图
        import plotly.graph_objects as go

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=trend_data["date"],
            y=trend_data["accuracy"],
            mode='lines+markers',
            name='准确率',
            line=dict(color='green', width=2),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title="准确率趋势图（过去30天）",
            xaxis_title="日期",
            yaxis_title="准确率 (%)",
            yaxis=dict(range=[0, 100]),
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 筛选器
        st.markdown("### 🔍 筛选分析")

        col1, col2 = st.columns(2)

        with col1:
            # 按花卉属筛选
            selected_genus = st.selectbox(
                "按花卉属筛选",
                options=["全部"] + sorted(list(set(item.flower_genus for item in items))),
                help="查看特定花卉属的准确率趋势"
            )

        with col2:
            # 按疾病类型筛选
            selected_disease = st.selectbox(
                "按疾病类型筛选",
                options=["全部"] + sorted(list(set(item.disease_name for item in items))),
                help="查看特定疾病的准确率趋势"
            )

        # 筛选后的数据（模拟）
        if selected_genus != "全部" or selected_disease != "全部":
            st.info(f"当前筛选：花卉属={selected_genus}, 疾病类型={selected_disease}")

            # 生成筛选后的趋势数据（模拟）
            filtered_trend_data = generate_accuracy_trend_data(
                days=30,
                current_accuracy=random.uniform(0.75, 0.95)
            )

            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(
                x=filtered_trend_data["date"],
                y=filtered_trend_data["accuracy"],
                mode='lines+markers',
                name='筛选后准确率',
                line=dict(color='orange', width=2),
                marker=dict(size=8)
            ))

            fig2.update_layout(
                title=f"筛选后的准确率趋势",
                xaxis_title="日期",
                yaxis_title="准确率 (%)",
                yaxis=dict(range=[0, 100]),
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")

        # 趋势分析摘要
        st.markdown("### 📝 趋势分析摘要")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "当前准确率",
                f"{trend_data['accuracy'][-1]:.1f}%",
                delta=f"{trend_data['accuracy'][-1] - trend_data['accuracy'][-7]:.1f}% (较7天前)"
            )

        with col2:
            avg_accuracy = sum(trend_data["accuracy"]) / len(trend_data["accuracy"])
            st.metric(
                "30天平均准确率",
                f"{avg_accuracy:.1f}%"
            )

        with col3:
            max_accuracy = max(trend_data["accuracy"])
            st.metric(
                "历史最高准确率",
                f"{max_accuracy:.1f}%"
            )

        # 导出趋势数据
        st.markdown("---")
        st.markdown("### 💾 导出趋势数据")

        trend_df = pd.DataFrame({
            "日期": trend_data["date"],
            "准确率 (%)": trend_data["accuracy"],
            "诊断量": trend_data["count"]
        })

        col1, col2 = st.columns(2)
        with col1:
            csv_data = trend_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 导出趋势数据CSV",
                data=csv_data,
                file_name=f"accuracy_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            json_data = trend_df.to_json(orient="records", force_ascii=False, indent=2)
            st.download_button(
                label="📥 导出趋势数据JSON",
                data=json_data,
                file_name=f"accuracy_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


def generate_accuracy_trend_data(days: int = 30, current_accuracy: float = 0.8):
    """
    生成模拟的准确率趋势数据

    Args:
        days: 天数
        current_accuracy: 当前准确率（0-1）

    Returns:
        包含日期、准确率、诊断量的字典
    """
    dates = []
    accuracies = []
    counts = []

    # 起始准确率（比当前低一些）
    start_accuracy = max(0.5, current_accuracy - random.uniform(0.1, 0.2))

    for i in range(days):
        date = datetime.now() - timedelta(days=days - i - 1)
        dates.append(date.strftime("%Y-%m-%d"))

        # 准确率逐渐提升（带随机波动）
        progress = i / (days - 1)
        accuracy = start_accuracy + (current_accuracy - start_accuracy) * progress
        accuracy += random.uniform(-0.05, 0.05)  # 随机波动
        accuracy = max(0, min(1, accuracy))  # 限制在0-1之间
        accuracies.append(accuracy * 100)  # 转换为百分比

        # 诊断量（模拟）
        count = random.randint(5, 20)
        counts.append(count)

    return {
        "date": dates,
        "accuracy": accuracies,
        "count": counts
    }


# ===== 侧边栏：数据摘要 =====
with st.sidebar:
    st.header("📋 数据摘要")

    if data_source:
        st.metric("数据源", {
            "batch": "批量推理",
            "history": "历史记录",
            "combined": "合并数据"
        }[data_source])

        st.metric("总样本数", len(items))

        if statistics:
            st.markdown("---")
            st.subheader("标注进度")

            st.metric("已标注", statistics.annotated_count)
            st.metric("未标注", statistics.unannotated_count)

            if statistics.accuracy_rate is not None:
                st.markdown("---")
                st.subheader("准确率")
                st.metric("整体准确率", f"{statistics.accuracy_rate*100:.1f}%")
                st.metric("正确数", statistics.correct_count)
                st.metric("错误数", statistics.incorrect_count)

        st.markdown("---")

        # 刷新数据
        if st.button("🔄 刷新统计", use_container_width=True):
            st.rerun()

        # 导出全部数据
        st.markdown("---")
        st.subheader("📥 导出全部数据")

        all_data = []
        for item in items:
            all_data.append({
                "图片名称": item.image_name,
                "花卉属": item.flower_genus,
                "诊断疾病": item.disease_name,
                "置信度分数": item.confidence_score,
                "置信度级别": item.confidence_level,
                "标注状态": item.annotation_status or "未标注",
                "实际疾病": item.actual_disease_name or "-",
                "备注": item.notes or "-",
                "诊断时间": item.diagnosed_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        df_all = pd.DataFrame(all_data)

        csv_all = df_all.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 导出全部数据CSV",
            data=csv_all,
            file_name=f"all_diagnosis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:
        st.info("暂无数据")
