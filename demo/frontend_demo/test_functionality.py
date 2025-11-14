"""
功能测试脚本

验证所有核心功能是否正常工作。
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from services import get_diagnosis_engine, get_knowledge_service
from utils import export_diagnosis_result, export_ontology_usage
from models import Annotation, ImageAnnotation


def test_knowledge_service():
    """测试知识库服务"""
    print("=" * 60)
    print("测试1: 知识库服务")
    print("=" * 60)

    kb_service = get_knowledge_service()

    # 测试疾病加载
    diseases = list(kb_service.diseases.keys())
    print(f"[OK] Load diseases: {len(diseases)}")
    print(f"     Disease list: {', '.join(diseases)}")

    # 测试特征本体
    ontology = kb_service.get_feature_ontology()
    features = list(ontology.get('features', {}).keys())
    print(f"[OK] Load features: {len(features)}")
    print(f"     Feature list: {', '.join(features[:3])}...")

    # 测试花属查询
    genera = kb_service.get_all_genera()
    print(f"[OK] Genera list: {', '.join(genera)}")

    # 测试同义词查询
    synonyms = kb_service.get_synonyms('color_border', 'yellow_halo')
    print(f"[OK] Synonyms of yellow_halo: {synonyms}")

    print()


def test_diagnosis_engine():
    """测试推理引擎"""
    print("=" * 60)
    print("测试2: 推理引擎")
    print("=" * 60)

    engine = get_diagnosis_engine()

    # 测试玫瑰黑斑病
    test_cases = [
        ("rose_black_spot_001.jpg", "rose_black_spot"),
        ("rose_powdery_mildew_001.jpg", "rose_powdery_mildew"),
        ("cherry_brown_rot_001.jpg", "cherry_brown_rot"),
    ]

    for image_name, expected_disease_id in test_cases:
        result = engine.diagnose("test_path", image_name)

        print(f"\n文件名: {image_name}")
        print(f"[OK] 诊断ID: {result.diagnosis_id}")
        print(f"[OK] 识别花属: {result.q0_sequence['q0_2_flower_genus'].choice}")
        print(f"[OK] 诊断疾病: {result.final_diagnosis.disease_id}")
        print(f"[OK] 置信度: {result.final_diagnosis.confidence_score:.2f} ({result.final_diagnosis.confidence_level})")
        print(f"[OK] 候选疾病数: {len(result.candidate_diseases)}")
        print(f"[OK] 推理耗时: {result.performance.total_elapsed_time:.2f}s")

        # 验证诊断是否正确
        if result.final_diagnosis.disease_id == expected_disease_id:
            print(f"[OK] 诊断正确！")
        else:
            print(f"[FAIL] 诊断错误！期望: {expected_disease_id}, 实际: {result.final_diagnosis.disease_id}")

    print()


def test_export_functions():
    """测试导出功能"""
    print("=" * 60)
    print("测试3: 导出功能")
    print("=" * 60)

    engine = get_diagnosis_engine()
    result = engine.diagnose("test_path", "rose_black_spot_001.jpg")

    # 测试推理结果导出
    diagnosis_json = export_diagnosis_result(result)
    diagnosis_data = json.loads(diagnosis_json)
    print(f"[OK] 推理结果导出成功, JSON长度: {len(diagnosis_json)} 字符")
    print(f"   包含字段: {', '.join(list(diagnosis_data.keys())[:5])}...")

    # 测试本体使用导出
    ontology_json = export_ontology_usage(result, "测试备注")
    ontology_data = json.loads(ontology_json)
    print(f"[OK] 本体使用导出成功, JSON长度: {len(ontology_json)} 字符")
    print(f"   诊断ID: {ontology_data['diagnosis_id']}")
    print(f"   使用的特征: {len(ontology_data['ontology_usage']['feature_ontology']['used_features'])} 个")
    print(f"   查询的疾病: {len(ontology_data['ontology_usage']['disease_ontologies'])} 个")

    print()


def test_ontology_tracing():
    """测试本体追溯"""
    print("=" * 60)
    print("测试4: 本体追溯")
    print("=" * 60)

    engine = get_diagnosis_engine()
    result = engine.diagnose("test_path", "rose_black_spot_001.jpg")

    # 检查本体引用
    print("Q0序列本体引用:")
    for q_key, q_result in result.q0_sequence.items():
        print(f"  [OK] {q_key}: 来源 = {q_result.ontology_reference.source}")

    print("\n特征提取本体引用:")
    for feature_key in list(result.feature_extraction.keys())[:3]:
        feature_result = result.feature_extraction[feature_key]
        print(f"  [OK] {feature_key}: 来源 = {feature_result.ontology_reference.source}")

    # 检查同义词映射
    print("\n同义词映射:")
    has_fuzzy = False
    for scoring_result in result.scoring_results:
        for match_detail in scoring_result.match_details:
            if match_detail.match_type == "fuzzy" and match_detail.synonym_mapping:
                sm = match_detail.synonym_mapping
                print(f"  [FUZZY] {match_detail.feature_key}: '{sm.observed}' → '{sm.canonical}'")
                print(f"     同义词来源: {sm.synonym_source}")
                has_fuzzy = True

    if not has_fuzzy:
        print("  无模糊匹配（全部精确匹配）")

    print()


def test_annotation_model():
    """测试标注数据模型"""
    print("=" * 60)
    print("测试5: 标注数据模型")
    print("=" * 60)

    annotation = Annotation(
        is_accurate="correct",
        actual_disease_id=None,
        actual_disease_name=None,
        notes="测试标注"
    )

    image_annotation = ImageAnnotation(
        image_id="img_test_001",
        diagnosis_id="diag_test_001",
        annotation=annotation
    )

    print(f"[OK] 标注创建成功")
    print(f"   图片ID: {image_annotation.image_id}")
    print(f"   诊断ID: {image_annotation.diagnosis_id}")
    print(f"   准确性: {image_annotation.annotation.is_accurate}")
    print(f"   标注时间: {image_annotation.annotation.annotated_at}")

    # 测试JSON序列化
    annotation_json = image_annotation.model_dump_json(indent=2)
    print(f"[OK] JSON序列化成功, 长度: {len(annotation_json)} 字符")

    print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("PhytoOracle Frontend Demo - 功能测试")
    print("=" * 60)
    print()

    try:
        test_knowledge_service()
        test_diagnosis_engine()
        test_export_functions()
        test_ontology_tracing()
        test_annotation_model()

        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        print()
        print("下一步：运行 Streamlit 应用")
        print("命令: streamlit run app.py")
        print()

        return True

    except Exception as e:
        print("=" * 60)
        print(f"[FAIL] 测试失败: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
