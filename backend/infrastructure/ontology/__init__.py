"""
知识库本体模块（Ontology Module）

功能：
- 提供知识库加载、索引、匹配的完整解决方案
- 支持五大知识库：疾病本体、特征本体、植物本体、宿主-疾病关系、视觉隐喻库
- 单例模式管理，避免重复加载

主要组件：
- KnowledgeBaseManager: 知识库管理器（单例，推荐使用）
- KnowledgeBaseLoader: 知识库加载器
- DiseaseIndexer: 疾病索引器
- FeatureMatcher: 特征匹配器

异常类：
- KnowledgeBaseError: 知识库基础异常
- KnowledgeBaseNotFoundError: 知识库文件或目录不存在
- KnowledgeBaseLoadError: 知识库加载失败
- KnowledgeBaseValidationError: 知识库数据验证失败

使用示例：
```python
from backend.infrastructure.ontology import KnowledgeBaseManager

# 获取知识库管理器单例
manager = KnowledgeBaseManager.get_instance()

# 查询候选疾病
candidates = manager.get_diseases_by_host("Rosa")

# 匹配疾病
score, reasoning = manager.match_disease(feature_vector, disease)

# 热重载知识库
manager.reload()
```
"""

from backend.infrastructure.ontology.manager import KnowledgeBaseManager
from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
from backend.infrastructure.ontology.indexer import DiseaseIndexer
from backend.infrastructure.ontology.matcher import FeatureMatcher
from backend.infrastructure.ontology.fuzzy_matcher import FuzzyMatchingEngine  # P2.4新增
from backend.infrastructure.ontology.weighted_scorer import WeightedDiagnosisScorer  # P2.5新增
from backend.infrastructure.ontology.exceptions import (
    KnowledgeBaseError,
    KnowledgeBaseNotFoundError,
    KnowledgeBaseLoadError,
    KnowledgeBaseValidationError
)

__all__ = [
    # 主要组件
    "KnowledgeBaseManager",
    "KnowledgeBaseLoader",
    "DiseaseIndexer",
    "FeatureMatcher",
    "FuzzyMatchingEngine",  # P2.4新增
    "WeightedDiagnosisScorer",  # P2.5新增

    # 异常类
    "KnowledgeBaseError",
    "KnowledgeBaseNotFoundError",
    "KnowledgeBaseLoadError",
    "KnowledgeBaseValidationError",
]
