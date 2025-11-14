"""
P4.4简单验证脚本 - 验证本体管理API代码正确性

不依赖pytest，直接使用FastAPI TestClient验证API功能
"""

import sys
from pathlib import Path

# 添加backend到路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from apps.api.main import app

def test_ontology_apis():
    """验证本体管理API功能"""
    client = TestClient(app)

    print("=" * 80)
    print("P4.4 本体管理API简单验证")
    print("=" * 80)

    # 测试1: 查询所有特征定义
    print("\n[测试1] GET /api/v1/ontology/features - 查询所有特征定义")
    try:
        response = client.get("/api/v1/ontology/features")
        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功：查询到 {data.get('total', 0)} 个特征")
            print(f"  版本: {data.get('version', 'N/A')}")

            # 显示部分特征
            features = data.get('features', [])
            if features:
                print(f"  示例特征:")
                for feature in features[:3]:
                    print(f"    - {feature.get('feature_id')}: {feature.get('feature_name')} ({feature.get('feature_type')})")
        else:
            print(f"  ❌ 失败：状态码 {response.status_code}")
            print(f"  响应: {response.json()}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

    # 测试2: 查询单个特征详情
    print("\n[测试2] GET /api/v1/ontology/features/symptom_type - 查询单个特征详情")
    try:
        response = client.get("/api/v1/ontology/features/symptom_type")
        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功：查询到特征 {data.get('feature_id')}")
            print(f"  特征名称: {data.get('feature_name')}")
            print(f"  特征类型: {data.get('feature_type')}")
            print(f"  允许值数量: {len(data.get('allowed_values', []))}")
            print(f"  允许值: {data.get('allowed_values', [])}")
        else:
            print(f"  ❌ 失败：状态码 {response.status_code}")
            print(f"  响应: {response.json()}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

    # 测试3: 查询不存在的特征（错误处理）
    print("\n[测试3] GET /api/v1/ontology/features/non_existent - 错误处理测试")
    try:
        response = client.get("/api/v1/ontology/features/non_existent")
        print(f"  状态码: {response.status_code}")

        if response.status_code == 404:
            data = response.json()
            print(f"  ✅ 成功：正确返回404错误")
            print(f"  错误码: {data.get('detail', {}).get('error')}")
            print(f"  错误信息: {data.get('detail', {}).get('message')}")
        else:
            print(f"  ❌ 失败：期望404，实际 {response.status_code}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

    # 测试4: 查询疾病-特征关联
    print("\n[测试4] GET /api/v1/ontology/associations - 查询疾病-特征关联")
    try:
        response = client.get("/api/v1/ontology/associations")
        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功：查询到 {data.get('total', 0)} 个疾病-特征关联")

            # 显示部分关联
            associations = data.get('associations', [])
            if associations:
                print(f"  示例关联:")
                for assoc in associations[:2]:
                    print(f"    - {assoc.get('disease_id')}: {assoc.get('disease_name')}")
                    print(f"      特征数量: {len(assoc.get('feature_vector', {}))}")
        else:
            print(f"  ❌ 失败：状态码 {response.status_code}")
            print(f"  响应: {response.json()}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

    # 测试5: OpenAPI文档
    print("\n[测试5] GET /openapi.json - 验证OpenAPI文档")
    try:
        response = client.get("/openapi.json")
        print(f"  状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            paths = data.get('paths', {})

            # 检查本体管理API端点
            ontology_endpoints = [
                "/api/v1/ontology/features",
                "/api/v1/ontology/features/{feature_id}",
                "/api/v1/ontology/associations"
            ]

            all_exist = all(endpoint in paths for endpoint in ontology_endpoints)

            if all_exist:
                print(f"  ✅ 成功：所有本体管理API端点都在OpenAPI文档中")
                for endpoint in ontology_endpoints:
                    print(f"    - {endpoint}")
            else:
                print(f"  ❌ 失败：部分端点缺失")
                for endpoint in ontology_endpoints:
                    if endpoint not in paths:
                        print(f"    缺失: {endpoint}")
        else:
            print(f"  ❌ 失败：状态码 {response.status_code}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

    print("\n" + "=" * 80)
    print("验证完成")
    print("=" * 80)


if __name__ == "__main__":
    test_ontology_apis()
