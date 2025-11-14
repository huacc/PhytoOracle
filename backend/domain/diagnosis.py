"""
诊断领域模型

功能：
- 定义诊断聚合根相关的领域模型
- 包含特征向量、诊断结果、诊断分数等核心模型
- 使用Pydantic V2进行数据验证

模型清单：
- ContentType: 图片内容类型枚举
- PlantCategory: 植物类别枚举
- FlowerGenus: 花卉种属枚举
- OrganType: 器官类型枚举
- Completeness: 完整性枚举
- AbnormalityStatus: 异常状态枚举
- ConfidenceLevel: 置信度级别枚举
- FeatureVector: 特征向量模型
- DiagnosisScore: 诊断分数模型
- DiagnosisResult: 诊断结果模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QADetail(BaseModel):
    """
    VLM问答对详情模型（P3.9新增）

    用于存储诊断过程中VLM的问答对，支持前端界面1展示完整推理过程

    字段说明：
    - question_id: 问题ID（如 "Q0.0", "Q0.1", "Q1", "Q2" 等）
    - question: 问题文本
    - answer: VLM的回答文本
    - image_url: 标注图URL（可选，如果VLM返回了标注图）
    """
    question_id: str = Field(
        ...,
        pattern=r"^Q\d+(\.\d+)?$",
        description="问题ID（如 Q0.0, Q1, Q2 等）"
    )
    question: str = Field(..., min_length=1, description="问题文本")
    answer: str = Field(..., min_length=1, description="VLM的回答文本")
    image_url: Optional[str] = Field(None, description="标注图URL（可选）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "Q0.0",
                "question": "这张图片的内容类型是什么？",
                "answer": "plant（植物）",
                "image_url": None
            }
        }
    )


class ContentType(str, Enum):
    """
    图片内容类型枚举

    用于Q0.0问题：判断图片内容类型

    枚举值：
    - PLANT: 植物图片
    - ANIMAL: 动物图片
    - PERSON: 人物图片
    - OBJECT: 物品图片
    - LANDSCAPE: 风景图片
    - OTHER: 其他类型
    """
    PLANT = "plant"
    ANIMAL = "animal"
    PERSON = "person"
    OBJECT = "object"
    LANDSCAPE = "landscape"
    OTHER = "other"


class PlantCategory(str, Enum):
    """
    植物类别枚举

    用于Q0.1问题：判断植物类别

    枚举值：
    - FLOWER: 花卉
    - VEGETABLE: 蔬菜
    - TREE: 树木
    - CROP: 农作物
    - GRASS: 草本植物
    - OTHER: 其他植物
    """
    FLOWER = "flower"
    VEGETABLE = "vegetable"
    TREE = "tree"
    CROP = "crop"
    GRASS = "grass"
    OTHER = "other"


class FlowerGenus(str, Enum):
    """
    花卉种属枚举（Genus级别）

    用于Q0.2问题：识别花卉种属，用于候选疾病剪枝

    枚举值：
    - ROSA: 蔷薇属（玫瑰、月季等）
    - PRUNUS: 李属（樱花、梅花等）
    - TULIPA: 郁金香属
    - DIANTHUS: 石竹属（康乃馨等）
    - PAEONIA: 芍药属（牡丹、芍药等）
    - OTHER: 其他花卉
    """
    ROSA = "Rosa"
    PRUNUS = "Prunus"
    TULIPA = "Tulipa"
    DIANTHUS = "Dianthus"
    PAEONIA = "Paeonia"
    OTHER = "Other"


class OrganType(str, Enum):
    """
    器官类型枚举

    用于Q0.3问题：识别花卉器官类型

    枚举值：
    - FLOWER: 花朵（包括花瓣、花蕊）
    - LEAF: 叶子

    注意：根据需求文档v1.3，仅支持花朵和叶子，移除茎和根
    """
    FLOWER = "flower"
    LEAF = "leaf"


class Completeness(str, Enum):
    """
    完整性枚举

    用于Q0.4问题：判断器官的完整性

    枚举值：
    - COMPLETE: 完整的器官（可见完整轮廓）
    - PARTIAL: 部分器官（被遮挡或残缺）
    - CLOSE_UP: 特写镜头（局部放大）
    """
    COMPLETE = "complete"
    PARTIAL = "partial"
    CLOSE_UP = "close_up"


class AbnormalityStatus(str, Enum):
    """
    异常状态枚举

    用于Q0.5问题：判断是否存在异常

    枚举值：
    - HEALTHY: 健康的（无明显异常）
    - ABNORMAL: 有异常（存在病征）
    """
    HEALTHY = "healthy"
    ABNORMAL = "abnormal"


class ConfidenceLevel(str, Enum):
    """
    置信度级别枚举（扩展版，包含兜底状态）

    用于表示诊断结果的置信程度

    枚举值：
    - CONFIRMED: 确诊（score ≥ 0.85 且 major_matched ≥ 2）
    - SUSPECTED: 疑似（0.60 ≤ score < 0.85 且 major_matched ≥ 1）
    - UNLIKELY: 不太可能（score < 0.60 或 major_matched = 0）
    - UNKNOWN: 知识库无数据（该花卉未收录）
    - VLM_FALLBACK: VLM兜底诊断（知识库外疾病）
    - SYSTEM_ERROR: 系统错误（VLM完全失败）

    注意：遵循需求文档v1.3的三层渐进诊断逻辑
    """
    CONFIRMED = "confirmed"          # 确诊
    SUSPECTED = "suspected"          # 疑似
    UNLIKELY = "unlikely"            # 不太可能
    UNKNOWN = "unknown"              # 知识库无数据
    VLM_FALLBACK = "vlm_fallback"   # VLM兜底诊断
    SYSTEM_ERROR = "system_error"    # 系统错误


class FeatureVector(BaseModel):
    """
    特征向量模型

    存储Q0-Q6问诊序列的所有回答，用于疾病匹配

    字段说明：
    - Q0特征（过滤阶段）：
        - content_type: 内容类型（Q0.0）
        - plant_category: 植物类别（Q0.1）
        - flower_genus: 花卉种属（Q0.2）
        - organ: 器官类型（Q0.3）
        - completeness: 完整性（Q0.4）
        - has_abnormality: 异常状态（Q0.5）

    - Q1-Q6特征（动态特征提取）：
        - symptom_type: 症状类型（斑点、溃疡、霉层等）
        - color_center: 症状中心颜色
        - color_border: 症状边缘颜色
        - location: 症状位置
        - size: 症状尺寸
        - distribution: 分布模式
        - additional_features: 其他特征（动态扩展）
    """
    model_config = ConfigDict(use_enum_values=True)

    # Q0特征（必填）
    content_type: ContentType = Field(..., description="图片内容类型（Q0.0）")
    plant_category: PlantCategory = Field(..., description="植物类别（Q0.1）")
    flower_genus: FlowerGenus = Field(..., description="花卉种属（Q0.2）")
    organ: OrganType = Field(..., description="器官类型（Q0.3）")
    completeness: Completeness = Field(..., description="完整性（Q0.4）")
    has_abnormality: AbnormalityStatus = Field(..., description="异常状态（Q0.5）")

    # Q1-Q6特征（可选，根据实际情况动态填充）
    symptom_type: Optional[str] = Field(None, description="症状类型（斑点、溃疡、霉层等）")
    color_center: Optional[str] = Field(None, description="症状中心颜色")
    color_border: Optional[str] = Field(None, description="症状边缘颜色")
    location: Optional[str] = Field(None, description="症状位置（叶尖、叶缘、叶面等）")
    size: Optional[str] = Field(None, description="症状尺寸（小、中、大）")
    distribution: Optional[str] = Field(None, description="分布模式（散发、聚集、环状等）")
    additional_features: Dict[str, Any] = Field(
        default_factory=dict,
        description="其他特征（动态扩展字段）"
    )


class DiagnosisScore(BaseModel):
    """
    诊断分数模型（扩展版，包含医学诊断逻辑）

    存储疾病匹配的评分详情，遵循医学诊断逻辑（主要特征+次要特征）

    字段说明：
    - total_score: 总分（0.0-1.0）
    - major_features_score: 主要特征得分（0.0-1.0）
    - minor_features_score: 次要特征得分（0.0-1.0）
    - optional_features_score: 可选特征得分（0.0-1.0）
    - major_matched: 主要特征匹配数量（通常需要≥2/2才能确诊）
    - major_total: 主要特征总数（通常为2）

    诊断等级判定规则（需求文档v1.3）：
    - confirmed: total_score ≥ 0.85 且 major_matched ≥ 2/2
    - suspected: 0.60 ≤ total_score < 0.85 且 major_matched ≥ 1/2
    - unlikely: total_score < 0.60 或 major_matched = 0
    """
    model_config = ConfigDict(frozen=True)  # 不可变对象，确保评分不被篡改

    total_score: float = Field(..., ge=0, le=1, description="总分（0.0-1.0）")
    major_features_score: float = Field(..., ge=0, le=1, description="主要特征得分（0.0-1.0）")
    minor_features_score: float = Field(..., ge=0, le=1, description="次要特征得分（0.0-1.0）")
    optional_features_score: float = Field(..., ge=0, le=1, description="可选特征得分（0.0-1.0）")

    # 医学诊断逻辑新增字段
    major_matched: int = Field(..., ge=0, description="主要特征匹配数量")
    major_total: int = Field(..., ge=0, description="主要特征总数（通常为2）")

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """
        诊断等级判定（严格遵循医学诊断逻辑）

        Returns:
            ConfidenceLevel: 置信度级别

        规则（需求文档v1.3定义）：
        - confirmed: total_score ≥ 0.85 且 major_matched ≥ 2/2
        - suspected: 0.60 ≤ total_score < 0.85 且 major_matched ≥ 1/2
        - unlikely: total_score < 0.60 或 major_matched = 0
        """
        if self.total_score >= 0.85 and self.major_matched >= 2:
            return ConfidenceLevel.CONFIRMED
        elif self.total_score >= 0.60 and self.major_matched >= 1:
            return ConfidenceLevel.SUSPECTED
        return ConfidenceLevel.UNLIKELY


class DiagnosisResult(BaseModel):
    """
    诊断结果模型（扩展版，支持兜底逻辑）

    存储完整的诊断结果，包括疾病信息、特征向量、评分详情、推理过程等

    字段说明：
    - diagnosis_id: 诊断唯一标识符（格式：diag_YYYYMMDD_NNN）
    - timestamp: 诊断时间戳
    - disease_id: 疾病ID（知识库中的疾病标识）
    - disease_name: 疾病名称
    - common_name_en: 英文常用名
    - pathogen: 病原体
    - level: 置信度级别（confirmed/suspected/unlikely等）
    - confidence: 置信度数值（0.0-1.0）
    - message: 兜底场景的说明信息
    - suggestion: 给用户的建议
    - vlm_suggestion: VLM开放式诊断结果
    - feature_vector: 特征向量（兜底场景可能为空）
    - scores: 评分详情（兜底场景可能为空）
    - reasoning: 推理过程（列表形式）
    - matched_rule: 匹配的诊断规则
    - candidates: 候选疾病列表（疑似诊断时）
    - qa_details: VLM问答对详情列表（P3.9新增）
    - vlm_provider: VLM提供商（gpt-4o/claude-3.5-sonnet等）
    - execution_time_ms: 执行耗时（毫秒）
    - error: 错误信息（如果有）
    """
    diagnosis_id: str = Field(
        ...,
        pattern=r"^diag_\d{8}_\d{3}$",
        description="诊断唯一标识符（格式：diag_YYYYMMDD_NNN）"
    )
    timestamp: datetime = Field(..., description="诊断时间戳")

    # 诊断结果
    disease_id: Optional[str] = Field(None, description="疾病ID（知识库中的疾病标识）")
    disease_name: str = Field(..., description="疾病名称")
    common_name_en: Optional[str] = Field(None, description="英文常用名")
    pathogen: Optional[str] = Field(None, description="病原体")
    level: ConfidenceLevel = Field(..., description="置信度级别")
    confidence: float = Field(..., ge=0, le=1, description="置信度数值（0.0-1.0）")

    # 兜底逻辑新增字段
    message: Optional[str] = Field(None, description="兜底场景的说明信息")
    suggestion: Optional[str] = Field(None, description="给用户的建议")
    vlm_suggestion: Optional[str] = Field(None, description="VLM开放式诊断结果")

    # 特征向量（兜底场景可能为空）
    feature_vector: Optional[FeatureVector] = Field(None, description="特征向量")

    # 评分详情（兜底场景可能为空）
    scores: Optional[DiagnosisScore] = Field(None, description="评分详情")

    # 推理过程
    reasoning: List[str] = Field(
        default_factory=list,
        description="推理过程（列表形式）"
    )
    matched_rule: Optional[str] = Field(None, description="匹配的诊断规则")

    # 候选疾病（疑似诊断时）
    candidates: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="候选疾病列表（疑似诊断时，Top 2-3）"
    )

    # P3.9新增：VLM问答对详情
    qa_details: List[QADetail] = Field(
        default_factory=list,
        description="VLM问答对详情列表（Q0-Q6问答对，P3.9新增）"
    )

    # 执行信息
    vlm_provider: str = Field(..., description="VLM提供商（gpt-4o/claude-3.5-sonnet等）")
    execution_time_ms: int = Field(..., description="执行耗时（毫秒）")

    # 错误信息
    error: Optional[str] = Field(None, description="错误信息（如果有）")


def main():
    """
    诊断领域模型使用示例

    演示如何：
    1. 使用枚举类型
    2. 创建特征向量
    3. 创建诊断分数并判定置信度级别
    4. 创建完整的诊断结果
    """
    from datetime import datetime

    print("=" * 80)
    print("诊断领域模型使用示例")
    print("=" * 80)

    # 1. 使用枚举类型
    print("\n[示例1] 使用枚举类型")
    print(f"  - ContentType.PLANT: {ContentType.PLANT}")
    print(f"  - PlantCategory.FLOWER: {PlantCategory.FLOWER}")
    print(f"  - FlowerGenus.ROSA: {FlowerGenus.ROSA}")
    print(f"  - OrganType.LEAF: {OrganType.LEAF}")
    print(f"  - Completeness.COMPLETE: {Completeness.COMPLETE}")
    print(f"  - AbnormalityStatus.ABNORMAL: {AbnormalityStatus.ABNORMAL}")

    # 2. 创建特征向量
    print("\n[示例2] 创建特征向量")
    feature_vector = FeatureVector(
        # Q0特征（必填）
        content_type=ContentType.PLANT,
        plant_category=PlantCategory.FLOWER,
        flower_genus=FlowerGenus.ROSA,
        organ=OrganType.LEAF,
        completeness=Completeness.COMPLETE,
        has_abnormality=AbnormalityStatus.ABNORMAL,
        # Q1-Q6特征（可选）
        symptom_type="necrosis_spot",
        color_center="black",
        color_border="yellow",
        location="lamina",
        size="medium",
        distribution="scattered",
        additional_features={
            "leaf_curling": "no",
            "margin_type": "irregular"
        }
    )

    print(f"  [OK] 成功创建特征向量")
    print(f"  - 内容类型: {feature_vector.content_type}")
    print(f"  - 植物类别: {feature_vector.plant_category}")
    print(f"  - 花卉种属: {feature_vector.flower_genus}")
    print(f"  - 器官类型: {feature_vector.organ}")
    print(f"  - 症状类型: {feature_vector.symptom_type}")
    print(f"  - 中心颜色: {feature_vector.color_center}")
    print(f"  - 边缘颜色: {feature_vector.color_border}")
    print(f"  - 附加特征: {feature_vector.additional_features}")

    # 3. 创建诊断分数（确诊级别）
    print("\n[示例3] 创建诊断分数（确诊级别）")
    score_confirmed = DiagnosisScore(
        total_score=0.92,
        major_features_score=0.95,
        minor_features_score=0.85,
        optional_features_score=0.60,
        major_matched=2,
        major_total=2
    )

    print(f"  [OK] 成功创建诊断分数")
    print(f"  - 总分: {score_confirmed.total_score}")
    print(f"  - 主要特征得分: {score_confirmed.major_features_score}")
    print(f"  - 主要特征匹配: {score_confirmed.major_matched}/{score_confirmed.major_total}")
    print(f"  - 置信度级别: {score_confirmed.confidence_level}")
    print(f"  - 判定: {'确诊' if score_confirmed.confidence_level == ConfidenceLevel.CONFIRMED else '非确诊'}")

    # 4. 创建诊断分数（疑似级别）
    print("\n[示例4] 创建诊断分数（疑似级别）")
    score_suspected = DiagnosisScore(
        total_score=0.72,
        major_features_score=0.80,
        minor_features_score=0.60,
        optional_features_score=0.50,
        major_matched=1,
        major_total=2
    )

    print(f"  [OK] 成功创建诊断分数")
    print(f"  - 总分: {score_suspected.total_score}")
    print(f"  - 主要特征匹配: {score_suspected.major_matched}/{score_suspected.major_total}")
    print(f"  - 置信度级别: {score_suspected.confidence_level}")
    print(f"  - 判定: {'疑似' if score_suspected.confidence_level == ConfidenceLevel.SUSPECTED else '非疑似'}")

    # 5. 创建诊断分数（不太可能）
    print("\n[示例5] 创建诊断分数（不太可能）")
    score_unlikely = DiagnosisScore(
        total_score=0.45,
        major_features_score=0.50,
        minor_features_score=0.40,
        optional_features_score=0.30,
        major_matched=0,
        major_total=2
    )

    print(f"  [OK] 成功创建诊断分数")
    print(f"  - 总分: {score_unlikely.total_score}")
    print(f"  - 主要特征匹配: {score_unlikely.major_matched}/{score_unlikely.major_total}")
    print(f"  - 置信度级别: {score_unlikely.confidence_level}")
    print(f"  - 判定: {'不太可能' if score_unlikely.confidence_level == ConfidenceLevel.UNLIKELY else '其他'}")

    # 6. 创建完整的诊断结果（确诊）
    print("\n[示例6] 创建完整的诊断结果（确诊）")
    diagnosis_result = DiagnosisResult(
        diagnosis_id="diag_20251112_001",
        timestamp=datetime.now(),
        disease_id="rose_black_spot",
        disease_name="玫瑰黑斑病",
        common_name_en="Rose Black Spot",
        pathogen="Diplocarpon rosae（真菌）",
        level=ConfidenceLevel.CONFIRMED,
        confidence=0.92,
        feature_vector=feature_vector,
        scores=score_confirmed,
        reasoning=[
            "Q0.2识别花卉种属为Rosa（蔷薇属）",
            "Q0.3识别器官为叶子（leaf）",
            "Q0.5判定存在异常",
            "Q1识别症状类型为坏死斑点（necrosis_spot）",
            "Q2识别边缘颜色为黄色（yellow），匹配黄色晕圈特征",
            "主要特征匹配2/2，总分0.92，达到确诊标准"
        ],
        matched_rule="R1: major_features >= 2/2",
        vlm_provider="gpt-4o",
        execution_time_ms=1850
    )

    print(f"  [OK] 成功创建诊断结果")
    print(f"  - 诊断ID: {diagnosis_result.diagnosis_id}")
    print(f"  - 疾病名称: {diagnosis_result.disease_name}")
    print(f"  - 置信度级别: {diagnosis_result.level}")
    print(f"  - 置信度数值: {diagnosis_result.confidence}")
    print(f"  - VLM提供商: {diagnosis_result.vlm_provider}")
    print(f"  - 执行耗时: {diagnosis_result.execution_time_ms}ms")
    print(f"  - 推理步骤数: {len(diagnosis_result.reasoning)}")

    # 7. 创建兜底诊断结果（VLM兜底）
    print("\n[示例7] 创建兜底诊断结果（VLM兜底）")
    fallback_result = DiagnosisResult(
        diagnosis_id="diag_20251112_002",
        timestamp=datetime.now(),
        disease_id=None,
        disease_name="未知疾病（VLM兜底诊断）",
        level=ConfidenceLevel.VLM_FALLBACK,
        confidence=0.75,
        message="该花卉不在知识库范围内，使用VLM进行开放式诊断",
        suggestion="建议咨询专业植物病理学家",
        vlm_suggestion="根据症状判断，可能是细菌性叶斑病，建议使用铜制剂喷雾防治",
        reasoning=[
            "Q0.2识别花卉种属为Hibiscus（不在知识库中）",
            "触发VLM兜底诊断流程"
        ],
        vlm_provider="gpt-4o",
        execution_time_ms=2100
    )

    print(f"  [OK] 成功创建兜底诊断结果")
    print(f"  - 诊断ID: {fallback_result.diagnosis_id}")
    print(f"  - 疾病名称: {fallback_result.disease_name}")
    print(f"  - 置信度级别: {fallback_result.level}")
    print(f"  - 消息: {fallback_result.message}")
    print(f"  - VLM建议: {fallback_result.vlm_suggestion}")
    print(f"  - 执行耗时: {fallback_result.execution_time_ms}ms")

    # 8. 验证不可变性（DiagnosisScore是frozen对象）
    print("\n[示例8] 验证不可变性（DiagnosisScore是frozen对象）")
    try:
        score_confirmed.total_score = 0.99  # 尝试修改
        print("  [FAIL] 不可变性验证失败：分数被成功修改")
    except Exception as e:
        print(f"  [OK] 不可变性验证通过：{type(e).__name__}")
        print(f"    DiagnosisScore对象不可修改，确保评分不被篡改")

    print("\n" + "=" * 80)
    print("示例执行完毕")
    print("=" * 80)


if __name__ == "__main__":
    main()
