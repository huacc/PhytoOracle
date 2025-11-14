"""
知识库服务 (KnowledgeService)

功能：
- 提供统一的知识库访问接口
- 实现知识库初始化和热更新
- 支持按种属、疾病ID等多维度查询
- 实现知识库版本管理（Git commit hash）

实现阶段：P3.5

架构说明：
- 属于应用服务层（Application Service Layer）
- 封装P2.3的KnowledgeBaseLoader
- 提供高层次的查询和管理接口
- 被DiagnosisService（P3.3）和API层（P4）调用

作者：AI Python Architect
日期：2025-11-13
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import subprocess
import json

from backend.infrastructure.ontology.loader import KnowledgeBaseLoader
from backend.domain.disease import DiseaseOntology
from backend.domain.feature import FeatureOntology
from backend.infrastructure.ontology.exceptions import (
    KnowledgeBaseNotFoundError,
    KnowledgeBaseLoadError,
)


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeServiceException(Exception):
    """
    知识库服务异常基类

    用于封装知识库服务层的各种异常
    """
    pass


class KnowledgeService:
    """
    知识库服务类

    核心功能：
    1. 知识库初始化（initialize方法）
    2. 知识库热更新（reload方法）
    3. 候选疾病查询（get_diseases_by_genus方法）
    4. 全部疾病查询（get_all_diseases方法）
    5. 单个疾病查询（get_disease_by_id方法）
    6. 知识库版本管理（记录Git commit hash）

    架构说明：
    - 属于应用服务层（Application Service Layer）
    - 依赖基础设施层的 KnowledgeBaseLoader
    - 提供高层次的查询和管理接口
    - 被 DiagnosisService 和 API 层调用

    使用示例：
    ```python
    from pathlib import Path
    from backend.services.knowledge_service import KnowledgeService

    # 初始化服务
    project_root = Path(__file__).resolve().parent.parent
    kb_path = project_root / "knowledge_base"
    service = KnowledgeService(kb_path)

    # 初始化知识库
    await service.initialize()

    # 查询疾病
    diseases = service.get_diseases_by_genus("Rosa")
    print(f"找到 {len(diseases)} 种玫瑰属疾病")

    # 热更新知识库
    await service.reload()
    ```
    """

    def __init__(
        self,
        kb_path: Path,
        auto_initialize: bool = True
    ):
        """
        初始化知识库服务

        Args:
            kb_path: 知识库根目录路径
            auto_initialize: 是否自动初始化知识库（默认 True）

        Raises:
            KnowledgeServiceException: 知识库路径不存在
        """
        if not kb_path.exists():
            raise KnowledgeServiceException(f"知识库路径不存在: {kb_path}")

        self.kb_path = kb_path
        self.loader: Optional[KnowledgeBaseLoader] = None

        # 知识库缓存
        self._diseases: List[DiseaseOntology] = []
        self._diseases_by_id: Dict[str, DiseaseOntology] = {}
        self._diseases_by_genus: Dict[str, List[DiseaseOntology]] = {}
        self._feature_ontology: Optional[FeatureOntology] = None

        # 元数据
        self._initialized = False
        self._last_loaded: Optional[datetime] = None
        self._version: Optional[str] = None
        self._git_commit_hash: Optional[str] = None

        # 自动初始化
        if auto_initialize:
            try:
                self.initialize()
            except Exception as e:
                logger.warning(f"自动初始化知识库失败: {e}，可稍后手动调用 initialize()")

        logger.info("KnowledgeService 初始化完成")

    def initialize(self) -> None:
        """
        初始化知识库

        加载所有知识库数据，构建索引和缓存

        Raises:
            KnowledgeServiceException: 知识库初始化失败

        使用示例：
        ```python
        service = KnowledgeService(kb_path, auto_initialize=False)

        # 手动初始化
        service.initialize()

        # 验证
        assert service.is_initialized()
        print(f"加载了 {len(service.get_all_diseases())} 种疾病")
        ```
        """
        logger.info("开始初始化知识库")

        try:
            # 1. 创建 KnowledgeBaseLoader
            self.loader = KnowledgeBaseLoader(self.kb_path)

            # 2. 加载所有疾病
            self._diseases = self.loader.get_all_diseases()
            logger.info(f"  - 加载了 {len(self._diseases)} 种疾病")

            # 3. 构建按 ID 索引
            self._diseases_by_id = {d.disease_id: d for d in self._diseases}

            # 4. 构建按种属索引
            self._diseases_by_genus = {}
            for disease in self._diseases:
                for genus in disease.host_plants:
                    if genus not in self._diseases_by_genus:
                        self._diseases_by_genus[genus] = []
                    self._diseases_by_genus[genus].append(disease)
            logger.info(f"  - 按种属索引构建完成：{len(self._diseases_by_genus)} 个种属")

            # 5. 加载特征本体
            self._feature_ontology = self.loader.get_feature_ontology()
            logger.info("  - 特征本体加载完成")

            # 6. 记录版本信息
            self._last_loaded = datetime.now()
            self._version = "v1.0"
            self._git_commit_hash = self._get_git_commit_hash()
            logger.info(f"  - 版本信息：{self._version}, Git Commit: {self._git_commit_hash or 'N/A'}")

            # 7. 标记为已初始化
            self._initialized = True

            logger.info("知识库初始化成功")

        except KnowledgeBaseNotFoundError as e:
            logger.error(f"知识库初始化失败（路径不存在）: {e}")
            raise KnowledgeServiceException(f"知识库初始化失败: {e}")
        except KnowledgeBaseLoadError as e:
            logger.error(f"知识库初始化失败（加载错误）: {e}")
            raise KnowledgeServiceException(f"知识库初始化失败: {e}")
        except Exception as e:
            logger.error(f"知识库初始化失败（未知错误）: {e}")
            raise KnowledgeServiceException(f"知识库初始化失败: {e}")

    def reload(self) -> None:
        """
        热更新知识库

        重新加载所有知识库数据，清除缓存并重建索引
        无需重启服务即可生效

        适用场景：
        - 管理后台修改了知识库数据
        - 添加了新的疾病定义
        - 更新了特征本体

        Raises:
            KnowledgeServiceException: 知识库重新加载失败

        使用示例：
        ```python
        # 修改知识库文件后
        service.reload()
        print(f"知识库已更新，最后加载时间: {service.get_last_loaded()}")
        ```
        """
        logger.info("开始热更新知识库")

        # 重新初始化（会重置所有缓存）
        self.initialize()

        logger.info("知识库热更新完成")

    def get_diseases_by_genus(
        self,
        genus: str
    ) -> List[DiseaseOntology]:
        """
        按花卉种属查询疾病

        用于P3.3的候选疾病筛选（基于Q0.2的flower_genus）

        Args:
            genus: 花卉种属（如 "Rosa", "Prunus"）

        Returns:
            List[DiseaseOntology]: 该种属的疾病列表（可能为空）

        使用示例：
        ```python
        # 查询玫瑰属疾病
        rose_diseases = service.get_diseases_by_genus("Rosa")
        for disease in rose_diseases:
            print(f"  - {disease.disease_name} ({disease.disease_id})")
        ```
        """
        self._check_initialized()

        # 从按种属索引中查询
        diseases = self._diseases_by_genus.get(genus, [])
        logger.info(f"查询种属 {genus} 的疾病：找到 {len(diseases)} 种")

        return diseases

    def get_all_diseases(self) -> List[DiseaseOntology]:
        """
        获取所有疾病

        用于管理后台展示、统计分析等

        Returns:
            List[DiseaseOntology]: 所有疾病列表

        使用示例：
        ```python
        all_diseases = service.get_all_diseases()
        print(f"知识库共有 {len(all_diseases)} 种疾病")
        ```
        """
        self._check_initialized()

        logger.info(f"查询所有疾病：共 {len(self._diseases)} 种")
        return self._diseases.copy()  # 返回副本，防止外部修改

    def get_disease_by_id(
        self,
        disease_id: str
    ) -> Optional[DiseaseOntology]:
        """
        按疾病ID查询单个疾病

        Args:
            disease_id: 疾病ID（如 "rose_black_spot"）

        Returns:
            DiseaseOntology: 疾病对象（如果找到）
            None: 如果疾病不存在

        使用示例：
        ```python
        disease = service.get_disease_by_id("rose_black_spot")
        if disease:
            print(f"疾病名称: {disease.disease_name}")
            print(f"病原体: {disease.pathogen}")
        else:
            print("疾病不存在")
        ```
        """
        self._check_initialized()

        disease = self._diseases_by_id.get(disease_id)
        if disease:
            logger.info(f"查询疾病 {disease_id}：找到")
        else:
            logger.warning(f"查询疾病 {disease_id}：未找到")

        return disease

    def get_knowledge_tree(self) -> Dict[str, Any]:
        """
        获取按宿主属分组的疾病树结构（P3.9新增）

        读取host_disease/associations.json文件，返回树形结构的知识库组织视图。
        用于前端界面4的知识库树展示。

        Returns:
            Dict[str, Any]: 树形结构的知识库数据
            ```python
            {
                "version": "1.0",
                "last_updated": "2025-01-14T10:30:45Z",
                "total_hosts": 5,
                "total_diseases": 13,
                "hosts": [
                    {
                        "genus": "Rosa",
                        "name_zh": "蔷薇属",
                        "name_en": "Rose",
                        "disease_count": 4,
                        "diseases": [
                            {
                                "disease_id": "rose_black_spot",
                                "disease_name": "玫瑰黑斑病",
                                "common_name_en": "Rose Black Spot",
                                "pathogen": "Diplocarpon rosae",
                                "prevalence": "common"
                            }
                        ]
                    }
                ]
            }
            ```

        Raises:
            KnowledgeServiceException: 读取文件失败

        使用示例：
        ```python
        tree = service.get_knowledge_tree()
        print(f"知识库包含 {tree['total_hosts']} 个宿主属")
        for host in tree['hosts']:
            print(f"  - {host['name_zh']}（{host['genus']}）：{host['disease_count']} 种疾病")
        ```
        """
        # P3.9新增：此方法不需要initialization，因为它直接读取JSON文件，不依赖self._diseases等初始化的数据结构

        # 读取associations.json文件
        associations_file = self.kb_path / "host_disease" / "associations.json"

        if not associations_file.exists():
            logger.error(f"associations.json文件不存在: {associations_file}")
            raise KnowledgeServiceException(
                f"associations.json不存在: {associations_file}"
            )

        try:
            with open(associations_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 提取必要字段
            version = data.get("version", "1.0")
            last_updated_str = data.get("last_updated", datetime.now().strftime("%Y-%m-%d"))
            # 转换为ISO 8601格式
            last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d").isoformat() + "Z"

            # 构建hosts列表
            hosts = []
            total_diseases = 0

            for association in data.get("associations", []):
                host_genus = association.get("host_genus", "")
                genus_name = association.get("genus_name", "")
                genus_name_en = association.get("genus_name_en", "")
                diseases_data = association.get("diseases", [])

                disease_count = len(diseases_data)
                total_diseases += disease_count

                # 构建疾病列表
                diseases = []
                for disease in diseases_data:
                    diseases.append({
                        "disease_id": disease.get("disease_id", ""),
                        "disease_name": disease.get("disease_name", ""),
                        "common_name_en": disease.get("common_name_en", ""),
                        "pathogen": disease.get("pathogen", ""),
                        "prevalence": disease.get("prevalence", "unknown")
                    })

                # 添加到hosts列表
                hosts.append({
                    "genus": host_genus,
                    "name_zh": genus_name,
                    "name_en": genus_name_en,
                    "disease_count": disease_count,
                    "diseases": diseases
                })

            # 构建返回结果
            result = {
                "version": version,
                "last_updated": last_updated,
                "total_hosts": len(hosts),
                "total_diseases": total_diseases,
                "hosts": hosts
            }

            logger.info(f"获取知识库树：{len(hosts)} 个宿主属，{total_diseases} 种疾病")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise KnowledgeServiceException(f"JSON解析失败: {e}")
        except Exception as e:
            logger.error(f"读取associations.json失败: {e}")
            raise KnowledgeServiceException(f"读取associations.json失败: {e}")

    def get_feature_ontology(self) -> Optional[FeatureOntology]:
        """
        获取特征本体

        Returns:
            FeatureOntology: 特征本体对象

        使用示例：
        ```python
        feature_ontology = service.get_feature_ontology()
        print(f"特征维度数: {len(feature_ontology.dimensions)}")
        ```
        """
        self._check_initialized()
        return self._feature_ontology

    def get_version_info(self) -> Dict[str, Any]:
        """
        获取知识库版本信息

        Returns:
            Dict[str, Any]: 版本信息字典
            ```python
            {
                "version": "v1.0",
                "last_loaded": datetime(...),
                "git_commit_hash": "abc123...",
                "disease_count": 2,
                "genus_count": 2
            }
            ```

        使用示例：
        ```python
        version_info = service.get_version_info()
        print(f"知识库版本: {version_info['version']}")
        print(f"Git Commit: {version_info['git_commit_hash']}")
        ```
        """
        self._check_initialized()

        return {
            "version": self._version,
            "last_loaded": self._last_loaded,
            "git_commit_hash": self._git_commit_hash,
            "disease_count": len(self._diseases),
            "genus_count": len(self._diseases_by_genus)
        }

    def get_last_loaded(self) -> Optional[datetime]:
        """
        获取最后加载时间

        Returns:
            datetime: 最后加载时间（如果已初始化）
            None: 如果未初始化

        使用示例：
        ```python
        last_loaded = service.get_last_loaded()
        if last_loaded:
            print(f"知识库最后加载时间: {last_loaded.strftime('%Y-%m-%d %H:%M:%S')}")
        ```
        """
        return self._last_loaded

    def is_initialized(self) -> bool:
        """
        检查知识库是否已初始化

        Returns:
            bool: True if initialized, False otherwise

        使用示例：
        ```python
        if service.is_initialized():
            print("知识库已就绪")
        else:
            service.initialize()
        ```
        """
        return self._initialized

    def _check_initialized(self) -> None:
        """
        检查知识库是否已初始化

        内部方法，在所有查询方法开始时调用

        Raises:
            KnowledgeServiceException: 如果知识库未初始化
        """
        if not self._initialized:
            raise KnowledgeServiceException(
                "知识库未初始化，请先调用 initialize() 方法"
            )

    def _get_git_commit_hash(self) -> Optional[str]:
        """
        获取当前 Git commit hash

        用于知识库版本管理和审计

        Returns:
            str: Git commit hash（短格式，前7位）
            None: 如果不是 Git 仓库或获取失败

        实现说明：
        - 使用 git rev-parse HEAD 获取当前 commit hash
        - 仅在 Git 仓库中有效
        - 失败时返回 None 而不抛出异常
        """
        try:
            # 获取项目根目录（知识库的上级目录）
            project_root = self.kb_path.parent

            # 执行 git rev-parse --short HEAD
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                commit_hash = result.stdout.strip()
                logger.info(f"  - 获取 Git commit hash: {commit_hash}")
                return commit_hash
            else:
                logger.warning(f"  - 获取 Git commit hash 失败: {result.stderr}")
                return None

        except FileNotFoundError:
            logger.warning("  - Git 未安装，无法获取 commit hash")
            return None
        except subprocess.TimeoutExpired:
            logger.warning("  - 获取 Git commit hash 超时")
            return None
        except Exception as e:
            logger.warning(f"  - 获取 Git commit hash 失败: {e}")
            return None


def main():
    """
    KnowledgeService 使用示例

    演示如何：
    1. 初始化 KnowledgeService
    2. 查询所有疾病
    3. 按种属查询疾病
    4. 按 ID 查询单个疾病
    5. 获取版本信息
    6. 热更新知识库
    """
    print("=" * 80)
    print("KnowledgeService 使用示例")
    print("=" * 80)

    # 1. 初始化服务
    print("\n[示例1] 初始化 KnowledgeService")
    project_root = Path(__file__).resolve().parent.parent
    kb_path = project_root / "knowledge_base"
    print(f"  知识库路径: {kb_path}")

    if not kb_path.exists():
        print(f"  [ERROR] 知识库路径不存在: {kb_path}")
        return

    try:
        service = KnowledgeService(kb_path, auto_initialize=True)
        print("  [OK] KnowledgeService 初始化完成")
    except KnowledgeServiceException as e:
        print(f"  [ERROR] 初始化失败: {e}")
        return

    # 2. 查询所有疾病
    print("\n[示例2] 查询所有疾病")
    try:
        all_diseases = service.get_all_diseases()
        print(f"  [OK] 知识库共有 {len(all_diseases)} 种疾病")
        for disease in all_diseases:
            print(f"    - {disease.disease_name} ({disease.disease_id})")
    except KnowledgeServiceException as e:
        print(f"  [ERROR] 查询失败: {e}")

    # 3. 按种属查询疾病
    print("\n[示例3] 按种属查询疾病（Rosa 玫瑰属）")
    try:
        rosa_diseases = service.get_diseases_by_genus("Rosa")
        print(f"  [OK] 玫瑰属疾病：{len(rosa_diseases)} 种")
        for disease in rosa_diseases:
            print(f"    - {disease.disease_name} ({disease.disease_id})")
    except KnowledgeServiceException as e:
        print(f"  [ERROR] 查询失败: {e}")

    # 4. 按 ID 查询单个疾病
    print("\n[示例4] 按 ID 查询单个疾病（rose_black_spot）")
    try:
        disease = service.get_disease_by_id("rose_black_spot")
        if disease:
            print(f"  [OK] 找到疾病")
            print(f"    - 疾病名称: {disease.disease_name}")
            print(f"    - 英文名: {disease.common_name_en}")
            print(f"    - 病原体: {disease.pathogen}")
            print(f"    - 主要特征数: {len(disease.major_features)}")
        else:
            print("  [INFO] 疾病不存在")
    except KnowledgeServiceException as e:
        print(f"  [ERROR] 查询失败: {e}")

    # 5. 获取版本信息
    print("\n[示例5] 获取知识库版本信息")
    try:
        version_info = service.get_version_info()
        print(f"  [OK] 版本信息:")
        print(f"    - 版本: {version_info['version']}")
        print(f"    - 最后加载: {version_info['last_loaded'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    - Git Commit: {version_info['git_commit_hash'] or 'N/A'}")
        print(f"    - 疾病数: {version_info['disease_count']}")
        print(f"    - 种属数: {version_info['genus_count']}")
    except KnowledgeServiceException as e:
        print(f"  [ERROR] 获取失败: {e}")

    # 6. 热更新知识库
    print("\n[示例6] 热更新知识库")
    try:
        print("  提示: 修改知识库文件后，可调用 reload() 方法")
        print("  这里演示热更新流程（实际未修改文件）")
        # service.reload()
        print("  [SKIP] 跳过实际执行（示例代码）")
    except KnowledgeServiceException as e:
        print(f"  [ERROR] 热更新失败: {e}")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
