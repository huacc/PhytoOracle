"""
知识库管理API Schema模型 (P4.3 实现)

功能：
- 定义知识库管理相关的API响应模型
- 用于FastAPI的响应序列化
- 遵循详细设计文档v2.0第6.3节的API协议定义

模型清单：
- DiseaseSchema: 疾病基本信息Schema
- DiseaseDetailSchema: 疾病详细信息Schema
- DiseaseListResponseSchema: 疾病列表响应Schema
- KnowledgeTreeHostSchema: 知识库树宿主节点Schema
- KnowledgeTreeDiseaseSchema: 知识库树疾病节点Schema
- KnowledgeTreeResponseSchema: 知识库树响应Schema
- HostDiseasesResponseSchema: 按宿主属查询疾病响应Schema

实现阶段：P4.3
对应设计文档：详细设计文档v2.0 第6.3节
作者：AI Python Architect
日期：2025-11-15
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class KnowledgeDiseaseSchema(BaseModel):
    """
    知识库疾病基本信息Schema

    用于知识库疾病列表查询响应

    字段说明：
    - disease_id: 疾病唯一标识符（如：rosa_blackspot）
    - disease_name: 疾病中文名称
    - common_name_en: 英文常用名
    - pathogen: 病原体（真菌、细菌、病毒等）
    - host_genus: 宿主属（如：Rosa, Prunus）

    对应设计文档：详细设计文档v2.0 第6.3.1节
    """
    disease_id: str = Field(..., description="疾病唯一标识符（如：rosa_blackspot）")
    disease_name: str = Field(..., description="疾病中文名称")
    common_name_en: str = Field(..., description="英文常用名")
    pathogen: str = Field(..., description="病原体（真菌、细菌、病毒等）")
    host_genus: Optional[str] = Field(None, description="宿主属（如：Rosa, Prunus）")


class DiseaseDetailSchema(BaseModel):
    """
    疾病详细信息Schema

    用于单个疾病详情查询响应

    字段说明：
    - version: 知识库版本号
    - disease_id: 疾病唯一标识符
    - disease_name: 疾病中文名称
    - common_name_en: 英文常用名
    - pathogen: 病原体
    - feature_vector: 疾病特征向量（完整）
    - feature_importance: 特征重要性（主要、次要、可选）
    - diagnosis_rules: 诊断规则（确诊、疑似）
    - visual_descriptions: 视觉描述（VLM识别线索）
    - host_plants: 宿主植物列表
    - typical_symptoms: 典型症状描述

    对应设计文档：详细设计文档v2.0 第6.3.2节
    """
    version: str = Field(..., description="知识库版本号（格式：X.Y）")
    disease_id: str = Field(..., description="疾病唯一标识符（如：rosa_blackspot）")
    disease_name: str = Field(..., description="疾病中文名称")
    common_name_en: str = Field(..., description="英文常用名")
    pathogen: str = Field(..., description="病原体（真菌、细菌、病毒等）")

    # 完整的疾病知识数据
    feature_vector: Dict[str, Any] = Field(..., description="疾病特征向量（完整）")
    feature_importance: Dict[str, Dict] = Field(..., description="特征重要性（major_features/minor_features/optional_features）")
    diagnosis_rules: Dict[str, List[Dict]] = Field(..., description="诊断规则（confirmed_rules/suspected_rules）")
    visual_descriptions: Dict[str, str] = Field(default_factory=dict, description="视觉描述（early_stage/advanced_stage等）")
    host_plants: List[Dict[str, str]] = Field(default_factory=list, description="宿主植物列表")
    typical_symptoms: str = Field(default="", description="典型症状描述")


class DiseaseListResponseSchema(BaseModel):
    """
    疾病列表响应Schema

    用于GET /api/v1/knowledge/diseases响应

    字段说明：
    - total: 疾病总数
    - diseases: 疾病列表

    对应设计文档：详细设计文档v2.0 第6.3.1节
    """
    total: int = Field(..., ge=0, description="疾病总数")
    diseases: List[KnowledgeDiseaseSchema] = Field(default_factory=list, description="疾病列表")


class KnowledgeTreeDiseaseSchema(BaseModel):
    """
    知识库树疾病节点Schema

    用于知识库树结构中的疾病节点

    字段说明：
    - disease_id: 疾病唯一标识符
    - disease_name: 疾病中文名称
    - common_name_en: 英文常用名
    - pathogen: 病原体
    - prevalence: 流行程度（common/rare/unknown）

    对应设计文档：详细设计文档v2.0 第6.3.3节（GET /api/v1/knowledge/tree）
    """
    disease_id: str = Field(..., description="疾病唯一标识符（如：rosa_blackspot）")
    disease_name: str = Field(..., description="疾病中文名称")
    common_name_en: str = Field(..., description="英文常用名")
    pathogen: str = Field(..., description="病原体")
    prevalence: str = Field(default="unknown", description="流行程度（common/rare/unknown）")


class KnowledgeTreeHostSchema(BaseModel):
    """
    知识库树宿主节点Schema

    用于知识库树结构中的宿主属节点

    字段说明：
    - genus: 宿主属（如：Rosa）
    - name_zh: 中文名称（如：蔷薇属）
    - name_en: 英文名称（如：Rose）
    - disease_count: 疾病数量
    - diseases: 疾病列表

    对应设计文档：详细设计文档v2.0 第6.3.3节（GET /api/v1/knowledge/tree）
    """
    genus: str = Field(..., description="宿主属（如：Rosa）")
    name_zh: str = Field(..., description="中文名称（如：蔷薇属）")
    name_en: str = Field(..., description="英文名称（如：Rose）")
    disease_count: int = Field(..., ge=0, description="疾病数量")
    diseases: List[KnowledgeTreeDiseaseSchema] = Field(default_factory=list, description="疾病列表")


class KnowledgeTreeResponseSchema(BaseModel):
    """
    知识库树响应Schema

    用于GET /api/v1/knowledge/tree响应

    字段说明：
    - version: 知识库版本号
    - last_updated: 最后更新时间（ISO 8601格式）
    - total_hosts: 宿主属总数
    - total_diseases: 疾病总数
    - hosts: 宿主属列表（按宿主属分组的疾病树）

    对应设计文档：详细设计文档v2.0 第6.3.3节（GET /api/v1/knowledge/tree）
    """
    version: str = Field(..., description="知识库版本号")
    last_updated: str = Field(..., description="最后更新时间（ISO 8601格式）")
    total_hosts: int = Field(..., ge=0, description="宿主属总数")
    total_diseases: int = Field(..., ge=0, description="疾病总数")
    hosts: List[KnowledgeTreeHostSchema] = Field(default_factory=list, description="宿主属列表")


class HostDiseasesResponseSchema(BaseModel):
    """
    按宿主属查询疾病响应Schema

    用于GET /api/v1/knowledge/hosts/{genus}响应

    字段说明：
    - genus: 宿主属（如：Rosa）
    - name_zh: 中文名称（如：蔷薇属）
    - name_en: 英文名称（如：Rose）
    - total: 疾病总数
    - diseases: 疾病列表

    对应设计文档：详细设计文档v2.0 第6.3.4节（GET /api/v1/knowledge/hosts/{genus}）
    """
    genus: str = Field(..., description="宿主属（如：Rosa）")
    name_zh: Optional[str] = Field(None, description="中文名称（如：蔷薇属）")
    name_en: Optional[str] = Field(None, description="英文名称（如：Rose）")
    total: int = Field(..., ge=0, description="疾病总数")
    diseases: List[KnowledgeDiseaseSchema] = Field(default_factory=list, description="疾病列表")


def main():
    """
    调用示例：演示如何使用知识库Schema

    此函数展示了如何创建和使用知识库管理API的Schema模型
    """
    print("=" * 60)
    print("知识库管理API Schema 调用示例")
    print("=" * 60)

    # 1. 创建疾病基本信息Schema
    disease = KnowledgeDiseaseSchema(
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Rose Black Spot",
        pathogen="Diplocarpon rosae (真菌)",
        host_genus="Rosa"
    )
    print("\n1. 疾病基本信息Schema：")
    print(disease.model_dump_json(indent=2, ensure_ascii=False))

    # 2. 创建疾病详细信息Schema
    disease_detail = DiseaseDetailSchema(
        version="4.1",
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Rose Black Spot",
        pathogen="Diplocarpon rosae (真菌)",
        feature_vector={
            "color_center": ["黑色", "深褐色"],
            "shape": ["圆形", "不规则形"],
            "size_mm": {"min": 1, "max": 12}
        },
        feature_importance={
            "major_features": ["color_center", "边缘特征"],
            "minor_features": ["分布位置"],
            "optional_features": ["发病环境"]
        },
        diagnosis_rules={
            "confirmed_rules": [{"rule": "黑色圆形斑点 + 黄色晕圈"}],
            "suspected_rules": [{"rule": "黑色斑点 + 叶片枯萎"}]
        },
        visual_descriptions={
            "early_stage": "叶片上出现黑色圆形斑点",
            "advanced_stage": "斑点扩大，周围有黄色晕圈"
        },
        host_plants=[{"genus": "Rosa", "name": "玫瑰"}],
        typical_symptoms="叶片上出现黑色圆形或不规则形斑点，直径1-12mm，周围常有黄色晕圈"
    )
    print("\n2. 疾病详细信息Schema：")
    print(f"  - 疾病ID: {disease_detail.disease_id}")
    print(f"  - 疾病名称: {disease_detail.disease_name}")
    print(f"  - 版本: {disease_detail.version}")
    print(f"  - 主要特征: {disease_detail.feature_importance['major_features']}")

    # 3. 创建知识库树响应Schema
    tree = KnowledgeTreeResponseSchema(
        version="1.0",
        last_updated="2025-01-14T10:30:45Z",
        total_hosts=2,
        total_diseases=5,
        hosts=[
            KnowledgeTreeHostSchema(
                genus="Rosa",
                name_zh="蔷薇属",
                name_en="Rose",
                disease_count=3,
                diseases=[
                    KnowledgeTreeDiseaseSchema(
                        disease_id="rosa_blackspot",
                        disease_name="玫瑰黑斑病",
                        common_name_en="Rose Black Spot",
                        pathogen="Diplocarpon rosae",
                        prevalence="common"
                    ),
                    KnowledgeTreeDiseaseSchema(
                        disease_id="rosa_powdery_mildew",
                        disease_name="玫瑰白粉病",
                        common_name_en="Rose Powdery Mildew",
                        pathogen="Podosphaera pannosa",
                        prevalence="common"
                    )
                ]
            ),
            KnowledgeTreeHostSchema(
                genus="Prunus",
                name_zh="李属",
                name_en="Cherry/Plum",
                disease_count=2,
                diseases=[
                    KnowledgeTreeDiseaseSchema(
                        disease_id="prunus_brown_rot",
                        disease_name="樱花褐腐病",
                        common_name_en="Brown Rot",
                        pathogen="Monilinia fructicola",
                        prevalence="common"
                    )
                ]
            )
        ]
    )
    print("\n3. 知识库树响应Schema：")
    print(f"  - 总宿主数: {tree.total_hosts}")
    print(f"  - 总疾病数: {tree.total_diseases}")
    print(f"  - 版本: {tree.version}")
    for host in tree.hosts:
        print(f"  - {host.name_zh}（{host.genus}）：{host.disease_count} 种疾病")

    # 4. 创建按宿主属查询疾病响应Schema
    host_diseases = HostDiseasesResponseSchema(
        genus="Rosa",
        name_zh="蔷薇属",
        name_en="Rose",
        total=3,
        diseases=[disease]
    )
    print("\n4. 按宿主属查询疾病响应Schema：")
    print(f"  - 宿主属: {host_diseases.genus} ({host_diseases.name_zh})")
    print(f"  - 疾病总数: {host_diseases.total}")
    print(f"  - 疾病列表: {len(host_diseases.diseases)} 条记录")

    print("\n" + "=" * 60)
    print("所有Schema模型测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    main()
