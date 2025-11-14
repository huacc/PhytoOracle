"""
API Schemas模块

导出所有API请求和响应Schema，便于外部导入使用

使用示例：
```python
from apps.api.schemas import (
    DiagnosisResponseSchema,
    KnowledgeDiseaseSchema,
    KnowledgeTreeResponseSchema,
    LoginRequest,
    LoginResponse
)
```
"""

# 诊断相关Schemas (P4.2升级版)
from .diagnosis import (
    DiagnosisRequest,
    QADetailSchema,
    DiagnosisScoreSchema,
    DiagnosisSchema,
    CandidateDiseaseSchema,
    DiagnosisResponseSchema,
    DiseaseSchema,
)

# 知识库管理Schemas (P4.3新增)
from .knowledge import (
    KnowledgeDiseaseSchema,
    DiseaseDetailSchema,
    DiseaseListResponseSchema,
    KnowledgeTreeDiseaseSchema,
    KnowledgeTreeHostSchema,
    KnowledgeTreeResponseSchema,
    HostDiseasesResponseSchema,
)

# 本体管理Schemas (P4.4新增)
from .ontology import (
    FeatureSchema,
    FeatureListResponseSchema,
    FeatureDetailSchema,
    DiseaseFeatureAssociationSchema,
    DiseaseFeatureListResponseSchema,
    OntologyTypeSchema,
    OntologyListResponseSchema,
    OntologyDetailSchema,
    DimensionSchema,
    EnumValueSchema,
)

# 认证相关Schemas
from .auth import (
    LoginRequest,
    LoginResponse,
    TokenData,
)

__all__ = [
    # 诊断Schemas (P4.2升级版)
    "DiagnosisRequest",
    "QADetailSchema",
    "DiagnosisScoreSchema",
    "DiagnosisSchema",
    "CandidateDiseaseSchema",
    "DiagnosisResponseSchema",
    "DiseaseSchema",
    # 知识库管理Schemas (P4.3新增)
    "KnowledgeDiseaseSchema",
    "DiseaseDetailSchema",
    "DiseaseListResponseSchema",
    "KnowledgeTreeDiseaseSchema",
    "KnowledgeTreeHostSchema",
    "KnowledgeTreeResponseSchema",
    "HostDiseasesResponseSchema",
    # 本体管理Schemas (P4.4新增)
    "FeatureSchema",
    "FeatureListResponseSchema",
    "FeatureDetailSchema",
    "DiseaseFeatureAssociationSchema",
    "DiseaseFeatureListResponseSchema",
    "OntologyTypeSchema",
    "OntologyListResponseSchema",
    "OntologyDetailSchema",
    "DimensionSchema",
    "EnumValueSchema",
    # 认证Schemas
    "LoginRequest",
    "LoginResponse",
    "TokenData",
]
