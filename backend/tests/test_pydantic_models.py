"""
Pydantic模型单元测试

功能：
- 测试所有Pydantic模型的创建和验证
- 验证必填字段、可选字段、数据类型等
- 确保模型符合P1.3验收标准

测试清单：
- test_feature_vector: 测试特征向量模型
- test_diagnosis_score: 测试诊断分数模型
- test_diagnosis_result: 测试诊断结果模型
- test_disease_ontology: 测试疾病本体模型
- test_plant_ontology: 测试植物本体模型
- test_feature_ontology: 测试特征本体模型
- test_value_objects: 测试值对象
- test_api_schemas: 测试API Schemas
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from domain import (
    ContentType,
    PlantCategory,
    FlowerGenus,
    OrganType,
    Completeness,
    AbnormalityStatus,
    ConfidenceLevel,
    FeatureVector,
    DiagnosisScore,
    DiagnosisResult,
    DiseaseOntology,
    PlantOntology,
    FeatureOntology,
    ImageHash,
    DiagnosisId,
)
from apps.api.schemas import (
    DiagnosedDiseaseSchema,
    DiagnosisResponseSchema,
    DiseaseSchema,
    LoginRequest,
    LoginResponse,
    TokenData,
)


def test_feature_vector():
    """测试特征向量模型"""
    feature_vector = FeatureVector(
        content_type=ContentType.PLANT,
        plant_category=PlantCategory.FLOWER,
        flower_genus=FlowerGenus.ROSA,
        organ=OrganType.LEAF,
        completeness=Completeness.COMPLETE,
        has_abnormality=AbnormalityStatus.ABNORMAL,
        symptom_type="spot",
        color_center="black",
        color_border="yellow",
        location="leaf_surface",
        size="medium",
        distribution="scattered",
        additional_features={"notes": "test"}
    )

    assert feature_vector.content_type == "plant"
    assert feature_vector.plant_category == "flower"
    assert feature_vector.flower_genus == "Rosa"
    assert feature_vector.organ == "leaf"
    assert feature_vector.completeness == "complete"
    assert feature_vector.has_abnormality == "abnormal"
    assert feature_vector.symptom_type == "spot"
    assert feature_vector.color_center == "black"
    print("[PASS] FeatureVector模型测试通过")


def test_diagnosis_score():
    """测试诊断分数模型"""
    # 测试确诊级别（total_score ≥ 0.85 且 major_matched ≥ 2）
    score_confirmed = DiagnosisScore(
        total_score=0.92,
        major_features_score=0.95,
        minor_features_score=0.85,
        optional_features_score=0.75,
        major_matched=2,
        major_total=2
    )
    assert score_confirmed.confidence_level == ConfidenceLevel.CONFIRMED
    print("[PASS] DiagnosisScore确诊级别测试通过")

    # 测试疑似级别（0.60 ≤ total_score < 0.85 且 major_matched ≥ 1）
    score_suspected = DiagnosisScore(
        total_score=0.75,
        major_features_score=0.80,
        minor_features_score=0.70,
        optional_features_score=0.65,
        major_matched=1,
        major_total=2
    )
    assert score_suspected.confidence_level == ConfidenceLevel.SUSPECTED
    print("[PASS] DiagnosisScore疑似级别测试通过")

    # 测试不太可能级别（total_score < 0.60 或 major_matched = 0）
    score_unlikely = DiagnosisScore(
        total_score=0.45,
        major_features_score=0.50,
        minor_features_score=0.40,
        optional_features_score=0.35,
        major_matched=0,
        major_total=2
    )
    assert score_unlikely.confidence_level == ConfidenceLevel.UNLIKELY
    print("[PASS] DiagnosisScore不太可能级别测试通过")


def test_diagnosis_result():
    """测试诊断结果模型"""
    diagnosis_result = DiagnosisResult(
        diagnosis_id="diag_20251112_001",
        timestamp=datetime.now(),
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Black Spot",
        pathogen="Diplocarpon rosae",
        level=ConfidenceLevel.CONFIRMED,
        confidence=0.92,
        vlm_provider="gpt-4o",
        execution_time_ms=2340
    )

    assert diagnosis_result.diagnosis_id == "diag_20251112_001"
    assert diagnosis_result.disease_name == "玫瑰黑斑病"
    assert diagnosis_result.level == ConfidenceLevel.CONFIRMED
    assert diagnosis_result.confidence == 0.92
    assert diagnosis_result.vlm_provider == "gpt-4o"
    print("[PASS] DiagnosisResult模型测试通过")


def test_disease_ontology():
    """测试疾病本体模型"""
    disease = DiseaseOntology(
        version="4.1",
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Black Spot",
        pathogen="Diplocarpon rosae (真菌)",
        feature_vector={
            "symptom_type": "spot",
            "color_center": "black"
        },
        feature_importance={
            "major_features": {
                "features": [
                    {"dimension": "color_center", "expected_values": ["black", "dark_brown"], "weight": 0.5}
                ]
            }
        },
        diagnosis_rules={
            "confirmed_rules": [],
            "suspected_rules": []
        },
        host_plants=["Rosa"],
        typical_symptoms=["叶片出现黑色圆形斑点"]
    )

    assert disease.version == "4.1"
    assert disease.disease_id == "rosa_blackspot"
    assert disease.disease_name == "玫瑰黑斑病"
    assert len(disease.get_major_features()) == 1
    assert disease.get_expected_values("color_center") == ["black", "dark_brown"]
    print("[PASS] DiseaseOntology模型测试通过")


def test_plant_ontology():
    """测试植物本体模型"""
    plant = PlantOntology(
        family="Rosaceae",
        genus="Rosa",
        species=["Rosa chinensis", "Rosa rugosa"],
        common_names={"zh": "玫瑰", "en": "Rose"},
        organ_anatomy={
            "leaf": ["pinnate", "serrated_margin"],
            "flower": ["5_petals"]
        },
        visual_cues={"leaf_shape": "羽状复叶"},
        susceptible_diseases=["rosa_blackspot", "rosa_powdery_mildew"]
    )

    assert plant.kingdom == "Plantae"
    assert plant.family == "Rosaceae"
    assert plant.genus == "Rosa"
    assert plant.common_names["zh"] == "玫瑰"
    assert len(plant.susceptible_diseases) == 2
    print("[PASS] PlantOntology模型测试通过")


def test_feature_ontology():
    """测试特征本体模型"""
    feature = FeatureOntology(
        version="1.0",
        dimensions={
            "color_center": {
                "type": "enum",
                "values": ["black", "brown", "yellow"],
                "description": "症状中心颜色"
            }
        },
        fuzzy_matching={
            "color_aliases": {
                "deep_black": ["black", "dark_brown"]
            }
        },
        symptom_types=[
            {"value": "spot", "label": "斑点"}
        ],
        colors={"black": ["deep_black", "dark_brown"]},
        sizes=["small", "medium", "large"],
        distribution_patterns=["scattered", "clustered"]
    )

    assert feature.version == "1.0"
    assert "color_center" in feature.dimensions
    assert len(feature.symptom_types) == 1
    print("[PASS] FeatureOntology模型测试通过")


def test_value_objects():
    """测试值对象"""
    # 测试ImageHash
    image_hash = ImageHash.from_bytes(b"test_image_data")
    assert len(image_hash.md5) == 32
    assert len(image_hash.sha256) == 64
    print("[PASS] ImageHash值对象测试通过")

    # 测试DiagnosisId（有效格式）
    diagnosis_id = DiagnosisId(value="diag_20251112_001")
    assert diagnosis_id.value == "diag_20251112_001"
    print("[PASS] DiagnosisId值对象测试通过")

    # 测试DiagnosisId（自动生成）
    generated_id = DiagnosisId.generate()
    assert generated_id.value.startswith("diag_")
    print("[PASS] DiagnosisId自动生成测试通过")

    # 测试DiagnosisId（无效格式）
    try:
        invalid_id = DiagnosisId(value="invalid_id")
        assert False, "应该抛出ValueError异常"
    except ValueError as e:
        assert "Invalid diagnosis ID format" in str(e)
        print("[PASS] DiagnosisId格式验证测试通过")


def test_api_schemas():
    """测试API Schemas"""
    # 测试DiagnosedDiseaseSchema
    disease = DiagnosedDiseaseSchema(
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Black Spot",
        pathogen="Diplocarpon rosae",
        confidence=0.92
    )
    assert disease.disease_id == "rosa_blackspot"
    assert disease.confidence == 0.92
    print("[PASS] DiagnosedDiseaseSchema测试通过")

    # 测试DiagnosisResponseSchema
    response = DiagnosisResponseSchema(
        diagnosis_id="diag_20251112_001",
        timestamp=datetime.now(),
        status="confirmed",
        confirmed_disease=disease,
        feature_vector={},
        vlm_provider="gpt-4o",
        execution_time_ms=2340
    )
    assert response.diagnosis_id == "diag_20251112_001"
    assert response.status == "confirmed"
    print("[PASS] DiagnosisResponseSchema测试通过")

    # 测试DiseaseSchema
    disease_schema = DiseaseSchema(
        disease_id="rosa_blackspot",
        disease_name="玫瑰黑斑病",
        common_name_en="Black Spot",
        pathogen="Diplocarpon rosae",
        pathogen_type="fungal",
        affected_plants=["Rosa"],
        typical_symptoms=["叶片出现黑色圆形斑点"]
    )
    assert disease_schema.disease_id == "rosa_blackspot"
    assert disease_schema.pathogen_type == "fungal"
    print("[PASS] DiseaseSchema测试通过")

    # 测试LoginRequest
    login_req = LoginRequest(
        username="admin",
        password="admin123"
    )
    assert login_req.username == "admin"
    print("[PASS] LoginRequest测试通过")

    # 测试LoginResponse
    login_res = LoginResponse(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        token_type="Bearer",
        expires_in=604800,
        username="admin"
    )
    assert login_res.token_type == "Bearer"
    assert login_res.expires_in == 604800
    print("[PASS] LoginResponse测试通过")

    # 测试TokenData
    token_data = TokenData(
        username="admin",
        user_id="550e8400-e29b-41d4-a716-446655440000"
    )
    assert token_data.username == "admin"
    print("[PASS] TokenData测试通过")


if __name__ == "__main__":
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("P1.3 Pydantic模型单元测试")
    print("=" * 60 + "\n")

    test_feature_vector()
    test_diagnosis_score()
    test_diagnosis_result()
    test_disease_ontology()
    test_plant_ontology()
    test_feature_ontology()
    test_value_objects()
    test_api_schemas()

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有Pydantic模型测试通过！")
    print("=" * 60 + "\n")
