"""
假数据知识库服务

加载和管理疾病定义、特征本体等知识库数据。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import streamlit as st

from config import (
    DISEASES_DIR,
    FEATURE_ONTOLOGY_FILE,
    DISEASE_TEMPLATES,
    ONTOLOGY_VERSION,
    ONTOLOGY_GIT_COMMIT,
)


class MockKnowledgeService:
    """假数据知识库服务"""

    def __init__(self):
        """初始化知识库服务"""
        self.diseases: Dict[str, Dict] = {}
        self.feature_ontology: Dict = {}
        self.load_knowledge_base()

    @st.cache_data
    def load_knowledge_base(_self) -> None:
        """
        加载知识库数据（疾病定义和特征本体）

        使用@st.cache_data装饰器缓存数据，避免重复加载
        """
        # 加载特征本体
        if FEATURE_ONTOLOGY_FILE.exists():
            with open(FEATURE_ONTOLOGY_FILE, 'r', encoding='utf-8') as f:
                _self.feature_ontology = json.load(f)
        else:
            _self.feature_ontology = _self._generate_default_ontology()

        # 加载所有疾病定义
        if DISEASES_DIR.exists():
            for disease_file in DISEASES_DIR.glob("*.json"):
                with open(disease_file, 'r', encoding='utf-8') as f:
                    disease_data = json.load(f)
                    disease_id = disease_data['disease_id']
                    _self.diseases[disease_id] = disease_data
        else:
            # 使用配置文件中的模板数据
            _self.diseases = DISEASE_TEMPLATES

    def _generate_default_ontology(self) -> Dict:
        """生成默认的特征本体（如果文件不存在）"""
        return {
            "version": ONTOLOGY_VERSION,
            "git_commit": ONTOLOGY_GIT_COMMIT,
            "features": {
                "symptom_type": {
                    "values": ["necrosis_spot", "powdery_coating", "necrosis_rot"],
                    "synonyms": {
                        "necrosis_spot": ["dark_spot", "black_spot"],
                        "powdery_coating": ["white_powder", "powdery_mildew"]
                    }
                },
                "color_center": {
                    "values": ["black", "brown", "white"],
                    "synonyms": {}
                },
                "color_border": {
                    "values": ["yellow", "yellow_halo", "none"],
                    "synonyms": {
                        "yellow_halo": ["yellow", "yellowish"]
                    }
                }
            }
        }

    def get_disease(self, disease_id: str) -> Optional[Dict]:
        """
        获取疾病定义

        Args:
            disease_id: 疾病ID

        Returns:
            疾病定义字典，如果不存在返回None
        """
        return self.diseases.get(disease_id)

    def get_diseases_by_genus(self, genus: str) -> List[Dict]:
        """
        根据花属获取候选疾病

        Args:
            genus: 花属名称（如 "Rosa"）

        Returns:
            疾病定义列表
        """
        candidates = []
        for disease_id, disease_data in self.diseases.items():
            if genus in disease_data.get('host_plants', []):
                candidates.append(disease_data)
        return candidates

    def get_all_genera(self) -> List[str]:
        """
        获取所有花属列表

        Returns:
            花属名称列表
        """
        genera = set()
        for disease_data in self.diseases.values():
            genera.update(disease_data.get('host_plants', []))
        return sorted(list(genera))

    def get_feature_ontology(self) -> Dict:
        """
        获取特征本体

        Returns:
            特征本体字典
        """
        return self.feature_ontology

    def get_feature_definition(self, feature_key: str) -> Optional[Dict]:
        """
        获取单个特征的定义

        Args:
            feature_key: 特征键名（如 "symptom_type"）

        Returns:
            特征定义字典，包含values和synonyms
        """
        features = self.feature_ontology.get('features', {})
        return features.get(feature_key)

    def get_synonyms(self, feature_key: str, canonical_value: str) -> List[str]:
        """
        获取特征值的同义词列表

        Args:
            feature_key: 特征键名
            canonical_value: 标准值

        Returns:
            同义词列表
        """
        feature_def = self.get_feature_definition(feature_key)
        if not feature_def:
            return []

        synonyms = feature_def.get('synonyms', {})
        return synonyms.get(canonical_value, [])

    def find_canonical_value(
        self,
        feature_key: str,
        observed_value: str
    ) -> tuple[Optional[str], bool]:
        """
        查找观测值对应的标准值

        Args:
            feature_key: 特征键名
            observed_value: 观测值

        Returns:
            (标准值, 是否精确匹配)
            - 精确匹配: (observed_value, True)
            - 同义词匹配: (canonical_value, False)
            - 未匹配: (None, False)
        """
        feature_def = self.get_feature_definition(feature_key)
        if not feature_def:
            return None, False

        # 1. 精确匹配：观测值在标准值列表中
        values = feature_def.get('values', [])
        if observed_value in values:
            return observed_value, True

        # 2. 同义词匹配：观测值是某个标准值的同义词
        synonyms = feature_def.get('synonyms', {})
        for canonical_value, synonym_list in synonyms.items():
            if observed_value in synonym_list:
                return canonical_value, False

        # 3. 未匹配
        return None, False

    def get_ontology_version_info(self) -> Dict[str, str]:
        """
        获取本体版本信息

        Returns:
            版本信息字典
        """
        return {
            "version": self.feature_ontology.get('version', ONTOLOGY_VERSION),
            "git_commit": self.feature_ontology.get('git_commit', ONTOLOGY_GIT_COMMIT),
        }


# 全局单例（使用Streamlit缓存）
@st.cache_resource
def get_knowledge_service() -> MockKnowledgeService:
    """
    获取知识库服务单例

    使用@st.cache_resource装饰器，确保整个session只创建一次
    """
    return MockKnowledgeService()
