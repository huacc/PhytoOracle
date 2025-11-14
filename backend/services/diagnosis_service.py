"""
诊断服务 (DiagnosisService)

功能：
- 实现完整的花卉疾病诊断流程
- Q0 逐级过滤：Q0.0-Q0.5 六步过滤机制
- Q1-Q6 动态特征提取
- 三层渐进诊断（VLM + 知识库 + 加权评分）
- VLM 兜底策略

实现阶段：
- P3.1: Q0 逐级过滤实现 ✓
- P3.2: Q1-Q6 动态特征提取 ✓
- P3.3: 三层渐进诊断流程 ✓
- P3.4: VLM 兜底策略 ✓

作者：AI Python Architect
日期：2025-11-13
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Domain 模型
from backend.domain.diagnosis import (
    ContentType,
    PlantCategory,
    FlowerGenus,
    OrganType,
    Completeness,
    AbnormalityStatus,
    FeatureVector,
    DiagnosisResult,
    ConfidenceLevel,
)

# VLM 客户端
from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient

# VLM 响应模型
from backend.infrastructure.llm.prompts.response_schema import (
    Q00Response,
    Q01Response,
    Q02Response,
    Q03Response,
    Q04Response,
    Q05Response,
    FeatureResponse,
)

# VLM 提示词
from backend.infrastructure.llm.prompts.q0_0_content import Q0_0_CONTENT_TYPE_PROMPT
from backend.infrastructure.llm.prompts.q0_1_category import Q0_1_PLANT_CATEGORY_PROMPT
from backend.infrastructure.llm.prompts.q0_2_genus import Q0_2_GENUS_PROMPT
from backend.infrastructure.llm.prompts.q0_3_organ import Q0_3_ORGAN_PROMPT
from backend.infrastructure.llm.prompts.q0_4_completeness import Q0_4_COMPLETENESS_PROMPT
from backend.infrastructure.llm.prompts.q0_5_abnormality import Q0_5_ABNORMALITY_PROMPT

# Q1-Q6 动态特征提取提示词构建器
from backend.infrastructure.llm.prompts.q1_q6_features import FeaturePromptBuilder

# VLM 兜底策略提示词
from backend.infrastructure.llm.prompts.fallback import (
    VLM_FALLBACK_DIAGNOSIS_PROMPT,
    VLMFallbackResponse,
)

# VLM 异常
from backend.infrastructure.llm.vlm_exceptions import (
    VLMException,
    AllProvidersFailedException,
)

# 知识库服务（P3.5）
from backend.services.knowledge_service import KnowledgeService

# 加权诊断评分器（P2.5）
from backend.infrastructure.ontology.weighted_scorer import WeightedDiagnosisScorer


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiagnosisException(Exception):
    """
    诊断服务异常基类

    用于封装诊断流程中的各种异常
    """
    pass


class UnsupportedImageException(DiagnosisException):
    """
    不支持的图像类型异常

    当图像内容不符合诊断要求时抛出（如非植物、非花卉等）
    """
    pass


class DiagnosisService:
    """
    诊断服务类

    核心功能：
    1. Q0 逐级过滤（Q0.0-Q0.5）
    2. Q1-Q6 动态特征提取（P3.2 实现）
    3. 三层渐进诊断（P3.3 实现）
    4. VLM 兜底策略（P3.4 实现）

    架构说明：
    - 属于应用服务层（Application Service Layer）
    - 依赖基础设施层的 VLM 客户端
    - 依赖领域模型层的诊断模型
    - 被 API 层调用（P4 阶段）

    使用示例：
    ```python
    from backend.services.diagnosis_service import DiagnosisService

    # 初始化服务
    service = DiagnosisService()

    # 执行 Q0 过滤
    with open("rose.jpg", "rb") as f:
        image_bytes = f.read()

    q0_responses = await service.execute_q0_sequence(image_bytes)
    print(f"花卉种属: {q0_responses['flower_genus']}")
    ```
    """

    def __init__(
        self,
        vlm_client: Optional[MultiProviderVLMClient] = None,
        knowledge_service: Optional[KnowledgeService] = None,
        diagnosis_scorer: Optional[WeightedDiagnosisScorer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化诊断服务

        Args:
            vlm_client: VLM 客户端实例（如果不提供，则创建默认实例）
            knowledge_service: 知识库服务实例（如果不提供，则创建默认实例）
            diagnosis_scorer: 加权诊断评分器实例（如果不提供，则创建默认实例）
            config: 配置字典（可选）

        配置选项：
        - enable_cache: 是否启用缓存（默认 True）
        - timeout: VLM 调用超时时间（秒，默认 30）
        - kb_path: 知识库路径（如果需要创建默认 KnowledgeService）

        使用示例：
        ```python
        # 使用默认配置
        service = DiagnosisService()

        # 使用自定义配置
        service = DiagnosisService(
            config={
                "enable_cache": False,
                "timeout": 60,
                "kb_path": "/path/to/knowledge_base"
            }
        )
        ```
        """
        self.vlm_client = vlm_client or MultiProviderVLMClient()
        self.config = config or {}

        # 初始化 Q1-Q6 特征提取提示词构建器
        self.feature_prompt_builder = FeaturePromptBuilder()

        # 初始化知识库服务（如果未提供）
        if knowledge_service is None:
            kb_path = Path(self.config.get(
                "kb_path",
                Path(__file__).resolve().parent.parent / "knowledge_base"
            ))
            self.knowledge_service = KnowledgeService(kb_path, auto_initialize=True)
        else:
            self.knowledge_service = knowledge_service

        # 初始化加权诊断评分器（如果未提供）
        if diagnosis_scorer is None:
            project_root = Path(__file__).resolve().parent.parent
            kb_path = project_root / "knowledge_base"
            weights_dir = project_root / "infrastructure" / "ontology" / "scoring_weights"
            fuzzy_rules_dir = project_root / "infrastructure" / "ontology" / "fuzzy_rules"
            self.diagnosis_scorer = WeightedDiagnosisScorer(kb_path, weights_dir, fuzzy_rules_dir)
        else:
            self.diagnosis_scorer = diagnosis_scorer

        logger.info("DiagnosisService 初始化完成")

    async def execute_q0_sequence(
        self,
        image_bytes: bytes
    ) -> Dict[str, Any]:
        """
        执行 Q0 逐级过滤序列（Q0.0-Q0.5）

        Q0 序列是诊断流程的前置过滤步骤，用于：
        1. 验证图像是否为植物
        2. 验证植物是否为花卉
        3. 识别花卉种属（用于候选疾病剪枝）
        4. 识别器官类型
        5. 检查完整性
        6. 判断是否存在异常

        早期退出机制：
        - 如果 Q0.0 不是植物 → 直接抛出 UnsupportedImageException
        - 如果 Q0.1 不是花卉 → 直接抛出 UnsupportedImageException

        Args:
            image_bytes: 图像字节数据

        Returns:
            Dict[str, Any]: Q0 响应字典，包含所有 Q0 问题的答案
            ```python
            {
                "content_type": "plant",
                "plant_category": "flower",
                "flower_genus": "Rosa",
                "organ": "leaf",
                "completeness": "complete",
                "has_abnormality": "abnormal",
                "q0_confidence": 0.92,  # 平均置信度
                "vlm_provider": "qwen-vl-plus"  # 实际使用的 VLM
            }
            ```

        Raises:
            UnsupportedImageException: 图像不支持（非植物或非花卉）
            VLMException: VLM 调用失败
            AllProvidersFailedException: 所有 VLM Provider 都失败

        使用示例：
        ```python
        with open("rose.jpg", "rb") as f:
            image_bytes = f.read()

        try:
            q0_responses = await service.execute_q0_sequence(image_bytes)
            print(f"识别为 {q0_responses['flower_genus']} 属花卉")
        except UnsupportedImageException as e:
            print(f"图像不支持: {e}")
        ```
        """
        logger.info("开始执行 Q0 逐级过滤序列")

        # 存储所有 Q0 响应
        q0_responses = {}
        confidences = []

        try:
            # Q0.0: 内容类型识别
            logger.info("[Q0.0] 识别内容类型")
            q0_0_response = await self._check_content_type(image_bytes)
            q0_responses["content_type"] = q0_0_response.choice
            confidences.append(q0_0_response.confidence)

            logger.info(f"[Q0.0] 内容类型: {q0_0_response.choice} (置信度: {q0_0_response.confidence:.2f})")

            # 早期退出：非植物图片
            if q0_0_response.choice != "plant":
                raise UnsupportedImageException(
                    f"不支持的图片类型: {q0_0_response.choice}。"
                    f"当前仅支持植物图片诊断。"
                    f"识别到的内容: {q0_0_response.reasoning or '未提供推理信息'}"
                )

            # Q0.1: 植物类别识别
            logger.info("[Q0.1] 识别植物类别")
            q0_1_response = await self._check_plant_category(image_bytes)
            q0_responses["plant_category"] = q0_1_response.choice
            confidences.append(q0_1_response.confidence)

            logger.info(f"[Q0.1] 植物类别: {q0_1_response.choice} (置信度: {q0_1_response.confidence:.2f})")

            # 早期退出：非花卉植物
            if q0_1_response.choice != "flower":
                raise UnsupportedImageException(
                    f"不支持的植物类别: {q0_1_response.choice}。"
                    f"当前仅支持观赏花卉诊断。"
                    f"识别到的植物类型: {q0_1_response.reasoning or '未提供推理信息'}"
                )

            # Q0.2: 花卉种属识别
            logger.info("[Q0.2] 识别花卉种属")
            q0_2_response = await self._check_flower_genus(image_bytes)
            q0_responses["flower_genus"] = q0_2_response.choice
            confidences.append(q0_2_response.confidence)

            logger.info(f"[Q0.2] 花卉种属: {q0_2_response.choice} (置信度: {q0_2_response.confidence:.2f})")

            # Q0.3: 器官识别
            logger.info("[Q0.3] 识别器官类型")
            q0_3_response = await self._check_organ(image_bytes)
            q0_responses["organ"] = q0_3_response.choice
            confidences.append(q0_3_response.confidence)

            logger.info(f"[Q0.3] 器官类型: {q0_3_response.choice} (置信度: {q0_3_response.confidence:.2f})")

            # Q0.4: 完整性检查
            logger.info("[Q0.4] 检查完整性")
            q0_4_response = await self._check_completeness(image_bytes)
            q0_responses["completeness"] = q0_4_response.choice
            confidences.append(q0_4_response.confidence)

            logger.info(f"[Q0.4] 完整性: {q0_4_response.choice} (置信度: {q0_4_response.confidence:.2f})")

            # Q0.5: 异常判断
            logger.info("[Q0.5] 判断是否存在异常")
            q0_5_response = await self._check_abnormality(image_bytes)
            q0_responses["has_abnormality"] = q0_5_response.choice
            confidences.append(q0_5_response.confidence)

            logger.info(f"[Q0.5] 异常状态: {q0_5_response.choice} (置信度: {q0_5_response.confidence:.2f})")

            # 计算平均置信度
            avg_confidence = sum(confidences) / len(confidences)
            q0_responses["q0_confidence"] = avg_confidence

            # 记录使用的 VLM Provider（从最后一次调用获取）
            # 注意：这里简化处理，假设所有调用都使用同一个 Provider
            q0_responses["vlm_provider"] = "qwen-vl-plus"  # 默认值，实际应从 vlm_client 获取

            logger.info(f"Q0 序列执行完成，平均置信度: {avg_confidence:.2f}")

            return q0_responses

        except UnsupportedImageException:
            # 重新抛出不支持的图像异常
            raise
        except VLMException as e:
            logger.error(f"Q0 序列执行失败（VLM 异常）: {e}")
            raise
        except Exception as e:
            logger.error(f"Q0 序列执行失败（未知错误）: {e}")
            raise DiagnosisException(f"Q0 序列执行失败: {e}")

    async def _check_content_type(self, image_bytes: bytes) -> Q00Response:
        """
        Q0.0: 检查内容类型

        识别图像的内容类型（植物、动物、人物、物体、风景、其他）

        Args:
            image_bytes: 图像字节数据

        Returns:
            Q00Response: 内容类型响应

        Raises:
            VLMException: VLM 调用失败
        """
        return await self.vlm_client.query_structured(
            prompt=Q0_0_CONTENT_TYPE_PROMPT,
            response_model=Q00Response,
            image_bytes=image_bytes
        )

    async def _check_plant_category(self, image_bytes: bytes) -> Q01Response:
        """
        Q0.1: 检查植物类别

        识别植物的大类（花卉、蔬菜、树木、农作物、草本、其他）

        Args:
            image_bytes: 图像字节数据

        Returns:
            Q01Response: 植物类别响应

        Raises:
            VLMException: VLM 调用失败
        """
        return await self.vlm_client.query_structured(
            prompt=Q0_1_PLANT_CATEGORY_PROMPT,
            response_model=Q01Response,
            image_bytes=image_bytes
        )

    async def _check_flower_genus(self, image_bytes: bytes) -> Q02Response:
        """
        Q0.2: 检查花卉种属

        识别花卉的属（Rosa、Prunus、Tulipa、Dianthus、Paeonia、unknown）
        用于候选疾病剪枝

        Args:
            image_bytes: 图像字节数据

        Returns:
            Q02Response: 花卉种属响应

        Raises:
            VLMException: VLM 调用失败
        """
        return await self.vlm_client.query_structured(
            prompt=Q0_2_GENUS_PROMPT,
            response_model=Q02Response,
            image_bytes=image_bytes
        )

    async def _check_organ(self, image_bytes: bytes) -> Q03Response:
        """
        Q0.3: 检查器官类型

        识别图像中展示的植物器官（花朵、叶片、或两者都有）

        Args:
            image_bytes: 图像字节数据

        Returns:
            Q03Response: 器官类型响应

        Raises:
            VLMException: VLM 调用失败
        """
        return await self.vlm_client.query_structured(
            prompt=Q0_3_ORGAN_PROMPT,
            response_model=Q03Response,
            image_bytes=image_bytes
        )

    async def _check_completeness(self, image_bytes: bytes) -> Q04Response:
        """
        Q0.4: 检查完整性

        判断器官的完整性（完整、部分、特写）

        Args:
            image_bytes: 图像字节数据

        Returns:
            Q04Response: 完整性响应

        Raises:
            VLMException: VLM 调用失败
        """
        return await self.vlm_client.query_structured(
            prompt=Q0_4_COMPLETENESS_PROMPT,
            response_model=Q04Response,
            image_bytes=image_bytes
        )

    async def _check_abnormality(self, image_bytes: bytes) -> Q05Response:
        """
        Q0.5: 检查异常状态

        判断是否存在异常（健康、异常）

        Args:
            image_bytes: 图像字节数据

        Returns:
            Q05Response: 异常状态响应

        Raises:
            VLMException: VLM 调用失败
        """
        return await self.vlm_client.query_structured(
            prompt=Q0_5_ABNORMALITY_PROMPT,
            response_model=Q05Response,
            image_bytes=image_bytes
        )

    async def execute_q1_q6_sequence(
        self,
        image_bytes: bytes,
        q0_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行 Q1-Q6 动态特征提取序列

        根据 Q0 序列的结果（特别是 Q0.5 异常判断），动态提取疾病特征

        Q1-Q6 序列是三层诊断流程的 Layer 1，用于：
        1. Q1: 识别症状类型（symptom_type）
        2. Q2-Q6: 根据 Q1 结果动态生成问题
           - 如 symptom_type = "necrosis_spot" → Q2: color_center, Q3: color_border, Q4: size, Q5: location, Q6: distribution
           - 如 symptom_type = "powdery_coating" → Q2: coverage_color, Q3: coverage_density, 等

        Args:
            image_bytes: 图像字节数据
            q0_responses: Q0 序列的响应字典（来自 execute_q0_sequence）

        Returns:
            Dict[str, Any]: Q1-Q6 响应字典，包含所有特征维度的答案
            ```python
            {
                "symptom_type": "necrosis_spot",
                "color_center": "black",
                "color_border": "yellow",
                "size": "medium",
                "location": "lamina",
                "distribution": "scattered",
                "q1_q6_confidence": 0.88,  # 平均置信度
                "uncertain_features": []    # 置信度 < 0.5 的特征
            }
            ```

        Raises:
            DiagnosisException: Q1-Q6 序列执行失败
            VLMException: VLM 调用失败

        使用示例：
        ```python
        # 先执行 Q0 序列
        q0_responses = await service.execute_q0_sequence(image_bytes)

        # 如果 Q0.5 判定为异常，执行 Q1-Q6 序列
        if q0_responses["has_abnormality"] == "abnormal":
            q1_q6_responses = await service.execute_q1_q6_sequence(image_bytes, q0_responses)
            print(f"症状类型: {q1_q6_responses['symptom_type']}")
        ```
        """
        logger.info("开始执行 Q1-Q6 动态特征提取序列")

        # 存储所有 Q1-Q6 响应
        q1_q6_responses = {}
        confidences = []
        uncertain_features = []

        try:
            # Q1: 症状类型识别
            logger.info("[Q1] 识别症状类型")
            q1_response = await self._extract_feature(image_bytes, "symptom_type")
            q1_q6_responses["symptom_type"] = q1_response.choice
            confidences.append(q1_response.confidence)

            # 处理不确定性
            if q1_response.confidence < 0.5:
                uncertain_features.append("symptom_type")
                logger.warning(f"[Q1] 置信度较低: {q1_response.confidence:.2f}")

            logger.info(f"[Q1] 症状类型: {q1_response.choice} (置信度: {q1_response.confidence:.2f})")

            # Q2-Q6: 根据症状类型动态生成问题
            # 这里我们提取所有特征维度（实际应用中可以根据 symptom_type 优化）
            feature_dimensions = [
                "color_center",
                "color_border",
                "size",
                "location",
                "distribution"
            ]

            for dimension in feature_dimensions:
                logger.info(f"[Q{feature_dimensions.index(dimension) + 2}] 提取特征: {dimension}")
                try:
                    response = await self._extract_feature(image_bytes, dimension)
                    q1_q6_responses[dimension] = response.choice
                    confidences.append(response.confidence)

                    # 处理不确定性
                    if response.confidence < 0.5:
                        uncertain_features.append(dimension)
                        logger.warning(f"[Q{feature_dimensions.index(dimension) + 2}] 置信度较低: {response.confidence:.2f}")

                    logger.info(
                        f"[Q{feature_dimensions.index(dimension) + 2}] {dimension}: {response.choice} "
                        f"(置信度: {response.confidence:.2f})"
                    )
                except Exception as e:
                    logger.error(f"特征 {dimension} 提取失败: {e}")
                    # 特征提取失败时使用默认值
                    q1_q6_responses[dimension] = "unknown"
                    uncertain_features.append(dimension)

            # 计算平均置信度
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            q1_q6_responses["q1_q6_confidence"] = avg_confidence
            q1_q6_responses["uncertain_features"] = uncertain_features

            logger.info(
                f"Q1-Q6 序列执行完成，平均置信度: {avg_confidence:.2f}, "
                f"不确定特征数: {len(uncertain_features)}"
            )

            return q1_q6_responses

        except VLMException as e:
            logger.error(f"Q1-Q6 序列执行失败（VLM 异常）: {e}")
            raise
        except Exception as e:
            logger.error(f"Q1-Q6 序列执行失败（未知错误）: {e}")
            raise DiagnosisException(f"Q1-Q6 序列执行失败: {e}")

    async def _extract_feature(
        self,
        image_bytes: bytes,
        dimension: str
    ) -> FeatureResponse:
        """
        提取单个特征维度

        Args:
            image_bytes: 图像字节数据
            dimension: 特征维度名称（如 "symptom_type", "color_center"）

        Returns:
            FeatureResponse: 特征响应

        Raises:
            VLMException: VLM 调用失败
        """
        # 使用 FeaturePromptBuilder 构建提示词
        prompt = self.feature_prompt_builder.build_prompt(dimension)
        prompt_text = prompt.render()

        # 调用 VLM
        return await self.vlm_client.query_structured(
            prompt=prompt_text,
            response_model=FeatureResponse,
            image_bytes=image_bytes
        )

    def build_feature_vector(
        self,
        q0_responses: Dict[str, Any],
        q1_q6_responses: Dict[str, Any]
    ) -> FeatureVector:
        """
        构建特征向量（FeatureVector Pydantic 对象）

        将 Q0-Q6 的所有响应合并为一个完整的特征向量对象

        Args:
            q0_responses: Q0 序列响应字典
            q1_q6_responses: Q1-Q6 序列响应字典

        Returns:
            FeatureVector: 特征向量对象

        使用示例：
        ```python
        q0_responses = await service.execute_q0_sequence(image_bytes)
        q1_q6_responses = await service.execute_q1_q6_sequence(image_bytes, q0_responses)

        # 构建特征向量
        feature_vector = service.build_feature_vector(q0_responses, q1_q6_responses)
        print(f"种属: {feature_vector.flower_genus}")
        print(f"症状类型: {feature_vector.symptom_type}")
        ```
        """
        # 构建 FeatureVector
        feature_vector = FeatureVector(
            # Q0 特征（必填）
            content_type=ContentType(q0_responses["content_type"]),
            plant_category=PlantCategory(q0_responses["plant_category"]),
            flower_genus=FlowerGenus(q0_responses["flower_genus"]),
            organ=OrganType(q0_responses["organ"]),
            completeness=Completeness(q0_responses["completeness"]),
            has_abnormality=AbnormalityStatus(q0_responses["has_abnormality"]),
            # Q1-Q6 特征（可选）
            symptom_type=q1_q6_responses.get("symptom_type"),
            color_center=q1_q6_responses.get("color_center"),
            color_border=q1_q6_responses.get("color_border"),
            size=q1_q6_responses.get("size"),
            location=q1_q6_responses.get("location"),
            distribution=q1_q6_responses.get("distribution"),
            additional_features={
                "q0_confidence": q0_responses.get("q0_confidence", 0.0),
                "q1_q6_confidence": q1_q6_responses.get("q1_q6_confidence", 0.0),
                "uncertain_features": q1_q6_responses.get("uncertain_features", [])
            }
        )

        logger.info(f"特征向量构建完成: {feature_vector.flower_genus} / {feature_vector.symptom_type}")
        return feature_vector

    async def diagnose(
        self,
        image_bytes: bytes
    ) -> DiagnosisResult:
        """
        执行完整的三层渐进诊断流程（P3.3 + P3.4）

        Layer 1: VLM 视觉特征提取（Q0-Q6）
        Layer 2: 知识库匹配引擎（候选疾病筛选 + 加权评分 + 排序）
        Layer 3: 置信度分层决策（High/Medium/Low）+ VLM 兜底策略

        Args:
            image_bytes: 图像字节数据

        Returns:
            DiagnosisResult: 完整的诊断结果

        Raises:
            UnsupportedImageException: 图像不支持（非植物或非花卉）
            DiagnosisException: 诊断流程执行失败
            VLMException: VLM 调用失败

        使用示例：
        ```python
        with open("rose_leaf.jpg", "rb") as f:
            image_bytes = f.read()

        # 执行完整诊断
        result = await service.diagnose(image_bytes)

        print(f"诊断结果: {result.disease_name}")
        print(f"置信度: {result.level.value}")
        print(f"总分: {result.scores.total_score}")
        ```
        """
        start_time = datetime.now()
        logger.info("开始执行完整诊断流程")

        try:
            # ========== Layer 1: VLM 视觉特征提取 ==========
            logger.info("[Layer 1] VLM 视觉特征提取")

            # 执行 Q0 序列
            q0_responses = await self.execute_q0_sequence(image_bytes)
            logger.info(f"  - Q0 完成：种属={q0_responses['flower_genus']}, 异常={q0_responses['has_abnormality']}")

            # 如果健康，直接返回
            if q0_responses["has_abnormality"] == "healthy":
                return self._build_healthy_result(start_time, q0_responses)

            # 执行 Q1-Q6 序列
            q1_q6_responses = await self.execute_q1_q6_sequence(image_bytes, q0_responses)
            logger.info(f"  - Q1-Q6 完成：症状类型={q1_q6_responses['symptom_type']}")

            # 构建特征向量
            feature_vector = self.build_feature_vector(q0_responses, q1_q6_responses)

            # ========== Layer 2: 知识库匹配引擎 ==========
            logger.info("[Layer 2] 知识库匹配引擎")

            # 候选疾病筛选（根据 flower_genus）
            genus = q0_responses["flower_genus"]
            候选疾病列表 = self.knowledge_service.get_diseases_by_genus(genus)
            logger.info(f"  - 候选疾病筛选：种属={genus}, 找到 {len(候选疾病列表)} 种疾病")

            # 如果没有候选疾病，触发兜底策略
            if not 候选疾病列表:
                logger.warning(f"  - 知识库中没有 {genus} 属的疾病，触发兜底策略")
                return await self._vlm_fallback_diagnosis(image_bytes, feature_vector, start_time)

            # 加权诊断评分
            ranked_results = self.diagnosis_scorer.score_candidates(feature_vector, 候选疾病列表)
            logger.info(f"  - 加权评分完成：Top 1 分数={ranked_results[0]['score'].total_score:.2f}")

            # ========== Layer 3: 置信度分层决策 ==========
            logger.info("[Layer 3] 置信度分层决策")

            top_result = ranked_results[0]
            top_score = top_result["score"]
            top_disease = top_result["disease"]

            # 检查是否需要兜底策略（所有候选疾病 score < 0.6）
            if top_score.total_score < 0.6:
                logger.warning(f"  - 最高分数 {top_score.total_score:.2f} < 0.6，触发兜底策略")
                return await self._vlm_fallback_diagnosis(image_bytes, feature_vector, start_time)

            # 计算执行时间
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # 根据置信度级别返回结果
            confidence_level = top_score.confidence_level

            if confidence_level == ConfidenceLevel.CONFIRMED:
                # 确诊
                return self._build_confirmed_result(
                    feature_vector, top_result, execution_time_ms, start_time
                )
            elif confidence_level == ConfidenceLevel.SUSPECTED:
                # 疑似（返回 Top 2-3 候选）
                candidates = ranked_results[:3] if len(ranked_results) >= 3 else ranked_results
                return self._build_suspected_result(
                    feature_vector, top_result, candidates, execution_time_ms, start_time
                )
            else:
                # 不太可能（触发兜底策略）
                logger.warning(f"  - 置信度级别为 UNLIKELY，触发兜底策略")
                return await self._vlm_fallback_diagnosis(image_bytes, feature_vector, start_time)

        except UnsupportedImageException:
            # 重新抛出不支持的图像异常
            raise
        except VLMException as e:
            logger.error(f"诊断流程失败（VLM 异常）: {e}")
            raise
        except Exception as e:
            logger.error(f"诊断流程失败（未知错误）: {e}")
            raise DiagnosisException(f"诊断流程失败: {e}")

    async def _vlm_fallback_diagnosis(
        self,
        image_bytes: bytes,
        feature_vector: Optional[FeatureVector],
        start_time: datetime
    ) -> DiagnosisResult:
        """
        VLM 兜底策略（P3.4）

        当知识库匹配失败时，调用 VLM 进行开放式诊断

        Args:
            image_bytes: 图像字节数据
            feature_vector: 特征向量（可能为空）
            start_time: 诊断开始时间

        Returns:
            DiagnosisResult: 兜底诊断结果

        Raises:
            VLMException: VLM 调用失败
        """
        logger.info("[VLM 兜底策略] 开始开放式诊断")

        try:
            # 调用 VLM 开放式诊断
            fallback_response = await self.vlm_client.query_structured(
                prompt=VLM_FALLBACK_DIAGNOSIS_PROMPT,
                response_model=VLMFallbackResponse,
                image_bytes=image_bytes
            )

            logger.info(f"  - VLM 推测: {fallback_response.disease_guess}")
            logger.info(f"  - 置信度: {fallback_response.confidence}")

            # 计算执行时间
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # 生成诊断 ID
            diagnosis_id = self._generate_diagnosis_id()

            # 构建兜底诊断结果
            result = DiagnosisResult(
                diagnosis_id=diagnosis_id,
                timestamp=datetime.now(),
                disease_id=None,  # 知识库外疾病，无 ID
                disease_name=fallback_response.disease_guess,
                common_name_en=None,
                pathogen=None,
                level=ConfidenceLevel.VLM_FALLBACK,
                confidence=self._parse_confidence(fallback_response.confidence),
                message="知识库无匹配疾病，使用 VLM 开放式诊断",
                suggestion="建议咨询专业植物病理学家以获得准确诊断",
                vlm_suggestion=f"{fallback_response.symptom_analysis}\n\n可能病因：\n" +
                              "\n".join(f"{i+1}. {cause}" for i, cause in enumerate(fallback_response.possible_causes)) +
                              f"\n\n处理建议：\n{fallback_response.treatment_suggestions}",
                feature_vector=feature_vector,
                scores=None,  # 兜底策略无评分
                reasoning=[
                    "知识库匹配失败（所有候选疾病 score < 0.6 或无候选疾病）",
                    "触发 VLM 兜底策略",
                    f"VLM 推测：{fallback_response.disease_guess}",
                    f"置信度：{fallback_response.confidence}"
                ],
                matched_rule="VLM_FALLBACK",
                candidates=None,
                vlm_provider="qwen-vl-plus",  # 从 VLM 客户端获取
                execution_time_ms=execution_time_ms,
                error=None
            )

            logger.info(f"[VLM 兜底策略] 完成，执行耗时：{execution_time_ms}ms")
            return result

        except VLMException as e:
            logger.error(f"VLM 兜底策略失败: {e}")
            raise
        except Exception as e:
            logger.error(f"VLM 兜底策略失败（未知错误）: {e}")
            raise DiagnosisException(f"VLM 兜底策略失败: {e}")

    def _build_healthy_result(
        self,
        start_time: datetime,
        q0_responses: Dict[str, Any]
    ) -> DiagnosisResult:
        """
        构建健康诊断结果

        Args:
            start_time: 诊断开始时间
            q0_responses: Q0 序列响应

        Returns:
            DiagnosisResult: 健康诊断结果
        """
        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        diagnosis_id = self._generate_diagnosis_id()

        return DiagnosisResult(
            diagnosis_id=diagnosis_id,
            timestamp=datetime.now(),
            disease_id=None,
            disease_name="健康植物（无明显异常）",
            level=ConfidenceLevel.CONFIRMED,
            confidence=q0_responses.get("q0_confidence", 0.95),
            message="Q0.5 判定为健康，无需进一步诊断",
            suggestion="植物健康状况良好，请继续保持正常养护",
            feature_vector=None,
            scores=None,
            reasoning=[
                "Q0.5 异常判断：healthy",
                "无明显病征，提前退出诊断流程"
            ],
            matched_rule="HEALTHY",
            vlm_provider="qwen-vl-plus",
            execution_time_ms=execution_time_ms
        )

    def _build_confirmed_result(
        self,
        feature_vector: FeatureVector,
        top_result: Dict[str, Any],
        execution_time_ms: int,
        start_time: datetime
    ) -> DiagnosisResult:
        """
        构建确诊结果

        Args:
            feature_vector: 特征向量
            top_result: 最高分候选疾病
            execution_time_ms: 执行耗时
            start_time: 开始时间

        Returns:
            DiagnosisResult: 确诊诊断结果
        """
        diagnosis_id = self._generate_diagnosis_id()
        disease = top_result["disease"]
        score = top_result["score"]
        reasoning = top_result["reasoning"]

        return DiagnosisResult(
            diagnosis_id=diagnosis_id,
            timestamp=datetime.now(),
            disease_id=disease.disease_id,
            disease_name=disease.disease_name,
            common_name_en=disease.common_name_en,
            pathogen=disease.pathogen,
            level=ConfidenceLevel.CONFIRMED,
            confidence=score.total_score,
            feature_vector=feature_vector,
            scores=score,
            reasoning=reasoning,
            matched_rule=f"CONFIRMED: major_matched={score.major_matched}/{score.major_total}, score={score.total_score:.2f}",
            candidates=None,
            vlm_provider="qwen-vl-plus",
            execution_time_ms=execution_time_ms
        )

    def _build_suspected_result(
        self,
        feature_vector: FeatureVector,
        top_result: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        execution_time_ms: int,
        start_time: datetime
    ) -> DiagnosisResult:
        """
        构建疑似结果

        Args:
            feature_vector: 特征向量
            top_result: 最高分候选疾病
            candidates: Top 2-3 候选疾病列表
            execution_time_ms: 执行耗时
            start_time: 开始时间

        Returns:
            DiagnosisResult: 疑似诊断结果
        """
        diagnosis_id = self._generate_diagnosis_id()
        disease = top_result["disease"]
        score = top_result["score"]
        reasoning = top_result["reasoning"]

        # 构建候选疾病列表
        candidates_data = []
        for candidate in candidates:
            candidates_data.append({
                "disease_id": candidate["disease"].disease_id,
                "disease_name": candidate["disease"].disease_name,
                "total_score": candidate["score"].total_score,
                "major_matched": f"{candidate['score'].major_matched}/{candidate['score'].major_total}"
            })

        return DiagnosisResult(
            diagnosis_id=diagnosis_id,
            timestamp=datetime.now(),
            disease_id=disease.disease_id,
            disease_name=disease.disease_name,
            common_name_en=disease.common_name_en,
            pathogen=disease.pathogen,
            level=ConfidenceLevel.SUSPECTED,
            confidence=score.total_score,
            message=f"疑似诊断，建议进一步观察或咨询专家",
            suggestion=f"可能是 {disease.disease_name}，但也可能是其他疾病，请参考候选列表",
            feature_vector=feature_vector,
            scores=score,
            reasoning=reasoning,
            matched_rule=f"SUSPECTED: major_matched={score.major_matched}/{score.major_total}, score={score.total_score:.2f}",
            candidates=candidates_data,
            vlm_provider="qwen-vl-plus",
            execution_time_ms=execution_time_ms
        )

    def _generate_diagnosis_id(self) -> str:
        """
        生成诊断 ID

        格式：diag_YYYYMMDD_NNN

        Returns:
            str: 诊断 ID
        """
        from datetime import datetime
        import random

        today = datetime.now().strftime("%Y%m%d")
        seq = random.randint(0, 999)
        return f"diag_{today}_{seq:03d}"

    def _parse_confidence(self, confidence_str: str) -> float:
        """
        解析置信度字符串为浮点数

        Args:
            confidence_str: 置信度字符串（high/medium/low）

        Returns:
            float: 置信度数值（0.0-1.0）
        """
        mapping = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        return mapping.get(confidence_str.lower(), 0.5)


async def main():
    """
    DiagnosisService 使用示例

    演示如何：
    1. 初始化 DiagnosisService
    2. 执行 Q0 逐级过滤序列
    3. 处理不支持的图像类型
    4. 处理 VLM 调用失败
    """
    print("=" * 80)
    print("DiagnosisService Q0 逐级过滤使用示例")
    print("=" * 80)

    # 1. 初始化服务
    print("\n[示例1] 初始化 DiagnosisService")
    service = DiagnosisService()
    print("  [OK] DiagnosisService 初始化完成")

    # 2. 准备测试图像（示例：读取玫瑰图片）
    # 注意：这里需要实际的图片文件路径
    print("\n[示例2] 准备测试图像")
    test_image_path = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "rose_black_spot.jpg"

    if test_image_path.exists():
        print(f"  [OK] 找到测试图像: {test_image_path}")

        with open(test_image_path, "rb") as f:
            image_bytes = f.read()

        # 3. 执行 Q0 序列
        print("\n[示例3] 执行 Q0 逐级过滤序列")
        try:
            q0_responses = await service.execute_q0_sequence(image_bytes)

            print("  [OK] Q0 序列执行成功")
            print(f"  - 内容类型: {q0_responses['content_type']}")
            print(f"  - 植物类别: {q0_responses['plant_category']}")
            print(f"  - 花卉种属: {q0_responses['flower_genus']}")
            print(f"  - 器官类型: {q0_responses['organ']}")
            print(f"  - 完整性: {q0_responses['completeness']}")
            print(f"  - 异常状态: {q0_responses['has_abnormality']}")
            print(f"  - 平均置信度: {q0_responses['q0_confidence']:.2f}")
            print(f"  - VLM Provider: {q0_responses['vlm_provider']}")

        except UnsupportedImageException as e:
            print(f"  [ERROR] 图像不支持: {e}")
        except VLMException as e:
            print(f"  [ERROR] VLM 调用失败: {e}")
        except Exception as e:
            print(f"  [ERROR] 未知错误: {e}")

    else:
        print(f"  [SKIP] 测试图像不存在: {test_image_path}")
        print("  提示: 请将测试图像放到 backend/tests/fixtures/ 目录下")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
