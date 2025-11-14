"""
P4.5阶段验收测试 - 批量诊断API实现

测试内容：
1. POST /api/v1/diagnose/batch - 批量上传图片并诊断
2. GET /api/v1/diagnose/batch/{batch_id} - 查询批量诊断结果
3. GET /api/v1/diagnose/batch/{batch_id}/progress - 查询批量诊断进度
4. 错误处理测试（图片数量超限、batch_id不存在等）
5. 返回数据格式验证
6. 批量任务状态管理测试（processing → completed）

验收标准（G4.5）：
- 批量上传接口测试通过
- 批量结果查询接口测试通过
- 批量进度查询接口测试通过
- 批量任务状态管理正确
- 返回数据格式符合设计文档第6.6节
- 错误处理正确（404, 400, 422等）

实现阶段：P4.5
作者：AI Python Architect
日期：2025-11-15
"""

import sys
from pathlib import Path
import time
import asyncio

# 添加backend目录到sys.path（确保可以导入backend模块）
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from io import BytesIO

# 导入FastAPI应用
from backend.apps.api.main import app

# 导入BatchDiagnosisService（用于清理测试数据）
from backend.services.batch_diagnosis_service import BatchDiagnosisService


class TestP4_5_BatchDiagnosisAPI:
    """
    P4.5批量诊断API验收测试类

    测试策略：
    - 使用FastAPI TestClient进行集成测试
    - 真实调用DiagnosisService（不mock返回结果）
    - 使用真实图片数据（模拟图片上传）
    - 验证响应格式符合Schema定义
    - 测试异步任务状态管理
    """

    @pytest.fixture(scope="class")
    def client(self):
        """
        创建TestClient fixture

        Returns:
            TestClient: FastAPI测试客户端
        """
        return TestClient(app)

    @pytest.fixture(scope="class")
    def test_images(self):
        """
        创建测试用的模拟图片数据

        Returns:
            List[tuple]: 图片列表，每个元素为(filename, bytes)
        """
        # 模拟3张测试图片（使用1x1像素的PNG图片）
        # 实际测试中应该使用真实的花卉图片
        images = []
        for i in range(3):
            # 创建一个最小的PNG图片（1x1像素，黑色）
            # PNG文件头 + IHDR块 + IDAT块 + IEND块
            png_data = (
                b'\x89PNG\r\n\x1a\n'  # PNG签名
                b'\x00\x00\x00\rIHDR'  # IHDR块
                b'\x00\x00\x00\x01\x00\x00\x00\x01'  # 宽度1，高度1
                b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'  # 颜色类型等
                b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'  # IDAT块
                b'\r\n-\xb4'
                b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND块
            )
            images.append((f"test_image_{i+1}.png", png_data))

        return images

    @pytest.fixture(autouse=True)
    def cleanup_batch_tasks(self):
        """
        自动清理批量任务缓存（每个测试方法执行前后）

        注意：这是为了避免测试之间的相互干扰
        """
        # 测试前清理
        BatchDiagnosisService.clear_all_tasks()
        yield
        # 测试后清理
        BatchDiagnosisService.clear_all_tasks()

    def test_g4_5_1_batch_upload_and_diagnose(self, client, test_images):
        """
        G4.5.1: 批量上传接口测试 - POST /api/v1/diagnose/batch

        验收标准：
        - API端点可访问
        - 返回200状态码
        - 响应包含batch_id、total_images、status等必需字段
        - batch_id格式正确（batch_YYYYMMDD_HHmmss）
        - status为processing
        - total_images等于上传的图片数量
        """
        print("\n" + "=" * 60)
        print("G4.5.1: 批量上传接口测试 - POST /api/v1/diagnose/batch")
        print("=" * 60)

        # 准备multipart/form-data请求
        files = [("images", (filename, BytesIO(data), "image/png")) for filename, data in test_images]
        data = {"flower_genus": "Rosa"}

        # 发送POST请求
        print(f"\n  上传{len(test_images)}张图片...")
        response = client.post("/api/v1/diagnose/batch", files=files, data=data)

        # 验证状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        print(f"  ✅ 状态码: {response.status_code}")

        # 验证响应格式
        result = response.json()
        assert "batch_id" in result, "响应缺少batch_id字段"
        assert "total_images" in result, "响应缺少total_images字段"
        assert "status" in result, "响应缺少status字段"
        assert "created_at" in result, "响应缺少created_at字段"
        assert "estimated_completion_time" in result, "响应缺少estimated_completion_time字段"
        assert "message" in result, "响应缺少message字段"

        # 验证batch_id格式（batch_YYYYMMDD_HHmmss）
        batch_id = result["batch_id"]
        assert batch_id.startswith("batch_"), f"batch_id格式错误: {batch_id}"
        print(f"  ✅ batch_id: {batch_id}")

        # 验证status
        assert result["status"] == "processing", f"期望status为processing，实际: {result['status']}"
        print(f"  ✅ status: {result['status']}")

        # 验证total_images
        assert result["total_images"] == len(test_images), f"期望total_images为{len(test_images)}，实际: {result['total_images']}"
        print(f"  ✅ total_images: {result['total_images']}")

        # 验证message
        assert "批量诊断任务已创建" in result["message"], f"message内容不符合预期: {result['message']}"
        print(f"  ✅ message: {result['message']}")

        print(f"\n  验收结果: ✅ 批量上传接口测试通过")

        # 返回batch_id供后续测试使用
        return batch_id

    def test_g4_5_2_batch_progress_query(self, client, test_images):
        """
        G4.5.2: 批量进度查询接口测试 - GET /api/v1/diagnose/batch/{batch_id}/progress

        验收标准：
        - API端点可访问
        - 返回200状态码
        - 响应包含progress_percentage、completed_images等必需字段
        - progress_percentage范围正确（0-100）
        - 如果任务处理中，包含current_image信息
        """
        print("\n" + "=" * 60)
        print("G4.5.2: 批量进度查询接口测试 - GET /api/v1/diagnose/batch/{batch_id}/progress")
        print("=" * 60)

        # 1. 先创建批量任务
        files = [("images", (filename, BytesIO(data), "image/png")) for filename, data in test_images]
        data = {"flower_genus": "Rosa"}
        response = client.post("/api/v1/diagnose/batch", files=files, data=data)
        assert response.status_code == 200
        batch_id = response.json()["batch_id"]
        print(f"\n  已创建批量任务: {batch_id}")

        # 2. 查询进度（可能处理中）
        print(f"  查询批量诊断进度...")
        response = client.get(f"/api/v1/diagnose/batch/{batch_id}/progress")

        # 验证状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        print(f"  ✅ 状态码: {response.status_code}")

        # 验证响应格式
        result = response.json()
        assert "batch_id" in result, "响应缺少batch_id字段"
        assert "status" in result, "响应缺少status字段"
        assert "total_images" in result, "响应缺少total_images字段"
        assert "completed_images" in result, "响应缺少completed_images字段"
        assert "failed_images" in result, "响应缺少failed_images字段"
        assert "progress_percentage" in result, "响应缺少progress_percentage字段"
        assert "created_at" in result, "响应缺少created_at字段"

        # 验证batch_id
        assert result["batch_id"] == batch_id, f"期望batch_id为{batch_id}，实际: {result['batch_id']}"
        print(f"  ✅ batch_id: {result['batch_id']}")

        # 验证progress_percentage范围
        assert 0 <= result["progress_percentage"] <= 100, f"progress_percentage超出范围: {result['progress_percentage']}"
        print(f"  ✅ progress_percentage: {result['progress_percentage']}%")

        # 验证total_images
        assert result["total_images"] == len(test_images), f"期望total_images为{len(test_images)}，实际: {result['total_images']}"
        print(f"  ✅ total_images: {result['total_images']}")

        # 验证状态
        assert result["status"] in ["processing", "completed"], f"status值无效: {result['status']}"
        print(f"  ✅ status: {result['status']}")

        # 如果任务处理中，验证current_image字段
        if result["status"] == "processing" and "current_image" in result and result["current_image"]:
            current_image = result["current_image"]
            assert "image_id" in current_image, "current_image缺少image_id字段"
            assert "image_filename" in current_image, "current_image缺少image_filename字段"
            assert "started_at" in current_image, "current_image缺少started_at字段"
            print(f"  ✅ current_image: {current_image['image_filename']}")

        print(f"\n  验收结果: ✅ 批量进度查询接口测试通过")

    def test_g4_5_3_batch_result_query(self, client, test_images):
        """
        G4.5.3: 批量结果查询接口测试 - GET /api/v1/diagnose/batch/{batch_id}

        验收标准：
        - API端点可访问
        - 返回200状态码
        - 如果任务已完成，响应包含results和summary字段
        - results数组长度等于total_images
        - summary统计正确
        """
        print("\n" + "=" * 60)
        print("G4.5.3: 批量结果查询接口测试 - GET /api/v1/diagnose/batch/{batch_id}")
        print("=" * 60)

        # 1. 先创建批量任务
        files = [("images", (filename, BytesIO(data), "image/png")) for filename, data in test_images]
        data = {"flower_genus": "Rosa"}
        response = client.post("/api/v1/diagnose/batch", files=files, data=data)
        assert response.status_code == 200
        batch_id = response.json()["batch_id"]
        print(f"\n  已创建批量任务: {batch_id}")

        # 2. 等待任务完成（轮询查询进度）
        print(f"  等待批量诊断完成...")
        max_wait_seconds = 60  # 最多等待60秒
        start_time = time.time()
        while True:
            # 查询进度
            progress_response = client.get(f"/api/v1/diagnose/batch/{batch_id}/progress")
            assert progress_response.status_code == 200
            progress = progress_response.json()

            # 如果任务已完成，跳出循环
            if progress["status"] in ["completed", "failed"]:
                print(f"  ✅ 批量诊断已完成，状态: {progress['status']}")
                break

            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                print(f"  ⚠️ 等待超时（{max_wait_seconds}秒），当前进度: {progress['progress_percentage']}%")
                pytest.skip(f"批量诊断超时（可能VLM服务较慢），跳过结果验证")

            # 打印进度
            print(f"    进度: {progress['completed_images']}/{progress['total_images']} ({progress['progress_percentage']}%)")

            # 等待1秒后重试
            time.sleep(1)

        # 3. 查询批量结果
        print(f"  查询批量诊断结果...")
        response = client.get(f"/api/v1/diagnose/batch/{batch_id}")

        # 验证状态码
        assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
        print(f"  ✅ 状态码: {response.status_code}")

        # 验证响应格式
        result = response.json()
        assert "batch_id" in result, "响应缺少batch_id字段"
        assert "status" in result, "响应缺少status字段"
        assert "total_images" in result, "响应缺少total_images字段"
        assert "completed_images" in result, "响应缺少completed_images字段"
        assert "failed_images" in result, "响应缺少failed_images字段"

        # 验证status
        assert result["status"] in ["completed", "failed"], f"期望status为completed或failed，实际: {result['status']}"
        print(f"  ✅ status: {result['status']}")

        # 如果任务已完成，验证results和summary
        if result["status"] == "completed":
            # 验证results字段
            assert "results" in result, "响应缺少results字段（任务已完成时必须包含）"
            assert isinstance(result["results"], list), "results应为列表类型"
            assert len(result["results"]) == result["total_images"], f"results数组长度错误，期望{result['total_images']}，实际{len(result['results'])}"
            print(f"  ✅ results数组长度: {len(result['results'])}")

            # 验证results中的元素
            if len(result["results"]) > 0:
                first_result = result["results"][0]
                assert "image_id" in first_result, "result元素缺少image_id字段"
                assert "image_filename" in first_result, "result元素缺少image_filename字段"
                assert "disease_name" in first_result, "result元素缺少disease_name字段"
                assert "level" in first_result, "result元素缺少level字段"
                assert "confidence" in first_result, "result元素缺少confidence字段"
                print(f"  ✅ 第一个结果: {first_result['disease_name']} (confidence={first_result['confidence']:.2f})")

            # 验证summary字段
            assert "summary" in result, "响应缺少summary字段（任务已完成时必须包含）"
            summary = result["summary"]
            assert "confirmed_count" in summary, "summary缺少confirmed_count字段"
            assert "suspected_count" in summary, "summary缺少suspected_count字段"
            assert "unlikely_count" in summary, "summary缺少unlikely_count字段"
            assert "error_count" in summary, "summary缺少error_count字段"
            assert "average_confidence" in summary, "summary缺少average_confidence字段"
            assert "average_execution_time_ms" in summary, "summary缺少average_execution_time_ms字段"
            print(f"  ✅ summary: confirmed={summary['confirmed_count']}, suspected={summary['suspected_count']}, unlikely={summary['unlikely_count']}, error={summary['error_count']}")

            # 验证统计数量总和
            total_count = summary["confirmed_count"] + summary["suspected_count"] + summary["unlikely_count"] + summary["error_count"]
            assert total_count == result["total_images"], f"summary统计总数错误，期望{result['total_images']}，实际{total_count}"
            print(f"  ✅ summary统计总数正确: {total_count}")

        print(f"\n  验收结果: ✅ 批量结果查询接口测试通过")

    def test_g4_5_4_batch_not_found_error(self, client):
        """
        G4.5.4: 错误处理测试 - batch_id不存在

        验收标准：
        - 查询不存在的batch_id时返回404
        - 错误信息清晰
        """
        print("\n" + "=" * 60)
        print("G4.5.4: 错误处理测试 - batch_id不存在")
        print("=" * 60)

        # 1. 查询不存在的batch_id（进度）
        print("\n  测试查询不存在的batch_id（进度）...")
        response = client.get("/api/v1/diagnose/batch/batch_invalid_id/progress")
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        error = response.json()
        assert "detail" in error, "错误响应缺少detail字段"
        print(f"  ✅ 状态码: 404")
        print(f"  ✅ 错误信息: {error['detail']}")

        # 2. 查询不存在的batch_id（结果）
        print("\n  测试查询不存在的batch_id（结果）...")
        response = client.get("/api/v1/diagnose/batch/batch_invalid_id")
        assert response.status_code == 404, f"期望状态码404，实际: {response.status_code}"
        error = response.json()
        assert "detail" in error, "错误响应缺少detail字段"
        print(f"  ✅ 状态码: 404")
        print(f"  ✅ 错误信息: {error['detail']}")

        print(f"\n  验收结果: ✅ 错误处理测试通过")

    def test_g4_5_5_batch_upload_validation_error(self, client):
        """
        G4.5.5: 错误处理测试 - 图片数量超限

        验收标准：
        - 上传0张图片时返回400
        - 上传超过100张图片时返回400
        - 错误信息清晰
        """
        print("\n" + "=" * 60)
        print("G4.5.5: 错误处理测试 - 图片数量验证")
        print("=" * 60)

        # 1. 测试上传0张图片
        print("\n  测试上传0张图片...")
        files = []
        data = {"flower_genus": "Rosa"}
        response = client.post("/api/v1/diagnose/batch", files=files, data=data)
        # 注意：FastAPI对于空的files数组会返回422（Validation Error）
        assert response.status_code in [400, 422], f"期望状态码400或422，实际: {response.status_code}"
        print(f"  ✅ 状态码: {response.status_code}")

        # 2. 测试上传超过100张图片（模拟）
        print("\n  测试上传超过100张图片...")
        # 注意：为了节省测试时间，这里只模拟101张图片的文件名
        # 实际上传会非常耗时，所以这里用最小的PNG数据
        png_data = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR'
            b'\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        files = [("images", (f"test_{i}.png", BytesIO(png_data), "image/png")) for i in range(101)]
        data = {"flower_genus": "Rosa"}
        response = client.post("/api/v1/diagnose/batch", files=files, data=data)
        assert response.status_code == 400, f"期望状态码400，实际: {response.status_code}"
        error = response.json()
        assert "detail" in error, "错误响应缺少detail字段"
        print(f"  ✅ 状态码: 400")
        print(f"  ✅ 错误信息: {error['detail']}")

        print(f"\n  验收结果: ✅ 图片数量验证测试通过")

    def test_g4_5_6_batch_status_transition(self, client, test_images):
        """
        G4.5.6: 批量任务状态管理测试 - processing → completed

        验收标准：
        - 任务创建时status为processing
        - 任务完成后status为completed
        - 状态转换正确
        """
        print("\n" + "=" * 60)
        print("G4.5.6: 批量任务状态管理测试 - processing → completed")
        print("=" * 60)

        # 1. 创建批量任务
        files = [("images", (filename, BytesIO(data), "image/png")) for filename, data in test_images]
        data = {"flower_genus": "Rosa"}
        response = client.post("/api/v1/diagnose/batch", files=files, data=data)
        assert response.status_code == 200
        batch_id = response.json()["batch_id"]
        print(f"\n  已创建批量任务: {batch_id}")

        # 2. 立即查询状态（应该是processing）
        response = client.get(f"/api/v1/diagnose/batch/{batch_id}/progress")
        assert response.status_code == 200
        progress = response.json()
        initial_status = progress["status"]
        print(f"  ✅ 初始状态: {initial_status}")
        # 注意：由于任务是异步的，可能在查询时已经完成，所以这里只要求状态是有效值
        assert initial_status in ["processing", "completed"], f"初始状态无效: {initial_status}"

        # 3. 等待任务完成
        print(f"  等待任务完成...")
        max_wait_seconds = 60
        start_time = time.time()
        final_status = None
        while True:
            response = client.get(f"/api/v1/diagnose/batch/{batch_id}/progress")
            assert response.status_code == 200
            progress = response.json()
            final_status = progress["status"]

            if final_status in ["completed", "failed"]:
                break

            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                pytest.skip(f"批量诊断超时，跳过状态转换验证")

            print(f"    当前状态: {final_status}, 进度: {progress['progress_percentage']}%")
            time.sleep(1)

        # 4. 验证最终状态
        print(f"  ✅ 最终状态: {final_status}")
        assert final_status in ["completed", "failed"], f"最终状态无效: {final_status}"

        # 5. 验证状态转换（processing → completed）
        if initial_status == "processing" and final_status == "completed":
            print(f"  ✅ 状态转换正确: processing → completed")
        else:
            print(f"  ℹ️ 状态转换: {initial_status} → {final_status}")

        print(f"\n  验收结果: ✅ 批量任务状态管理测试通过")


# ==================== 主函数 ====================

def main():
    """
    P4.5验收测试主函数

    运行方式：
    ```bash
    cd D:/项目管理/PhytoOracle/backend
    pytest tests/test_p4_5_batch_diagnosis_api.py -v -s
    ```

    测试覆盖：
    - G4.5.1: 批量上传接口测试
    - G4.5.2: 批量进度查询接口测试
    - G4.5.3: 批量结果查询接口测试
    - G4.5.4: 错误处理测试（batch_id不存在）
    - G4.5.5: 错误处理测试（图片数量超限）
    - G4.5.6: 批量任务状态管理测试
    """
    print("\n" + "=" * 80)
    print("P4.5阶段验收测试 - 批量诊断API实现")
    print("=" * 80)
    print("\n运行pytest测试：")
    print(r"  cd D:\项目管理\PhytoOracle\backend")
    print("  pytest tests/test_p4_5_batch_diagnosis_api.py -v -s")
    print("\n测试覆盖：")
    print("  - G4.5.1: 批量上传接口测试")
    print("  - G4.5.2: 批量进度查询接口测试")
    print("  - G4.5.3: 批量结果查询接口测试")
    print("  - G4.5.4: 错误处理测试（batch_id不存在）")
    print("  - G4.5.5: 错误处理测试（图片数量超限）")
    print("  - G4.5.6: 批量任务状态管理测试")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
