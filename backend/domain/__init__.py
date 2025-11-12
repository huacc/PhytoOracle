"""
领域模型包

导出所有领域模型，便于外部导入使用

使用示例：
```python
from domain import (
    DiagnosisResult,
    FeatureVector,
    DiseaseOntology,
    PlantOntology,
    FeatureOntology,
    ImageHash,
    DiagnosisId
)
```
"""

# 诊断领域模型
from .diagnosis import (
    ContentType,
    PlantCategory,
    FlowerGenus,
    OrganType,
    Completeness,
    AbnormalityStatus,
    ConfidenceLevel,
    FeatureVector,
    DiagnosisScore,
    DiagnosisResult,
)

# 疾病本体
from .disease import DiseaseOntology

# 植物本体
from .plant import PlantOntology

# 特征本体
from .feature import FeatureOntology

# 值对象
from .value_objects import ImageHash, DiagnosisId

__all__ = [
    # 枚举类
    "ContentType",
    "PlantCategory",
    "FlowerGenus",
    "OrganType",
    "Completeness",
    "AbnormalityStatus",
    "ConfidenceLevel",
    # 诊断模型
    "FeatureVector",
    "DiagnosisScore",
    "DiagnosisResult",
    # 本体模型
    "DiseaseOntology",
    "PlantOntology",
    "FeatureOntology",
    # 值对象
    "ImageHash",
    "DiagnosisId",
]
