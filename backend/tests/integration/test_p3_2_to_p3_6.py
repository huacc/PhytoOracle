"""
P3.2-P3.6 集成测试

测试范围：
- P3.2: Q1-Q6动态特征提取
- P3.3: 三层渐进诊断流程
- P3.4: VLM兜底策略
- P3.5: 知识库服务集成
- P3.6: 图片服务集成

测试方法：
1. 使用Mock VLM避免真实API调用
2. 测试完整诊断流程
3. 测试异常场景和边界情况
4. 验证服务间协作

作者：AI Python Architect
日期：2025-11-13
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from backend.services.diagnosis_service import DiagnosisService, DiagnosisException
from backend.services.knowledge_service import KnowledgeService
from backend.services.image_service import ImageService
from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology


# ============================================================================
# 测试工具函数
# ============================================================================

def create_mock_q0_responses() -> Dict[str, Any]:
    """创建Mock的Q0响应"""
    return {
        "q0_0_content": {"is_image_clear": "yes", "content_type": "flower"},
        "q0_1_category": {"category": "diseased"},
        "q0_2_genus": {"flower_genus": "Rosa"},
        "q0_3_organ": {"organ": "leaf"},
        "q0_4_completeness": {"completeness": "complete"},
        "q0_5_abnormality": {"abnormality": "present"}
    }


def create_mock_q1_q6_responses() -> Dict[str, Any]:
    """创建Mock的Q1-Q6响应"""
    return {
        "q1_color": {"feature_value": "black_spots"},
        "q2_texture": {"feature_value": "rough"},
        "q3_shape": {"feature_value": "circular"},
        "q4_distribution": {"feature_value": "scattered"},
        "q5_size": {"feature_value": "medium"},
        "q6_context": {"feature_value": "leaf_edges"}
    }


def create_mock_disease(disease_id: str, disease_name: str, genus: str) -> DiseaseOntology:
    """创建Mock疾病对象"""
    return DiseaseOntology(
        version="1.0",
        disease_id=disease_id,
        disease_name=disease_name,
        common_name_en=f"Test {disease_name}",
        pathogen=f"Pathogen of {disease_name}",
        feature_vector={
            "symptom_type": "necrosis_spot",
            "color_center": ["black"],
            "shape": ["circular"],
        },
        feature_importance={
            "major_features": {
                "features": [
                    {"dimension": "color", "expected_values": ["black_spots"], "weight": 0.9},
                    {"dimension": "shape", "expected_values": ["circular"], "weight": 0.8},
                ]
            },
            "minor_features": {
                "features": [
                    {"dimension": "size", "expected_values": ["medium"], "weight": 0.5},
                ]
            },
            "optional_features": {
                "features": [
                    {"dimension": "distribution", "expected_values": ["scattered"], "weight": 0.7},
                ]
            }
        },
        diagnosis_rules={
            "confirmed": [{"rule_id": "R1", "logic": "major >= 2", "confidence": 0.95}],
            "suspected": []
        },
        host_plants=[genus]
    )


# ============================================================================
# P3.2: Q1-Q6动态特征提取测试
# ============================================================================

class TestQ1Q6FeatureExtraction:
    """P3.2: Q1-Q6动态特征提取测试"""

    @pytest.fixture
    def mock_diagnosis_service(self, tmp_path):
        """创建Mock的DiagnosisService"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock KnowledgeService
        mock_kb_service = Mock(spec=KnowledgeService)
        mock_kb_service.get_diseases_by_genus.return_value = []

        # Mock VLM客户端
        mock_vlm_client = AsyncMock()

        with patch('backend.services.diagnosis_service.KnowledgeService', return_value=mock_kb_service), \
             patch('backend.services.diagnosis_service.MultiProviderVLMClient', return_value=mock_vlm_client):
            service = DiagnosisService(kb_path)
            service.vlm_client = mock_vlm_client
            return service

    @pytest.mark.asyncio
    async def test_execute_q1_q6_sequence_success(self, mock_diagnosis_service):
        """测试：成功执行Q1-Q6特征提取"""
        # 准备
        image_bytes = b"fake_image_data"
        q0_responses = create_mock_q0_responses()

        # Mock VLM返回
        mock_diagnosis_service.vlm_client.extract_features.side_effect = [
            {"feature_value": "black_spots"},  # Q1
            {"feature_value": "rough"},        # Q2
            {"feature_value": "circular"},     # Q3
            {"feature_value": "scattered"},    # Q4
            {"feature_value": "medium"},       # Q5
            {"feature_value": "leaf_edges"},   # Q6
        ]

        # 执行
        result = await mock_diagnosis_service.execute_q1_q6_sequence(image_bytes, q0_responses)

        # 验证
        assert "q1_color" in result
        assert "q2_texture" in result
        assert "q3_shape" in result
        assert "q4_distribution" in result
        assert "q5_size" in result
        assert "q6_context" in result

        # 验证VLM调用次数
        assert mock_diagnosis_service.vlm_client.extract_features.call_count == 6

    @pytest.mark.asyncio
    async def test_build_feature_vector(self, mock_diagnosis_service):
        """测试：构建特征向量"""
        # 准备
        q0_responses = create_mock_q0_responses()
        q1_q6_responses = create_mock_q1_q6_responses()

        # 执行
        feature_vector = mock_diagnosis_service.build_feature_vector(q0_responses, q1_q6_responses)

        # 验证
        assert "flower_genus" in feature_vector
        assert "organ" in feature_vector
        assert "color" in feature_vector
        assert "shape" in feature_vector
        assert feature_vector["flower_genus"] == "Rosa"

    @pytest.mark.asyncio
    async def test_execute_q1_q6_with_vlm_failure(self, mock_diagnosis_service):
        """测试：VLM调用失败时的处理"""
        # 准备
        image_bytes = b"fake_image_data"
        q0_responses = create_mock_q0_responses()

        # Mock VLM调用失败
        mock_diagnosis_service.vlm_client.extract_features.side_effect = Exception("VLM API错误")

        # 执行 & 验证
        with pytest.raises(DiagnosisException):
            await mock_diagnosis_service.execute_q1_q6_sequence(image_bytes, q0_responses)


# ============================================================================
# P3.3: 三层渐进诊断流程测试
# ============================================================================

class TestThreeLayerDiagnosisFlow:
    """P3.3: 三层渐进诊断流程测试"""

    @pytest.fixture
    def mock_diagnosis_service_full(self, tmp_path):
        """创建完整Mock的DiagnosisService"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock疾病数据
        mock_diseases = [
            create_mock_disease("rose_black_spot", "玫瑰黑斑病", "Rosa"),
            create_mock_disease("rose_rust", "玫瑰锈病", "Rosa"),
        ]

        # Mock KnowledgeService
        mock_kb_service = Mock(spec=KnowledgeService)
        mock_kb_service.get_diseases_by_genus.return_value = mock_diseases

        # Mock VLM客户端
        mock_vlm_client = AsyncMock()

        # Mock匹配器
        mock_matcher = Mock()
        mock_matcher.match.return_value = [
            {"disease_id": "rose_black_spot", "disease_name": "玫瑰黑斑病", "score": 0.85},
            {"disease_id": "rose_rust", "disease_name": "玫瑰锈病", "score": 0.45},
        ]

        with patch('backend.services.diagnosis_service.KnowledgeService', return_value=mock_kb_service), \
             patch('backend.services.diagnosis_service.MultiProviderVLMClient', return_value=mock_vlm_client), \
             patch('backend.services.diagnosis_service.FuzzyMatcher', return_value=mock_matcher):
            service = DiagnosisService(kb_path)
            service.vlm_client = mock_vlm_client
            service.kb_service = mock_kb_service
            service.matcher = mock_matcher
            return service

    @pytest.mark.asyncio
    async def test_diagnose_confirmed_case(self, mock_diagnosis_service_full):
        """测试：确诊病例（score >= 0.8）"""
        # 准备
        image_bytes = b"fake_image_data"

        # Mock Q0和Q1-Q6响应
        mock_diagnosis_service_full.execute_q0_sequence = AsyncMock(return_value=create_mock_q0_responses())
        mock_diagnosis_service_full.execute_q1_q6_sequence = AsyncMock(return_value=create_mock_q1_q6_responses())

        # 执行
        result = await mock_diagnosis_service_full.diagnose(image_bytes)

        # 验证
        assert result["diagnosis_status"] == "confirmed"
        assert result["top_disease"]["disease_id"] == "rose_black_spot"
        assert result["top_disease"]["confidence_score"] >= 0.8
        assert "flower_genus" in result
        assert result["flower_genus"] == "Rosa"

    @pytest.mark.asyncio
    async def test_diagnose_suspected_case(self, mock_diagnosis_service_full):
        """测试：疑似病例（0.5 <= score < 0.8）"""
        # 准备
        image_bytes = b"fake_image_data"

        # Mock返回中等置信度
        mock_diagnosis_service_full.matcher.match.return_value = [
            {"disease_id": "rose_black_spot", "disease_name": "玫瑰黑斑病", "score": 0.65},
        ]

        mock_diagnosis_service_full.execute_q0_sequence = AsyncMock(return_value=create_mock_q0_responses())
        mock_diagnosis_service_full.execute_q1_q6_sequence = AsyncMock(return_value=create_mock_q1_q6_responses())

        # 执行
        result = await mock_diagnosis_service_full.diagnose(image_bytes)

        # 验证
        assert result["diagnosis_status"] == "suspected"
        assert 0.5 <= result["top_disease"]["confidence_score"] < 0.8

    @pytest.mark.asyncio
    async def test_diagnose_healthy_case(self, mock_diagnosis_service_full):
        """测试：健康植株（Q0.1 category=healthy）"""
        # 准备
        image_bytes = b"fake_image_data"

        # Mock Q0返回健康
        mock_q0_responses = create_mock_q0_responses()
        mock_q0_responses["q0_1_category"]["category"] = "healthy"

        mock_diagnosis_service_full.execute_q0_sequence = AsyncMock(return_value=mock_q0_responses)

        # 执行
        result = await mock_diagnosis_service_full.diagnose(image_bytes)

        # 验证
        assert result["diagnosis_status"] == "healthy"
        assert "提前终止" in result.get("diagnosis_reason", "")

    @pytest.mark.asyncio
    async def test_diagnose_unknown_genus(self, mock_diagnosis_service_full):
        """测试：未知种属"""
        # 准备
        image_bytes = b"fake_image_data"

        # Mock Q0返回未知种属
        mock_q0_responses = create_mock_q0_responses()
        mock_q0_responses["q0_2_genus"]["flower_genus"] = "Unknown"

        # Mock知识库返回空
        mock_diagnosis_service_full.kb_service.get_diseases_by_genus.return_value = []

        mock_diagnosis_service_full.execute_q0_sequence = AsyncMock(return_value=mock_q0_responses())
        mock_diagnosis_service_full.execute_q1_q6_sequence = AsyncMock(return_value=create_mock_q1_q6_responses())

        # 执行
        result = await mock_diagnosis_service_full.diagnose(image_bytes)

        # 验证（应触发VLM兜底）
        assert result is not None


# ============================================================================
# P3.4: VLM兜底策略测试
# ============================================================================

class TestVLMFallbackStrategy:
    """P3.4: VLM兜底策略测试"""

    @pytest.fixture
    def mock_diagnosis_service_fallback(self, tmp_path):
        """创建带兜底的DiagnosisService"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        mock_kb_service = Mock(spec=KnowledgeService)
        mock_vlm_client = AsyncMock()

        with patch('backend.services.diagnosis_service.KnowledgeService', return_value=mock_kb_service), \
             patch('backend.services.diagnosis_service.MultiProviderVLMClient', return_value=mock_vlm_client):
            service = DiagnosisService(kb_path)
            service.vlm_client = mock_vlm_client
            return service

    @pytest.mark.asyncio
    async def test_vlm_fallback_triggered_low_confidence(self, mock_diagnosis_service_fallback):
        """测试：低置信度触发VLM兜底（score < 0.5）"""
        # 准备
        image_bytes = b"fake_image_data"
        feature_vector = {"flower_genus": "Rosa", "color": "black_spots"}
        q0_responses = create_mock_q0_responses()

        # Mock VLM兜底返回
        mock_diagnosis_service_fallback.vlm_client.fallback_diagnosis.return_value = {
            "disease_name": "VLM诊断：玫瑰黑斑病（可能）",
            "confidence_level": "suspected",
            "reasoning": "VLM兜底分析"
        }

        # 执行
        result = await mock_diagnosis_service_fallback._vlm_fallback_diagnosis(
            image_bytes=image_bytes,
            feature_vector=feature_vector,
            q0_responses=q0_responses
        )

        # 验证
        assert result["diagnosis_status"] == "suspected"
        assert "VLM兜底" in result.get("diagnosis_reason", "")

    @pytest.mark.asyncio
    async def test_vlm_fallback_triggered_unknown_genus(self, mock_diagnosis_service_fallback):
        """测试：未知种属触发VLM兜底"""
        # 准备
        image_bytes = b"fake_image_data"
        feature_vector = {"flower_genus": "Unknown"}
        q0_responses = create_mock_q0_responses()

        # Mock VLM兜底返回
        mock_diagnosis_service_fallback.vlm_client.fallback_diagnosis.return_value = {
            "disease_name": "未知疾病（需人工鉴定）",
            "confidence_level": "unknown",
            "reasoning": "种属不在知识库中"
        }

        # 执行
        result = await mock_diagnosis_service_fallback._vlm_fallback_diagnosis(
            image_bytes=image_bytes,
            feature_vector=feature_vector,
            q0_responses=q0_responses
        )

        # 验证
        assert result is not None
        assert "VLM兜底" in result.get("diagnosis_reason", "")


# ============================================================================
# P3.5: 知识库服务集成测试
# ============================================================================

class TestKnowledgeServiceIntegration:
    """P3.5: 知识库服务集成测试"""

    @pytest.fixture
    def real_knowledge_service(self, tmp_path):
        """创建真实的KnowledgeService（使用Mock数据）"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock KnowledgeBaseLoader
        mock_diseases = [
            create_mock_disease("rose_black_spot", "玫瑰黑斑病", "Rosa"),
            create_mock_disease("peony_leaf_blight", "牡丹叶枯病", "Paeonia"),
        ]

        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = mock_diseases
        mock_loader.get_feature_ontology.return_value = Mock(spec=FeatureOntology)

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            service = KnowledgeService(kb_path, auto_initialize=True)
            return service

    def test_knowledge_service_initialized(self, real_knowledge_service):
        """测试：知识库服务已初始化"""
        assert real_knowledge_service.is_initialized()

    def test_knowledge_service_query_by_genus(self, real_knowledge_service):
        """测试：按种属查询疾病"""
        # 查询玫瑰属
        rosa_diseases = real_knowledge_service.get_diseases_by_genus("Rosa")
        assert len(rosa_diseases) == 1
        assert rosa_diseases[0].disease_id == "rose_black_spot"

        # 查询牡丹属
        paeonia_diseases = real_knowledge_service.get_diseases_by_genus("Paeonia")
        assert len(paeonia_diseases) == 1

    def test_knowledge_service_get_version_info(self, real_knowledge_service):
        """测试：获取版本信息"""
        version_info = real_knowledge_service.get_version_info()
        assert version_info["disease_count"] == 2
        assert version_info["genus_count"] == 2


# ============================================================================
# P3.6: 图片服务集成测试
# ============================================================================

class TestImageServiceIntegration:
    """P3.6: 图片服务集成测试"""

    @pytest.fixture
    def real_image_service(self, tmp_path):
        """创建真实的ImageService（使用临时存储）"""
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test_images.db"

        # Mock LocalImageStorage和ImageRepository
        mock_storage = Mock()
        mock_storage.base_path = storage_path
        mock_storage.save_image.return_value = {
            "relative_path": "2025-11-13/test_img.jpg",
            "full_path": str(storage_path / "2025-11-13/test_img.jpg")
        }

        mock_repository = Mock()
        mock_repository.save.return_value = None
        mock_repository.query.return_value = []
        mock_repository.update_accuracy_label.return_value = True
        mock_repository.soft_delete.return_value = True

        with patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):
            service = ImageService(storage_path, db_path)
            service.storage = mock_storage
            service.repository = mock_repository
            return service

    def test_image_service_save_and_query(self, real_image_service):
        """测试：保存图片并查询"""
        # 保存图片
        result = real_image_service.save_image(
            image_bytes=b"test_data",
            flower_genus="Rosa",
            diagnosis_id="diag_001",
            disease_id="rose_black_spot"
        )

        assert "image_id" in result
        assert "file_path" in result

        # 验证调用
        real_image_service.storage.save_image.assert_called_once()
        real_image_service.repository.save.assert_called_once()

    def test_image_service_update_accuracy(self, real_image_service):
        """测试：更新准确性标签"""
        # 更新标签
        updated = real_image_service.update_accuracy_label("img_001", "correct")

        assert updated is True
        real_image_service.repository.update_accuracy_label.assert_called_once_with("img_001", "correct")

    def test_image_service_delete(self, real_image_service):
        """测试：删除图片"""
        # 删除图片
        deleted = real_image_service.delete_image("img_001")

        assert deleted is True
        real_image_service.repository.soft_delete.assert_called_once_with("img_001")


# ============================================================================
# 端到端集成测试
# ============================================================================

class TestEndToEndIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_complete_diagnosis_flow_with_image_saving(self, tmp_path):
        """测试：完整诊断流程 + 图片保存"""
        # 准备环境
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()
        storage_path = tmp_path / "uploads"
        db_path = tmp_path / "test.db"

        # Mock所有依赖
        mock_kb_service = Mock(spec=KnowledgeService)
        mock_kb_service.get_diseases_by_genus.return_value = [
            create_mock_disease("rose_black_spot", "玫瑰黑斑病", "Rosa")
        ]

        mock_vlm_client = AsyncMock()
        mock_vlm_client.extract_features.return_value = {"feature_value": "black_spots"}

        mock_matcher = Mock()
        mock_matcher.match.return_value = [
            {"disease_id": "rose_black_spot", "disease_name": "玫瑰黑斑病", "score": 0.85}
        ]

        mock_storage = Mock()
        mock_storage.save_image.return_value = {
            "relative_path": "2025-11-13/img_001.jpg",
            "full_path": str(storage_path / "2025-11-13/img_001.jpg")
        }

        mock_repository = Mock()

        # 创建服务
        with patch('backend.services.diagnosis_service.KnowledgeService', return_value=mock_kb_service), \
             patch('backend.services.diagnosis_service.MultiProviderVLMClient', return_value=mock_vlm_client), \
             patch('backend.services.diagnosis_service.FuzzyMatcher', return_value=mock_matcher), \
             patch('backend.services.image_service.LocalImageStorage', return_value=mock_storage), \
             patch('backend.services.image_service.ImageRepository', return_value=mock_repository):

            diagnosis_service = DiagnosisService(kb_path)
            diagnosis_service.vlm_client = mock_vlm_client
            diagnosis_service.kb_service = mock_kb_service
            diagnosis_service.matcher = mock_matcher

            diagnosis_service.execute_q0_sequence = AsyncMock(return_value=create_mock_q0_responses())
            diagnosis_service.execute_q1_q6_sequence = AsyncMock(return_value=create_mock_q1_q6_responses())

            image_service = ImageService(storage_path, db_path)
            image_service.storage = mock_storage
            image_service.repository = mock_repository

            # 执行诊断
            image_bytes = b"fake_image_data"
            diagnosis_result = await diagnosis_service.diagnose(image_bytes)

            # 验证诊断结果
            assert diagnosis_result["diagnosis_status"] == "confirmed"
            diagnosis_id = diagnosis_result["diagnosis_id"]
            disease_id = diagnosis_result["top_disease"]["disease_id"]

            # 保存图片
            save_result = image_service.save_image(
                image_bytes=image_bytes,
                flower_genus=diagnosis_result["flower_genus"],
                diagnosis_id=diagnosis_id,
                disease_id=disease_id,
                disease_name=diagnosis_result["top_disease"]["disease_name"],
                confidence_level=diagnosis_result["diagnosis_status"]
            )

            # 验证图片保存
            assert "image_id" in save_result
            mock_storage.save_image.assert_called_once()
            mock_repository.save.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
