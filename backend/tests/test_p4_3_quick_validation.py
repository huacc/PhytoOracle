"""
P4.3 知识库API快速验证脚本

直接运行脚本，不依赖pytest，验证知识库API功能
"""

import sys
from pathlib import Path

# 添加backend目录到sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from apps.api.main import app


def test_knowledge_apis():
    """测试知识库管理API"""
    print("=" * 80)
    print("P4.3 知识库管理API验收测试")
    print("=" * 80)

    client = TestClient(app)

    # 测试1: GET /api/v1/knowledge/diseases
    print("\n[测试1] GET /api/v1/knowledge/diseases - 查询所有疾病")
    try:
        response = client.get("/api/v1/knowledge/diseases")
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功：疾病总数 = {data['total']}")
            if data['total'] > 0:
                print(f"  示例疾病: {data['diseases'][0]['disease_name']}")
        else:
            print(f"  ❌ 失败：{response.json()}")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试2: GET /api/v1/knowledge/diseases?genus=Rosa
    print("\n[测试2] GET /api/v1/knowledge/diseases?genus=Rosa - 按宿主属筛选")
    try:
        response = client.get("/api/v1/knowledge/diseases?genus=Rosa")
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功：Rosa属疾病数 = {data['total']}")
        else:
            print(f"  ❌ 失败：{response.json()}")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试3: GET /api/v1/knowledge/tree
    print("\n[测试3] GET /api/v1/knowledge/tree - 获取知识库树")
    try:
        response = client.get("/api/v1/knowledge/tree")
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功：宿主属数 = {data['total_hosts']}, 疾病总数 = {data['total_diseases']}")
            for host in data['hosts'][:3]:  # 只显示前3个
                print(f"    - {host['name_zh']}（{host['genus']}）：{host['disease_count']} 种疾病")
        else:
            print(f"  ❌ 失败：{response.json()}")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试4: GET /api/v1/knowledge/diseases/{disease_id}
    print("\n[测试4] GET /api/v1/knowledge/diseases/{{disease_id}} - 查询疾病详情")
    try:
        # 先获取一个疾病ID
        all_response = client.get("/api/v1/knowledge/diseases")
        if all_response.status_code == 200 and all_response.json()['total'] > 0:
            disease_id = all_response.json()['diseases'][0]['disease_id']
            response = client.get(f"/api/v1/knowledge/diseases/{disease_id}")
            print(f"  状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 成功：获取到疾病详情")
                print(f"    - 疾病ID: {data['disease_id']}")
                print(f"    - 疾病名称: {data['disease_name']}")
                print(f"    - 版本: {data['version']}")
                print(f"    - 主要特征: {data['feature_importance']['major_features'][:3]}...")
            else:
                print(f"  ❌ 失败：{response.json()}")
        else:
            print(f"  ⚠️ 跳过：没有疾病数据")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试5: GET /api/v1/knowledge/hosts/{genus}
    print("\n[测试5] GET /api/v1/knowledge/hosts/{{genus}} - 按宿主属查询疾病")
    try:
        # 先获取一个宿主属
        tree_response = client.get("/api/v1/knowledge/tree")
        if tree_response.status_code == 200 and len(tree_response.json()['hosts']) > 0:
            genus = tree_response.json()['hosts'][0]['genus']
            response = client.get(f"/api/v1/knowledge/hosts/{genus}")
            print(f"  状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 成功：{genus} 属疾病数 = {data['total']}")
                print(f"    - 中文名: {data.get('name_zh', '未知')}")
                print(f"    - 英文名: {data.get('name_en', '未知')}")
            else:
                print(f"  ❌ 失败：{response.json()}")
        else:
            print(f"  ⚠️ 跳过：没有宿主属数据")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试6: 错误处理 - 疾病不存在
    print("\n[测试6] 错误处理 - 疾病不存在")
    try:
        response = client.get("/api/v1/knowledge/diseases/nonexistent_disease")
        print(f"  状态码: {response.status_code}")
        if response.status_code == 404:
            print(f"  ✅ 成功：正确返回404")
        else:
            print(f"  ❌ 失败：期望404，实际{response.status_code}")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试7: 错误处理 - 宿主属不存在
    print("\n[测试7] 错误处理 - 宿主属不存在")
    try:
        response = client.get("/api/v1/knowledge/hosts/NonExistentGenus")
        print(f"  状态码: {response.status_code}")
        if response.status_code == 404:
            print(f"  ✅ 成功：正确返回404")
        else:
            print(f"  ❌ 失败：期望404，实际{response.status_code}")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    # 测试8: OpenAPI文档
    print("\n[测试8] OpenAPI文档测试")
    try:
        docs_response = client.get("/docs")
        openapi_response = client.get("/openapi.json")
        print(f"  /docs 状态码: {docs_response.status_code}")
        print(f"  /openapi.json 状态码: {openapi_response.status_code}")
        if docs_response.status_code == 200 and openapi_response.status_code == 200:
            openapi_spec = openapi_response.json()
            knowledge_paths = [p for p in openapi_spec.get('paths', {}).keys() if '/knowledge/' in p]
            print(f"  ✅ 成功：OpenAPI文档包含 {len(knowledge_paths)} 个知识库端点")
            for path in knowledge_paths:
                print(f"    - {path}")
        else:
            print(f"  ❌ 失败：OpenAPI文档不可访问")
    except Exception as e:
        print(f"  ❌ 异常：{e}")

    print("\n" + "=" * 80)
    print("P4.3 知识库管理API验收测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_knowledge_apis()
