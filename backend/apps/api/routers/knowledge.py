"""
知识库管理API路由模块 (P4.3 实现)

功能：
- GET /api/v1/knowledge/diseases - 查询所有疾病
- GET /api/v1/knowledge/diseases/{disease_id} - 查询单个疾病详情
- GET /api/v1/knowledge/tree - 获取知识库树（按宿主属分组）
- GET /api/v1/knowledge/hosts/{genus} - 按宿主属查询疾病

实现阶段：P4.3
对应设计文档：详细设计文档v2.0 第6.3节

架构说明：
- 使用FastAPI的APIRouter创建路由
- 通过Depends注入KnowledgeService
- 响应格式使用knowledge.py中定义的Schema
- 复用P3.2实现的KnowledgeService方法

作者：AI Python Architect
日期：2025-11-15
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

# Schema导入
from backend.apps.api.schemas.knowledge import (
    KnowledgeDiseaseSchema,
    DiseaseDetailSchema,
    DiseaseListResponseSchema,
    KnowledgeTreeResponseSchema,
    HostDiseasesResponseSchema,
)

# 依赖注入
from backend.apps.api.deps import get_knowledge_service

# Service导入
from backend.services.knowledge_service import KnowledgeService, KnowledgeServiceException

# Domain模型
from backend.domain.disease import DiseaseOntology


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 创建路由器
router = APIRouter()


@router.get(
    "/knowledge/diseases",
    response_model=DiseaseListResponseSchema,
    summary="查询所有疾病",
    description="获取知识库中所有疾病的列表，支持按宿主属筛选"
)
async def list_diseases(
    genus: Optional[str] = Query(None, description="宿主属筛选（如：Rosa, Prunus）"),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> DiseaseListResponseSchema:
    """
    查询所有疾病

    Args:
        genus: 可选的宿主属筛选参数（如：Rosa, Prunus）
        knowledge_service: 注入的知识库服务

    Returns:
        DiseaseListResponseSchema: 疾病列表响应

    Raises:
        HTTPException 500: 知识库服务异常

    使用示例：
    - GET /api/v1/knowledge/diseases - 获取所有疾病
    - GET /api/v1/knowledge/diseases?genus=Rosa - 获取玫瑰属疾病
    """
    try:
        logger.info(f"查询疾病列表，宿主属筛选: {genus or '无'}")

        # 1. 根据是否有genus参数，调用不同的查询方法
        if genus:
            # 按宿主属查询
            diseases: list[DiseaseOntology] = knowledge_service.get_diseases_by_genus(genus)
        else:
            # 获取所有疾病
            diseases: list[DiseaseOntology] = knowledge_service.get_all_diseases()

        # 2. 转换为Schema格式
        disease_schemas = []
        for disease in diseases:
            # 提取宿主属（从host_plants中获取第一个genus）
            host_genus = None
            if disease.host_plants and len(disease.host_plants) > 0:
                host_genus = disease.host_plants[0].get("genus")

            disease_schema = KnowledgeDiseaseSchema(
                disease_id=disease.disease_id,
                disease_name=disease.disease_name,
                common_name_en=disease.common_name_en,
                pathogen=disease.pathogen,
                host_genus=host_genus
            )
            disease_schemas.append(disease_schema)

        # 3. 构建响应
        response = DiseaseListResponseSchema(
            total=len(disease_schemas),
            diseases=disease_schemas
        )

        logger.info(f"成功查询到 {response.total} 种疾病")
        return response

    except KnowledgeServiceException as e:
        logger.error(f"知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": str(e),
                "detail": "知识库服务异常，请检查知识库是否正确初始化"
            }
        )
    except Exception as e:
        logger.error(f"查询疾病列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "查询疾病列表失败",
                "detail": str(e)
            }
        )


@router.get(
    "/knowledge/diseases/{disease_id}",
    response_model=DiseaseDetailSchema,
    summary="查询单个疾病详情",
    description="根据疾病ID获取疾病的完整知识数据，包括特征向量、诊断规则、视觉描述等"
)
async def get_disease_detail(
    disease_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> DiseaseDetailSchema:
    """
    查询单个疾病详情

    Args:
        disease_id: 疾病唯一标识符（如：rosa_blackspot）
        knowledge_service: 注入的知识库服务

    Returns:
        DiseaseDetailSchema: 疾病详细信息

    Raises:
        HTTPException 404: 疾病不存在
        HTTPException 500: 知识库服务异常

    使用示例：
    - GET /api/v1/knowledge/diseases/rosa_blackspot - 获取玫瑰黑斑病详情
    """
    try:
        logger.info(f"查询疾病详情，disease_id: {disease_id}")

        # 1. 查询疾病
        disease: Optional[DiseaseOntology] = knowledge_service.get_disease_by_id(disease_id)

        # 2. 检查是否找到
        if disease is None:
            logger.warning(f"疾病不存在: {disease_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "DISEASE_NOT_FOUND",
                    "message": f"疾病不存在: {disease_id}",
                    "detail": "请检查disease_id是否正确"
                }
            )

        # 3. 转换为Schema格式
        disease_detail_schema = DiseaseDetailSchema(
            version=disease.version,
            disease_id=disease.disease_id,
            disease_name=disease.disease_name,
            common_name_en=disease.common_name_en,
            pathogen=disease.pathogen,
            feature_vector=disease.feature_vector,
            feature_importance=disease.feature_importance,
            diagnosis_rules=disease.diagnosis_rules,
            visual_descriptions=disease.visual_descriptions,
            host_plants=disease.host_plants,
            typical_symptoms=disease.typical_symptoms
        )

        logger.info(f"成功查询疾病详情: {disease.disease_name}")
        return disease_detail_schema

    except HTTPException:
        # 重新抛出HTTP异常（404）
        raise
    except KnowledgeServiceException as e:
        logger.error(f"知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": str(e),
                "detail": "知识库服务异常，请检查知识库是否正确初始化"
            }
        )
    except Exception as e:
        logger.error(f"查询疾病详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "查询疾病详情失败",
                "detail": str(e)
            }
        )


@router.get(
    "/knowledge/tree",
    response_model=KnowledgeTreeResponseSchema,
    summary="获取知识库树",
    description="获取按宿主属分组的疾病树结构，用于前端知识库目录树展示"
)
async def get_knowledge_tree(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> KnowledgeTreeResponseSchema:
    """
    获取知识库树

    获取按宿主属分组的疾病树结构，用于前端知识库目录树展示。
    此接口复用P3.9实现的get_knowledge_tree()方法。

    Args:
        knowledge_service: 注入的知识库服务

    Returns:
        KnowledgeTreeResponseSchema: 知识库树结构

    Raises:
        HTTPException 500: 知识库服务异常

    使用示例：
    - GET /api/v1/knowledge/tree - 获取完整知识库树
    """
    try:
        logger.info("获取知识库树")

        # 1. 调用KnowledgeService的get_knowledge_tree()方法（P3.9已实现）
        tree_data = knowledge_service.get_knowledge_tree()

        # 2. 转换为Schema格式（直接使用KnowledgeTreeResponseSchema的model_validate）
        # 因为get_knowledge_tree()返回的字典格式与Schema定义完全一致
        tree_schema = KnowledgeTreeResponseSchema.model_validate(tree_data)

        logger.info(f"成功获取知识库树：{tree_schema.total_hosts}个宿主属，{tree_schema.total_diseases}种疾病")
        return tree_schema

    except KnowledgeServiceException as e:
        logger.error(f"知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": str(e),
                "detail": "知识库服务异常，请检查associations.json文件是否存在"
            }
        )
    except Exception as e:
        logger.error(f"获取知识库树失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "获取知识库树失败",
                "detail": str(e)
            }
        )


@router.get(
    "/knowledge/hosts/{genus}",
    response_model=HostDiseasesResponseSchema,
    summary="按宿主属查询疾病",
    description="根据宿主属（如：Rosa, Prunus）查询该属下的所有疾病"
)
async def get_diseases_by_host(
    genus: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
) -> HostDiseasesResponseSchema:
    """
    按宿主属查询疾病

    Args:
        genus: 宿主属（如：Rosa, Prunus）
        knowledge_service: 注入的知识库服务

    Returns:
        HostDiseasesResponseSchema: 宿主属疾病列表

    Raises:
        HTTPException 404: 宿主属不存在或无疾病
        HTTPException 500: 知识库服务异常

    使用示例：
    - GET /api/v1/knowledge/hosts/Rosa - 获取玫瑰属的所有疾病
    - GET /api/v1/knowledge/hosts/Prunus - 获取樱花属的所有疾病
    """
    try:
        logger.info(f"按宿主属查询疾病，genus: {genus}")

        # 1. 查询该宿主属的所有疾病
        diseases: list[DiseaseOntology] = knowledge_service.get_diseases_by_genus(genus)

        # 2. 检查是否找到疾病
        if not diseases or len(diseases) == 0:
            logger.warning(f"宿主属无疾病或不存在: {genus}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "HOST_GENUS_NOT_FOUND",
                    "message": f"宿主属无疾病或不存在: {genus}",
                    "detail": "请检查genus参数是否正确（支持：Rosa, Prunus, Tulipa, Dianthus, Paeonia）"
                }
            )

        # 3. 转换为Schema格式
        disease_schemas = []
        for disease in diseases:
            # 提取宿主属（从host_plants中获取第一个genus）
            host_genus = None
            if disease.host_plants and len(disease.host_plants) > 0:
                host_genus = disease.host_plants[0].get("genus")

            disease_schema = KnowledgeDiseaseSchema(
                disease_id=disease.disease_id,
                disease_name=disease.disease_name,
                common_name_en=disease.common_name_en,
                pathogen=disease.pathogen,
                host_genus=host_genus
            )
            disease_schemas.append(disease_schema)

        # 4. 构建响应（需要从knowledge_tree中获取宿主属的中英文名称）
        # 为了简化，先尝试从knowledge_tree中查找
        name_zh = None
        name_en = None
        try:
            tree_data = knowledge_service.get_knowledge_tree()
            for host in tree_data.get("hosts", []):
                if host.get("genus") == genus:
                    name_zh = host.get("name_zh")
                    name_en = host.get("name_en")
                    break
        except Exception as e:
            logger.warning(f"获取宿主属名称失败，使用默认值: {e}")

        response = HostDiseasesResponseSchema(
            genus=genus,
            name_zh=name_zh,
            name_en=name_en,
            total=len(disease_schemas),
            diseases=disease_schemas
        )

        logger.info(f"成功查询宿主属 {genus} 的疾病：{response.total} 种")
        return response

    except HTTPException:
        # 重新抛出HTTP异常（404）
        raise
    except KnowledgeServiceException as e:
        logger.error(f"知识库服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "KNOWLEDGE_SERVICE_ERROR",
                "message": str(e),
                "detail": "知识库服务异常，请检查知识库是否正确初始化"
            }
        )
    except Exception as e:
        logger.error(f"按宿主属查询疾病失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "按宿主属查询疾病失败",
                "detail": str(e)
            }
        )


def main():
    """
    调用示例：演示如何测试知识库管理API

    此函数展示了如何使用FastAPI的TestClient测试知识库管理路由
    """
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    print("=" * 60)
    print("知识库管理API 路由测试示例")
    print("=" * 60)

    # 创建FastAPI应用并注册路由
    app = FastAPI()
    app.include_router(router, prefix="/api/v1", tags=["Knowledge"])

    # 创建TestClient
    client = TestClient(app)

    # 1. 测试GET /api/v1/knowledge/diseases（所有疾病）
    print("\n1. 测试GET /api/v1/knowledge/diseases（所有疾病）")
    response = client.get("/api/v1/knowledge/diseases")
    print(f"  - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 疾病总数: {data.get('total')}")
        print(f"  - 疾病列表: {len(data.get('diseases', []))} 条记录")
    else:
        print(f"  - 错误: {response.json()}")

    # 2. 测试GET /api/v1/knowledge/diseases?genus=Rosa（按宿主属筛选）
    print("\n2. 测试GET /api/v1/knowledge/diseases?genus=Rosa（按宿主属筛选）")
    response = client.get("/api/v1/knowledge/diseases?genus=Rosa")
    print(f"  - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 玫瑰属疾病数: {data.get('total')}")
    else:
        print(f"  - 错误: {response.json()}")

    # 3. 测试GET /api/v1/knowledge/diseases/{disease_id}（疾病详情）
    print("\n3. 测试GET /api/v1/knowledge/diseases/rosa_blackspot（疾病详情）")
    response = client.get("/api/v1/knowledge/diseases/rosa_blackspot")
    print(f"  - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 疾病名称: {data.get('disease_name')}")
        print(f"  - 疾病ID: {data.get('disease_id')}")
        print(f"  - 版本: {data.get('version')}")
    elif response.status_code == 404:
        print(f"  - 疾病不存在（符合预期）")
    else:
        print(f"  - 错误: {response.json()}")

    # 4. 测试GET /api/v1/knowledge/tree（知识库树）
    print("\n4. 测试GET /api/v1/knowledge/tree（知识库树）")
    response = client.get("/api/v1/knowledge/tree")
    print(f"  - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 总宿主数: {data.get('total_hosts')}")
        print(f"  - 总疾病数: {data.get('total_diseases')}")
        print(f"  - 版本: {data.get('version')}")
    else:
        print(f"  - 错误: {response.json()}")

    # 5. 测试GET /api/v1/knowledge/hosts/{genus}（按宿主属查询）
    print("\n5. 测试GET /api/v1/knowledge/hosts/Rosa（按宿主属查询）")
    response = client.get("/api/v1/knowledge/hosts/Rosa")
    print(f"  - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - 宿主属: {data.get('genus')} ({data.get('name_zh')})")
        print(f"  - 疾病总数: {data.get('total')}")
    elif response.status_code == 404:
        print(f"  - 宿主属不存在（符合预期）")
    else:
        print(f"  - 错误: {response.json()}")

    print("\n" + "=" * 60)
    print("所有路由测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
