"""
API Schemas模块

导出所有API请求和响应Schema，便于外部导入使用

使用示例：
```python
from apps.api.schemas import (
    DiagnosisResponseSchema,
    LoginRequest,
    LoginResponse
)
```
"""

# 诊断相关Schemas
from .diagnosis import (
    DiagnosisRequest,
    DiagnosedDiseaseSchema,
    DiagnosisResponseSchema,
    DiseaseSchema,
)

# 认证相关Schemas
from .auth import (
    LoginRequest,
    LoginResponse,
    TokenData,
)

__all__ = [
    # 诊断Schemas
    "DiagnosisRequest",
    "DiagnosedDiseaseSchema",
    "DiagnosisResponseSchema",
    "DiseaseSchema",
    # 认证Schemas
    "LoginRequest",
    "LoginResponse",
    "TokenData",
]
