"""
KnowledgeService 单元测试

测试范围：
1. 知识库初始化
2. 按种属查询疾病
3. 按ID查询单个疾病
4. 获取所有疾病
5. 获取版本信息
6. 热更新知识库
7. 异常处理

作者：AI Python Architect
日期：2025-11-13
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from backend.services.knowledge_service import (
    KnowledgeService,
    KnowledgeServiceException,
)
from backend.infrastructure.ontology.exceptions import (
    KnowledgeBaseNotFoundError,
    KnowledgeBaseLoadError,
)
from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology


class TestKnowledgeServiceInitialization:
    """知识库服务初始化测试"""

    def test_init_with_valid_path(self, tmp_path):
        """测试：使用有效路径初始化"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock KnowledgeBaseLoader
        with patch('backend.services.knowledge_service.KnowledgeBaseLoader'):
            # 执行（禁用auto_initialize）
            service = KnowledgeService(kb_path, auto_initialize=False)

            # 验证
            assert service.kb_path == kb_path
            assert not service.is_initialized()

    def test_init_with_invalid_path(self):
        """测试：使用无效路径初始化应抛出异常"""
        # 准备
        invalid_path = Path("/nonexistent/path")

        # 执行 & 验证
        with pytest.raises(KnowledgeServiceException, match="知识库路径不存在"):
            KnowledgeService(invalid_path, auto_initialize=False)

    def test_auto_initialize_success(self, tmp_path):
        """测试：自动初始化成功"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock依赖
        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = [
            self._create_mock_disease("rose_black_spot", "Rosa"),
        ]
        mock_loader.get_feature_ontology.return_value = Mock(spec=FeatureOntology)

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            # 执行
            service = KnowledgeService(kb_path, auto_initialize=True)

            # 验证
            assert service.is_initialized()
            assert len(service.get_all_diseases()) == 1

    def test_auto_initialize_failure(self, tmp_path, caplog):
        """测试：自动初始化失败时记录警告"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock加载失败
        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', side_effect=KnowledgeBaseLoadError("加载失败")):
            # 执行
            service = KnowledgeService(kb_path, auto_initialize=True)

            # 验证
            assert not service.is_initialized()
            assert "自动初始化知识库失败" in caplog.text

    @staticmethod
    def _create_mock_disease(disease_id: str, genus: str) -> DiseaseOntology:
        """创建Mock疾病对象"""
        return DiseaseOntology(
            version="1.0",
            disease_id=disease_id,
            disease_name=f"测试疾病_{disease_id}",
            common_name_en=f"Test Disease {disease_id}",
            pathogen=f"测试病原体_{disease_id}",
            feature_vector={"symptom_type": "test"},
            feature_importance={"major_features": {"features": []}},
            diagnosis_rules={"confirmed": [], "suspected": []},
            host_plants=[genus]
        )


class TestKnowledgeServiceQueries:
    """知识库服务查询测试"""

    @pytest.fixture
    def mock_service(self, tmp_path):
        """创建Mock的KnowledgeService"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # 创建Mock疾病
        diseases = [
            self._create_disease("rose_black_spot", "Rosa", "玫瑰黑斑病"),
            self._create_disease("rose_powdery_mildew", "Rosa", "玫瑰白粉病"),
            self._create_disease("peony_leaf_blight", "Paeonia", "牡丹叶枯病"),
        ]

        # Mock KnowledgeBaseLoader
        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = diseases
        mock_loader.get_feature_ontology.return_value = Mock(spec=FeatureOntology)

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            service = KnowledgeService(kb_path, auto_initialize=True)
            return service

    def test_get_all_diseases(self, mock_service):
        """测试：获取所有疾病"""
        # 执行
        all_diseases = mock_service.get_all_diseases()

        # 验证
        assert len(all_diseases) == 3
        assert all(isinstance(d, DiseaseOntology) for d in all_diseases)

    def test_get_diseases_by_genus_found(self, mock_service):
        """测试：按种属查询（找到）"""
        # 执行
        rosa_diseases = mock_service.get_diseases_by_genus("Rosa")

        # 验证
        assert len(rosa_diseases) == 2
        assert all(d.disease_id.startswith("rose_") for d in rosa_diseases)

    def test_get_diseases_by_genus_not_found(self, mock_service):
        """测试：按种属查询（未找到）"""
        # 执行
        diseases = mock_service.get_diseases_by_genus("NonExistent")

        # 验证
        assert len(diseases) == 0

    def test_get_disease_by_id_found(self, mock_service):
        """测试：按ID查询疾病（找到）"""
        # 执行
        disease = mock_service.get_disease_by_id("rose_black_spot")

        # 验证
        assert disease is not None
        assert disease.disease_id == "rose_black_spot"
        assert disease.disease_name == "玫瑰黑斑病"

    def test_get_disease_by_id_not_found(self, mock_service):
        """测试：按ID查询疾病（未找到）"""
        # 执行
        disease = mock_service.get_disease_by_id("nonexistent_disease")

        # 验证
        assert disease is None

    def test_get_feature_ontology(self, mock_service):
        """测试：获取特征本体"""
        # 执行
        feature_ontology = mock_service.get_feature_ontology()

        # 验证
        assert feature_ontology is not None

    @staticmethod
    def _create_disease(disease_id: str, genus: str, disease_name: str) -> DiseaseOntology:
        """创建疾病对象"""
        return DiseaseOntology(
            version="1.0",
            disease_id=disease_id,
            disease_name=disease_name,
            common_name_en=f"Test {disease_name}",
            pathogen=f"Pathogen of {disease_name}",
            feature_vector={"symptom_type": "test"},
            feature_importance={"major_features": {"features": []}},
            diagnosis_rules={"confirmed": [], "suspected": []},
            host_plants=[genus]
        )


class TestKnowledgeServiceVersionManagement:
    """知识库服务版本管理测试"""

    @pytest.fixture
    def initialized_service(self, tmp_path):
        """创建已初始化的服务"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = []
        mock_loader.get_feature_ontology.return_value = Mock()

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            with patch.object(KnowledgeService, '_get_git_commit_hash', return_value='abc1234'):
                service = KnowledgeService(kb_path, auto_initialize=True)
                return service

    def test_get_version_info(self, initialized_service):
        """测试：获取版本信息"""
        # 执行
        version_info = initialized_service.get_version_info()

        # 验证
        assert "version" in version_info
        assert "last_loaded" in version_info
        assert "git_commit_hash" in version_info
        assert "disease_count" in version_info
        assert "genus_count" in version_info

        assert version_info["version"] == "v1.0"
        assert version_info["git_commit_hash"] == "abc1234"
        assert isinstance(version_info["last_loaded"], datetime)

    def test_get_last_loaded(self, initialized_service):
        """测试：获取最后加载时间"""
        # 执行
        last_loaded = initialized_service.get_last_loaded()

        # 验证
        assert last_loaded is not None
        assert isinstance(last_loaded, datetime)

    def test_is_initialized(self, initialized_service):
        """测试：检查是否已初始化"""
        # 验证
        assert initialized_service.is_initialized() is True


class TestKnowledgeServiceReload:
    """知识库服务热更新测试"""

    def test_reload_success(self, tmp_path):
        """测试：热更新成功"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # 第一次加载：1种疾病
        mock_loader_1 = Mock()
        mock_loader_1.get_all_diseases.return_value = [
            DiseaseOntology(
                version="1.0",
                disease_id="disease_1",
                disease_name="疾病1",
                common_name_en="Disease 1",
                pathogen="病原体1",
                feature_vector={"symptom_type": "test"},
                feature_importance={"major_features": {"features": []}},
                diagnosis_rules={"confirmed": [], "suspected": []},
                host_plants=["Rosa"]
            )
        ]
        mock_loader_1.get_feature_ontology.return_value = Mock()

        # 第二次加载：2种疾病
        mock_loader_2 = Mock()
        mock_loader_2.get_all_diseases.return_value = [
            DiseaseOntology(
                version="1.0",
                disease_id="disease_1",
                disease_name="疾病1",
                common_name_en="Disease 1",
                pathogen="病原体1",
                feature_vector={"symptom_type": "test"},
                feature_importance={"major_features": {"features": []}},
                diagnosis_rules={"confirmed": [], "suspected": []},
                host_plants=["Rosa"]
            ),
            DiseaseOntology(
                version="1.0",
                disease_id="disease_2",
                disease_name="疾病2",
                common_name_en="Disease 2",
                pathogen="病原体2",
                feature_vector={"symptom_type": "test"},
                feature_importance={"major_features": {"features": []}},
                diagnosis_rules={"confirmed": [], "suspected": []},
                host_plants=["Paeonia"]
            )
        ]
        mock_loader_2.get_feature_ontology.return_value = Mock()

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', side_effect=[mock_loader_1, mock_loader_2]):
            # 首次初始化
            service = KnowledgeService(kb_path, auto_initialize=True)
            assert len(service.get_all_diseases()) == 1

            # 热更新
            service.reload()

            # 验证
            assert len(service.get_all_diseases()) == 2


class TestKnowledgeServiceExceptionHandling:
    """知识库服务异常处理测试"""

    def test_query_before_initialization(self, tmp_path):
        """测试：初始化前查询应抛出异常"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        service = KnowledgeService(kb_path, auto_initialize=False)

        # 验证各种查询方法都抛出异常
        with pytest.raises(KnowledgeServiceException, match="知识库未初始化"):
            service.get_all_diseases()

        with pytest.raises(KnowledgeServiceException, match="知识库未初始化"):
            service.get_diseases_by_genus("Rosa")

        with pytest.raises(KnowledgeServiceException, match="知识库未初始化"):
            service.get_disease_by_id("test_id")

        with pytest.raises(KnowledgeServiceException, match="知识库未初始化"):
            service.get_feature_ontology()

        with pytest.raises(KnowledgeServiceException, match="知识库未初始化"):
            service.get_version_info()

    def test_initialize_with_load_error(self, tmp_path):
        """测试：加载错误时初始化应抛出异常"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock加载失败
        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', side_effect=KnowledgeBaseLoadError("加载失败")):
            service = KnowledgeService(kb_path, auto_initialize=False)

            # 执行 & 验证
            with pytest.raises(KnowledgeServiceException, match="知识库初始化失败"):
                service.initialize()


class TestGitCommitHashRetrieval:
    """Git commit hash 获取测试"""

    def test_get_git_commit_hash_success(self, tmp_path):
        """测试：成功获取Git commit hash"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock subprocess.run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc1234\n"

        with patch('subprocess.run', return_value=mock_result):
            service = KnowledgeService(kb_path, auto_initialize=False)
            commit_hash = service._get_git_commit_hash()

            # 验证
            assert commit_hash == "abc1234"

    def test_get_git_commit_hash_failure(self, tmp_path):
        """测试：获取Git commit hash失败"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock subprocess.run失败
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "not a git repository"

        with patch('subprocess.run', return_value=mock_result):
            service = KnowledgeService(kb_path, auto_initialize=False)
            commit_hash = service._get_git_commit_hash()

            # 验证
            assert commit_hash is None

    def test_get_git_commit_hash_not_installed(self, tmp_path):
        """测试：Git未安装时返回None"""
        # 准备
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # Mock subprocess.run抛出FileNotFoundError
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            service = KnowledgeService(kb_path, auto_initialize=False)
            commit_hash = service._get_git_commit_hash()

            # 验证
            assert commit_hash is None


class TestKnowledgeServiceGetKnowledgeTree:
    """P3.9新增：知识库树结构获取测试"""

    @pytest.fixture
    def mock_service_with_associations(self, tmp_path):
        """创建带有associations.json的Mock服务"""
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        # 创建host_disease目录
        host_disease_dir = kb_path / "host_disease"
        host_disease_dir.mkdir()

        # 创建associations.json文件
        associations_data = {
            "version": "1.0",
            "last_updated": "2025-11-13",
            "associations": [
                {
                    "host_genus": "Rosa",
                    "genus_name": "玫瑰属",
                    "genus_name_en": "Rose",
                    "diseases": [
                        {
                            "disease_id": "rose_black_spot",
                            "disease_name": "玫瑰黑斑病",
                            "common_name_en": "Black Spot of Rose",
                            "pathogen": "Diplocarpon rosae",
                            "prevalence": "common"
                        },
                        {
                            "disease_id": "rose_powdery_mildew",
                            "disease_name": "玫瑰白粉病",
                            "common_name_en": "Powdery Mildew of Rose",
                            "pathogen": "Podosphaera pannosa",
                            "prevalence": "very_common"
                        }
                    ]
                },
                {
                    "host_genus": "Paeonia",
                    "genus_name": "牡丹属",
                    "genus_name_en": "Peony",
                    "diseases": [
                        {
                            "disease_id": "peony_leaf_blight",
                            "disease_name": "牡丹叶枯病",
                            "common_name_en": "Leaf Blight of Peony",
                            "pathogen": "Cladosporium paeoniae",
                            "prevalence": "common"
                        }
                    ]
                }
            ]
        }

        import json
        associations_file = host_disease_dir / "associations.json"
        with open(associations_file, "w", encoding="utf-8") as f:
            json.dump(associations_data, f, ensure_ascii=False, indent=2)

        # 创建Mock服务
        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = []
        mock_loader.get_feature_ontology.return_value = Mock()

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            service = KnowledgeService(kb_path, auto_initialize=False)
            return service

    def test_get_knowledge_tree_success(self, mock_service_with_associations):
        """测试：P3.9新增 - 成功获取知识库树"""
        # 执行
        tree = mock_service_with_associations.get_knowledge_tree()

        # 验证顶层结构
        assert "version" in tree
        assert "last_updated" in tree
        assert "total_hosts" in tree
        assert "total_diseases" in tree
        assert "hosts" in tree

        # 验证version
        assert tree["version"] == "1.0"

        # 验证统计信息
        assert tree["total_hosts"] == 2
        assert tree["total_diseases"] == 3

        # 验证hosts列表
        assert isinstance(tree["hosts"], list)
        assert len(tree["hosts"]) == 2

    def test_get_knowledge_tree_host_structure(self, mock_service_with_associations):
        """测试：P3.9新增 - 验证宿主结构"""
        # 执行
        tree = mock_service_with_associations.get_knowledge_tree()

        # 获取第一个宿主（Rosa）
        rosa_host = tree["hosts"][0]

        # 验证宿主字段
        assert rosa_host["genus"] == "Rosa"
        assert rosa_host["name_zh"] == "玫瑰属"
        assert rosa_host["name_en"] == "Rose"
        assert rosa_host["disease_count"] == 2
        assert "diseases" in rosa_host
        assert isinstance(rosa_host["diseases"], list)

    def test_get_knowledge_tree_disease_structure(self, mock_service_with_associations):
        """测试：P3.9新增 - 验证疾病结构"""
        # 执行
        tree = mock_service_with_associations.get_knowledge_tree()

        # 获取第一个疾病
        rosa_host = tree["hosts"][0]
        first_disease = rosa_host["diseases"][0]

        # 验证疾病字段
        assert "disease_id" in first_disease
        assert "disease_name" in first_disease
        assert "common_name_en" in first_disease
        assert "pathogen" in first_disease
        assert "prevalence" in first_disease

        # 验证具体值
        assert first_disease["disease_id"] == "rose_black_spot"
        assert first_disease["disease_name"] == "玫瑰黑斑病"
        assert first_disease["prevalence"] == "common"

    def test_get_knowledge_tree_date_format(self, mock_service_with_associations):
        """测试：P3.9新增 - 验证日期格式转换为ISO 8601"""
        # 执行
        tree = mock_service_with_associations.get_knowledge_tree()

        # 验证日期格式（应该是ISO 8601格式）
        last_updated = tree["last_updated"]
        assert last_updated == "2025-11-13T00:00:00Z"

    def test_get_knowledge_tree_file_not_found(self, tmp_path):
        """测试：P3.9新增 - associations.json不存在时抛出异常"""
        # 准备：创建知识库但不创建associations.json
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = []

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            service = KnowledgeService(kb_path, auto_initialize=False)

            # 执行 & 验证
            with pytest.raises(KnowledgeServiceException, match="associations.json不存在"):
                service.get_knowledge_tree()

    def test_get_knowledge_tree_invalid_json(self, tmp_path):
        """测试：P3.9新增 - JSON格式错误时抛出异常"""
        # 准备：创建无效的JSON文件
        kb_path = tmp_path / "knowledge_base"
        kb_path.mkdir()

        host_disease_dir = kb_path / "host_disease"
        host_disease_dir.mkdir()

        associations_file = host_disease_dir / "associations.json"
        with open(associations_file, "w") as f:
            f.write("{invalid json")

        mock_loader = Mock()
        mock_loader.get_all_diseases.return_value = []

        with patch('backend.services.knowledge_service.KnowledgeBaseLoader', return_value=mock_loader):
            service = KnowledgeService(kb_path, auto_initialize=False)

            # 执行 & 验证
            with pytest.raises(KnowledgeServiceException, match="JSON解析失败"):
                service.get_knowledge_tree()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
