"""
历史数据管理服务

管理推理历史记录，包括单张推理和批量推理的数据。
"""
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from models import DiagnosisResult, BatchDiagnosisItem


class HistoryManager:
    """历史数据管理器"""

    SESSION_KEY_HISTORY = "diagnosis_history"
    SESSION_KEY_DIAGNOSIS_RESULTS = "diagnosis_results_dict"

    @classmethod
    def initialize_session_state(cls) -> None:
        """初始化session state"""
        if cls.SESSION_KEY_HISTORY not in st.session_state:
            st.session_state[cls.SESSION_KEY_HISTORY] = []

        if cls.SESSION_KEY_DIAGNOSIS_RESULTS not in st.session_state:
            st.session_state[cls.SESSION_KEY_DIAGNOSIS_RESULTS] = {}

    @classmethod
    def add_diagnosis_record(
        cls,
        diagnosis_result: DiagnosisResult,
        image_name: str,
        annotation_status: Optional[str] = None,
        actual_disease_id: Optional[str] = None,
        actual_disease_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        添加单张推理记录到历史

        Args:
            diagnosis_result: 推理结果
            image_name: 图片名称
            annotation_status: 标注状态
            actual_disease_id: 实际疾病ID
            actual_disease_name: 实际疾病名称
            notes: 标注备注
        """
        cls.initialize_session_state()

        # 创建BatchDiagnosisItem
        item = BatchDiagnosisItem(
            image_name=image_name,
            image_id=diagnosis_result.image_id,
            diagnosis_id=diagnosis_result.diagnosis_id,
            flower_genus=diagnosis_result.q0_sequence["q0_2_flower_genus"].choice,
            disease_id=diagnosis_result.final_diagnosis.disease_id,
            disease_name=diagnosis_result.final_diagnosis.disease_name,
            confidence_level=diagnosis_result.final_diagnosis.confidence_level,
            confidence_score=diagnosis_result.final_diagnosis.confidence_score,
            annotation_status=annotation_status,
            actual_disease_id=actual_disease_id,
            actual_disease_name=actual_disease_name,
            notes=notes,
            diagnosed_at=diagnosis_result.timestamp  # 修复: 使用 timestamp 而不是 created_at
        )

        # 添加到历史列表
        st.session_state[cls.SESSION_KEY_HISTORY].append(item)

        # 存储完整的诊断结果
        st.session_state[cls.SESSION_KEY_DIAGNOSIS_RESULTS][diagnosis_result.image_id] = diagnosis_result

    @classmethod
    def get_all_history_items(cls) -> List[BatchDiagnosisItem]:
        """获取所有历史记录"""
        cls.initialize_session_state()
        return st.session_state[cls.SESSION_KEY_HISTORY]

    @classmethod
    def get_diagnosis_result(cls, image_id: str) -> Optional[DiagnosisResult]:
        """
        根据image_id获取完整的诊断结果

        Args:
            image_id: 图片ID

        Returns:
            诊断结果对象，如果不存在则返回None
        """
        cls.initialize_session_state()
        return st.session_state[cls.SESSION_KEY_DIAGNOSIS_RESULTS].get(image_id)

    @classmethod
    def get_all_diagnosis_results(cls) -> Dict[str, DiagnosisResult]:
        """获取所有诊断结果"""
        cls.initialize_session_state()
        return st.session_state[cls.SESSION_KEY_DIAGNOSIS_RESULTS]

    @classmethod
    def update_annotation(
        cls,
        image_id: str,
        annotation_status: str,
        actual_disease_id: Optional[str] = None,
        actual_disease_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        更新历史记录的标注信息

        Args:
            image_id: 图片ID
            annotation_status: 标注状态
            actual_disease_id: 实际疾病ID
            actual_disease_name: 实际疾病名称
            notes: 标注备注
        """
        cls.initialize_session_state()

        # 更新历史记录
        history = st.session_state[cls.SESSION_KEY_HISTORY]
        for item in history:
            if item.image_id == image_id:
                item.annotation_status = annotation_status
                item.actual_disease_id = actual_disease_id
                item.actual_disease_name = actual_disease_name
                item.notes = notes
                break

    @classmethod
    def clear_history(cls) -> None:
        """清空历史记录"""
        st.session_state[cls.SESSION_KEY_HISTORY] = []
        st.session_state[cls.SESSION_KEY_DIAGNOSIS_RESULTS] = {}

    @classmethod
    def get_history_statistics(cls) -> Dict[str, int]:
        """
        获取历史记录统计信息

        Returns:
            统计信息字典
        """
        cls.initialize_session_state()
        history = st.session_state[cls.SESSION_KEY_HISTORY]

        total = len(history)
        annotated = sum(1 for item in history if item.annotation_status is not None)
        correct = sum(1 for item in history if item.annotation_status == "correct")
        incorrect = sum(1 for item in history if item.annotation_status == "incorrect")
        uncertain = sum(1 for item in history if item.annotation_status == "uncertain")

        return {
            "total": total,
            "annotated": annotated,
            "unannotated": total - annotated,
            "correct": correct,
            "incorrect": incorrect,
            "uncertain": uncertain,
            "accuracy_rate": correct / annotated if annotated > 0 else None
        }


def get_history_manager() -> HistoryManager:
    """获取历史管理器实例"""
    return HistoryManager
