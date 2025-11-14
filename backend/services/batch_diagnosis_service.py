"""
批量诊断服务 (BatchDiagnosisService) - P4.5实现

功能：
- 管理批量诊断任务的生命周期
- 异步执行批量图片诊断（使用asyncio.create_task）
- 内存存储任务状态（全局字典缓存）
- 提供进度查询和结果查询接口

核心特性：
- 支持最多100张图片批量上传
- 复用DiagnosisService.diagnose()进行单图诊断
- 任务状态管理：processing → completed/failed
- 手动刷新方案（无WebSocket/自动轮询）

实现阶段：P4.5
对应设计文档：详细设计文档v2.0 第6.6节

架构说明：
- BatchTask: 批量任务数据类（内存存储）
- BatchDiagnosisService: 批量诊断服务类
  - create_batch_task(): 创建批量任务
  - _execute_batch_diagnosis(): 后台异步执行批量诊断
  - get_batch_result(): 获取批量诊断结果
  - get_batch_progress(): 获取批量诊断进度

作者：AI Python Architect
日期：2025-11-15
"""

import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import time

# DiagnosisService
from backend.services.diagnosis_service import DiagnosisService, UnsupportedImageException

# ImageService
from backend.services.image_service import ImageService

# Domain模型
from backend.domain.diagnosis import DiagnosisResult, ConfidenceLevel

# VLM异常
from backend.infrastructure.llm.vlm_exceptions import VLMException


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 批量任务数据类 ====================

@dataclass
class ImageTask:
    """
    单个图片任务

    字段说明：
    - image_id: 图片ID
    - image_filename: 图片文件名
    - image_bytes: 图片字节数据
    - flower_genus: 花卉种属（可选）
    - status: 任务状态（pending | processing | completed | failed）
    - started_at: 开始处理时间
    - completed_at: 完成处理时间
    - diagnosis_result: 诊断结果（DiagnosisResult对象）
    - execution_time_ms: 执行耗时（毫秒）
    - error: 错误信息
    """
    image_id: str
    image_filename: str
    image_bytes: bytes
    flower_genus: Optional[str] = None
    status: str = "pending"  # pending | processing | completed | failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    diagnosis_result: Optional[DiagnosisResult] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


@dataclass
class BatchTask:
    """
    批量诊断任务

    字段说明：
    - batch_id: 批量任务ID（格式：batch_YYYYMMDD_HHmmss）
    - status: 任务状态（processing | completed | failed）
    - total_images: 总图片数量
    - completed_images: 已完成图片数量
    - failed_images: 失败图片数量
    - created_at: 创建时间
    - completed_at: 完成时间
    - image_tasks: 图片任务列表（List[ImageTask]）
    - current_image_task: 当前处理中的图片任务
    """
    batch_id: str
    status: str = "processing"  # processing | completed | failed
    total_images: int = 0
    completed_images: int = 0
    failed_images: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    image_tasks: List[ImageTask] = field(default_factory=list)
    current_image_task: Optional[ImageTask] = None


# ==================== 批量诊断服务类 ====================

class BatchDiagnosisService:
    """
    批量诊断服务类

    功能：
    - 创建批量诊断任务
    - 异步执行批量诊断（后台任务）
    - 查询批量诊断结果
    - 查询批量诊断进度

    依赖：
    - DiagnosisService: 单图诊断服务
    - ImageService: 图片存储服务

    使用示例：
    ```python
    # 1. 创建服务实例
    service = BatchDiagnosisService(
        diagnosis_service=diagnosis_service,
        image_service=image_service
    )

    # 2. 创建批量任务
    batch_id = await service.create_batch_task(
        images=[
            {"filename": "rose1.jpg", "bytes": b"..."},
            {"filename": "rose2.jpg", "bytes": b"..."}
        ],
        flower_genus="Rosa"
    )

    # 3. 查询进度
    progress = service.get_batch_progress(batch_id)

    # 4. 查询结果
    result = service.get_batch_result(batch_id)
    ```
    """

    # 全局批量任务缓存（内存存储）
    # 格式：{batch_id: BatchTask}
    _batch_tasks: Dict[str, BatchTask] = {}

    def __init__(
        self,
        diagnosis_service: DiagnosisService,
        image_service: ImageService,
        max_images_per_batch: int = 100,
        estimated_time_per_image_ms: int = 4000
    ):
        """
        初始化批量诊断服务

        Args:
            diagnosis_service: 诊断服务实例
            image_service: 图片服务实例
            max_images_per_batch: 单批次最大图片数量（默认100）
            estimated_time_per_image_ms: 单张图片预计耗时（默认4000ms）
        """
        self.diagnosis_service = diagnosis_service
        self.image_service = image_service
        self.max_images_per_batch = max_images_per_batch
        self.estimated_time_per_image_ms = estimated_time_per_image_ms

        logger.info(f"✅ BatchDiagnosisService初始化成功")
        logger.info(f"   - max_images_per_batch: {max_images_per_batch}")
        logger.info(f"   - estimated_time_per_image_ms: {estimated_time_per_image_ms}")

    async def create_batch_task(
        self,
        images: List[Dict[str, Any]],
        flower_genus: Optional[str] = None
    ) -> str:
        """
        创建批量诊断任务

        Args:
            images: 图片列表，每个元素包含：
                - filename: 文件名
                - bytes: 图片字节数据
            flower_genus: 花卉种属（可选，应用于所有图片）

        Returns:
            batch_id: 批量任务ID（格式：batch_YYYYMMDD_HHmmss）

        Raises:
            ValueError: 图片数量超过限制

        说明：
        - 验证图片数量（最多max_images_per_batch张）
        - 生成batch_id（基于当前时间戳）
        - 创建BatchTask对象并缓存到_batch_tasks
        - 启动后台异步任务（asyncio.create_task）
        """
        # 1. 验证图片数量
        if len(images) == 0:
            raise ValueError("图片数量不能为0")

        if len(images) > self.max_images_per_batch:
            raise ValueError(
                f"上传图片数量超过限制(最多{self.max_images_per_batch}张)，实际上传: {len(images)}"
            )

        # 2. 生成batch_id（格式：batch_YYYYMMDD_HHmmss）
        now = datetime.now()
        batch_id = f"batch_{now.strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"📦 创建批量诊断任务: {batch_id}")
        logger.info(f"   - total_images: {len(images)}")
        logger.info(f"   - flower_genus: {flower_genus}")

        # 3. 创建ImageTask列表
        image_tasks = []
        for idx, img in enumerate(images):
            # 生成image_id（格式：img_YYYYMMDD_HHmmss_001）
            image_id = f"img_{now.strftime('%Y%m%d_%H%M%S')}_{idx+1:03d}"

            image_task = ImageTask(
                image_id=image_id,
                image_filename=img["filename"],
                image_bytes=img["bytes"],
                flower_genus=flower_genus
            )
            image_tasks.append(image_task)

        # 4. 创建BatchTask对象
        batch_task = BatchTask(
            batch_id=batch_id,
            status="processing",
            total_images=len(images),
            completed_images=0,
            failed_images=0,
            created_at=now,
            image_tasks=image_tasks
        )

        # 5. 缓存到全局字典
        self._batch_tasks[batch_id] = batch_task

        # 6. 启动后台异步任务
        asyncio.create_task(self._execute_batch_diagnosis(batch_id))

        logger.info(f"✅ 批量任务创建成功: {batch_id}，后台任务已启动")
        return batch_id

    async def _execute_batch_diagnosis(self, batch_id: str):
        """
        后台异步执行批量诊断（私有方法）

        Args:
            batch_id: 批量任务ID

        说明：
        - 遍历image_tasks，逐个调用DiagnosisService.diagnose()
        - 更新每个ImageTask的状态和结果
        - 更新BatchTask的completed_images、failed_images
        - 所有图片处理完成后，更新BatchTask.status = completed
        - 异常处理：单张图片失败不影响其他图片
        """
        batch_task = self._batch_tasks.get(batch_id)
        if not batch_task:
            logger.error(f"❌ 批量任务不存在: {batch_id}")
            return

        logger.info(f"🚀 开始执行批量诊断: {batch_id}")
        start_time = time.time()

        try:
            # 遍历所有图片任务
            for idx, image_task in enumerate(batch_task.image_tasks):
                # 更新当前处理的图片
                batch_task.current_image_task = image_task
                image_task.status = "processing"
                image_task.started_at = datetime.now()

                logger.info(f"   [{idx+1}/{batch_task.total_images}] 开始处理: {image_task.image_filename}")

                try:
                    # 调用DiagnosisService.diagnose()
                    image_start_time = time.time()
                    diagnosis_result = await self.diagnosis_service.diagnose(
                        image_bytes=image_task.image_bytes
                    )
                    image_end_time = time.time()

                    # 计算执行耗时
                    execution_time_ms = int((image_end_time - image_start_time) * 1000)

                    # 更新ImageTask
                    image_task.status = "completed"
                    image_task.completed_at = datetime.now()
                    image_task.diagnosis_result = diagnosis_result
                    image_task.execution_time_ms = execution_time_ms

                    # 更新BatchTask计数
                    batch_task.completed_images += 1

                    logger.info(f"   ✅ 诊断成功: {image_task.image_filename} ({execution_time_ms}ms)")
                    logger.info(f"      疾病: {diagnosis_result.disease_name} (confidence={diagnosis_result.confidence:.2f})")

                except UnsupportedImageException as e:
                    # 图像不支持（非植物或非花卉）
                    image_task.status = "failed"
                    image_task.completed_at = datetime.now()
                    image_task.error = f"UnsupportedImage: {str(e)}"
                    batch_task.failed_images += 1

                    logger.warning(f"   ⚠️ 图像不支持: {image_task.image_filename} - {str(e)}")

                except VLMException as e:
                    # VLM调用失败
                    image_task.status = "failed"
                    image_task.completed_at = datetime.now()
                    image_task.error = f"VLMError: {str(e)}"
                    batch_task.failed_images += 1

                    logger.error(f"   ❌ VLM调用失败: {image_task.image_filename} - {str(e)}")

                except Exception as e:
                    # 其他未知异常
                    image_task.status = "failed"
                    image_task.completed_at = datetime.now()
                    image_task.error = f"UnknownError: {str(e)}"
                    batch_task.failed_images += 1

                    logger.error(f"   ❌ 诊断失败: {image_task.image_filename} - {str(e)}")

            # 所有图片处理完成
            batch_task.status = "completed"
            batch_task.completed_at = datetime.now()
            batch_task.current_image_task = None

            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)

            logger.info(f"✅ 批量诊断完成: {batch_id}")
            logger.info(f"   - 总耗时: {total_time_ms}ms ({total_time_ms/1000:.1f}s)")
            logger.info(f"   - 成功: {batch_task.completed_images}, 失败: {batch_task.failed_images}")

        except Exception as e:
            # 批量任务整体失败（不太可能发生）
            batch_task.status = "failed"
            batch_task.completed_at = datetime.now()
            logger.error(f"❌ 批量诊断任务失败: {batch_id} - {str(e)}")

    def get_batch_result(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        获取批量诊断结果

        Args:
            batch_id: 批量任务ID

        Returns:
            dict: 批量诊断结果（符合BatchResultResponse Schema）
            None: 如果batch_id不存在

        说明：
        - 如果任务状态为processing，返回处理中响应
        - 如果任务状态为completed，返回完整结果（包含results和summary）
        - 如果任务状态为failed，返回失败响应
        """
        batch_task = self._batch_tasks.get(batch_id)
        if not batch_task:
            return None

        # 基础信息
        result = {
            "batch_id": batch_task.batch_id,
            "status": batch_task.status,
            "total_images": batch_task.total_images,
            "completed_images": batch_task.completed_images,
            "failed_images": batch_task.failed_images,
            "created_at": batch_task.created_at.isoformat() + "Z"
        }

        # 如果任务正在处理中
        if batch_task.status == "processing":
            # 计算预计完成时间
            if batch_task.completed_images > 0:
                # 基于已完成图片的平均耗时估算
                avg_time_ms = sum(
                    t.execution_time_ms for t in batch_task.image_tasks
                    if t.execution_time_ms is not None
                ) / batch_task.completed_images
                remaining_images = batch_task.total_images - batch_task.completed_images
                estimated_remaining_ms = int(avg_time_ms * remaining_images)
            else:
                # 基于默认预估时间
                estimated_remaining_ms = self.estimated_time_per_image_ms * batch_task.total_images

            estimated_completion_time = datetime.now() + timedelta(milliseconds=estimated_remaining_ms)

            result["estimated_completion_time"] = estimated_completion_time.isoformat() + "Z"
            result["message"] = "批量诊断进行中，请稍后刷新查询"

        # 如果任务已完成
        elif batch_task.status == "completed":
            result["completed_at"] = batch_task.completed_at.isoformat() + "Z"

            # 计算总执行耗时
            execution_time_ms = int(
                (batch_task.completed_at - batch_task.created_at).total_seconds() * 1000
            )
            result["execution_time_ms"] = execution_time_ms

            # 构建results数组
            results = []
            for image_task in batch_task.image_tasks:
                if image_task.status == "completed" and image_task.diagnosis_result:
                    # 诊断成功
                    diagnosis_result = image_task.diagnosis_result
                    results.append({
                        "image_id": image_task.image_id,
                        "image_filename": image_task.image_filename,
                        "diagnosis_id": f"diag_{image_task.image_id}",
                        "disease_id": diagnosis_result.disease_id or "unknown",
                        "disease_name": diagnosis_result.disease_name,
                        "level": diagnosis_result.level.value if isinstance(diagnosis_result.level, ConfidenceLevel) else diagnosis_result.level,
                        "confidence": diagnosis_result.confidence,
                        "vlm_provider": diagnosis_result.vlm_provider or "qwen-vl-plus",
                        "execution_time_ms": image_task.execution_time_ms
                    })
                else:
                    # 诊断失败
                    results.append({
                        "image_id": image_task.image_id,
                        "image_filename": image_task.image_filename,
                        "diagnosis_id": None,
                        "disease_id": None,
                        "disease_name": "诊断失败",
                        "level": "error",
                        "confidence": 0.0,
                        "vlm_provider": "unknown",
                        "execution_time_ms": image_task.execution_time_ms or 0,
                        "error": image_task.error
                    })

            result["results"] = results

            # 构建summary统计
            confirmed_count = sum(
                1 for t in batch_task.image_tasks
                if t.status == "completed" and t.diagnosis_result and t.diagnosis_result.level in [ConfidenceLevel.CONFIRMED, "confirmed"]
            )
            suspected_count = sum(
                1 for t in batch_task.image_tasks
                if t.status == "completed" and t.diagnosis_result and t.diagnosis_result.level in [ConfidenceLevel.SUSPECTED, "suspected"]
            )
            unlikely_count = sum(
                1 for t in batch_task.image_tasks
                if t.status == "completed" and t.diagnosis_result and t.diagnosis_result.level in [ConfidenceLevel.UNLIKELY, "unlikely"]
            )
            error_count = batch_task.failed_images

            # 计算平均置信度（仅统计成功的任务）
            success_tasks = [
                t for t in batch_task.image_tasks
                if t.status == "completed" and t.diagnosis_result
            ]
            if success_tasks:
                average_confidence = sum(
                    t.diagnosis_result.confidence for t in success_tasks
                ) / len(success_tasks)
                average_execution_time_ms = sum(
                    t.execution_time_ms for t in success_tasks
                ) / len(success_tasks)
            else:
                average_confidence = 0.0
                average_execution_time_ms = 0

            result["summary"] = {
                "confirmed_count": confirmed_count,
                "suspected_count": suspected_count,
                "unlikely_count": unlikely_count,
                "error_count": error_count,
                "average_confidence": round(average_confidence, 2),
                "average_execution_time_ms": int(average_execution_time_ms)
            }

        # 如果任务失败
        elif batch_task.status == "failed":
            result["completed_at"] = batch_task.completed_at.isoformat() + "Z"
            result["message"] = "批量诊断任务失败"

        return result

    def get_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        获取批量诊断进度

        Args:
            batch_id: 批量任务ID

        Returns:
            dict: 批量诊断进度（符合BatchProgressResponse Schema）
            None: 如果batch_id不存在

        说明：
        - 返回当前进度百分比、已完成数量、失败数量等
        - 如果任务正在处理中，返回current_image信息
        - 如果任务已完成，返回completed_at
        """
        batch_task = self._batch_tasks.get(batch_id)
        if not batch_task:
            return None

        # 计算进度百分比
        progress_percentage = int(
            (batch_task.completed_images + batch_task.failed_images) / batch_task.total_images * 100
        )

        result = {
            "batch_id": batch_task.batch_id,
            "status": batch_task.status,
            "total_images": batch_task.total_images,
            "completed_images": batch_task.completed_images,
            "failed_images": batch_task.failed_images,
            "progress_percentage": progress_percentage,
            "created_at": batch_task.created_at.isoformat() + "Z"
        }

        # 如果任务正在处理中
        if batch_task.status == "processing":
            # 当前处理的图片信息
            if batch_task.current_image_task:
                result["current_image"] = {
                    "image_id": batch_task.current_image_task.image_id,
                    "image_filename": batch_task.current_image_task.image_filename,
                    "started_at": batch_task.current_image_task.started_at.isoformat() + "Z"
                }

            # 计算平均单张图片耗时（基于已完成的图片）
            completed_tasks = [
                t for t in batch_task.image_tasks
                if t.status == "completed" and t.execution_time_ms is not None
            ]
            if completed_tasks:
                average_time_per_image_ms = int(
                    sum(t.execution_time_ms for t in completed_tasks) / len(completed_tasks)
                )
                result["average_time_per_image_ms"] = average_time_per_image_ms

                # 预计完成时间
                remaining_images = batch_task.total_images - batch_task.completed_images - batch_task.failed_images
                estimated_remaining_ms = average_time_per_image_ms * remaining_images
                estimated_completion_time = datetime.now() + timedelta(milliseconds=estimated_remaining_ms)
                result["estimated_completion_time"] = estimated_completion_time.isoformat() + "Z"
            else:
                # 使用默认预估时间
                estimated_remaining_ms = self.estimated_time_per_image_ms * (
                    batch_task.total_images - batch_task.completed_images - batch_task.failed_images
                )
                estimated_completion_time = datetime.now() + timedelta(milliseconds=estimated_remaining_ms)
                result["estimated_completion_time"] = estimated_completion_time.isoformat() + "Z"

        # 如果任务已完成
        elif batch_task.status in ["completed", "failed"]:
            result["completed_at"] = batch_task.completed_at.isoformat() + "Z"
            if batch_task.status == "completed":
                result["message"] = "批量诊断已完成，可查询完整结果"
            else:
                result["message"] = "批量诊断任务失败"

        return result

    @classmethod
    def clear_all_tasks(cls):
        """
        清空所有批量任务缓存（用于测试）

        注意：生产环境请谨慎使用
        """
        cls._batch_tasks.clear()
        logger.info("✅ 已清空所有批量任务缓存")

    @classmethod
    def get_all_batch_ids(cls) -> List[str]:
        """
        获取所有批量任务ID（用于测试）

        Returns:
            List[str]: 批量任务ID列表
        """
        return list(cls._batch_tasks.keys())


# ==================== 主函数 ====================

async def main():
    """
    BatchDiagnosisService使用示例

    演示如何创建批量任务、查询进度、查询结果
    """
    print("\n" + "=" * 60)
    print("BatchDiagnosisService使用示例")
    print("=" * 60 + "\n")

    # 说明：本示例仅演示接口调用方式，不实际执行诊断
    # 实际使用时需要注入DiagnosisService和ImageService

    print("✅ 使用示例（伪代码）：")
    print()
    print("# 1. 创建服务实例")
    print("service = BatchDiagnosisService(")
    print("    diagnosis_service=diagnosis_service,")
    print("    image_service=image_service")
    print(")")
    print()
    print("# 2. 创建批量任务")
    print("batch_id = await service.create_batch_task(")
    print("    images=[")
    print("        {'filename': 'rose1.jpg', 'bytes': b'...'},")
    print("        {'filename': 'rose2.jpg', 'bytes': b'...'},")
    print("    ],")
    print("    flower_genus='Rosa'")
    print(")")
    print(f"# batch_id: batch_20251115_143000")
    print()
    print("# 3. 查询进度")
    print("progress = service.get_batch_progress(batch_id)")
    print("# progress: {")
    print("#   'batch_id': 'batch_20251115_143000',")
    print("#   'status': 'processing',")
    print("#   'progress_percentage': 46,")
    print("#   'completed_images': 23,")
    print("#   'total_images': 50")
    print("# }")
    print()
    print("# 4. 查询结果（任务完成后）")
    print("result = service.get_batch_result(batch_id)")
    print("# result: {")
    print("#   'batch_id': 'batch_20251115_143000',")
    print("#   'status': 'completed',")
    print("#   'results': [...],  # 所有诊断结果")
    print("#   'summary': {...}   # 汇总统计")
    print("# }")

    print("\n" + "=" * 60)
    print("✅ 示例完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
