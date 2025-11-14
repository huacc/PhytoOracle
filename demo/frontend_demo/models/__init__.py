"""
models包初始化文件

导出所有数据模型，便于外部引用。
"""
from .diagnosis_result import (
    DiagnosisResult,
    OntologyReference,
    Q0StepResult,
    FeatureExtractionResult,
    SynonymMapping,
    MismatchExplanation,
    MatchDetail,
    CandidateDisease,
    ScoringResult,
    FinalDiagnosis,
    PerformanceMetrics,
    OntologyUsageSummary,
)
from .ontology_usage import (
    OntologyUsage,
    OntologyUsageExport,
    FuzzyMapping,
    DiseaseOntologyUsage,
    FeatureOntologyUsage,
)
from .annotation import (
    Annotation,
    ImageAnnotation,
)
from .batch_result import (
    BatchDiagnosisItem,
    BatchStatistics,
    ConfusionMatrixData,
    BatchDiagnosisResult,
)

__all__ = [
    # 诊断结果相关
    "DiagnosisResult",
    "OntologyReference",
    "Q0StepResult",
    "FeatureExtractionResult",
    "SynonymMapping",
    "MismatchExplanation",
    "MatchDetail",
    "CandidateDisease",
    "ScoringResult",
    "FinalDiagnosis",
    "PerformanceMetrics",
    "OntologyUsageSummary",
    # 本体使用相关
    "OntologyUsage",
    "OntologyUsageExport",
    "FuzzyMapping",
    "DiseaseOntologyUsage",
    "FeatureOntologyUsage",
    # 标注相关
    "Annotation",
    "ImageAnnotation",
    # 批量推理相关
    "BatchDiagnosisItem",
    "BatchStatistics",
    "ConfusionMatrixData",
    "BatchDiagnosisResult",
]
