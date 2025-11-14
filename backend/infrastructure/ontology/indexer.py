"""
疾病索引器

功能：
- 为疾病知识库构建多维度索引，支持快速检索
- 按宿主植物索引（用于候选疾病筛选）
- 按症状特征索引（用于特征匹配）
- 支持模糊匹配和多条件查询

类清单：
- DiseaseIndexer: 疾病索引器（主类）
"""

from typing import List, Dict, Set
from collections import defaultdict

from backend.domain.disease import DiseaseOntology


class DiseaseIndexer:
    """
    疾病索引器

    为疾病知识库构建多维度索引，支持快速检索：
    1. 按宿主植物索引（genus level）
    2. 按症状特征索引（symptom_type + color_center）
    3. 按疾病ID索引（用于快速查询）

    使用示例：
    ```python
    from backend.infrastructure.ontology.loader import KnowledgeBaseLoader

    # 加载知识库
    loader = KnowledgeBaseLoader(kb_path)
    diseases = loader.get_all_diseases()

    # 构建索引
    indexer = DiseaseIndexer(diseases)

    # 按宿主植物查询
    candidates = indexer.get_by_host("Rosa")

    # 按症状特征查询
    candidates = indexer.get_by_symptom("necrosis_spot", "black")

    # 按多个宿主查询
    candidates = indexer.get_by_hosts(["Rosa", "Prunus"])
    ```
    """

    def __init__(self, diseases: List[DiseaseOntology]):
        """
        初始化疾病索引器

        Args:
            diseases: 疾病本体列表

        内部构建：
        - by_host: {genus -> [Disease]} 宿主植物索引
        - by_symptom: {symptom_key -> [Disease]} 症状特征索引
        - by_id: {disease_id -> Disease} 疾病ID索引
        """
        self.diseases = diseases
        self.by_host: Dict[str, List[DiseaseOntology]] = defaultdict(list)
        self.by_symptom: Dict[str, List[DiseaseOntology]] = defaultdict(list)
        self.by_id: Dict[str, DiseaseOntology] = {}

        # 构建索引
        self._build_index()

    def _build_index(self) -> None:
        """
        构建索引

        内部方法，在初始化时自动调用

        索引构建逻辑：
        1. 遍历所有疾病
        2. 按宿主植物索引（一个疾病可能有多个宿主）
        3. 按症状特征索引（索引所有特征组：主要、次要、可选）
        4. 按疾病ID索引（用于快速查询）
        """
        for disease in self.diseases:
            # 1. 按宿主植物索引
            for host in disease.host_plants:
                self.by_host[host].append(disease)

            # 2. 按症状特征索引（索引所有特征组）
            feature_importance = disease.feature_importance

            # 索引所有特征组（major, minor, optional）
            for group_name in ["major_features", "minor_features", "optional_features"]:
                feature_group = feature_importance.get(group_name, {})
                features = feature_group.get("features", [])

                for feature in features:
                    dimension = feature.get("dimension")
                    expected_values = feature.get("expected_values", [])

                    # 按症状类型索引
                    if dimension == "symptom_type":
                        for value in expected_values:
                            symptom_key = f"symptom:{value}"
                            if disease not in self.by_symptom[symptom_key]:
                                self.by_symptom[symptom_key].append(disease)

                    # 按中心颜色索引
                    elif dimension == "color_center":
                        for value in expected_values:
                            color_key = f"color_center:{value}"
                            if disease not in self.by_symptom[color_key]:
                                self.by_symptom[color_key].append(disease)

                    # 按边缘颜色索引
                    elif dimension == "color_border":
                        for value in expected_values:
                            border_key = f"color_border:{value}"
                            if disease not in self.by_symptom[border_key]:
                                self.by_symptom[border_key].append(disease)

            # 3. 按疾病ID索引
            self.by_id[disease.disease_id] = disease

    def get_by_host(self, genus: str) -> List[DiseaseOntology]:
        """
        根据宿主植物获取候选疾病

        Args:
            genus: 植物属名（如 "Rosa"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表

        示例：
        ```python
        # 查询Rosa属植物的所有疾病
        candidates = indexer.get_by_host("Rosa")
        print(f"Rosa属候选疾病数: {len(candidates)}")
        for disease in candidates:
            print(f"  - {disease.disease_name}")
        ```
        """
        return self.by_host.get(genus, [])

    def get_by_hosts(self, genera: List[str]) -> List[DiseaseOntology]:
        """
        根据多个宿主植物获取候选疾病（取并集）

        Args:
            genera: 植物属名列表（如 ["Rosa", "Prunus"]）

        Returns:
            List[DiseaseOntology]: 候选疾病列表（去重）

        示例：
        ```python
        # 查询Rosa和Prunus属植物的所有疾病（合并）
        candidates = indexer.get_by_hosts(["Rosa", "Prunus"])
        print(f"候选疾病数: {len(candidates)}")
        ```
        """
        # 使用集合去重（基于disease_id）
        disease_set: Set[str] = set()
        result = []

        for genus in genera:
            for disease in self.by_host.get(genus, []):
                if disease.disease_id not in disease_set:
                    disease_set.add(disease.disease_id)
                    result.append(disease)

        return result

    def get_by_symptom_type(self, symptom_type: str) -> List[DiseaseOntology]:
        """
        根据症状类型获取候选疾病

        Args:
            symptom_type: 症状类型（如 "necrosis_spot"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表

        示例：
        ```python
        # 查询所有具有"坏死斑点"症状的疾病
        candidates = indexer.get_by_symptom_type("necrosis_spot")
        print(f"具有坏死斑点症状的疾病数: {len(candidates)}")
        ```
        """
        symptom_key = f"symptom:{symptom_type}"
        return self.by_symptom.get(symptom_key, [])

    def get_by_color_center(self, color: str) -> List[DiseaseOntology]:
        """
        根据中心颜色获取候选疾病

        Args:
            color: 中心颜色（如 "black"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表

        示例：
        ```python
        # 查询所有症状中心为黑色的疾病
        candidates = indexer.get_by_color_center("black")
        print(f"症状中心为黑色的疾病数: {len(candidates)}")
        ```
        """
        color_key = f"color_center:{color}"
        return self.by_symptom.get(color_key, [])

    def get_by_color_border(self, color: str) -> List[DiseaseOntology]:
        """
        根据边缘颜色获取候选疾病

        Args:
            color: 边缘颜色（如 "yellow"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表

        示例：
        ```python
        # 查询所有症状边缘为黄色的疾病
        candidates = indexer.get_by_color_border("yellow")
        print(f"症状边缘为黄色的疾病数: {len(candidates)}")
        ```
        """
        border_key = f"color_border:{color}"
        return self.by_symptom.get(border_key, [])

    def get_by_symptom(self, symptom_type: str, color_center: str) -> List[DiseaseOntology]:
        """
        根据症状特征组合获取候选疾病（交集）

        Args:
            symptom_type: 症状类型（如 "necrosis_spot"）
            color_center: 中心颜色（如 "black"）

        Returns:
            List[DiseaseOntology]: 候选疾病列表（同时满足两个条件）

        示例：
        ```python
        # 查询症状为"黑色坏死斑点"的疾病
        candidates = indexer.get_by_symptom("necrosis_spot", "black")
        print(f"黑色坏死斑点疾病数: {len(candidates)}")
        ```
        """
        # 获取两个条件的候选疾病
        candidates_by_symptom = set(d.disease_id for d in self.get_by_symptom_type(symptom_type))
        candidates_by_color = set(d.disease_id for d in self.get_by_color_center(color_center))

        # 取交集
        intersection = candidates_by_symptom & candidates_by_color

        # 返回疾病对象列表
        return [self.by_id[did] for did in intersection if did in self.by_id]

    def get_by_id(self, disease_id: str) -> DiseaseOntology | None:
        """
        根据疾病ID获取疾病本体

        Args:
            disease_id: 疾病ID（如 "rose_black_spot"）

        Returns:
            DiseaseOntology | None: 疾病本体对象，如果不存在则返回None

        示例：
        ```python
        disease = indexer.get_by_id("rose_black_spot")
        if disease:
            print(f"疾病名称: {disease.disease_name}")
        ```
        """
        return self.by_id.get(disease_id)

    def get_all_diseases(self) -> List[DiseaseOntology]:
        """
        获取所有疾病本体

        Returns:
            List[DiseaseOntology]: 疾病本体列表
        """
        return self.diseases

    def get_all_hosts(self) -> List[str]:
        """
        获取所有宿主植物属名

        Returns:
            List[str]: 宿主植物属名列表（去重）

        示例：
        ```python
        hosts = indexer.get_all_hosts()
        print(f"知识库包含的宿主植物: {hosts}")
        # 输出: ['Rosa', 'Prunus', 'Tulipa', 'Dianthus', 'Paeonia']
        ```
        """
        return list(self.by_host.keys())

    def get_statistics(self) -> Dict[str, int]:
        """
        获取索引统计信息

        Returns:
            Dict[str, int]: 统计信息字典

        示例：
        ```python
        stats = indexer.get_statistics()
        print(f"疾病总数: {stats['total_diseases']}")
        print(f"宿主植物数: {stats['total_hosts']}")
        print(f"症状特征索引数: {stats['total_symptom_keys']}")
        ```
        """
        return {
            "total_diseases": len(self.diseases),
            "total_hosts": len(self.by_host),
            "total_symptom_keys": len(self.by_symptom),
            "total_indexed_entries": sum(len(v) for v in self.by_host.values()) +
                                     sum(len(v) for v in self.by_symptom.values())
        }


def main():
    """
    DiseaseIndexer 使用示例

    演示如何：
    1. 初始化疾病索引器
    2. 按宿主植物查询候选疾病
    3. 按症状特征查询候选疾病
    4. 按多个条件组合查询
    5. 获取索引统计信息
    """
    from pathlib import Path
    from backend.infrastructure.ontology.loader import KnowledgeBaseLoader

    print("=" * 80)
    print("DiseaseIndexer 使用示例")
    print("=" * 80)

    # 1. 初始化知识库加载器和索引器
    print("\n[示例1] 初始化疾病索引器")
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = project_root / "backend" / "knowledge_base"

    try:
        loader = KnowledgeBaseLoader(kb_path)
        diseases = loader.get_all_diseases()
        indexer = DiseaseIndexer(diseases)
        print(f"  [OK] 疾病索引器初始化成功")
        print(f"    - 索引疾病数: {len(diseases)}")
    except Exception as e:
        print(f"  [FAIL] 疾病索引器初始化失败: {e}")
        return

    # 2. 按宿主植物查询候选疾病
    print("\n[示例2] 按宿主植物查询候选疾病")
    host_genus = "Rosa"
    candidates = indexer.get_by_host(host_genus)
    print(f"  宿主植物: {host_genus}")
    print(f"  候选疾病数: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name} ({disease.disease_id})")
        print(f"      病原体: {disease.pathogen}")

    # 3. 按症状类型查询候选疾病
    print("\n[示例3] 按症状类型查询候选疾病")
    symptom_type = "necrosis_spot"
    candidates = indexer.get_by_symptom_type(symptom_type)
    print(f"  症状类型: {symptom_type}")
    print(f"  候选疾病数: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name}")

    # 4. 按中心颜色查询候选疾病
    print("\n[示例4] 按中心颜色查询候选疾病")
    color_center = "black"
    candidates = indexer.get_by_color_center(color_center)
    print(f"  中心颜色: {color_center}")
    print(f"  候选疾病数: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name}")

    # 5. 按边缘颜色查询候选疾病
    print("\n[示例5] 按边缘颜色查询候选疾病")
    color_border = "yellow"
    candidates = indexer.get_by_color_border(color_border)
    print(f"  边缘颜色: {color_border}")
    print(f"  候选疾病数: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name}")

    # 6. 按症状特征组合查询（交集）
    print("\n[示例6] 按症状特征组合查询")
    symptom_type = "necrosis_spot"
    color_center = "black"
    candidates = indexer.get_by_symptom(symptom_type, color_center)
    print(f"  症状类型: {symptom_type}")
    print(f"  中心颜色: {color_center}")
    print(f"  候选疾病数（交集）: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name}")

    # 7. 按多个宿主查询（并集）
    print("\n[示例7] 按多个宿主查询")
    hosts = ["Rosa", "Prunus"]
    candidates = indexer.get_by_hosts(hosts)
    print(f"  宿主植物: {hosts}")
    print(f"  候选疾病数（并集）: {len(candidates)}")
    for disease in candidates:
        print(f"    - {disease.disease_name} (宿主: {', '.join(disease.host_plants)})")

    # 8. 获取所有宿主植物
    print("\n[示例8] 获取所有宿主植物")
    all_hosts = indexer.get_all_hosts()
    print(f"  知识库包含的宿主植物数: {len(all_hosts)}")
    print(f"  宿主植物列表: {', '.join(all_hosts)}")

    # 9. 获取索引统计信息
    print("\n[示例9] 获取索引统计信息")
    stats = indexer.get_statistics()
    print(f"  索引统计:")
    print(f"    - 疾病总数: {stats['total_diseases']}")
    print(f"    - 宿主植物数: {stats['total_hosts']}")
    print(f"    - 症状特征索引键数: {stats['total_symptom_keys']}")
    print(f"    - 总索引条目数: {stats['total_indexed_entries']}")

    # 10. 按ID查询疾病
    print("\n[示例10] 按ID查询疾病")
    disease_id = "rose_black_spot"
    disease = indexer.get_by_id(disease_id)
    if disease:
        print(f"  [OK] 找到疾病: {disease.disease_name}")
        print(f"    - ID: {disease.disease_id}")
        print(f"    - 英文名: {disease.common_name_en}")
    else:
        print(f"  [FAIL] 疾病不存在: {disease_id}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
