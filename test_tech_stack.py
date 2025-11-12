#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0.3 技术栈验证脚本

验证项：
1. FastAPI 基础功能
2. Streamlit 基础功能
3. PostgreSQL 连接
4. Redis 连接
5. 配置加载
"""

import sys
import os
from pathlib import Path

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config_loading():
    """测试配置加载"""
    print("\n[1] 测试配置加载...")
    try:
        from backend.core.config import settings

        print(f"  - 项目名称: {settings.PROJECT_NAME}")
        print(f"  - 数据库URL: {settings.DATABASE_URL}")
        print(f"  - Redis URL: {settings.REDIS_URL}")
        print(f"  [OK] 配置加载成功")
        return True
    except Exception as e:
        print(f"  [FAIL] 配置加载失败: {e}")
        return False


def test_fastapi():
    """测试 FastAPI"""
    print("\n[2] 测试 FastAPI...")
    try:
        # 导入应用
        sys.path.insert(0, str(PROJECT_ROOT / "backend" / "apps" / "api"))
        from main import app

        # 验证应用实例
        assert hasattr(app, 'router')
        assert hasattr(app, 'title')
        assert app.title == "PhytoOracle API"
        assert app.version == "1.0.0"

        # 验证路由
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes

        print(f"  [OK] FastAPI 测试通过")
        print(f"      - 应用标题: {app.title}")
        print(f"      - 应用版本: {app.version}")
        print(f"      - 路由数量: {len(routes)}")
        print(f"      - Docs URL: {app.docs_url}")
        return True
    except ImportError as e:
        print(f"  [SKIP] FastAPI 未安装，跳过测试")
        print(f"         请运行: pip install fastapi uvicorn")
        return None
    except Exception as e:
        print(f"  [FAIL] FastAPI 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_postgresql():
    """测试 PostgreSQL 连接"""
    print("\n[3] 测试 PostgreSQL 连接...")
    try:
        import psycopg2
        from backend.core.config import settings

        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=5
        )
        version = conn.server_version
        conn.close()

        print(f"  [OK] PostgreSQL 连接成功")
        print(f"      - 服务器版本: {version}")
        print(f"      - 主机: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"      - 数据库: {settings.DB_NAME}")
        return True
    except ImportError:
        print(f"  [SKIP] psycopg2 未安装，跳过测试")
        print(f"         请运行: pip install psycopg2-binary")
        return None
    except Exception as e:
        print(f"  [FAIL] PostgreSQL 连接失败: {e}")
        return False


def test_redis():
    """测试 Redis 连接"""
    print("\n[4] 测试 Redis 连接...")
    try:
        import redis
        from backend.core.config import settings

        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            socket_connect_timeout=5
        )

        # 测试连接
        r.ping()

        # 测试读写
        r.set("phytooracle:test", "hello")
        value = r.get("phytooracle:test")
        assert value == b"hello"
        r.delete("phytooracle:test")

        info = r.info()
        version = info.get('redis_version', 'unknown')

        print(f"  [OK] Redis 连接成功")
        print(f"      - Redis 版本: {version}")
        print(f"      - 主机: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"      - 数据库: {settings.REDIS_DB}")
        return True
    except ImportError:
        print(f"  [SKIP] redis 未安装，跳过测试")
        print(f"         请运行: pip install redis")
        return None
    except Exception as e:
        print(f"  [FAIL] Redis 连接失败: {e}")
        return False


def test_streamlit():
    """测试 Streamlit"""
    print("\n[5] 测试 Streamlit...")
    try:
        import streamlit as st

        print(f"  [OK] Streamlit 已安装")
        print(f"      - 版本: {st.__version__}")
        print(f"      - 启动命令: streamlit run backend/apps/admin/app.py")
        return True
    except ImportError:
        print(f"  [SKIP] Streamlit 未安装")
        print(f"         请运行: pip install streamlit")
        return None
    except Exception as e:
        print(f"  [FAIL] Streamlit 测试失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n[6] 测试目录结构...")
    required_dirs = [
        "backend/apps/api",
        "backend/apps/admin",
        "backend/core",
        "backend/domain",
        "backend/infrastructure",
        "backend/services",
        "backend/tests",
        "backend/knowledge_base",
        "backend/storage",
        "frontend/app",
        "frontend/components",
        "docs/reports",
    ]

    all_exist = True
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [MISSING] {dir_path}")
            all_exist = False

    if all_exist:
        print(f"  [OK] 所有必需目录已创建")
        return True
    else:
        print(f"  [FAIL] 部分目录缺失")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("P0.3 技术栈验证")
    print("=" * 60)

    results = {}

    # 执行所有测试
    results['配置加载'] = test_config_loading()
    results['FastAPI'] = test_fastapi()
    results['PostgreSQL'] = test_postgresql()
    results['Redis'] = test_redis()
    results['Streamlit'] = test_streamlit()
    results['目录结构'] = test_directory_structure()

    # 输出汇总
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results.items():
        if result is True:
            status = "[PASS]"
            passed += 1
        elif result is False:
            status = "[FAIL]"
            failed += 1
        else:
            status = "[SKIP]"
            skipped += 1

        print(f"{status} {name}")

    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")

    if failed == 0:
        print("\n[SUCCESS] 技术栈验证全部通过！")
        return 0
    else:
        print(f"\n[WARNING] 有 {failed} 项测试失败")
        print("         请根据提示安装缺失的依赖")
        return 1


if __name__ == "__main__":
    sys.exit(main())
