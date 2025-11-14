"""
图片管理API路由模块 (P4.6 实现)

功能：
- GET /api/v1/images - 查询图片列表（支持分页、筛选）
- PATCH /api/v1/images/{image_id}/accuracy - 标注诊断准确性

实现阶段：P4.6
对应设计文档：详细设计文档v2.0 第6.7节

架构说明：
- 使用FastAPI的APIRouter创建路由
- 通过Depends注入ImageService
- 请求验证使用ImageListRequest、AccuracyUpdateRequest
- 响应格式使用ImageListResponse、AccuracyUpdateResponse
- 深度复用P3.6的ImageService和P3.9的update_accuracy_label方法

作者：AI Python Architect
日期：2025-11-15
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import time
import os

from fastapi import APIRouter, Depends, Query, HTTPException, status, Path as PathParam
from fastapi.responses import JSONResponse

# Schema导入
from backend.apps.api.schemas.images import (
    ImageListRequest,
    ImageListResponse,
    ImageItemSchema,
    ImageDiagnosisInfo,
    AccuracyUpdateRequest,
    AccuracyUpdateResponse,
)

# 依赖注入
from backend.apps.api.deps import get_image_service

# 服务导入
from backend.services.image_service import ImageService, ImageServiceException


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 创建路由器
router = APIRouter()


# ==================== 图片列表查询路由 ====================


def _map_accuracy_status_to_db(accuracy_status: Optional[str]) -> Optional[str]:
    """
    将API的accuracy_status映射为数据库的is_accurate字段

    API枚举值：
    - accurate -> correct
    - inaccurate -> incorrect
    - not_marked -> unknown

    Args:
        accuracy_status: API的准确性状态（accurate/inaccurate/not_marked）

    Returns:
        str: 数据库的is_accurate字段值（correct/incorrect/unknown）
        None: 如果accuracy_status为None
    """
    if accuracy_status is None:
        return None

    mapping = {
        "accurate": "correct",
        "inaccurate": "incorrect",
        "not_marked": "unknown"
    }

    return mapping.get(accuracy_status, accuracy_status)


def _map_db_accuracy_to_api(is_accurate: Optional[str]) -> str:
    """
    将数据库的is_accurate字段映射为API的accuracy_status

    数据库字段值：
    - correct -> accurate
    - incorrect -> inaccurate
    - unknown -> not_marked

    Args:
        is_accurate: 数据库的is_accurate字段值（correct/incorrect/unknown）

    Returns:
        str: API的准确性状态（accurate/inaccurate/not_marked）
    """
    if is_accurate is None:
        return "not_marked"

    mapping = {
        "correct": "accurate",
        "incorrect": "inaccurate",
        "unknown": "not_marked"
    }

    return mapping.get(is_accurate, "not_marked")


def _get_image_metadata(file_path: str, storage_base_path: Path) -> dict:
    """
    获取图片元数据（文件大小、尺寸、格式等）

    Args:
        file_path: 图片相对路径
        storage_base_path: 存储根目录

    Returns:
        dict: 包含file_size_bytes、width、height、format的字典
    """
    try:
        # 构建绝对路径
        full_path = storage_base_path / file_path

        # 如果文件不存在，返回空元数据
        if not full_path.exists():
            logger.warning(f"图片文件不存在: {full_path}")
            return {
                "file_size_bytes": None,
                "width": None,
                "height": None,
                "format": None
            }

        # 获取文件大小
        file_size_bytes = full_path.stat().st_size

        # 获取图片格式（从文件扩展名推断）
        format_ext = full_path.suffix.lower().lstrip(".")
        if format_ext == "jpeg":
            format_ext = "jpg"

        # 尝试获取图片尺寸（需要PIL库）
        width = None
        height = None
        try:
            from PIL import Image
            with Image.open(full_path) as img:
                width, height = img.size
        except ImportError:
            logger.debug("PIL库未安装，无法获取图片尺寸")
        except Exception as e:
            logger.debug(f"获取图片尺寸失败: {e}")

        return {
            "file_size_bytes": file_size_bytes,
            "width": width,
            "height": height,
            "format": format_ext if format_ext else None
        }

    except Exception as e:
        logger.warning(f"获取图片元数据失败: {e}")
        return {
            "file_size_bytes": None,
            "width": None,
            "height": None,
            "format": None
        }


@router.get(
    "/images",
    response_model=ImageListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询图片列表",
    description="查询图片列表（支持分页、筛选），返回图片元数据和关联的诊断信息",
    tags=["Images"]
)
async def list_images(
    start_date: Optional[str] = Query(None, description="开始日期（ISO 8601格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO 8601格式）"),
    flower_genus: Optional[str] = Query(None, description="花卉种属筛选"),
    has_diagnosis: Optional[bool] = Query(None, description="是否已诊断（true/false）"),
    accuracy_status: Optional[str] = Query(None, description="准确性标注状态（accurate/inaccurate/not_marked）"),
    page: int = Query(1, ge=1, description="页码（默认1）"),
    page_size: int = Query(50, ge=1, le=100, description="每页条数（默认50，最大100）"),
    image_service: ImageService = Depends(get_image_service),
) -> ImageListResponse:
    """
    查询图片列表（P4.6）

    请求参数：
    - start_date: 开始日期（ISO 8601格式，可选）
    - end_date: 结束日期（ISO 8601格式，可选）
    - flower_genus: 花卉种属筛选（可选）
    - has_diagnosis: 是否已诊断（true/false，可选）
    - accuracy_status: 准确性标注状态（accurate/inaccurate/not_marked，可选）
    - page: 页码（默认1）
    - page_size: 每页条数（默认50，最大100）

    响应格式：
    - total: 总记录数
    - page: 当前页码
    - page_size: 每页条数
    - images: 图片信息列表（List[ImageItemSchema]）

    异常处理：
    - 400: 参数验证失败（日期格式错误、accuracy_status枚举值无效等）
    - 500: 图片服务异常

    对应设计文档：详细设计文档v2.0 第6.7.1节
    """
    start_time = time.time()
    logger.info(f"收到图片列表查询请求: page={page}, page_size={page_size}, flower_genus={flower_genus}, accuracy_status={accuracy_status}")

    try:
        # 1. 参数验证和转换
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": f"start_date格式错误: {e}",
                        "detail": "请使用ISO 8601格式（如：2025-01-01T00:00:00Z）"
                    }
                )

        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "ValidationError",
                        "message": f"end_date格式错误: {e}",
                        "detail": "请使用ISO 8601格式（如：2025-01-31T23:59:59Z）"
                    }
                )

        # 验证accuracy_status枚举值
        if accuracy_status and accuracy_status not in ["accurate", "inaccurate", "not_marked"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": f"无效的accuracy_status: {accuracy_status}",
                    "detail": "有效值：accurate, inaccurate, not_marked"
                }
            )

        # 将API的accuracy_status映射为数据库的is_accurate字段
        is_accurate_db = _map_accuracy_status_to_db(accuracy_status)

        # 2. 调用ImageService查询图片（先不分页，获取所有符合条件的记录）
        logger.info(f"调用ImageService查询图片: flower_genus={flower_genus}, is_accurate={is_accurate_db}, start_date={start_date_obj}, end_date={end_date_obj}")

        all_images = image_service.query_images(
            flower_genus=flower_genus,
            is_accurate=is_accurate_db,
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        # 3. 如果has_diagnosis参数存在，过滤已诊断/未诊断的图片
        if has_diagnosis is not None:
            if has_diagnosis:
                # 只保留已诊断的图片（diagnosis_id不为空）
                all_images = [img for img in all_images if img.get("diagnosis_id")]
            else:
                # 只保留未诊断的图片（diagnosis_id为空）
                all_images = [img for img in all_images if not img.get("diagnosis_id")]

        # 4. 计算分页
        total = len(all_images)
        offset = (page - 1) * page_size
        limit = page_size

        # 分页切片
        paginated_images = all_images[offset:offset + limit]

        logger.info(f"查询结果: total={total}, page={page}, page_size={page_size}, current_count={len(paginated_images)}")

        # 5. 转换为ImageItemSchema
        image_items = []
        for img in paginated_images:
            # 获取图片元数据（文件大小、尺寸、格式）
            metadata = _get_image_metadata(
                img["file_path"],
                image_service.storage.base_path
            )

            # 构建诊断信息（如果存在）
            diagnosis_info = None
            if img.get("diagnosis_id"):
                # TODO: 从diagnoses表查询完整的诊断信息（当前仅使用images表的字段）
                diagnosis_info = ImageDiagnosisInfo(
                    diagnosis_id=img["diagnosis_id"],
                    disease_id=img.get("disease_id", "unknown"),
                    disease_name=img.get("disease_name", "未知"),
                    level=img.get("confidence_level", "unknown"),
                    confidence=0.0,  # TODO: 从diagnoses表获取
                    diagnosed_at=img.get("uploaded_at", datetime.now().isoformat())
                )

            # 构建ImageItemSchema
            image_item = ImageItemSchema(
                image_id=img["image_id"],
                image_filename=Path(img["file_path"]).name,
                image_path=img["file_path"],
                uploaded_at=img["uploaded_at"],
                file_size_bytes=metadata["file_size_bytes"],
                width=metadata["width"],
                height=metadata["height"],
                format=metadata["format"],
                diagnosis=diagnosis_info,
                accuracy_status=_map_db_accuracy_to_api(img.get("is_accurate")),
                accuracy_marked_at=img.get("updated_at") if img.get("is_accurate") in ["correct", "incorrect"] else None,
                accuracy_marked_by=None  # TODO: 从user表获取
            )

            image_items.append(image_item)

        # 6. 构建响应
        response = ImageListResponse(
            total=total,
            page=page,
            page_size=page_size,
            images=image_items
        )

        total_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"图片列表查询完成: total_time={total_time_ms}ms")

        return response

    except HTTPException:
        # 重新抛出HTTPException
        raise

    except ImageServiceException as e:
        # 图片服务异常
        logger.error(f"图片服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "IMAGE_SERVICE_ERROR",
                "message": "图片服务内部错误",
                "detail": str(e)
            }
        )

    except Exception as e:
        # 其他未知异常
        logger.exception(f"图片列表查询异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


# ==================== 准确性标注路由 ====================


@router.patch(
    "/images/{image_id}/accuracy",
    response_model=AccuracyUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="标注诊断准确性",
    description="标注诊断结果的准确性（accurate/inaccurate），支持备注和标注人信息",
    tags=["Images"]
)
async def update_accuracy(
    image_id: str = PathParam(..., description="图片ID"),
    request: AccuracyUpdateRequest = ...,
    image_service: ImageService = Depends(get_image_service),
) -> AccuracyUpdateResponse:
    """
    标注诊断准确性（P4.6）

    路径参数：
    - image_id: 图片ID

    请求参数：
    - accuracy_status: 准确性状态（accurate/inaccurate）
    - comment: 标注备注（可选）
    - marked_by: 标注人（可选）

    响应格式：
    - image_id: 图片ID
    - accuracy_status: 准确性状态（accurate/inaccurate）
    - comment: 标注备注
    - marked_at: 标注时间（ISO 8601格式）
    - marked_by: 标注人
    - diagnosis_id: 关联的诊断ID（可选）
    - message: 提示消息

    异常处理：
    - 400: 参数验证失败（accuracy_status枚举值无效、该图片尚未诊断等）
    - 404: image_id不存在
    - 500: 图片服务异常

    对应设计文档：详细设计文档v2.0 第6.7.2节
    """
    start_time = time.time()
    logger.info(f"收到准确性标注请求: image_id={image_id}, accuracy_status={request.accuracy_status}, marked_by={request.marked_by}")

    try:
        # 1. 验证accuracy_status枚举值
        if request.accuracy_status not in ["accurate", "inaccurate"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": f"无效的accuracy_status: {request.accuracy_status}",
                    "detail": "有效值：accurate, inaccurate"
                }
            )

        # 2. 查询图片元数据（验证图片是否存在）
        image_data = image_service.repository.get_by_id(image_id)
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "IMAGE_NOT_FOUND",
                    "message": f"图片不存在: {image_id}",
                    "detail": "请检查image_id是否正确"
                }
            )

        # 3. 验证图片是否已诊断（diagnosis_id不为空）
        if not image_data.get("diagnosis_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": "该图片尚未进行诊断，无法标注准确性",
                    "detail": "请先执行诊断后再标注准确性",
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": f"trace_{image_id}"
                }
            )

        # 4. 将API的accuracy_status映射为数据库的is_accurate字段
        is_accurate_db = _map_accuracy_status_to_db(request.accuracy_status)

        # 5. 调用ImageService更新准确性标签（复用P3.9的update_accuracy_label方法）
        logger.info(f"调用ImageService.update_accuracy_label: image_id={image_id}, is_accurate={is_accurate_db}, user_feedback={request.comment}")

        updated = image_service.update_accuracy_label(
            image_id=image_id,
            is_accurate=is_accurate_db,
            user_feedback=request.comment
        )

        if not updated:
            # 理论上不会走到这里（因为前面已经验证过图片存在）
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "IMAGE_NOT_FOUND",
                    "message": f"图片不存在或已删除: {image_id}",
                    "detail": "请检查image_id是否正确"
                }
            )

        # 6. 构建响应
        marked_at = datetime.now().isoformat()
        response = AccuracyUpdateResponse(
            image_id=image_id,
            accuracy_status=request.accuracy_status,
            comment=request.comment,
            marked_at=marked_at,
            marked_by=request.marked_by,
            diagnosis_id=image_data.get("diagnosis_id"),
            message="准确性标注已保存"
        )

        total_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"准确性标注完成: total_time={total_time_ms}ms")

        return response

    except HTTPException:
        # 重新抛出HTTPException
        raise

    except ImageServiceException as e:
        # 图片服务异常
        logger.error(f"图片服务异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "IMAGE_SERVICE_ERROR",
                "message": "图片服务内部错误",
                "detail": str(e)
            }
        )

    except Exception as e:
        # 其他未知异常
        logger.exception(f"准确性标注异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "detail": str(e)
            }
        )


# ==================== 主函数 ====================


def main():
    """
    图片管理路由模块测试示例

    说明：
    - 本模块是FastAPI路由，不能直接运行
    - 需要通过FastAPI应用（main.py）注册后使用
    - 运行方式：uvicorn apps.api.main:app --reload
    - 测试方式：使用Postman或curl发送请求

    测试示例：
    ```bash
    # 查询图片列表（无筛选）
    curl -X GET "http://localhost:8000/api/v1/images?page=1&page_size=50"

    # 查询图片列表（带筛选条件）
    curl -X GET "http://localhost:8000/api/v1/images?flower_genus=Rosa&accuracy_status=accurate&page=1&page_size=20"

    # 标注准确性
    curl -X PATCH "http://localhost:8000/api/v1/images/img_20250114_001/accuracy" \
      -H "Content-Type: application/json" \
      -d '{
        "accuracy_status": "accurate",
        "comment": "诊断结果准确",
        "marked_by": "expert@example.com"
      }'
    ```
    """
    print("=" * 80)
    print("图片管理API路由模块 (P4.6)")
    print("=" * 80)
    print("\n本模块是FastAPI路由模块，不能直接运行。")
    print("请通过以下方式使用：")
    print("\n1. 启动FastAPI服务：")
    print("   cd D:\\项目管理\\PhytoOracle\\backend")
    print("   uvicorn apps.api.main:app --reload")
    print("\n2. 访问Swagger UI测试接口：")
    print("   http://localhost:8000/docs")
    print("\n3. 支持的API接口：")
    print("   - GET /api/v1/images (查询图片列表)")
    print("   - PATCH /api/v1/images/{image_id}/accuracy (标注准确性)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
