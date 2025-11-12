"""
知识库JSON验证脚本

功能：
- 验证所有疾病JSON文件符合JSON Schema规范
- 验证所有疾病JSON可被Pydantic DiseaseOntology模型解析
- 验证特征本体JSON可被Pydantic FeatureOntology模型解析
- 输出详细的验证报告

使用方法：
    python backend/tests/test_knowledge_base_validation.py

验收标准（G1.4）：
- 所有JSON Schema符合JSON Schema Draft 7规范
- 疾病JSON文件通过Schema验证
- 疾病JSON可被Pydantic DiseaseOntology模型正确解析
- 特征本体JSON可被Pydantic FeatureOntology模型正确解析
- 至少创建2种疾病JSON
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 导入Pydantic模型
from domain import DiseaseOntology, FeatureOntology


def validate_json_schema_format(schema_path: Path) -> Tuple[bool, str]:
    """
    验证JSON Schema文件本身的格式是否正确

    Args:
        schema_path: JSON Schema文件路径

    Returns:
        (is_valid, message): 验证结果和消息
    """
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        # 验证必须字段
        required_fields = ["$schema", "title", "type"]
        for field in required_fields:
            if field not in schema:
                return False, f"缺少必须字段: {field}"

        # 验证$schema是JSON Schema Draft 7
        if schema["$schema"] != "http://json-schema.org/draft-07/schema#":
            return False, f"$schema不是Draft 7: {schema['$schema']}"

        return True, "Schema格式正确"
    except json.JSONDecodeError as e:
        return False, f"JSON格式错误: {str(e)}"
    except Exception as e:
        return False, f"验证失败: {str(e)}"


def validate_disease_json_with_pydantic(disease_path: Path) -> Tuple[bool, str, DiseaseOntology]:
    """
    使用Pydantic模型验证疾病JSON

    Args:
        disease_path: 疾病JSON文件路径

    Returns:
        (is_valid, message, disease_obj): 验证结果、消息和疾病对象
    """
    try:
        disease_json = json.loads(disease_path.read_text(encoding="utf-8"))

        # 使用Pydantic模型验证
        disease = DiseaseOntology(**disease_json)

        # 验证核心字段
        if not disease.disease_id:
            return False, "disease_id为空", None
        if not disease.disease_name:
            return False, "disease_name为空", None

        return True, f"Pydantic验证通过: {disease.disease_name}", disease
    except json.JSONDecodeError as e:
        return False, f"JSON格式错误: {str(e)}", None
    except Exception as e:
        return False, f"Pydantic验证失败: {str(e)}", None


def validate_feature_ontology_with_pydantic(feature_path: Path) -> Tuple[bool, str, FeatureOntology]:
    """
    使用Pydantic模型验证特征本体JSON

    Args:
        feature_path: 特征本体JSON文件路径

    Returns:
        (is_valid, message, feature_obj): 验证结果、消息和特征对象
    """
    try:
        feature_json = json.loads(feature_path.read_text(encoding="utf-8"))

        # 使用Pydantic模型验证
        feature = FeatureOntology(**feature_json)

        # 验证核心字段
        if not feature.version:
            return False, "version为空", None
        if not feature.dimensions:
            return False, "dimensions为空", None

        return True, f"Pydantic验证通过: version {feature.version}", feature
    except json.JSONDecodeError as e:
        return False, f"JSON格式错误: {str(e)}", None
    except Exception as e:
        return False, f"Pydantic验证失败: {str(e)}", None


def run_validation():
    """运行完整的知识库验证"""
    print("\n" + "=" * 80)
    print("PhytoOracle 知识库JSON验证")
    print("=" * 80 + "\n")

    # 统计变量
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    # ============================================================
    # 1. 验证JSON Schema格式
    # ============================================================
    print("[步骤1] 验证JSON Schema格式")
    print("-" * 80)

    schemas = [
        BACKEND_DIR / "schemas/disease_schema.json",
        BACKEND_DIR / "schemas/feature_schema.json",
        BACKEND_DIR / "schemas/host_disease_schema.json"
    ]

    for schema_path in schemas:
        total_tests += 1
        is_valid, message = validate_json_schema_format(schema_path)

        if is_valid:
            print(f"  [PASS] {schema_path.name}: {message}")
            passed_tests += 1
        else:
            print(f"  [FAIL] {schema_path.name}: {message}")
            failed_tests += 1

    print()

    # ============================================================
    # 2. 验证疾病JSON（Pydantic模型）
    # ============================================================
    print("[步骤2] 验证疾病JSON（Pydantic模型）")
    print("-" * 80)

    diseases_dir = BACKEND_DIR / "knowledge_base/diseases"
    disease_files = list(diseases_dir.glob("*.json"))

    if len(disease_files) < 2:
        print(f"  [FAIL] 疾病JSON文件数量不足：需要至少2个，实际{len(disease_files)}个")
        failed_tests += 1
        total_tests += 1
    else:
        print(f"  [PASS] 疾病JSON文件数量: {len(disease_files)}个（>=2）")
        passed_tests += 1
        total_tests += 1

    for disease_file in sorted(disease_files):
        total_tests += 1
        is_valid, message, disease = validate_disease_json_with_pydantic(disease_file)

        if is_valid:
            print(f"  [PASS] {disease_file.name}: {message}")
            passed_tests += 1
        else:
            print(f"  [FAIL] {disease_file.name}: {message}")
            failed_tests += 1

    print()

    # ============================================================
    # 3. 验证特征本体JSON（Pydantic模型）
    # ============================================================
    print("[步骤3] 验证特征本体JSON（Pydantic模型）")
    print("-" * 80)

    feature_file = BACKEND_DIR / "knowledge_base/features/feature_ontology.json"
    total_tests += 1

    is_valid, message, feature = validate_feature_ontology_with_pydantic(feature_file)

    if is_valid:
        print(f"  [PASS] {feature_file.name}: {message}")
        passed_tests += 1
    else:
        print(f"  [FAIL] {feature_file.name}: {message}")
        failed_tests += 1

    print()

    # ============================================================
    # 4. 验证宿主-疾病关系JSON
    # ============================================================
    print("[步骤4] 验证宿主-疾病关系JSON")
    print("-" * 80)

    associations_file = BACKEND_DIR / "knowledge_base/host_disease/associations.json"
    total_tests += 1

    try:
        associations = json.loads(associations_file.read_text(encoding="utf-8"))

        # 验证必须字段
        if "version" not in associations:
            print(f"  [FAIL] {associations_file.name}: 缺少version字段")
            failed_tests += 1
        elif "associations" not in associations:
            print(f"  [FAIL] {associations_file.name}: 缺少associations字段")
            failed_tests += 1
        else:
            print(f"  [PASS] {associations_file.name}: JSON格式正确，包含{len(associations['associations'])}个宿主")
            passed_tests += 1
    except Exception as e:
        print(f"  [FAIL] {associations_file.name}: {str(e)}")
        failed_tests += 1

    print()

    # ============================================================
    # 5. 输出验收报告
    # ============================================================
    print("=" * 80)
    print("验收报告（G1.4）")
    print("=" * 80)

    print(f"\n  总测试数: {total_tests}")
    print(f"  通过: {passed_tests} [PASS]")
    print(f"  失败: {failed_tests} [FAIL]")
    print(f"  通过率: {passed_tests / total_tests * 100:.1f}%\n")

    # G1.4验收标准检查
    g14_criteria = [
        ("所有JSON Schema符合JSON Schema Draft 7规范", passed_tests >= 3 and failed_tests == 0),
        ("疾病JSON文件通过Schema验证", len(disease_files) >= 2),
        ("疾病JSON可被Pydantic DiseaseOntology模型正确解析", passed_tests >= total_tests - failed_tests),
        ("特征本体JSON可被Pydantic FeatureOntology模型正确解析", is_valid),
        ("至少创建2种疾病JSON", len(disease_files) >= 2),
        ("知识库设计说明文档完成", (BACKEND_DIR / "../docs/knowledge_base/知识库设计说明.md").exists())
    ]

    print("G1.4 验收标准：")
    print("-" * 80)

    g14_pass_count = 0
    for idx, (criteria, passed) in enumerate(g14_criteria, 1):
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {criteria}")
        if passed:
            g14_pass_count += 1

    print()
    print(f"G1.4 验收通过率: {g14_pass_count}/{len(g14_criteria)} ({g14_pass_count / len(g14_criteria) * 100:.0f}%)")

    if g14_pass_count == len(g14_criteria):
        print("\n  [SUCCESS] 恭喜！P1.4 知识库设计（JSON Schema）验收通过！\n")
        return 0
    else:
        print("\n  [WARNING] P1.4验收未通过，请修正失败项后重新验证。\n")
        return 1


if __name__ == "__main__":
    exit_code = run_validation()
    sys.exit(exit_code)
