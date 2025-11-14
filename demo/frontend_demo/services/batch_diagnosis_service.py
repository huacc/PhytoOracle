"""
批量推理服务

提供批量图片推理、统计分析、混淆矩阵计算等功能。
"""
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import time

from models import (
    DiagnosisResult,
    BatchDiagnosisItem,
    BatchStatistics,
    ConfusionMatrixData,
    BatchDiagnosisResult,
    Annotation,
)
from services.mock_diagnosis_engine import get_diagnosis_engine


class BatchDiagnosisService:
    """批量推理服务"""

    def __init__(self):
        """初始化服务"""
        self.engine = get_diagnosis_engine()

    def create_batch(
        self,
        image_files: List[Tuple[str, str]]  # List of (image_path, image_name)
    ) -> BatchDiagnosisResult:
        """
        创建批量推理任务

        Args:
            image_files: 图片文件列表 [(path, name), ...]

        Returns:
            批量推理结果（初始状态）
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"

        return BatchDiagnosisResult(
            batch_id=batch_id,
            created_at=datetime.now(),
            total_images=len(image_files),
            completed_count=0,
            failed_count=0,
            status="processing",
            items=[]
        )

    def process_batch(
        self,
        batch_result: BatchDiagnosisResult,
        image_files: List[Tuple[str, str]],
        progress_callback: Optional[callable] = None
    ) -> BatchDiagnosisResult:
        """
        执行批量推理

        Args:
            batch_result: 批量推理结果对象
            image_files: 图片文件列表 [(path, name), ...]
            progress_callback: 进度回调函数 callback(current, total)

        Returns:
            更新后的批量推理结果
        """
        items = []

        for idx, (image_path, image_name) in enumerate(image_files):
            try:
                # 模拟推理延迟（0.3-0.5秒）
                time.sleep(0.3)

                # 执行推理
                diagnosis_result: DiagnosisResult = self.engine.diagnose(
                    image_path=image_path,
                    image_name=image_name
                )

                # 转换为BatchDiagnosisItem
                item = BatchDiagnosisItem(
                    image_name=image_name,
                    image_id=diagnosis_result.image_id,
                    diagnosis_id=diagnosis_result.diagnosis_id,
                    flower_genus=diagnosis_result.q0_sequence["q0_2_flower_genus"].choice,
                    disease_id=diagnosis_result.final_diagnosis.disease_id,
                    disease_name=diagnosis_result.final_diagnosis.disease_name,
                    confidence_level=diagnosis_result.final_diagnosis.confidence_level,
                    confidence_score=diagnosis_result.final_diagnosis.confidence_score,
                    annotation_status=None,  # 初始未标注
                    actual_disease_id=None,
                    actual_disease_name=None,
                    notes=None,
                    diagnosed_at=diagnosis_result.timestamp
                )

                items.append(item)
                batch_result.completed_count += 1

            except Exception as e:
                print(f"[Error] 推理失败: {image_name}, 错误: {str(e)}")
                batch_result.failed_count += 1

            # 调用进度回调
            if progress_callback:
                progress_callback(idx + 1, len(image_files))

        batch_result.items = items
        batch_result.status = "completed" if batch_result.failed_count == 0 else "partial_failed"

        # 计算统计数据
        batch_result.statistics = self.calculate_statistics(items)

        return batch_result

    def calculate_statistics(
        self,
        items: List[BatchDiagnosisItem],
        annotations: Optional[Dict[str, Annotation]] = None
    ) -> BatchStatistics:
        """
        计算统计数据

        Args:
            items: 批量推理结果项列表
            annotations: 标注数据字典 {image_id: Annotation}

        Returns:
            统计数据
        """
        # 应用标注数据（如果提供）
        if annotations:
            for item in items:
                if item.image_id in annotations:
                    ann = annotations[item.image_id]
                    item.annotation_status = ann.is_accurate
                    item.actual_disease_id = ann.actual_disease_id
                    item.actual_disease_name = ann.actual_disease_name
                    item.notes = ann.notes

        # 基础统计
        total_count = len(items)
        annotated_items = [item for item in items if item.annotation_status is not None]
        annotated_count = len(annotated_items)
        unannotated_count = total_count - annotated_count

        correct_count = sum(1 for item in annotated_items if item.annotation_status == "correct")
        incorrect_count = sum(1 for item in annotated_items if item.annotation_status == "incorrect")
        uncertain_count = sum(1 for item in annotated_items if item.annotation_status == "uncertain")

        accuracy_rate = correct_count / annotated_count if annotated_count > 0 else None

        # 按置信度级别统计
        by_confidence = {}
        for level in ["confirmed", "suspected", "unlikely"]:
            level_items = [item for item in items if item.confidence_level == level]
            level_annotated = [item for item in level_items if item.annotation_status is not None]
            level_correct = sum(1 for item in level_annotated if item.annotation_status == "correct")

            by_confidence[level] = {
                "total": len(level_items),
                "annotated": len(level_annotated),
                "correct": level_correct,
                "accuracy": level_correct / len(level_annotated) if len(level_annotated) > 0 else None
            }

        # 按花卉属统计
        by_genus = {}
        all_genera = set(item.flower_genus for item in items)
        for genus in all_genera:
            genus_items = [item for item in items if item.flower_genus == genus]
            genus_annotated = [item for item in genus_items if item.annotation_status is not None]
            genus_correct = sum(1 for item in genus_annotated if item.annotation_status == "correct")

            by_genus[genus] = {
                "total": len(genus_items),
                "annotated": len(genus_annotated),
                "correct": genus_correct,
                "accuracy": genus_correct / len(genus_annotated) if len(genus_annotated) > 0 else None
            }

        return BatchStatistics(
            total_count=total_count,
            annotated_count=annotated_count,
            unannotated_count=unannotated_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            uncertain_count=uncertain_count,
            accuracy_rate=accuracy_rate,
            by_confidence=by_confidence,
            by_genus=by_genus
        )

    def calculate_confusion_matrix(
        self,
        items: List[BatchDiagnosisItem]
    ) -> Optional[ConfusionMatrixData]:
        """
        计算混淆矩阵

        Args:
            items: 批量推理结果项列表

        Returns:
            混淆矩阵数据（如果没有已标注样本，返回None）
        """
        # 只统计已标注的项
        annotated_items = [
            item for item in items
            if item.annotation_status in ["correct", "incorrect"] and item.actual_disease_id
        ]

        if not annotated_items:
            return None

        # 收集所有疾病标签
        all_diseases = set()
        for item in annotated_items:
            all_diseases.add(item.actual_disease_name)
            all_diseases.add(item.disease_name)

        labels = sorted(list(all_diseases))
        label_to_idx = {label: idx for idx, label in enumerate(labels)}

        # 初始化矩阵
        n = len(labels)
        matrix = [[0 for _ in range(n)] for _ in range(n)]

        # 填充矩阵
        for item in annotated_items:
            # 使用实际疾病作为行（actual），诊断疾病作为列（predicted）
            actual_label = item.actual_disease_name if item.annotation_status == "incorrect" else item.disease_name
            predicted_label = item.disease_name

            actual_idx = label_to_idx[actual_label]
            predicted_idx = label_to_idx[predicted_label]

            matrix[actual_idx][predicted_idx] += 1

        return ConfusionMatrixData(
            labels=labels,
            matrix=matrix,
            total_samples=len(annotated_items)
        )

    def update_annotation(
        self,
        batch_result: BatchDiagnosisResult,
        image_id: str,
        annotation: Annotation
    ) -> BatchDiagnosisResult:
        """
        更新单个图片的标注

        Args:
            batch_result: 批量推理结果
            image_id: 图片ID
            annotation: 标注数据

        Returns:
            更新后的批量推理结果
        """
        for item in batch_result.items:
            if item.image_id == image_id:
                item.annotation_status = annotation.is_accurate
                item.actual_disease_id = annotation.actual_disease_id
                item.actual_disease_name = annotation.actual_disease_name
                item.notes = annotation.notes
                break

        # 重新计算统计数据
        batch_result.statistics = self.calculate_statistics(batch_result.items)
        batch_result.confusion_matrix = self.calculate_confusion_matrix(batch_result.items)

        return batch_result

    def batch_update_annotations(
        self,
        batch_result: BatchDiagnosisResult,
        annotations: Dict[str, Annotation]
    ) -> BatchDiagnosisResult:
        """
        批量更新标注

        Args:
            batch_result: 批量推理结果
            annotations: 标注数据字典 {image_id: Annotation}

        Returns:
            更新后的批量推理结果
        """
        for image_id, annotation in annotations.items():
            batch_result = self.update_annotation(batch_result, image_id, annotation)

        return batch_result


# 全局单例
_batch_service_instance = None


def get_batch_diagnosis_service() -> BatchDiagnosisService:
    """获取批量推理服务单例"""
    global _batch_service_instance
    if _batch_service_instance is None:
        _batch_service_instance = BatchDiagnosisService()
    return _batch_service_instance
