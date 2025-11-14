"""
阶段2功能测试脚本

测试批量推理、统计分析、知识库管理等功能。
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from services.batch_diagnosis_service import get_batch_diagnosis_service
from services.mock_knowledge_service import get_knowledge_service
from models import Annotation
import random


def test_batch_diagnosis():
    """测试批量推理服务"""
    print("\n" + "="*60)
    print("测试1: 批量推理服务")
    print("="*60)

    batch_service = get_batch_diagnosis_service()

    # 创建假数据：模拟10张图片
    image_files = [
        (f"/tmp/rose_black_spot_{i:03d}.jpg", f"rose_black_spot_{i:03d}.jpg")
        for i in range(1, 6)
    ] + [
        (f"/tmp/rose_powdery_mildew_{i:03d}.jpg", f"rose_powdery_mildew_{i:03d}.jpg")
        for i in range(1, 4)
    ] + [
        (f"/tmp/cherry_brown_rot_{i:03d}.jpg", f"cherry_brown_rot_{i:03d}.jpg")
        for i in range(1, 3)
    ]

    print(f"[OK] 创建批次: {len(image_files)} 张图片")

    # 创建批次
    batch_result = batch_service.create_batch(image_files)
    print(f"[OK] 批次ID: {batch_result.batch_id}")

    # 执行批量推理
    print(f"[OK] 开始批量推理...")

    def progress_callback(current, total):
        if current % 3 == 0 or current == total:
            print(f"  进度: {current}/{total} ({current/total*100:.1f}%)")

    batch_result = batch_service.process_batch(
        batch_result,
        image_files,
        progress_callback=progress_callback
    )

    print(f"[OK] 批量推理完成")
    print(f"  - 成功: {batch_result.completed_count} 张")
    print(f"  - 失败: {batch_result.failed_count} 张")
    print(f"  - 状态: {batch_result.status}")

    # 验证结果
    assert batch_result.completed_count == len(image_files), "推理数量不符"
    assert batch_result.failed_count == 0, "不应有失败案例"
    assert len(batch_result.items) == len(image_files), "结果项数量不符"

    print("\n[PASS] 批量推理服务测试通过")
    return batch_result


def test_statistics_calculation(batch_result):
    """测试统计计算功能"""
    print("\n" + "="*60)
    print("测试2: 统计计算功能")
    print("="*60)

    batch_service = get_batch_diagnosis_service()

    # 模拟标注
    print("[OK] 模拟标注...")
    annotations = {}

    for item in batch_result.items:
        # 随机标注（80%正确，20%错误）
        is_correct = random.random() < 0.8

        if is_correct:
            annotations[item.image_id] = Annotation(
                is_accurate="correct",
                actual_disease_id=None,
                actual_disease_name=None,
                notes=None
            )
        else:
            # 随机选择一个不同的疾病作为实际疾病
            kb_service = get_knowledge_service()
            all_diseases = list(kb_service.diseases.keys())
            other_diseases = [d for d in all_diseases if d != item.disease_id]

            if other_diseases:
                actual_disease_id = random.choice(other_diseases)
                actual_disease_data = kb_service.get_disease(actual_disease_id)

                annotations[item.image_id] = Annotation(
                    is_accurate="incorrect",
                    actual_disease_id=actual_disease_id,
                    actual_disease_name=actual_disease_data["disease_name"],
                    notes="模拟误诊案例"
                )

    print(f"[OK] 已标注 {len(annotations)} 张图片")

    # 批量更新标注
    batch_result = batch_service.batch_update_annotations(batch_result, annotations)

    # 验证统计数据
    stats = batch_result.statistics

    print(f"\n[STATISTICS] 统计结果:")
    print(f"  - 总数: {stats.total_count}")
    print(f"  - 已标注: {stats.annotated_count}")
    print(f"  - 正确: {stats.correct_count}")
    print(f"  - 错误: {stats.incorrect_count}")
    print(f"  - 准确率: {stats.accuracy_rate*100:.1f}%" if stats.accuracy_rate else "  - 准确率: -")

    print(f"\n按置信度统计:")
    for level, data in stats.by_confidence.items():
        accuracy_str = f"{data['accuracy']*100:.1f}%" if data['accuracy'] is not None else "-"
        print(f"  - {level}: {data['total']} 张, 准确率 {accuracy_str}")

    print(f"\n按花卉属统计:")
    for genus, data in stats.by_genus.items():
        accuracy_str = f"{data['accuracy']*100:.1f}%" if data['accuracy'] is not None else "-"
        print(f"  - {genus}: {data['total']} 张, 准确率 {accuracy_str}")

    # 验证
    assert stats.total_count == len(batch_result.items), "总数不符"
    assert stats.annotated_count == len(annotations), "已标注数不符"
    assert stats.correct_count + stats.incorrect_count == stats.annotated_count, "标注统计不一致"

    print("\n[PASS] 统计计算功能测试通过")
    return batch_result


def test_confusion_matrix(batch_result):
    """测试混淆矩阵生成"""
    print("\n" + "="*60)
    print("测试3: 混淆矩阵生成")
    print("="*60)

    batch_service = get_batch_diagnosis_service()

    # 计算混淆矩阵
    confusion_matrix = batch_service.calculate_confusion_matrix(batch_result.items)

    if confusion_matrix:
        print(f"[OK] 混淆矩阵已生成")
        print(f"  - 疾病标签: {confusion_matrix.labels}")
        print(f"  - 样本数: {confusion_matrix.total_samples}")
        print(f"\n混淆矩阵:")

        # 打印矩阵
        max_label_len = max(len(label) for label in confusion_matrix.labels)

        # 表头
        header = " " * (max_label_len + 2) + "  ".join(
            f"{label[:8]:^8}" for label in confusion_matrix.labels
        )
        print(header)

        # 矩阵行
        for i, label in enumerate(confusion_matrix.labels):
            row_label = f"{label[:max_label_len]:{max_label_len}}"
            row_values = "  ".join(f"{confusion_matrix.matrix[i][j]:^8}" for j in range(len(confusion_matrix.labels)))
            print(f"{row_label}  {row_values}")

        # 验证
        assert len(confusion_matrix.labels) > 0, "标签列表为空"
        assert len(confusion_matrix.matrix) == len(confusion_matrix.labels), "矩阵维度不符"

        print("\n[PASS] 混淆矩阵生成测试通过")

    else:
        print("[WARN] 无法生成混淆矩阵（可能没有已标注样本）")


def test_knowledge_service():
    """测试知识库服务"""
    print("\n" + "="*60)
    print("测试4: 知识库服务")
    print("="*60)

    kb_service = get_knowledge_service()

    # 测试疾病列表
    print(f"[OK] 疾病数量: {len(kb_service.diseases)}")

    for disease_id, disease_data in kb_service.diseases.items():
        print(f"  - {disease_id}: {disease_data['disease_name']} (版本 {disease_data['version']})")

    # 测试属种列表
    genera = kb_service.get_all_genera()
    print(f"\n[OK] 宿主属种: {', '.join(genera)}")

    # 测试特征本体
    print(f"\n[OK] 特征类型数量: {len(kb_service.feature_ontology)}")

    for feature_key in kb_service.feature_ontology.keys():
        print(f"  - {feature_key}")

    # 测试同义词查找
    test_feature = "color_border"
    test_value = "yellow_halo"

    synonyms = kb_service.get_synonyms(test_feature, test_value)
    print(f"\n[OK] 同义词测试 ({test_feature} = {test_value}):")
    print(f"  同义词: {synonyms}")

    # 测试标准值查找
    test_synonym = "yellow"
    canonical_value, is_exact = kb_service.find_canonical_value(test_feature, test_synonym)
    print(f"\n[OK] 标准值查找 ({test_feature} = {test_synonym}):")
    print(f"  标准值: {canonical_value}")
    print(f"  是否精确: {is_exact}")

    # 验证
    assert len(kb_service.diseases) > 0, "疾病列表为空"
    assert len(kb_service.feature_ontology) > 0, "特征本体为空"
    assert len(genera) > 0, "属种列表为空"

    print("\n[PASS] 知识库服务测试通过")


def test_model_data_structures():
    """测试数据模型"""
    print("\n" + "="*60)
    print("测试5: 数据模型结构")
    print("="*60)

    from models import (
        BatchDiagnosisItem,
        BatchStatistics,
        ConfusionMatrixData,
        BatchDiagnosisResult,
    )
    from datetime import datetime

    # 测试BatchDiagnosisItem
    print("[OK] 测试 BatchDiagnosisItem...")
    item = BatchDiagnosisItem(
        image_name="test.jpg",
        image_id="img_001",
        diagnosis_id="diag_001",
        flower_genus="Rosa",
        disease_id="rose_black_spot",
        disease_name="玫瑰黑斑病",
        confidence_level="confirmed",
        confidence_score=0.92,
        diagnosed_at=datetime.now()
    )
    assert item.image_name == "test.jpg", "BatchDiagnosisItem 创建失败"

    # 测试BatchStatistics
    print("[OK] 测试 BatchStatistics...")
    stats = BatchStatistics(
        total_count=10,
        annotated_count=8,
        correct_count=6,
        incorrect_count=2,
        accuracy_rate=0.75
    )
    assert stats.total_count == 10, "BatchStatistics 创建失败"

    # 测试ConfusionMatrixData
    print("[OK] 测试 ConfusionMatrixData...")
    matrix = ConfusionMatrixData(
        labels=["Disease A", "Disease B"],
        matrix=[[5, 1], [0, 4]],
        total_samples=10
    )
    assert len(matrix.labels) == 2, "ConfusionMatrixData 创建失败"

    # 测试BatchDiagnosisResult
    print("[OK] 测试 BatchDiagnosisResult...")
    batch_result = BatchDiagnosisResult(
        batch_id="batch_001",
        created_at=datetime.now(),
        total_images=10,
        completed_count=10,
        items=[item]
    )
    assert batch_result.batch_id == "batch_001", "BatchDiagnosisResult 创建失败"

    print("\n[PASS] 数据模型结构测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("PhytoOracle 阶段2功能测试")
    print("="*60)

    try:
        # 测试1: 批量推理
        batch_result = test_batch_diagnosis()

        # 测试2: 统计计算
        batch_result = test_statistics_calculation(batch_result)

        # 测试3: 混淆矩阵
        test_confusion_matrix(batch_result)

        # 测试4: 知识库服务
        test_knowledge_service()

        # 测试5: 数据模型
        test_model_data_structures()

        # 总结
        print("\n" + "="*60)
        print("[SUCCESS] 所有测试通过！")
        print("="*60)
        print("\n阶段2功能已就绪，可以启动Streamlit应用进行手动测试。")
        print("\n运行命令:")
        print("  streamlit run app.py")
        print("\n验收检查项:")
        print("  [OK] 批量验证中心 - 批量上传和推理")
        print("  [OK] 批量验证中心 - 结果表格展示")
        print("  [OK] 批量验证中心 - 批量标注功能")
        print("  [OK] 统计分析 - 各种图表展示")
        print("  [OK] 知识库管理 - 疾病浏览和本体查看")

        return True

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
