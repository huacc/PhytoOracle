"""
诊断API路由模块 (P4.2 实现)

功能：
- POST /api/v1/diagnose - 执行疾病诊断
- GET /api/v1/diagnose/{diagnosis_id} - 查询诊断结果

实现阶段：P4.2
对应设计文档：详细设计文档v2.0 第6.2节

架构说明：
- 使用FastAPI的APIRouter创建路由
- 通过Depends注入DiagnosisService和ImageService
- 请求验证使用UploadFile（图片上传）
- 响应格式使用DiagnosisResponseSchema

作者：AI Python Architect
日期：2025-11-15
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import time

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse

# Schema导入
from backend.apps.api.schemas.diagnosis import (
    DiagnosisResponseSchema,
    DiagnosisSchema,
    DiagnosisScoreSchema,
    CandidateDiseaseSchema,
)

# 依赖注入
from backend.apps.api.deps import (
    get_diagnosis_service,
    get_image_service,
)

# Service导入
from backend.services.diagnosis_service import DiagnosisService, UnsupportedImageException
from backend.services.image_service import ImageService

# Domain模型
from backend.domain.diagnosis import DiagnosisResult, ConfidenceLevel

# VLM异常
from backend.infrastructure.llm.vlm_exceptions import VLMException


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 创建路由器
router = APIRouter()


def _convert_diagnosis_result_to_response(
    result: DiagnosisResult,
    image_id: Optional[str] = None,
    image_path: Optional[str] = None
) -> DiagnosisResponseSchema:
    """
    将DiagnosisResult转换为DiagnosisResponseSchema

    Args:
        result: 诊断服务返回的DiagnosisResult对象
        image_id: 图片ID（可选）
        image_path: 图片存储路径（可选）

    Returns:
        DiagnosisResponseSchema: API响应Schema对象

    说明：
    - 处理兜底场景（knowledge_base_fallback、no_candidate）
    - 转换评分详情（DiagnosisScore -> DiagnosisScoreSchema）
    - 转换候选疾病列表（candidates -> List[CandidateDiseaseSchema]）
    """
    # 1. 构建诊断信息
    diagnosis_schema = DiagnosisSchema(
        disease_id=result.disease_id or "unknown",
        disease_name=result.disease_name,
        common_name_en=result.common_name_en,
        pathogen=result.pathogen,
        level=result.level.value if isinstance(result.level, ConfidenceLevel) else result.level,
        confidence=result.confidence
    )

    # 2. 转换特征向量为Dict格式
    feature_vector_dict = {}
    if result.feature_vector:
        # 将FeatureVector对象转换为字典
        feature_vector_dict = result.feature_vector.model_dump()

    # 3. 转换评分详情（如果存在）
    scores_schema = None
    if result.scores:
        scores_schema = DiagnosisScoreSchema(
            total_score=result.scores.total_score,
            major_features=result.scores.major_features,
            minor_features=result.scores.minor_features,
            optional_features=result.scores.optional_features,
            completeness_modifier=result.scores.completeness_modifier,
            major_matched=result.scores.major_matched,
            major_total=result.scores.major_total
        )

    # 4. 转换候选疾病列表（如果存在）
    candidates_schema = None
    if result.candidates:
        candidates_schema = [
            CandidateDiseaseSchema(
                disease_id=candidate.get("disease_id", "unknown"),
                disease_name=candidate.get("disease_name", "未知"),
                score=candidate.get("score", 0.0),
                level=candidate.get("level", "unlikely")
            )
            for candidate in result.candidates
        ]

    # 5. 构建元数据
    metadata = {}
    if image_id:
        metadata["image_id"] = image_id
    if image_path:
        metadata["image_path"] = str(image_path)
    # 从result中提取知识库版本（如果存在）
    if hasattr(result, "metadata") and result.metadata:
        metadata.update(result.metadata)

    # 6. 构建响应Schema
    return DiagnosisResponseSchema(
        diagnosis_id=result.diagnosis_id,
        timestamp=result.timestamp,
        diagnosis=diagnosis_schema,
        feature_vector=feature_vector_dict,
        scores=scores_schema,
        reasoning=result.reasoning,
        candidates=candidates_schema,
        vlm_provider=result.vlm_provider,
        execution_time_ms=result.execution_time_ms,
        metadata=metadata if metadata else None
    )


@router.post(
    "/diagnose",
    response_model=DiagnosisResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="执行疾病诊断",
    description="上传花卉图片，执行VLM特征提取和知识库匹配，返回诊断结果",
    tags=["Diagnosis"]
)
async def diagnose(
    image: UploadFile = File(..., description="图片文件（JPG/PNG/HEIC）"),
    flower_genus: Optional[str] = Form(None, description="花卉种属（可选，提高准确率）"),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
    image_service: ImageService = Depends(get_image_service),
) -> DiagnosisResponseSchema:
    """
    执行疾病诊断（单图诊断）

    请求参数：
    - image: 图片文件（multipart/form-data）
    - flower_genus: 花卉种属（可选，Rosa/Prunus/Tulipa/Dianthus/Paeonia）

    响应格式：
    - diagnosis_id: 诊断唯一标识符
    - timestamp: 诊断时间戳
    - diagnosis: 诊断结果（disease_id、disease_name、level、confidence）
    - feature_vector: VLM提取的特征向量
    - scores: 特征匹配得分详情
    - reasoning: 诊断推理过程
    - candidates: 候选疾病列表
    - vlm_provider: VLM提供商
    - execution_time_ms: 执行耗时

    异常处理：
    - 400: 图片格式无效或不支持的图像类型
    - 500: VLM服务异常或诊断服务异常
    - 503: 所有VLM提供商不可用

    对应设计文档：详细设计文档v2.0 第6.2.1节
    """
    start_time = time.time()
    logger.info(f"收到诊断请求: filename={image.filename}, flower_genus={flower_genus}")

    try:
        # 1. 读取图片内容
        image_bytes = await image.read()
        logger.info(f"图片读取成功: size={len(image_bytes)} bytes")

        # 2. 调用诊断服务执行诊断
        logger.info("开始执行诊断流程...")
        diagnosis_result = await diagnosis_service.diagnose(image_bytes=image_bytes)
        logger.info(f"诊断完成: disease={diagnosis_result.disease_name}, level={diagnosis_result.level}")

        # 3. 保存图片（如果诊断成功）
        image_id = None
        image_path = None
        try:
            # 根据诊断结果决定存储分类
            # confirmed -> labeled/genus/disease_id
            # suspected -> unlabeled/genus
            # unlikely -> unlabeled/unknown
            if diagnosis_result.level == ConfidenceLevel.CONFIRMED:
                # 确诊：保存到labeled/{genus}/{disease_id}目录
                category = "labeled"
                subcategory = diagnosis_result.feature_vector.flower_genus.value if diagnosis_result.feature_vector else "unknown"
                disease_folder = diagnosis_result.disease_id or "unknown"
                storage_path = Path(category) / subcategory / disease_folder
            elif diagnosis_result.level == ConfidenceLevel.SUSPECTED:
                # 疑似：保存到unlabeled/{genus}目录
                category = "unlabeled"
                subcategory = diagnosis_result.feature_vector.flower_genus.value if diagnosis_result.feature_vector else "unknown"
                storage_path = Path(category) / subcategory
            else:
                # 不太可能/兜底：保存到unlabeled/unknown目录
                category = "unlabeled"
                subcategory = "unknown"
                storage_path = Path(category) / subcategory

            # 保存图片
            image_id = await image_service.save_image(
                image_bytes=image_bytes,
                filename=image.filename or "unknown.jpg",
                relative_path=str(storage_path),
                diagnosis_id=diagnosis_result.diagnosis_id
            )
            logger.info(f"图片保存成功: image_id={image_id}, path={storage_path}")

            # 获取图片完整路径（用于响应中的metadata）
            # 注意：这里不直接暴露磁盘绝对路径，而是返回相对路径
            image_path = storage_path / image.filename

        except Exception as e:
            # 图片保存失败不影响诊断结果返回
            logger.warning(f"图片保存失败（不影响诊断结果）: {e}")

        # 4. 转换为响应Schema
        response = _convert_diagnosis_result_to_response(
            result=diagnosis_result,
            image_id=image_id,
            image_path=str(image_path) if image_path else None
        )

        # 5. 计算总耗时
        total_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"诊断请求处理完成: total_time={total_time_ms}ms")

        return response

    except UnsupportedImageException as e:
        # 不支持的图像类型（如非植物、非花卉）
        logger.error(f"不支持的图像类型: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "UNSUPPORTED_IMAGE_TYPE",
                "message": str(e),
                "detail": "图片内容不符合诊断要求（非花卉植物图片）"
            }
        )

    except VLMException as e:
        # VLM服务异常（已在main.py的异常处理器中处理，但这里也可以捕获）
        logger.error(f"VLM服务异常: {e}")
        raise

    except Exception as e:
        # 其他未知异常
        logger.exception(f"诊断服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DIAGNOSIS_SERVICE_ERROR",
                "message": "诊断服务内部错误",
                "detail": str(e)
            }
        )


@router.get(
    "/diagnose/{diagnosis_id}",
    response_model=DiagnosisResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="查询诊断结果",
    description="根据诊断ID查询诊断结果（从数据库或缓存中获取）",
    tags=["Diagnosis"]
)
async def get_diagnosis_result(
    diagnosis_id: str,
    image_service: ImageService = Depends(get_image_service),
) -> DiagnosisResponseSchema:
    """
    查询诊断结果

    路径参数：
    - diagnosis_id: 诊断唯一标识符（格式：diag_YYYYMMDD_NNN）

    响应格式：
    - 与POST /diagnose接口相同

    异常处理：
    - 404: 诊断结果不存在
    - 500: 数据库查询异常

    对应设计文档：详细设计文档v2.0 第6.2.2节（注：v2.0中该接口未详细定义，这里基于最佳实践实现）

    说明：
    - 本阶段（P4.2）暂未实现诊断结果持久化到数据库
    - 当前返回404，提示功能尚未实现
    - 后续阶段（P4.3或P4.4）将实现数据库存储和查询功能
    """
    logger.info(f"查询诊断结果: diagnosis_id={diagnosis_id}")

    # TODO: P4.3或P4.4阶段实现诊断结果持久化和查询
    # 当前阶段（P4.2）暂不实现该功能
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "NOT_IMPLEMENTED",
            "message": "诊断结果查询功能尚未实现",
            "detail": "该功能将在P4.3或P4.4阶段实现诊断结果持久化后提供"
        }
    )


def main():
    """
    诊断路由模块测试示例

    说明：
    - 本模块是FastAPI路由，不能直接运行
    - 需要通过FastAPI应用（main.py）注册后使用
    - 运行方式：uvicorn apps.api.main:app --reload
    - 测试方式：使用Postman或curl发送请求

    测试示例：
    ```bash
    # 单图诊断
    curl -X POST http://localhost:8000/api/v1/diagnose \
      -F "image=@test_image.jpg" \
      -F "flower_genus=Prunus"

    # 查询诊断结果
    curl -X GET http://localhost:8000/api/v1/diagnose/diag_20251115_001
    ```
    """
    print("=" * 80)
    print("诊断API路由模块")
    print("=" * 80)
    print("\n本模块是FastAPI路由模块，不能直接运行。")
    print("请通过以下方式使用：")
    print("\n1. 启动FastAPI服务：")
    print("   cd D:\\项目管理\\PhytoOracle\\backend")
    print("   uvicorn apps.api.main:app --reload")
    print("\n2. 访问Swagger UI测试接口：")
    print("   http://localhost:8000/docs")
    print("\n3. 使用Postman或curl测试：")
    print("   POST http://localhost:8000/api/v1/diagnose")
    print("   - Form Data: image (file)")
    print("   - Form Data: flower_genus (optional, string)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
