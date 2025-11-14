"""
P4.6 图片管理API验收测试

功能：
- 测试GET /api/v1/images - 查询图片列表（支持分页、筛选）
- 测试PATCH /api/v1/images/{image_id}/accuracy - 标注诊断准确性

测试用例：
1. test_list_images_no_filter - 测试图片列表查询（无筛选条件）
2. test_list_images_with_filter - 测试图片列表查询（带筛选条件）
3. test_list_images_pagination - 测试分页功能（page, page_size）
4. test_update_accuracy_accurate - 测试准确性标注（accurate）
5. test_update_accuracy_inaccurate - 测试准确性标注（inaccurate）
6. test_update_accuracy_not_found - 测试错误处理（image_id不存在）
7. test_update_accuracy_no_diagnosis - 测试错误处理（该图片尚未诊断）

实现阶段：P4.6
对应设计文档：详细设计文档v2.0 第6.7节

作者：AI Python Architect
日期：2025-11-15
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# 添加backend目录到sys.path（使用相对路径）
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 添加项目根目录到sys.path
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入FastAPI测试客户端
from fastapi.testclient import TestClient

# 导入FastAPI应用
from backend.apps.api.main import app

# 导入ImageService（用于准备测试数据）
from backend.services.image_service import ImageService


# 创建测试客户端
client = TestClient(app)


# ==================== 测试辅助函数 ====================


def setup_test_data():
    """
    准备测试数据

    创建3张测试图片：
    1. img_test_001 - Rosa属，已诊断（rose_black_spot），准确性：correct
    2. img_test_002 - Prunus属，已诊断（cherry_powdery_mildew），准确性：unknown
    3. img_test_003 - Rosa属，未诊断，准确性：unknown

    Returns:
        dict: 包含测试数据的字典
    """
    print("\n" + "="*80)
    print("准备测试数据...")
    print("="*80)

    # 初始化ImageService
    project_root = backend_dir
    storage_path = project_root / "uploads"
    db_path = project_root / "data" / "test_images_p4_6.db"

    # 清理旧数据库（确保测试环境干净）
    if db_path.exists():
        db_path.unlink()
        print(f"  ✅ 清理旧数据库: {db_path}")

    image_service = ImageService(storage_path, db_path)

    # 创建测试图片字节数据（简单的1x1像素PNG）
    test_image_bytes = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    # 创建测试图片1（已诊断，准确性：correct）
    result1 = image_service.save_image(
        image_bytes=test_image_bytes,
        flower_genus="Rosa",
        diagnosis_id="diag_test_001",
        disease_id="rose_black_spot",
        disease_name="玫瑰黑斑病",
        confidence_level="confirmed"
    )
    image_id_1 = result1["image_id"]

    # 更新准确性标签为correct
    image_service.update_accuracy_label(image_id_1, "correct", "测试用准确诊断")
    print(f"  ✅ 创建测试图片1: {image_id_1} (Rosa, 已诊断, correct)")

    # 创建测试图片2（已诊断，准确性：unknown）
    result2 = image_service.save_image(
        image_bytes=test_image_bytes,
        flower_genus="Prunus",
        diagnosis_id="diag_test_002",
        disease_id="cherry_powdery_mildew",
        disease_name="樱花白粉病",
        confidence_level="suspected"
    )
    image_id_2 = result2["image_id"]
    print(f"  ✅ 创建测试图片2: {image_id_2} (Prunus, 已诊断, unknown)")

    # 创建测试图片3（未诊断，准确性：unknown）
    result3 = image_service.save_image(
        image_bytes=test_image_bytes,
        flower_genus="Rosa",
        diagnosis_id=None,  # 未诊断
        disease_id=None,
        disease_name=None,
        confidence_level=None
    )
    image_id_3 = result3["image_id"]
    print(f"  ✅ 创建测试图片3: {image_id_3} (Rosa, 未诊断, unknown)")

    test_data = {
        "image_id_1": image_id_1,  # Rosa, 已诊断, correct
        "image_id_2": image_id_2,  # Prunus, 已诊断, unknown
        "image_id_3": image_id_3,  # Rosa, 未诊断, unknown
    }

    print(f"  ✅ 测试数据准备完成")
    return test_data


# ==================== 测试用例 ====================


def test_list_images_no_filter(test_data):
    """
    测试1：图片列表查询（无筛选条件）

    验证点：
    - HTTP状态码200
    - 返回total >= 3（至少3张测试图片）
    - 返回images数组不为空
    - 每个图片包含必需字段（image_id、image_filename、image_path等）
    """
    print("\n" + "="*80)
    print("【测试1】图片列表查询（无筛选条件）")
    print("="*80)

    response = client.get("/api/v1/images?page=1&page_size=50")

    # 验证状态码
    assert response.status_code == 200, f"❌ HTTP状态码错误: {response.status_code}"
    print(f"  ✅ HTTP状态码: {response.status_code}")

    # 验证响应结构
    data = response.json()
    assert "total" in data, "❌ 响应缺少total字段"
    assert "page" in data, "❌ 响应缺少page字段"
    assert "page_size" in data, "❌ 响应缺少page_size字段"
    assert "images" in data, "❌ 响应缺少images字段"
    print(f"  ✅ 响应结构正确")

    # 验证total >= 3
    assert data["total"] >= 3, f"❌ total数量不足: {data['total']} < 3"
    print(f"  ✅ total = {data['total']} (>= 3)")

    # 验证images数组不为空
    assert len(data["images"]) > 0, "❌ images数组为空"
    print(f"  ✅ images数组长度: {len(data['images'])}")

    # 验证第一个图片的必需字段
    first_image = data["images"][0]
    required_fields = ["image_id", "image_filename", "image_path", "uploaded_at", "accuracy_status"]
    for field in required_fields:
        assert field in first_image, f"❌ 图片缺少{field}字段"
    print(f"  ✅ 图片包含所有必需字段")

    print(f"\n  📊 查询结果：")
    print(f"     - total: {data['total']}")
    print(f"     - page: {data['page']}, page_size: {data['page_size']}")
    print(f"     - images count: {len(data['images'])}")
    for img in data["images"][:3]:  # 显示前3条
        print(f"       * {img['image_id']}: {img['image_filename']} ({img['accuracy_status']})")

    return True


def test_list_images_with_filter(test_data):
    """
    测试2：图片列表查询（带筛选条件）

    筛选条件：
    - flower_genus = Rosa
    - accuracy_status = accurate

    验证点：
    - HTTP状态码200
    - 返回total >= 1（至少1张Rosa属的accurate图片）
    - 所有图片的accuracy_status都是accurate
    """
    print("\n" + "="*80)
    print("【测试2】图片列表查询（带筛选条件：flower_genus=Rosa, accuracy_status=accurate）")
    print("="*80)

    response = client.get("/api/v1/images?flower_genus=Rosa&accuracy_status=accurate&page=1&page_size=20")

    # 验证状态码
    assert response.status_code == 200, f"❌ HTTP状态码错误: {response.status_code}"
    print(f"  ✅ HTTP状态码: {response.status_code}")

    # 验证响应结构
    data = response.json()
    assert "total" in data, "❌ 响应缺少total字段"
    assert "images" in data, "❌ 响应缺少images字段"
    print(f"  ✅ 响应结构正确")

    # 验证total >= 1
    assert data["total"] >= 1, f"❌ total数量不足: {data['total']} < 1"
    print(f"  ✅ total = {data['total']} (>= 1)")

    # 验证所有图片的accuracy_status都是accurate
    for img in data["images"]:
        assert img["accuracy_status"] == "accurate", f"❌ 图片{img['image_id']}的accuracy_status不是accurate: {img['accuracy_status']}"
    print(f"  ✅ 所有图片的accuracy_status都是accurate")

    print(f"\n  📊 查询结果：")
    print(f"     - total: {data['total']}")
    print(f"     - images count: {len(data['images'])}")
    for img in data["images"]:
        print(f"       * {img['image_id']}: {img['image_filename']} (genus=?, accuracy={img['accuracy_status']})")

    return True


def test_list_images_pagination(test_data):
    """
    测试3：分页功能（page, page_size）

    测试方案：
    - 第1页：page=1, page_size=2
    - 第2页：page=2, page_size=2

    验证点：
    - 第1页返回2条记录
    - 第2页返回至少1条记录
    - 两页的image_id不重复
    """
    print("\n" + "="*80)
    print("【测试3】分页功能（page=1, page_size=2 和 page=2, page_size=2）")
    print("="*80)

    # 第1页
    response1 = client.get("/api/v1/images?page=1&page_size=2")
    assert response1.status_code == 200, f"❌ 第1页HTTP状态码错误: {response1.status_code}"
    data1 = response1.json()
    assert len(data1["images"]) == 2, f"❌ 第1页图片数量错误: {len(data1['images'])} != 2"
    print(f"  ✅ 第1页返回2条记录")

    # 第2页
    response2 = client.get("/api/v1/images?page=2&page_size=2")
    assert response2.status_code == 200, f"❌ 第2页HTTP状态码错误: {response2.status_code}"
    data2 = response2.json()
    assert len(data2["images"]) >= 1, f"❌ 第2页图片数量不足: {len(data2['images'])} < 1"
    print(f"  ✅ 第2页返回至少1条记录")

    # 验证两页的image_id不重复
    page1_ids = {img["image_id"] for img in data1["images"]}
    page2_ids = {img["image_id"] for img in data2["images"]}
    overlap = page1_ids & page2_ids
    assert len(overlap) == 0, f"❌ 两页的image_id有重复: {overlap}"
    print(f"  ✅ 两页的image_id不重复")

    print(f"\n  📊 分页结果：")
    print(f"     - 第1页: {[img['image_id'] for img in data1['images']]}")
    print(f"     - 第2页: {[img['image_id'] for img in data2['images']]}")

    return True


def test_update_accuracy_accurate(test_data):
    """
    测试4：准确性标注（accurate）

    测试步骤：
    1. 标注image_id_2为accurate
    2. 验证响应包含accuracy_status=accurate
    3. 查询图片列表验证标注已生效

    验证点：
    - HTTP状态码200
    - 响应包含image_id、accuracy_status、marked_at、message
    - accuracy_status = accurate
    - 查询图片列表时该图片的accuracy_status已更新
    """
    print("\n" + "="*80)
    print(f"【测试4】准确性标注（accurate）: {test_data['image_id_2']}")
    print("="*80)

    # 标注准确性
    request_data = {
        "accuracy_status": "accurate",
        "comment": "测试用：诊断结果准确",
        "marked_by": "test_user@example.com"
    }

    response = client.patch(
        f"/api/v1/images/{test_data['image_id_2']}/accuracy",
        json=request_data
    )

    # 验证状态码
    assert response.status_code == 200, f"❌ HTTP状态码错误: {response.status_code}"
    print(f"  ✅ HTTP状态码: {response.status_code}")

    # 验证响应结构
    data = response.json()
    assert "image_id" in data, "❌ 响应缺少image_id字段"
    assert "accuracy_status" in data, "❌ 响应缺少accuracy_status字段"
    assert "marked_at" in data, "❌ 响应缺少marked_at字段"
    assert "message" in data, "❌ 响应缺少message字段"
    print(f"  ✅ 响应结构正确")

    # 验证accuracy_status = accurate
    assert data["accuracy_status"] == "accurate", f"❌ accuracy_status错误: {data['accuracy_status']}"
    print(f"  ✅ accuracy_status = accurate")

    # 验证image_id正确
    assert data["image_id"] == test_data["image_id_2"], f"❌ image_id错误: {data['image_id']}"
    print(f"  ✅ image_id正确: {data['image_id']}")

    print(f"\n  📊 标注结果：")
    print(f"     - image_id: {data['image_id']}")
    print(f"     - accuracy_status: {data['accuracy_status']}")
    print(f"     - marked_at: {data['marked_at']}")
    print(f"     - message: {data['message']}")

    # 查询图片列表验证标注已生效
    list_response = client.get(f"/api/v1/images?accuracy_status=accurate")
    list_data = list_response.json()
    image_ids = [img["image_id"] for img in list_data["images"]]
    assert test_data["image_id_2"] in image_ids, f"❌ 标注后的图片未出现在accurate列表中"
    print(f"  ✅ 查询图片列表验证：图片已出现在accurate列表中")

    return True


def test_update_accuracy_inaccurate(test_data):
    """
    测试5：准确性标注（inaccurate）

    测试步骤：
    1. 标注image_id_1为inaccurate（之前是correct）
    2. 验证响应包含accuracy_status=inaccurate
    3. 查询图片列表验证标注已生效

    验证点：
    - HTTP状态码200
    - accuracy_status = inaccurate
    - 查询图片列表时该图片的accuracy_status已更新
    """
    print("\n" + "="*80)
    print(f"【测试5】准确性标注（inaccurate）: {test_data['image_id_1']}")
    print("="*80)

    # 标注准确性
    request_data = {
        "accuracy_status": "inaccurate",
        "comment": "测试用：诊断结果不准确",
        "marked_by": "test_user@example.com"
    }

    response = client.patch(
        f"/api/v1/images/{test_data['image_id_1']}/accuracy",
        json=request_data
    )

    # 验证状态码
    assert response.status_code == 200, f"❌ HTTP状态码错误: {response.status_code}"
    print(f"  ✅ HTTP状态码: {response.status_code}")

    # 验证accuracy_status = inaccurate
    data = response.json()
    assert data["accuracy_status"] == "inaccurate", f"❌ accuracy_status错误: {data['accuracy_status']}"
    print(f"  ✅ accuracy_status = inaccurate")

    print(f"\n  📊 标注结果：")
    print(f"     - image_id: {data['image_id']}")
    print(f"     - accuracy_status: {data['accuracy_status']}")
    print(f"     - comment: {data.get('comment', 'N/A')}")

    # 查询图片列表验证标注已生效
    list_response = client.get(f"/api/v1/images?accuracy_status=inaccurate")
    list_data = list_response.json()
    image_ids = [img["image_id"] for img in list_data["images"]]
    assert test_data["image_id_1"] in image_ids, f"❌ 标注后的图片未出现在inaccurate列表中"
    print(f"  ✅ 查询图片列表验证：图片已出现在inaccurate列表中")

    return True


def test_update_accuracy_not_found(test_data):
    """
    测试6：错误处理（image_id不存在）

    测试步骤：
    1. 尝试标注一个不存在的image_id
    2. 验证返回404错误

    验证点：
    - HTTP状态码404
    - 响应包含error字段
    - error = IMAGE_NOT_FOUND
    """
    print("\n" + "="*80)
    print("【测试6】错误处理（image_id不存在）")
    print("="*80)

    # 使用不存在的image_id
    fake_image_id = "img_not_exist_999"

    request_data = {
        "accuracy_status": "accurate",
        "comment": "测试用",
        "marked_by": "test_user@example.com"
    }

    response = client.patch(
        f"/api/v1/images/{fake_image_id}/accuracy",
        json=request_data
    )

    # 验证状态码
    assert response.status_code == 404, f"❌ HTTP状态码错误: {response.status_code} (期望404)"
    print(f"  ✅ HTTP状态码: {response.status_code}")

    # 验证响应包含error字段
    data = response.json()
    assert "detail" in data, "❌ 响应缺少detail字段"
    assert "error" in data["detail"], "❌ 响应缺少error字段"
    assert data["detail"]["error"] == "IMAGE_NOT_FOUND", f"❌ error类型错误: {data['detail']['error']}"
    print(f"  ✅ error类型: {data['detail']['error']}")

    print(f"\n  📊 错误响应：")
    print(f"     - error: {data['detail']['error']}")
    print(f"     - message: {data['detail']['message']}")

    return True


def test_update_accuracy_no_diagnosis(test_data):
    """
    测试7：错误处理（该图片尚未诊断）

    测试步骤：
    1. 尝试标注一个未诊断的图片（image_id_3）
    2. 验证返回400错误

    验证点：
    - HTTP状态码400
    - 响应包含error字段
    - error = ValidationError
    - message包含"尚未进行诊断"
    """
    print("\n" + "="*80)
    print(f"【测试7】错误处理（该图片尚未诊断）: {test_data['image_id_3']}")
    print("="*80)

    request_data = {
        "accuracy_status": "accurate",
        "comment": "测试用",
        "marked_by": "test_user@example.com"
    }

    response = client.patch(
        f"/api/v1/images/{test_data['image_id_3']}/accuracy",
        json=request_data
    )

    # 验证状态码
    assert response.status_code == 400, f"❌ HTTP状态码错误: {response.status_code} (期望400)"
    print(f"  ✅ HTTP状态码: {response.status_code}")

    # 验证响应包含error字段
    data = response.json()
    assert "detail" in data, "❌ 响应缺少detail字段"
    assert "error" in data["detail"], "❌ 响应缺少error字段"
    assert data["detail"]["error"] == "ValidationError", f"❌ error类型错误: {data['detail']['error']}"
    print(f"  ✅ error类型: {data['detail']['error']}")

    # 验证message包含"尚未进行诊断"
    assert "尚未进行诊断" in data["detail"]["message"], f"❌ message内容错误: {data['detail']['message']}"
    print(f"  ✅ message内容正确")

    print(f"\n  📊 错误响应：")
    print(f"     - error: {data['detail']['error']}")
    print(f"     - message: {data['detail']['message']}")

    return True


# ==================== 主函数 ====================


def main():
    """
    P4.6 图片管理API验收测试主函数

    测试流程：
    1. 准备测试数据
    2. 执行7个测试用例
    3. 统计测试结果
    4. 生成测试报告
    """
    print("\n" + "="*80)
    print("🧪 P4.6 图片管理API验收测试")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    # 准备测试数据
    test_data = setup_test_data()

    # 执行测试用例
    test_cases = [
        ("测试1：图片列表查询（无筛选条件）", test_list_images_no_filter),
        ("测试2：图片列表查询（带筛选条件）", test_list_images_with_filter),
        ("测试3：分页功能（page, page_size）", test_list_images_pagination),
        ("测试4：准确性标注（accurate）", test_update_accuracy_accurate),
        ("测试5：准确性标注（inaccurate）", test_update_accuracy_inaccurate),
        ("测试6：错误处理（image_id不存在）", test_update_accuracy_not_found),
        ("测试7：错误处理（该图片尚未诊断）", test_update_accuracy_no_diagnosis),
    ]

    passed = 0
    failed = 0
    results = []

    for test_name, test_func in test_cases:
        try:
            result = test_func(test_data)
            if result:
                passed += 1
                results.append((test_name, "PASSED"))
                print(f"\n  ✅ {test_name} - PASSED")
            else:
                failed += 1
                results.append((test_name, "FAILED"))
                print(f"\n  ❌ {test_name} - FAILED")
        except AssertionError as e:
            failed += 1
            results.append((test_name, f"FAILED - {e}"))
            print(f"\n  ❌ {test_name} - FAILED")
            print(f"     原因: {e}")
        except Exception as e:
            failed += 1
            results.append((test_name, f"ERROR - {e}"))
            print(f"\n  ❌ {test_name} - ERROR")
            print(f"     原因: {e}")

    # 测试总结
    total_time = time.time() - start_time

    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    print(f"总测试用例: {len(test_cases)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⏱️  总耗时: {total_time:.2f}秒")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "-"*80)
    print("详细结果:")
    print("-"*80)
    for idx, (test_name, status) in enumerate(results, start=1):
        status_icon = "✅" if "PASSED" in status else "❌"
        print(f"{idx}. {status_icon} {test_name}: {status}")

    print("\n" + "="*80)
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️ 有 {failed} 个测试失败，请检查！")
    print("="*80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
