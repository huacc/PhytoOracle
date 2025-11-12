#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试远程服务器 192.168.0.119 上的服务连接"""

import sys
import os

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

def test_postgresql():
    """测试 PostgreSQL 连接"""
    try:
        import psycopg2
        # 尝试多个可能的数据库名称
        databases = ["digitalseer", "phytooracle", "postgres"]
        last_error = None

        for dbname in databases:
            try:
                conn = psycopg2.connect(
                    host="192.168.0.119",
                    port=5432,
                    database=dbname,
                    user="admin",
                    password="123456",
                    connect_timeout=5
                )
                version = conn.server_version
                conn.close()
                print(f"[OK] PostgreSQL 连接成功: Database={dbname}, Server version {version}")
                return True
            except psycopg2.OperationalError as e:
                last_error = e
                continue

        print(f"[FAIL] PostgreSQL 连接失败: {last_error}")
        return False
    except ImportError:
        print("[FAIL] PostgreSQL 测试失败: 缺少 psycopg2 模块")
        print("   安装命令: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"[FAIL] PostgreSQL 连接失败: {e}")
        return False

def test_redis():
    """测试 Redis 连接"""
    try:
        import redis
        r = redis.Redis(
            host="192.168.0.119",
            port=6379,
            password="123456",
            db=0,
            socket_connect_timeout=5
        )
        info = r.info()
        version = info.get('redis_version', 'unknown')
        print(f"[OK] Redis 连接成功: Version {version}")
        return True
    except ImportError:
        print("[FAIL] Redis 测试失败: 缺少 redis 模块")
        print("   安装命令: pip install redis")
        return False
    except Exception as e:
        print(f"[FAIL] Redis 连接失败: {e}")
        return False

def test_elasticsearch():
    """测试 Elasticsearch 连接"""
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch(
            ["http://192.168.0.119:9200"],
            basic_auth=("elastic", "123456"),
            request_timeout=5
        )
        info = es.info()
        version = info['version']['number']
        cluster = info['cluster_name']
        print(f"[OK] Elasticsearch 连接成功: Version {version}, Cluster: {cluster}")
        return True
    except ImportError:
        print("[FAIL] Elasticsearch 测试失败: 缺少 elasticsearch 模块")
        print("   安装命令: pip install elasticsearch")
        return False
    except Exception as e:
        print(f"[FAIL] Elasticsearch 连接失败: {e}")
        return False

def test_jena_fuseki():
    """测试 Jena Fuseki 连接"""
    try:
        import requests
        response = requests.get("http://192.168.0.119:3030/$/ping", timeout=5)
        if response.status_code == 200:
            print(f"[OK] Jena Fuseki 连接成功: HTTP {response.status_code}")
            return True
        else:
            print(f"[WARN] Jena Fuseki 响应异常: HTTP {response.status_code}")
            return False
    except ImportError:
        print("[FAIL] Jena Fuseki 测试失败: 缺少 requests 模块")
        print("   安装命令: pip install requests")
        return False
    except Exception as e:
        print(f"[FAIL] Jena Fuseki 连接失败: {e}")
        return False

def test_rabbitmq():
    """测试 RabbitMQ 连接"""
    try:
        import pika
        credentials = pika.PlainCredentials('admin', '123456')
        parameters = pika.ConnectionParameters(
            host='192.168.0.119',
            port=5672,
            credentials=credentials,
            connection_attempts=3,
            retry_delay=2
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print(f"[OK] RabbitMQ 连接成功")
        return True
    except ImportError:
        print("[FAIL] RabbitMQ 测试失败: 缺少 pika 模块")
        print("   安装命令: pip install pika")
        return False
    except Exception as e:
        print(f"[FAIL] RabbitMQ 连接失败: {e}")
        return False

def main():
    print("=" * 60)
    print("PhytoOracle 远程服务连接测试 (192.168.0.119)")
    print("=" * 60)
    print()

    results = {}

    print("1. 测试 PostgreSQL (5432)...")
    results['PostgreSQL'] = test_postgresql()
    print()

    print("2. 测试 Redis (6379)...")
    results['Redis'] = test_redis()
    print()

    print("3. 测试 Elasticsearch (9200)...")
    results['Elasticsearch'] = test_elasticsearch()
    print()

    print("4. 测试 Jena Fuseki (3030)...")
    results['Jena Fuseki'] = test_jena_fuseki()
    print()

    print("5. 测试 RabbitMQ (5672)...")
    results['RabbitMQ'] = test_rabbitmq()
    print()

    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for service, status in results.items():
        status_text = "[OK]" if status else "[FAIL]"
        print(f"{status_text} {service}: {'成功' if status else '失败'}")

    success_count = sum(results.values())
    total_count = len(results)
    print()
    print(f"总计: {success_count}/{total_count} 个服务测试通过")

    if success_count == total_count:
        print("\n[SUCCESS] 所有服务连接正常！")
        return 0
    else:
        print(f"\n[WARNING] 有 {total_count - success_count} 个服务连接失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
