"""
统计分析图表组件

提供混淆矩阵、准确率分布、统计卡片等可视化组件。
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional
import pandas as pd

from models import BatchStatistics, ConfusionMatrixData, BatchDiagnosisItem


def render_statistics_cards(stats: BatchStatistics) -> None:
    """
    渲染统计卡片

    Args:
        stats: 统计数据
    """
    st.subheader("📈 整体统计")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="总诊断量",
            value=stats.total_count,
            help="批量推理的图片总数"
        )

    with col2:
        st.metric(
            label="已标注",
            value=stats.annotated_count,
            delta=f"{stats.annotated_count/stats.total_count*100:.1f}%" if stats.total_count > 0 else "0%",
            help="已完成人工标注的图片数量"
        )

    with col3:
        if stats.accuracy_rate is not None:
            st.metric(
                label="准确率",
                value=f"{stats.accuracy_rate*100:.1f}%",
                delta=f"{stats.correct_count}/{stats.annotated_count}",
                help="标注为正确的比例"
            )
        else:
            st.metric(
                label="准确率",
                value="-",
                help="暂无已标注数据"
            )

    with col4:
        st.metric(
            label="误诊案例",
            value=stats.incorrect_count,
            delta=f"{stats.incorrect_count/stats.annotated_count*100:.1f}%" if stats.annotated_count > 0 else "0%",
            delta_color="inverse",
            help="标注为错误的图片数量"
        )


def render_confidence_distribution(stats: BatchStatistics) -> None:
    """
    渲染置信度分布图表

    Args:
        stats: 统计数据
    """
    st.subheader("📊 按置信度级别统计")

    if not stats.by_confidence:
        st.info("暂无数据")
        return

    # 准备数据
    levels = []
    totals = []
    annotated_list = []
    correct_list = []
    accuracy_list = []

    for level in ["confirmed", "suspected", "unlikely"]:
        if level in stats.by_confidence:
            data = stats.by_confidence[level]
            levels.append({"confirmed": "确诊", "suspected": "疑似", "unlikely": "不太可能"}[level])
            totals.append(data["total"])
            annotated_list.append(data["annotated"])
            correct_list.append(data["correct"])
            accuracy_list.append(data["accuracy"] * 100 if data["accuracy"] is not None else 0)

    # 创建条形图
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='总数',
        x=levels,
        y=totals,
        text=totals,
        textposition='auto',
        marker_color='lightblue'
    ))

    fig.add_trace(go.Bar(
        name='已标注',
        x=levels,
        y=annotated_list,
        text=annotated_list,
        textposition='auto',
        marker_color='lightgreen'
    ))

    fig.add_trace(go.Bar(
        name='正确',
        x=levels,
        y=correct_list,
        text=correct_list,
        textposition='auto',
        marker_color='green'
    ))

    fig.update_layout(
        barmode='group',
        xaxis_title="置信度级别",
        yaxis_title="数量",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 显示准确率表格
    df = pd.DataFrame({
        "置信度级别": levels,
        "总数": totals,
        "已标注": annotated_list,
        "正确数": correct_list,
        "准确率": [f"{acc:.1f}%" if acc > 0 else "-" for acc in accuracy_list]
    })

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_genus_distribution(stats: BatchStatistics) -> None:
    """
    渲染花卉属分布图表

    Args:
        stats: 统计数据
    """
    st.subheader("🌸 按花卉属统计")

    if not stats.by_genus:
        st.info("暂无数据")
        return

    # 准备数据
    genera = []
    totals = []
    annotated_list = []
    correct_list = []
    accuracy_list = []

    for genus, data in sorted(stats.by_genus.items()):
        genera.append(genus)
        totals.append(data["total"])
        annotated_list.append(data["annotated"])
        correct_list.append(data["correct"])
        accuracy_list.append(data["accuracy"] * 100 if data["accuracy"] is not None else 0)

    # 创建双轴图表
    fig = go.Figure()

    # 左侧Y轴：数量
    fig.add_trace(go.Bar(
        name='总数',
        x=genera,
        y=totals,
        text=totals,
        textposition='auto',
        marker_color='lightblue',
        yaxis='y'
    ))

    fig.add_trace(go.Bar(
        name='正确数',
        x=genera,
        y=correct_list,
        text=correct_list,
        textposition='auto',
        marker_color='green',
        yaxis='y'
    ))

    # 右侧Y轴：准确率
    fig.add_trace(go.Scatter(
        name='准确率',
        x=genera,
        y=accuracy_list,
        text=[f"{acc:.1f}%" for acc in accuracy_list],
        textposition='top center',
        mode='lines+markers+text',
        marker=dict(size=10, color='orange'),
        line=dict(width=2, color='orange'),
        yaxis='y2'
    ))

    fig.update_layout(
        xaxis_title="花卉属",
        yaxis=dict(title="数量", side='left'),
        yaxis2=dict(title="准确率 (%)", overlaying='y', side='right', range=[0, 110]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 显示详细表格
    df = pd.DataFrame({
        "花卉属": genera,
        "总数": totals,
        "已标注": annotated_list,
        "正确数": correct_list,
        "准确率": [f"{acc:.1f}%" if acc > 0 else "-" for acc in accuracy_list]
    })

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_confusion_matrix(matrix_data: ConfusionMatrixData) -> None:
    """
    渲染混淆矩阵热力图

    Args:
        matrix_data: 混淆矩阵数据
    """
    st.subheader("🔥 混淆矩阵")

    if matrix_data.total_samples == 0:
        st.info("暂无已标注样本，无法生成混淆矩阵")
        return

    st.caption(f"基于 {matrix_data.total_samples} 个已标注样本")

    # 创建热力图
    fig = px.imshow(
        matrix_data.matrix,
        labels=dict(x="预测疾病", y="实际疾病", color="样本数"),
        x=matrix_data.labels,
        y=matrix_data.labels,
        color_continuous_scale="Blues",
        text_auto=True,
        aspect="auto"
    )

    fig.update_layout(
        height=500,
        xaxis_title="预测疾病",
        yaxis_title="实际疾病"
    )

    fig.update_xaxes(side="bottom")

    st.plotly_chart(fig, use_container_width=True)

    # 计算对角线准确率
    diagonal_sum = sum(matrix_data.matrix[i][i] for i in range(len(matrix_data.labels)))
    total_sum = sum(sum(row) for row in matrix_data.matrix)

    if total_sum > 0:
        overall_accuracy = diagonal_sum / total_sum
        st.metric("整体准确率", f"{overall_accuracy*100:.1f}%", help="对角线元素之和 / 总样本数")


def render_confidence_score_histogram(items: List[BatchDiagnosisItem]) -> None:
    """
    渲染置信度分数直方图

    Args:
        items: 批量推理结果项列表
    """
    st.subheader("📉 置信度分数分布")

    if not items:
        st.info("暂无数据")
        return

    # 提取置信度分数
    scores = [item.confidence_score for item in items]
    annotated_items = [item for item in items if item.annotation_status is not None]
    correct_scores = [item.confidence_score for item in annotated_items if item.annotation_status == "correct"]
    incorrect_scores = [item.confidence_score for item in annotated_items if item.annotation_status == "incorrect"]

    # 创建叠加直方图
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=scores,
        name='全部',
        opacity=0.5,
        marker_color='lightblue',
        nbinsx=20
    ))

    if correct_scores:
        fig.add_trace(go.Histogram(
            x=correct_scores,
            name='正确',
            opacity=0.7,
            marker_color='green',
            nbinsx=20
        ))

    if incorrect_scores:
        fig.add_trace(go.Histogram(
            x=incorrect_scores,
            name='错误',
            opacity=0.7,
            marker_color='red',
            nbinsx=20
        ))

    fig.update_layout(
        barmode='overlay',
        xaxis_title="置信度分数",
        yaxis_title="样本数",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 显示统计信息
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("平均置信度", f"{sum(scores)/len(scores):.3f}")

    with col2:
        if correct_scores:
            st.metric("正确案例平均", f"{sum(correct_scores)/len(correct_scores):.3f}")

    with col3:
        if incorrect_scores:
            st.metric("错误案例平均", f"{sum(incorrect_scores)/len(incorrect_scores):.3f}")


def render_disease_distribution_pie(items: List[BatchDiagnosisItem]) -> None:
    """
    渲染诊断疾病分布饼图

    Args:
        items: 批量推理结果项列表
    """
    st.subheader("🥧 诊断疾病分布")

    if not items:
        st.info("暂无数据")
        return

    # 统计疾病分布
    disease_counts = {}
    for item in items:
        disease_name = item.disease_name
        disease_counts[disease_name] = disease_counts.get(disease_name, 0) + 1

    # 创建饼图
    fig = go.Figure(data=[go.Pie(
        labels=list(disease_counts.keys()),
        values=list(disease_counts.values()),
        hole=0.3,
        textinfo='label+percent+value',
        textposition='auto'
    )])

    fig.update_layout(
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
    )

    st.plotly_chart(fig, use_container_width=True)
