"""
本体管理API Schema模型 (P4.4 实现)

功能：
- 定义本体管理相关的API响应模型
- 用于FastAPI的响应序列化
- 遵循详细设计文档v2.0第6.5节和6.8节的API协议定义

模型清单：
- OntologyTypeSchema: 本体类型Schema（用于本体列表）
- OntologyListResponseSchema: 本体类型列表响应Schema
- EnumValueSchema: 枚举值Schema
- DimensionSchema: 特征维度Schema
- OntologyDetailSchema: 本体详情Schema
- DiseaseFeatureAssociationSchema: 疾病-特征关联Schema
- DiseaseFeatureListResponseSchema: 疾病-特征关联列表响应Schema

实现阶段：P4.4
对应设计文档：详细设计文档v2.0 第6.5节、6.8节
作者：AI Python Architect
日期：2025-11-15
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class OntologyTypeSchema(BaseModel):
    """
    本体类型Schema

    用于本体类型列表查询响应

    字段说明：
    - type_id: 本体类型ID（如：symptom_type、color、location、size）
    - type_name: 本体类型名称（如：症状类型本体、颜色本体）
    - description: 本体描述
    - dimension_count: 维度数量
    - enum_value_count: 枚举值数量
    - last_updated: 最后更新时间

    对应设计文档：详细设计文档v2.0 第6.5.1节、6.8.1节
    """
    type_id: str = Field(..., description="本体类型ID（如：symptom_type、color、location、size）")
    type_name: str = Field(..., description="本体类型名称（如：症状类型本体、颜色本体）")
    description: str = Field(default="", description="本体描述")
    dimension_count: int = Field(default=0, ge=0, description="维度数量")
    enum_value_count: int = Field(default=0, ge=0, description="枚举值数量")
    last_updated: Optional[str] = Field(None, description="最后更新时间（ISO格式）")


class OntologyListResponseSchema(BaseModel):
    """
    本体类型列表响应Schema

    用于GET /api/v1/ontology/list响应

    字段说明：
    - total_types: 本体类型总数
    - ontology_types: 本体类型列表

    对应设计文档：详细设计文档v2.0 第6.5.1节
    """
    total_types: int = Field(..., ge=0, description="本体类型总数")
    ontology_types: List[OntologyTypeSchema] = Field(default_factory=list, description="本体类型列表")


class EnumValueSchema(BaseModel):
    """
    枚举值Schema

    用于特征维度的枚举值定义

    字段说明：
    - value: 枚举值（如：necrosis_spot、black、small）
    - label_zh: 中文标签
    - label_en: 英文标签
    - description: 描述
    - vlm_visual_clues: VLM视觉识别线索（可选）
    - visual_examples: 视觉示例列表（可选）
    - count_in_knowledge_base: 知识库中使用该枚举值的疾病数量（可选）
    - visual_metaphors: 视觉隐喻列表（可选）
    - color_group: 颜色分组（仅用于颜色本体，可选）
    - hex_code: 十六进制颜色代码（仅用于颜色本体，可选）

    对应设计文档：详细设计文档v2.0 第6.8.2节
    """
    value: str = Field(..., description="枚举值（如：necrosis_spot、black、small）")
    label_zh: Optional[str] = Field(None, description="中文标签")
    label_en: Optional[str] = Field(None, description="英文标签")
    description: Optional[str] = Field(None, description="描述")
    vlm_visual_clues: Optional[str] = Field(None, description="VLM视觉识别线索")
    visual_examples: Optional[List[str]] = Field(None, description="视觉示例列表")
    count_in_knowledge_base: Optional[int] = Field(None, description="知识库中使用该枚举值的疾病数量")
    visual_metaphors: Optional[List[str]] = Field(None, description="视觉隐喻列表")

    # 颜色本体专用字段
    color_group: Optional[str] = Field(None, description="颜色分组（仅用于颜色本体）")
    hex_code: Optional[str] = Field(None, description="十六进制颜色代码（仅用于颜色本体）")

    # 扩展字段（接受feature_ontology.json中的任意字段）
    class Config:
        extra = "allow"  # 允许额外字段（如pathology、size_range等）


class DimensionSchema(BaseModel):
    """
    特征维度Schema

    用于本体详情中的维度定义

    字段说明：
    - dimension_id: 维度ID（如：symptom_type、color_center）
    - dimension_name: 维度名称
    - description: 描述
    - is_required: 是否必需
    - type: 数据类型（enum等）
    - enum_values: 枚举值列表

    对应设计文档：详细设计文档v2.0 第6.8.2节
    """
    dimension_id: str = Field(..., description="维度ID（如：symptom_type、color_center）")
    dimension_name: Optional[str] = Field(None, description="维度名称")
    description: Optional[str] = Field(None, description="描述")
    is_required: Optional[bool] = Field(None, description="是否必需")
    type: Optional[str] = Field(None, description="数据类型（enum等）")
    enum_values: Optional[List[EnumValueSchema]] = Field(None, description="枚举值列表")


class OntologyDetailSchema(BaseModel):
    """
    本体详情Schema

    用于GET /api/v1/ontology/{type_id}响应

    字段说明：
    - type_id: 本体类型ID
    - type_name: 本体类型名称
    - description: 本体描述
    - dimensions: 维度列表
    - fuzzy_matching_rules: 模糊匹配规则（可选）
    - metadata: 元数据（创建时间、更新时间、版本号）

    对应设计文档：详细设计文档v2.0 第6.8.2节
    """
    type_id: str = Field(..., description="本体类型ID（如：symptom_type、color）")
    type_name: str = Field(..., description="本体类型名称（如：症状类型本体）")
    description: Optional[str] = Field(None, description="本体描述")
    dimensions: List[DimensionSchema] = Field(default_factory=list, description="维度列表")
    fuzzy_matching_rules: Optional[Dict[str, Any]] = Field(None, description="模糊匹配规则")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据（created_at、updated_at、version）")


class FeatureSchema(BaseModel):
    """
    特征Schema（简化版）

    用于特征本体查询API的单个特征表示

    字段说明：
    - feature_id: 特征ID（如：symptom_type、color_center）
    - feature_name: 特征名称
    - feature_type: 特征类型（enum、numeric等）
    - feature_category: 特征分类（symptom、appearance等）
    - allowed_values: 允许的枚举值列表（仅enum类型）
    - description: 特征描述
    """
    feature_id: str = Field(..., description="特征ID（如：symptom_type、color_center）")
    feature_name: str = Field(..., description="特征名称")
    feature_type: str = Field(..., description="特征类型（enum、numeric等）")
    feature_category: Optional[str] = Field(None, description="特征分类（symptom、appearance等）")
    allowed_values: Optional[List[str]] = Field(None, description="允许的枚举值列表（仅enum类型）")
    description: Optional[str] = Field(None, description="特征描述")


class FeatureListResponseSchema(BaseModel):
    """
    特征列表响应Schema

    用于GET /api/v1/ontology/features响应

    字段说明：
    - total: 特征总数
    - features: 特征列表
    - version: 特征本体版本号
    """
    total: int = Field(..., ge=0, description="特征总数")
    features: List[FeatureSchema] = Field(default_factory=list, description="特征列表")
    version: Optional[str] = Field(None, description="特征本体版本号")


class FeatureDetailSchema(BaseModel):
    """
    特征详情Schema

    用于GET /api/v1/ontology/features/{feature_id}响应

    字段说明：
    - feature_id: 特征ID
    - feature_name: 特征名称
    - feature_type: 特征类型
    - feature_category: 特征分类
    - description: 特征描述
    - allowed_values: 允许的枚举值列表
    - enum_definitions: 枚举值定义（详细）
    - constraints: 约束条件
    - fuzzy_matching_rules: 该特征的模糊匹配规则
    """
    feature_id: str = Field(..., description="特征ID")
    feature_name: str = Field(..., description="特征名称")
    feature_type: str = Field(..., description="特征类型（enum、numeric等）")
    feature_category: Optional[str] = Field(None, description="特征分类")
    description: Optional[str] = Field(None, description="特征描述")
    allowed_values: Optional[List[str]] = Field(None, description="允许的枚举值列表")
    enum_definitions: Optional[Dict[str, Any]] = Field(None, description="枚举值定义（详细，包含cn_term、vlm_description等）")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")
    fuzzy_matching_rules: Optional[Dict[str, Any]] = Field(None, description="该特征的模糊匹配规则")


class DiseaseFeatureAssociationSchema(BaseModel):
    """
    疾病-特征关联Schema

    用于表示单个疾病的特征关联

    字段说明：
    - disease_id: 疾病ID
    - disease_name: 疾病名称
    - feature_vector: 特征向量（疾病的所有特征值）
    - feature_importance: 特征重要性（major_features、minor_features）
    """
    disease_id: str = Field(..., description="疾病ID")
    disease_name: str = Field(..., description="疾病名称")
    feature_vector: Dict[str, Any] = Field(default_factory=dict, description="特征向量（疾病的所有特征值）")
    feature_importance: Optional[Dict[str, Dict]] = Field(None, description="特征重要性（major_features、minor_features）")


class DiseaseFeatureListResponseSchema(BaseModel):
    """
    疾病-特征关联列表响应Schema

    用于GET /api/v1/ontology/associations响应

    字段说明：
    - total: 疾病总数
    - associations: 疾病-特征关联列表
    """
    total: int = Field(..., ge=0, description="疾病总数")
    associations: List[DiseaseFeatureAssociationSchema] = Field(default_factory=list, description="疾病-特征关联列表")


def main():
    """
    本体管理Schema使用示例

    演示如何：
    1. 创建本体类型Schema
    2. 创建本体详情Schema
    3. 创建特征Schema
    4. 创建疾病-特征关联Schema
    """
    print("=" * 80)
    print("本体管理Schema使用示例")
    print("=" * 80)

    # 1. 创建本体类型Schema
    print("\n[示例1] 创建本体类型Schema")
    ontology_type = OntologyTypeSchema(
        type_id="symptom_type",
        type_name="症状类型本体",
        description="定义花卉疾病的症状类型及枚举值",
        dimension_count=1,
        enum_value_count=8,
        last_updated="2025-11-15T10:00:00Z"
    )
    print(f"  本体类型: {ontology_type.type_name}")
    print(f"  维度数: {ontology_type.dimension_count}")
    print(f"  枚举值数: {ontology_type.enum_value_count}")

    # 2. 创建本体列表响应Schema
    print("\n[示例2] 创建本体列表响应Schema")
    ontology_list = OntologyListResponseSchema(
        total_types=1,
        ontology_types=[ontology_type]
    )
    print(f"  本体类型总数: {ontology_list.total_types}")
    print(f"  第一个本体类型: {ontology_list.ontology_types[0].type_name}")

    # 3. 创建枚举值Schema
    print("\n[示例3] 创建枚举值Schema")
    enum_value = EnumValueSchema(
        value="necrosis_spot",
        label_zh="坏死斑点",
        label_en="Necrotic spot",
        description="圆形或不规则形状的局部变色区域",
        vlm_visual_clues="小型圆形或近圆形的褐色或黑色斑点",
        count_in_knowledge_base=12
    )
    print(f"  枚举值: {enum_value.value}")
    print(f"  中文标签: {enum_value.label_zh}")
    print(f"  知识库使用数: {enum_value.count_in_knowledge_base}")

    # 4. 创建维度Schema
    print("\n[示例4] 创建维度Schema")
    dimension = DimensionSchema(
        dimension_id="symptom_type",
        dimension_name="症状类型",
        description="疾病的主要症状表现形式",
        is_required=True,
        type="enum",
        enum_values=[enum_value]
    )
    print(f"  维度ID: {dimension.dimension_id}")
    print(f"  维度名称: {dimension.dimension_name}")
    print(f"  是否必需: {dimension.is_required}")

    # 5. 创建本体详情Schema
    print("\n[示例5] 创建本体详情Schema")
    ontology_detail = OntologyDetailSchema(
        type_id="symptom_type",
        type_name="症状类型本体",
        description="定义花卉疾病的症状类型及枚举值",
        dimensions=[dimension],
        fuzzy_matching_rules=None,
        metadata={
            "created_at": "2025-11-12T08:00:00Z",
            "updated_at": "2025-11-15T10:00:00Z",
            "version": "1.0"
        }
    )
    print(f"  本体类型: {ontology_detail.type_name}")
    print(f"  维度数: {len(ontology_detail.dimensions)}")
    print(f"  版本: {ontology_detail.metadata.get('version')}")

    # 6. 创建特征Schema
    print("\n[示例6] 创建特征Schema")
    feature = FeatureSchema(
        feature_id="symptom_type",
        feature_name="症状类型",
        feature_type="enum",
        feature_category="symptom",
        allowed_values=["necrosis_spot", "powdery_coating", "chlorosis"],
        description="疾病的主要症状表现形式"
    )
    print(f"  特征ID: {feature.feature_id}")
    print(f"  特征名称: {feature.feature_name}")
    print(f"  允许值数: {len(feature.allowed_values)}")

    # 7. 创建疾病-特征关联Schema
    print("\n[示例7] 创建疾病-特征关联Schema")
    association = DiseaseFeatureAssociationSchema(
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        feature_vector={
            "symptom_type": "necrosis_spot",
            "color_center": "black",
            "size": "medium"
        },
        feature_importance={
            "major_features": {"symptom_type": 1.0, "color_center": 0.9},
            "minor_features": {"size": 0.5}
        }
    )
    print(f"  疾病ID: {association.disease_id}")
    print(f"  疾病名称: {association.disease_name}")
    print(f"  特征数: {len(association.feature_vector)}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
