"""
本体管理API路由模块 (P4.4 实现)

功能：
- GET /api/v1/ontology/features - 查询所有特征定义
- GET /api/v1/ontology/features/{feature_id} - 查询单个特征详情
- GET /api/v1/ontology/associations - 查询疾病-特征关联

实现阶段：P4.4
对应设计文档：详细设计文档v2.0 第6.5节、6.8节

架构说明：
- 使用FastAPI的APIRouter创建路由
- 通过Depends注入KnowledgeService
- 响应格式使用ontology.py中定义的Schema
- 复用P3.2实现的KnowledgeService方法

作者：AI Python Architect
日期：2025-11-15
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

# Schema导入
from backend.apps.api.schemas.ontology import (
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

# 依赖注入
from backend.apps.api.deps import get_knowledge_service

# Service导入
from backend.services.knowledge_service import KnowledgeService, KnowledgeServiceException

# Domain模型
from backend.domain.feature import FeatureOntology
from backend.domain.disease import DiseaseOntology


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 创建路由器
router = APIRouter()


@router.get(
    "/ontology/features",
    response_model=FeatureListResponseSchema,
    summary="查询所有特征定义",
    description="获取所有特征本体定义，包括特征ID、名称、类型、分类等基本信息",
    tags=["Ontology"]
)
async def list_features(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> FeatureListResponseSchema:
    """
    查询所有特征定义 (P4.4)

    功能：
    - 从特征本体中提取所有特征维度
    - 转换为FeatureSchema格式
    - 返回特征列表和版本号

    Args:
        knowledge_service: 知识库服务（依赖注入）

    Returns:
        FeatureListResponseSchema: 特征列表响应

    Raises:
        HTTPException 500: 知识库服务异常
    """
    try:
        logger.info("[P4.4] 开始查询所有特征定义")

        # 1. 获取特征本体
        feature_ontology = knowledge_service.get_feature_ontology()

        if feature_ontology is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "FEATURE_ONTOLOGY_NOT_LOADED",
                    "message": "特征本体未加载",
                    "detail": "知识库服务未正确初始化"
                }
            )

        # 2. 从dimensions中提取所有特征
        features: List[FeatureSchema] = []

        for feature_id, dimension_info in feature_ontology.dimensions.items():
            # 提取基本信息
            feature_type = dimension_info.get("type", "unknown")
            description = dimension_info.get("description", "")

            # 提取允许值（仅enum类型）
            allowed_values = None
            if feature_type == "enum":
                allowed_values = dimension_info.get("values", [])

            # 推断特征分类
            feature_category = _infer_feature_category(feature_id)

            # 构建FeatureSchema
            feature_schema = FeatureSchema(
                feature_id=feature_id,
                feature_name=description or feature_id,  # 使用description作为feature_name
                feature_type=feature_type,
                feature_category=feature_category,
                allowed_values=allowed_values,
                description=description
            )

            features.append(feature_schema)

        # 3. 构建响应
        response = FeatureListResponseSchema(
            total=len(features),
            features=features,
            version=feature_ontology.version
        )

        logger.info(f"[P4.4] 查询所有特征定义成功：{len(features)} 个特征")
        return response

    except KnowledgeServiceException as e:
        logger.error(f"[P4.4] 知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": f"知识库服务异常: {str(e)}",
                "detail": "请联系系统管理员"
            }
        )
    except Exception as e:
        logger.error(f"[P4.4] 查询特征定义失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"查询特征定义失败: {str(e)}",
                "detail": "请联系系统管理员"
            }
        )


@router.get(
    "/ontology/features/{feature_id}",
    response_model=FeatureDetailSchema,
    summary="查询单个特征详情",
    description="获取指定特征的详细信息，包括枚举值定义、约束条件、模糊匹配规则等",
    tags=["Ontology"]
)
async def get_feature_detail(
    feature_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> FeatureDetailSchema:
    """
    查询单个特征详情 (P4.4)

    功能：
    - 从特征本体中查询指定特征的完整信息
    - 包含枚举值定义、约束条件、模糊匹配规则等
    - 返回详细的特征信息

    Args:
        feature_id: 特征ID（如：symptom_type、color_center）
        knowledge_service: 知识库服务（依赖注入）

    Returns:
        FeatureDetailSchema: 特征详情响应

    Raises:
        HTTPException 404: 特征不存在
        HTTPException 500: 知识库服务异常
    """
    try:
        logger.info(f"[P4.4] 开始查询特征详情: {feature_id}")

        # 1. 获取特征本体
        feature_ontology = knowledge_service.get_feature_ontology()

        if feature_ontology is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "FEATURE_ONTOLOGY_NOT_LOADED",
                    "message": "特征本体未加载",
                    "detail": "知识库服务未正确初始化"
                }
            )

        # 2. 检查特征是否存在
        if feature_id not in feature_ontology.dimensions:
            logger.warning(f"[P4.4] 特征不存在: {feature_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "FEATURE_NOT_FOUND",
                    "message": f"特征不存在: {feature_id}",
                    "detail": f"请检查feature_id是否正确。可用特征: {list(feature_ontology.dimensions.keys())}"
                }
            )

        # 3. 获取特征维度信息
        dimension_info = feature_ontology.dimensions[feature_id]

        # 4. 提取基本信息
        feature_type = dimension_info.get("type", "unknown")
        description = dimension_info.get("description", "")

        # 5. 提取允许值和枚举定义
        allowed_values = None
        enum_definitions = None

        if feature_type == "enum":
            allowed_values = dimension_info.get("values", [])
            enum_definitions = dimension_info.get("value_definitions", {})

        # 6. 推断特征分类
        feature_category = _infer_feature_category(feature_id)

        # 7. 提取该特征的模糊匹配规则
        fuzzy_matching_rules = _extract_fuzzy_matching_rules(feature_id, feature_ontology)

        # 8. 构建FeatureDetailSchema
        feature_detail = FeatureDetailSchema(
            feature_id=feature_id,
            feature_name=description or feature_id,
            feature_type=feature_type,
            feature_category=feature_category,
            description=description,
            allowed_values=allowed_values,
            enum_definitions=enum_definitions,
            constraints=None,  # 当前版本暂无约束条件
            fuzzy_matching_rules=fuzzy_matching_rules
        )

        logger.info(f"[P4.4] 查询特征详情成功: {feature_id}")
        return feature_detail

    except HTTPException:
        # 重新抛出HTTPException
        raise
    except KnowledgeServiceException as e:
        logger.error(f"[P4.4] 知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": f"知识库服务异常: {str(e)}",
                "detail": "请联系系统管理员"
            }
        )
    except Exception as e:
        logger.error(f"[P4.4] 查询特征详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"查询特征详情失败: {str(e)}",
                "detail": "请联系系统管理员"
            }
        )


@router.get(
    "/ontology/associations",
    response_model=DiseaseFeatureListResponseSchema,
    summary="查询疾病-特征关联",
    description="获取所有疾病的特征关联信息，包括特征向量和特征重要性",
    tags=["Ontology"]
)
async def list_disease_feature_associations(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> DiseaseFeatureListResponseSchema:
    """
    查询疾病-特征关联 (P4.4)

    功能：
    - 从所有疾病中提取特征向量
    - 构建疾病-特征关联列表
    - 返回每个疾病的feature_vector和feature_importance

    Args:
        knowledge_service: 知识库服务（依赖注入）

    Returns:
        DiseaseFeatureListResponseSchema: 疾病-特征关联列表响应

    Raises:
        HTTPException 500: 知识库服务异常
    """
    try:
        logger.info("[P4.4] 开始查询疾病-特征关联")

        # 1. 获取所有疾病
        diseases = knowledge_service.get_all_diseases()

        if diseases is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "DISEASES_NOT_LOADED",
                    "message": "疾病知识库未加载",
                    "detail": "知识库服务未正确初始化"
                }
            )

        # 2. 构建疾病-特征关联列表
        associations: List[DiseaseFeatureAssociationSchema] = []

        for disease in diseases:
            # 构建DiseaseFeatureAssociationSchema
            association = DiseaseFeatureAssociationSchema(
                disease_id=disease.disease_id,
                disease_name=disease.disease_name,
                feature_vector=disease.feature_vector,
                feature_importance=disease.feature_importance
            )
            associations.append(association)

        # 3. 构建响应
        response = DiseaseFeatureListResponseSchema(
            total=len(associations),
            associations=associations
        )

        logger.info(f"[P4.4] 查询疾病-特征关联成功：{len(associations)} 个疾病")
        return response

    except KnowledgeServiceException as e:
        logger.error(f"[P4.4] 知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": f"知识库服务异常: {str(e)}",
                "detail": "请联系系统管理员"
            }
        )
    except Exception as e:
        logger.error(f"[P4.4] 查询疾病-特征关联失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"查询疾病-特征关联失败: {str(e)}",
                "detail": "请联系系统管理员"
            }
        )


# ==================== 辅助函数 ====================

def _infer_feature_category(feature_id: str) -> Optional[str]:
    """
    根据特征ID推断特征分类

    Args:
        feature_id: 特征ID

    Returns:
        特征分类（symptom、appearance、location、dimension等）
    """
    # 症状类型
    if feature_id in ["symptom_type"]:
        return "symptom"

    # 外观特征（颜色、尺寸等）
    if feature_id in ["color_center", "color_border", "size", "coverage"]:
        return "appearance"

    # 位置特征
    if feature_id in ["location"]:
        return "location"

    # 分布模式
    if feature_id in ["distribution"]:
        return "distribution"

    # 默认分类
    return "other"


def _extract_fuzzy_matching_rules(feature_id: str, feature_ontology: FeatureOntology) -> Optional[Dict[str, Any]]:
    """
    从特征本体中提取指定特征的模糊匹配规则

    Args:
        feature_id: 特征ID
        feature_ontology: 特征本体对象

    Returns:
        模糊匹配规则（如果存在）
    """
    fuzzy_matching = feature_ontology.fuzzy_matching

    if not fuzzy_matching:
        return None

    # 提取与该特征相关的模糊匹配规则
    related_rules = {}

    # 颜色别名（color_center、color_border）
    if feature_id in ["color_center", "color_border"]:
        if "color_aliases" in fuzzy_matching:
            related_rules["color_aliases"] = fuzzy_matching["color_aliases"]

    # 尺寸顺序和容差（size）
    if feature_id == "size":
        if "size_order" in fuzzy_matching:
            related_rules["size_order"] = fuzzy_matching["size_order"]
        if "size_tolerance" in fuzzy_matching:
            related_rules["size_tolerance"] = fuzzy_matching["size_tolerance"]

    # 症状类型同义词（symptom_type）
    if feature_id == "symptom_type":
        if "synonym_mapping" in fuzzy_matching:
            related_rules["synonym_mapping"] = fuzzy_matching["synonym_mapping"]

    return related_rules if related_rules else None


def main():
    """
    本体管理API路由使用示例

    演示如何：
    1. 启动FastAPI服务器
    2. 调用本体管理API
    3. 测试各个端点
    """
    print("=" * 80)
    print("本体管理API路由使用示例")
    print("=" * 80)

    print("\n[说明]")
    print("本模块定义了本体管理API路由，需要在FastAPI应用中注册后使用。")
    print("\n[注册路由]")
    print("在 backend/apps/api/main.py 中添加：")
    print("  from backend.apps.api.routers import ontology")
    print("  app.include_router(ontology.router, prefix='/api/v1', tags=['Ontology'])")

    print("\n[启动服务器]")
    print("  cd backend")
    print("  uvicorn apps.api.main:app --reload")

    print("\n[API端点]")
    print("1. 查询所有特征定义:")
    print("   GET http://localhost:8000/api/v1/ontology/features")
    print("   响应: { total, features: [{ feature_id, feature_name, feature_type, ... }], version }")

    print("\n2. 查询单个特征详情:")
    print("   GET http://localhost:8000/api/v1/ontology/features/{feature_id}")
    print("   例如: GET http://localhost:8000/api/v1/ontology/features/symptom_type")
    print("   响应: { feature_id, feature_name, enum_definitions, fuzzy_matching_rules, ... }")

    print("\n3. 查询疾病-特征关联:")
    print("   GET http://localhost:8000/api/v1/ontology/associations")
    print("   响应: { total, associations: [{ disease_id, disease_name, feature_vector, ... }] }")

    print("\n[OpenAPI文档]")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc: http://localhost:8000/redoc")

    print("\n" + "=" * 80)
    print("使用示例说明完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
