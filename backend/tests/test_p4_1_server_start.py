"""
P4.1 FastAPI服务器启动测试

验证点：
- FastAPI服务可以正常启动
- /docs 可访问
- 基础路由返回正确响应

运行方式：
cd D:\\项目管理\\PhytoOracle
python backend\\tests\\test_p4_1_server_start.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.apps.api.main import app
from fastapi.testclient import TestClient

# 创建测试客户端
client = TestClient(app)


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "PhytoOracle API is running"
    assert data["version"] == "1.0.0"
    assert data["status"] == "healthy"
    print("✅ 根路径测试通过")


def test_health_endpoint():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ /health 测试通过")


def test_ping_endpoint():
    """测试ping接口"""
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["ping"] == "pong"
    print("✅ /ping 测试通过")


def test_docs_endpoint():
    """测试Swagger文档"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Swagger UI" in response.content or b"swagger" in response.content
    print("✅ /docs 可访问")


def test_redoc_endpoint():
    """测试ReDoc文档"""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert b"ReDoc" in response.content or b"redoc" in response.content
    print("✅ /redoc 可访问")


if __name__ == "__main__":
    # 设置UTF-8编码
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("="*60)
    print("P4.1 FastAPI服务器启动测试")
    print("="*60)

    try:
        test_root_endpoint()
        test_health_endpoint()
        test_ping_endpoint()
        test_docs_endpoint()
        test_redoc_endpoint()

        print("\n" + "="*60)
        print("✅ 所有测试通过！FastAPI服务运行正常")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        sys.exit(1)
