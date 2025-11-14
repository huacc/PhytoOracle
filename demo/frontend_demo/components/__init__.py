"""
components包初始化文件

导出所有UI组件。
"""
from .diagnosis_visualizer import render_diagnosis_result
from .ontology_tracer import (
    render_ontology_reference,
    render_synonym_mapping,
    render_mismatch_explanation,
    render_match_type_badge,
    render_confidence_badge,
    render_confidence_level_badge,
)
from .annotation_panel import (
    render_annotation_panel,
    display_annotation_summary,
)
from .comparison_components import (
    render_image_comparison_selector,
    render_side_by_side_comparison,
    render_difference_analysis,
)

__all__ = [
    # 推理可视化
    "render_diagnosis_result",
    # 本体追溯
    "render_ontology_reference",
    "render_synonym_mapping",
    "render_mismatch_explanation",
    "render_match_type_badge",
    "render_confidence_badge",
    "render_confidence_level_badge",
    # 标注面板
    "render_annotation_panel",
    "display_annotation_summary",
    # 图片对比
    "render_image_comparison_selector",
    "render_side_by_side_comparison",
    "render_difference_analysis",
]
