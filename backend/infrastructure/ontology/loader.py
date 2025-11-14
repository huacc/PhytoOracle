"""
知识库加载器

功能：
- 从JSON文件加载五大知识库：疾病本体、特征本体、植物本体、宿主-疾病关系、视觉隐喻库
- 将JSON数据解析为Pydantic领域模型（类型安全）
- 支持热重载（管理后台调用 reload() 方法）
- 提供统一的知识库查询接口

类清单：
- KnowledgeBaseLoader: 知识库加载器（主类）
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology
from backend.domain.plant import PlantOntology
from backend.infrastructure.ontology.exceptions import (
    KnowledgeBaseNotFoundError,
    KnowledgeBaseLoadError,
    KnowledgeBaseValidationError
)


class KnowledgeBaseLoader:
    """
    知识库加载器

    负责从JSON文件加载五大知识库：
    1. 疾病本体库（Disease Ontology）
    2. 特征本体库（Feature Ontology）
    3. 植物本体库（Plant Ontology）
    4. 宿主-疾病关系库（Host-Disease Associations）
    5. 视觉隐喻库（Visual Metaphor Library，嵌入在特征本体中）

    使用示例：
    ```python
    from pathlib import Path

    # 初始化加载器（使用相对路径）
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = project_root / "backend" / "knowledge_base"
    loader = KnowledgeBaseLoader(kb_path)

    # 加载所有疾病本体
    diseases = loader.load_all_diseases()

    # 加载特征本体
    feature_ontology = loader.load_feature_ontology()

    # 按ID查询疾病
    disease = loader.get_disease_by_id("rose_black_spot")

    # 热重载知识库
    loader.reload()
    ```
    """

    def __init__(self, base_path: Path):
        """
        初始化知识库加载器

        Args:
            base_path: 知识库根目录路径（使用相对路径）

        Raises:
            KnowledgeBaseNotFoundError: 知识库根目录不存在
        """
        if not base_path.exists():
            raise KnowledgeBaseNotFoundError(f"知识库根目录不存在: {base_path}")

        self.base_path = base_path
        self.kb_path = base_path  # 添加别名属性（用于兼容性）
        self.diseases_path = base_path / "diseases"
        self.features_path = base_path / "features"
        self.plants_path = base_path / "plants"
        self.host_disease_path = base_path / "host_disease"

        # 内部缓存（用于查询和热重载）
        self._diseases: List[DiseaseOntology] = []
        self._diseases_dict: Dict[str, DiseaseOntology] = {}
        self._feature_ontology: Optional[FeatureOntology] = None
        self._plants: List[PlantOntology] = []
        self._host_disease_associations: Optional[Dict[str, Any]] = None

        # 初始化时自动加载
        self._load_all()

    def _load_all(self) -> None:
        """
        加载所有知识库

        内部方法，在初始化和热重载时调用

        加载顺序：
        1. 疾病本体库（必需）
        2. 特征本体库（必需）
        3. 宿主-疾病关系库（可选）
        4. 植物本体库（可选）
        """
        # 1. 加载疾病本体库
        self._diseases = self.load_all_diseases()
        self._diseases_dict = {d.disease_id: d for d in self._diseases}

        # 2. 加载特征本体库
        self._feature_ontology = self.load_feature_ontology()

        # 3. 加载宿主-疾病关系库（可选）
        try:
            self._host_disease_associations = self._load_host_disease_associations()
        except KnowledgeBaseNotFoundError:
            self._host_disease_associations = None

        # 4. 加载植物本体库（可选）
        try:
            self._plants = self.load_all_plants()
        except KnowledgeBaseNotFoundError:
            self._plants = []

    def load_all_diseases(self) -> List[DiseaseOntology]:
        """
        加载所有疾病本体

        从 `knowledge_base/diseases/*.json` 加载所有疾病JSON文件，
        并解析为 `DiseaseOntology` Pydantic模型

        Returns:
            List[DiseaseOntology]: 疾病本体列表

        Raises:
            KnowledgeBaseNotFoundError: 疾病知识库目录不存在
            KnowledgeBaseLoadError: JSON文件加载失败
            KnowledgeBaseValidationError: Pydantic模型验证失败

        示例：
        ```python
        diseases = loader.load_all_diseases()
        print(f"加载了 {len(diseases)} 种疾病")
        for disease in diseases:
            print(f"  - {disease.disease_name} ({disease.disease_id})")
        ```
        """
        if not self.diseases_path.exists():
            raise KnowledgeBaseNotFoundError(f"疾病知识库目录不存在: {self.diseases_path}")

        diseases = []
        json_files = list(self.diseases_path.glob("*.json"))

        if len(json_files) == 0:
            raise KnowledgeBaseNotFoundError(f"疾病知识库目录为空: {self.diseases_path}")

        for json_file in json_files:
            try:
                # 读取JSON文件
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 使用Pydantic验证数据
                disease = DiseaseOntology(**data)
                diseases.append(disease)

            except json.JSONDecodeError as e:
                raise KnowledgeBaseLoadError(f"疾病文件JSON格式错误: {json_file.name}, 原因: {e}")
            except ValidationError as e:
                raise KnowledgeBaseValidationError(f"疾病文件验证失败: {json_file.name}, 原因: {e}")
            except Exception as e:
                raise KnowledgeBaseLoadError(f"疾病文件加载失败: {json_file.name}, 原因: {e}")

        return diseases

    def load_feature_ontology(self) -> FeatureOntology:
        """
        加载特征本体库

        从 `knowledge_base/features/feature_ontology.json` 加载特征本体，
        并解析为 `FeatureOntology` Pydantic模型

        特征本体包含：
        - 特征维度定义（dimensions）
        - 模糊匹配规则（fuzzy_matching）
        - 症状类型定义（symptom_types）
        - 颜色定义（colors）
        - 尺寸定义（sizes）
        - 分布模式定义（distribution_patterns）
        - 视觉隐喻库（嵌入在dimensions中）

        Returns:
            FeatureOntology: 特征本体对象

        Raises:
            KnowledgeBaseNotFoundError: 特征本体文件不存在
            KnowledgeBaseLoadError: JSON文件加载失败
            KnowledgeBaseValidationError: Pydantic模型验证失败

        示例：
        ```python
        feature_ontology = loader.load_feature_ontology()
        print(f"特征维度数: {len(feature_ontology.dimensions)}")
        print(f"症状类型数: {len(feature_ontology.symptom_types)}")
        ```
        """
        ontology_file = self.features_path / "feature_ontology.json"
        if not ontology_file.exists():
            raise KnowledgeBaseNotFoundError(f"特征本体文件不存在: {ontology_file}")

        try:
            # 读取JSON文件
            with open(ontology_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 使用Pydantic验证数据
            feature_ontology = FeatureOntology(**data)
            return feature_ontology

        except json.JSONDecodeError as e:
            raise KnowledgeBaseLoadError(f"特征本体JSON格式错误: {ontology_file.name}, 原因: {e}")
        except ValidationError as e:
            raise KnowledgeBaseValidationError(f"特征本体验证失败: {ontology_file.name}, 原因: {e}")
        except Exception as e:
            raise KnowledgeBaseLoadError(f"特征本体加载失败: {ontology_file.name}, 原因: {e}")

    def load_all_plants(self) -> List[PlantOntology]:
        """
        加载植物本体库

        从 `knowledge_base/plants/*.json` 加载植物本体（v1.2+预留），
        并解析为 `PlantOntology` Pydantic模型

        如果植物本体文件不存在，可以从疾病本体中提取宿主植物信息（降级方案）

        Returns:
            List[PlantOntology]: 植物本体列表

        Raises:
            KnowledgeBaseNotFoundError: 植物本体目录不存在（降级到从疾病提取）

        示例：
        ```python
        plants = loader.load_all_plants()
        print(f"加载了 {len(plants)} 种植物")
        for plant in plants:
            print(f"  - {plant.common_names.get('zh', 'Unknown')} ({plant.genus})")
        ```
        """
        # 方案1: 从plants目录加载（v1.2+）
        if self.plants_path.exists():
            plants = []
            for json_file in self.plants_path.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    plant = PlantOntology(**data)
                    plants.append(plant)
                except Exception as e:
                    # 植物本体加载失败不影响系统运行
                    print(f"警告: 植物文件加载失败: {json_file.name}, 原因: {e}")
                    continue

            # 如果成功加载了植物本体，返回
            if plants:
                return plants

        # 方案2: 从疾病本体中提取宿主植物（降级方案）
        # 从已加载的疾病中提取宿主植物
        plants_dict: Dict[str, PlantOntology] = {}
        for disease in self._diseases:
            for host in disease.host_plants:
                if host not in plants_dict:
                    plants_dict[host] = PlantOntology(
                        family="Unknown",  # 科信息缺失
                        genus=host,
                        common_names={"en": host},
                        species=[],
                        susceptible_diseases=[disease.disease_id]
                    )
                else:
                    # 添加易感疾病
                    if disease.disease_id not in plants_dict[host].susceptible_diseases:
                        plants_dict[host].susceptible_diseases.append(disease.disease_id)

        return list(plants_dict.values())

    def _load_host_disease_associations(self) -> Dict[str, Any]:
        """
        加载宿主-疾病关系库

        从 `knowledge_base/host_disease/associations.json` 加载宿主-疾病关联关系

        Returns:
            Dict[str, Any]: 宿主-疾病关系数据

        Raises:
            KnowledgeBaseNotFoundError: 宿主-疾病关系文件不存在
        """
        associations_file = self.host_disease_path / "associations.json"
        if not associations_file.exists():
            raise KnowledgeBaseNotFoundError(f"宿主-疾病关系文件不存在: {associations_file}")

        try:
            with open(associations_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise KnowledgeBaseLoadError(f"宿主-疾病关系加载失败: {associations_file.name}, 原因: {e}")

    def get_disease_by_id(self, disease_id: str) -> Optional[DiseaseOntology]:
        """
        根据疾病ID获取疾病本体

        Args:
            disease_id: 疾病ID（如 "rose_black_spot"）

        Returns:
            Optional[DiseaseOntology]: 疾病本体对象，如果不存在则返回None

        示例：
        ```python
        disease = loader.get_disease_by_id("rose_black_spot")
        if disease:
            print(f"疾病名称: {disease.disease_name}")
        else:
            print("疾病不存在")
        ```
        """
        return self._diseases_dict.get(disease_id)

    def get_all_diseases(self) -> List[DiseaseOntology]:
        """
        获取所有疾病本体（从缓存）

        Returns:
            List[DiseaseOntology]: 疾病本体列表
        """
        return self._diseases

    def get_feature_ontology(self) -> Optional[FeatureOntology]:
        """
        获取特征本体（从缓存）

        Returns:
            Optional[FeatureOntology]: 特征本体对象
        """
        return self._feature_ontology

    def get_all_plants(self) -> List[PlantOntology]:
        """
        获取所有植物本体（从缓存）

        Returns:
            List[PlantOntology]: 植物本体列表
        """
        return self._plants

    def get_host_disease_associations(self) -> Optional[Dict[str, Any]]:
        """
        获取宿主-疾病关系（从缓存）

        Returns:
            Optional[Dict[str, Any]]: 宿主-疾病关系数据
        """
        return self._host_disease_associations

    def get_diseases_by_host(self, host_genus: str) -> List[str]:
        """
        根据宿主植物获取候选疾病ID列表

        Args:
            host_genus: 宿主植物属名（如 "Rosa"）

        Returns:
            List[str]: 候选疾病ID列表

        示例：
        ```python
        disease_ids = loader.get_diseases_by_host("Rosa")
        print(f"Rosa属植物的候选疾病: {disease_ids}")
        # 输出: ['rose_black_spot', 'rose_powdery_mildew', 'rose_rust', 'rose_downy_mildew']
        ```
        """
        if self._host_disease_associations is None:
            # 降级方案：从疾病本体中查找
            return [d.disease_id for d in self._diseases if host_genus in d.host_plants]

        # 从宿主-疾病关系库中查找
        associations = self._host_disease_associations.get("associations", [])
        for assoc in associations:
            if assoc.get("host_genus") == host_genus:
                return [d.get("disease_id") for d in assoc.get("diseases", [])]

        return []

    def reload(self) -> None:
        """
        热重载知识库

        重新加载所有知识库文件，更新内部缓存

        使用场景：
        - 管理后台修改了疾病本体JSON文件
        - 管理后台添加了新的疾病
        - 需要立即生效，不重启服务

        示例：
        ```python
        # 管理后台调用
        loader.reload()
        print("知识库已重新加载")
        ```
        """
        self._load_all()


def main():
    """
    KnowledgeBaseLoader 使用示例

    演示如何：
    1. 初始化加载器（使用相对路径）
    2. 加载所有疾病本体
    3. 加载特征本体
    4. 按ID查询疾病
    5. 根据宿主植物查询候选疾病
    6. 热重载知识库
    """
    print("=" * 80)
    print("KnowledgeBaseLoader 使用示例")
    print("=" * 80)

    # 1. 初始化加载器（使用相对路径）
    print("\n[示例1] 初始化知识库加载器")
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    kb_path = project_root / "backend" / "knowledge_base"
    print(f"  知识库路径: {kb_path}")

    try:
        loader = KnowledgeBaseLoader(kb_path)
        print(f"  [OK] 知识库加载器初始化成功")
    except KnowledgeBaseNotFoundError as e:
        print(f"  [FAIL] 知识库加载器初始化失败: {e}")
        return

    # 2. 加载所有疾病本体
    print("\n[示例2] 加载所有疾病本体")
    diseases = loader.get_all_diseases()
    print(f"  加载了 {len(diseases)} 种疾病:")
    for disease in diseases:
        print(f"    - {disease.disease_name} ({disease.disease_id})")
        print(f"      病原体: {disease.pathogen}")
        print(f"      宿主植物: {', '.join(disease.host_plants)}")

    # 3. 加载特征本体
    print("\n[示例3] 加载特征本体")
    feature_ontology = loader.get_feature_ontology()
    if feature_ontology:
        print(f"  [OK] 特征本体加载成功")
        print(f"    - 版本: {feature_ontology.version}")
        print(f"    - 特征维度数: {len(feature_ontology.dimensions)}")
        print(f"    - 症状类型数: {len(feature_ontology.symptom_types)}")

        # 显示模糊匹配规则
        fuzzy = feature_ontology.fuzzy_matching
        if "color_aliases" in fuzzy:
            print(f"    - 颜色别名组数: {len(fuzzy['color_aliases'])}")
        if "size_tolerance" in fuzzy:
            print(f"    - 尺寸容差: ±{fuzzy['size_tolerance']} 级")
    else:
        print(f"  [FAIL] 特征本体加载失败")

    # 4. 按ID查询疾病
    print("\n[示例4] 按ID查询疾病")
    disease_id = "rose_black_spot"
    disease = loader.get_disease_by_id(disease_id)
    if disease:
        print(f"  [OK] 找到疾病: {disease.disease_name}")
        print(f"    - ID: {disease.disease_id}")
        print(f"    - 英文名: {disease.common_name_en}")
        print(f"    - 病原体: {disease.pathogen}")
        print(f"    - 主要特征数: {len(disease.get_major_features())}")
    else:
        print(f"  [FAIL] 疾病不存在: {disease_id}")

    # 5. 根据宿主植物查询候选疾病
    print("\n[示例5] 根据宿主植物查询候选疾病")
    host_genus = "Rosa"
    disease_ids = loader.get_diseases_by_host(host_genus)
    print(f"  宿主植物: {host_genus}")
    print(f"  候选疾病数: {len(disease_ids)}")
    for did in disease_ids:
        disease = loader.get_disease_by_id(did)
        if disease:
            print(f"    - {disease.disease_name} ({did})")

    # 6. 加载植物本体
    print("\n[示例6] 加载植物本体")
    plants = loader.get_all_plants()
    print(f"  加载了 {len(plants)} 种植物:")
    for plant in plants:
        print(f"    - {plant.common_names.get('zh', plant.genus)} ({plant.genus})")
        print(f"      科: {plant.family}")
        print(f"      易感疾病数: {len(plant.susceptible_diseases)}")

    # 7. 热重载知识库（模拟）
    print("\n[示例7] 热重载知识库")
    print(f"  重载前疾病数: {len(loader.get_all_diseases())}")
    try:
        loader.reload()
        print(f"  [OK] 知识库重载成功")
        print(f"  重载后疾病数: {len(loader.get_all_diseases())}")
    except Exception as e:
        print(f"  [FAIL] 知识库重载失败: {e}")

    # 8. 获取宿主-疾病关系
    print("\n[示例8] 获取宿主-疾病关系")
    associations = loader.get_host_disease_associations()
    if associations:
        print(f"  [OK] 宿主-疾病关系加载成功")
        print(f"    - 版本: {associations.get('version')}")
        print(f"    - 宿主数: {len(associations.get('associations', []))}")
    else:
        print(f"  [INFO] 宿主-疾病关系文件不存在（使用降级方案）")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
