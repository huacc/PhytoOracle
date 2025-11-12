"""
数据库DDL验证脚本

功能：
- 连接PostgreSQL数据库
- 执行init_db.sql创建表结构
- 执行seed_data.sql插入初始化数据
- 验证表和索引创建成功
"""

import asyncio
import asyncpg
from pathlib import Path
import sys

# 添加backend到Python路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.config import settings


async def execute_sql_file(conn, sql_file: Path):
    """
    执行SQL文件

    Args:
        conn: asyncpg连接对象
        sql_file: SQL文件路径
    """
    print(f"\n{'='*60}")
    print(f"执行SQL文件: {sql_file.name}")
    print(f"{'='*60}\n")

    # 读取SQL文件
    sql_content = sql_file.read_text(encoding='utf-8')

    # 执行SQL（注意：asyncpg不支持DO块的RAISE NOTICE，需要使用普通execute）
    try:
        await conn.execute(sql_content)
        print(f"[SUCCESS] {sql_file.name} 执行成功！\n")
        return True
    except Exception as e:
        print(f"[FAILED] {sql_file.name} 执行失败：{e}\n")
        return False


async def verify_tables(conn):
    """
    验证所有表创建成功

    Args:
        conn: asyncpg连接对象

    Returns:
        bool: 验证是否通过
    """
    print(f"\n{'='*60}")
    print("验证表结构")
    print(f"{'='*60}\n")

    # 查询所有表
    tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)

    expected_tables = {'diagnoses', 'images', 'api_keys', 'admin_users', 'knowledge_versions'}
    actual_tables = {row['table_name'] for row in tables}

    print(f"预期表数量: {len(expected_tables)}")
    print(f"实际表数量: {len(actual_tables)}")
    print(f"\n已创建的表:")

    all_pass = True
    for table in expected_tables:
        if table in actual_tables:
            print(f"  [OK] {table}")
        else:
            print(f"  [MISS] {table} (缺失)")
            all_pass = False

    # 检查额外的表
    extra_tables = actual_tables - expected_tables
    if extra_tables:
        print(f"\n[WARN] 发现额外的表: {', '.join(extra_tables)}")

    return all_pass


async def verify_indexes(conn):
    """
    验证所有索引创建成功

    Args:
        conn: asyncpg连接对象

    Returns:
        bool: 验证是否通过
    """
    print(f"\n{'='*60}")
    print("验证索引结构")
    print(f"{'='*60}\n")

    # 查询所有索引（排除主键和唯一约束自动创建的索引）
    indexes = await conn.fetch("""
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname;
    """)

    print(f"已创建的索引数量: {len(indexes)}")
    print(f"\n索引列表:")

    for idx in indexes:
        print(f"  [OK] {idx['tablename']}.{idx['indexname']}")

    # 预期至少15个索引
    expected_min_indexes = 15

    if len(indexes) >= expected_min_indexes:
        print(f"\n[PASS] 索引数量符合预期（>= {expected_min_indexes}）")
        return True
    else:
        print(f"\n[FAIL] 索引数量不足（预期 >= {expected_min_indexes}，实际 {len(indexes)}）")
        return False


async def verify_seed_data(conn):
    """
    验证初始化数据插入成功

    Args:
        conn: asyncpg连接对象

    Returns:
        bool: 验证是否通过
    """
    print(f"\n{'='*60}")
    print("验证初始化数据")
    print(f"{'='*60}\n")

    # 验证管理员账号
    admin_count = await conn.fetchval("SELECT COUNT(*) FROM admin_users;")
    print(f"管理员账号数量: {admin_count}")
    if admin_count >= 1:
        # 查询管理员信息
        admin = await conn.fetchrow("""
            SELECT username, is_active, created_at
            FROM admin_users
            WHERE username = 'admin';
        """)
        if admin:
            print(f"  [OK] 默认管理员账号: {admin['username']}")
            print(f"     激活状态: {admin['is_active']}")
            print(f"     创建时间: {admin['created_at']}")
        else:
            print(f"  [FAIL] 默认管理员账号 'admin' 不存在")
            return False
    else:
        print(f"  [FAIL] 管理员账号数量不足")
        return False

    # 验证API Key
    api_key_count = await conn.fetchval("SELECT COUNT(*) FROM api_keys;")
    print(f"\nAPI Key数量: {api_key_count}")
    if api_key_count >= 1:
        print(f"  [OK] 开发用API Key已创建")
    else:
        print(f"  [FAIL] API Key未创建")
        return False

    # 验证知识库版本
    kb_version_count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_versions;")
    print(f"\n知识库版本数量: {kb_version_count}")
    if kb_version_count >= 1:
        # 查询当前版本
        kb_version = await conn.fetchrow("""
            SELECT commit_hash, disease_count, is_current
            FROM knowledge_versions
            WHERE is_current = TRUE;
        """)
        if kb_version:
            print(f"  [OK] 当前知识库版本: {kb_version['commit_hash']}")
            print(f"     疾病数量: {kb_version['disease_count']}")
        else:
            print(f"  [FAIL] 未找到当前激活的知识库版本")
            return False
    else:
        print(f"  [FAIL] 知识库版本未创建")
        return False

    return True


async def main():
    """
    主函数：执行DDL验证流程
    """
    print(f"\n{'='*60}")
    print("PhytoOracle 数据库DDL验证")
    print(f"{'='*60}")
    print(f"\n数据库配置:")
    print(f"  Host: {settings.DB_HOST}")
    print(f"  Port: {settings.DB_PORT}")
    print(f"  Database: {settings.DB_NAME}")
    print(f"  User: {settings.DB_USER}")

    # 连接数据库
    print(f"\n正在连接数据库...")
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        print(f"[SUCCESS] 数据库连接成功！")
    except Exception as e:
        print(f"[FAILED] 数据库连接失败：{e}")
        return False

    try:
        # SQL文件路径
        scripts_dir = BACKEND_DIR / "scripts"
        init_db_sql = scripts_dir / "init_db.sql"
        seed_data_sql = scripts_dir / "seed_data.sql"

        # 1. 执行init_db.sql
        if not await execute_sql_file(conn, init_db_sql):
            return False

        # 2. 验证表结构
        if not await verify_tables(conn):
            print("\n[FAIL] 表结构验证失败！")
            return False

        # 3. 验证索引
        if not await verify_indexes(conn):
            print("\n[FAIL] 索引验证失败！")
            return False

        # 4. 执行seed_data.sql
        if not await execute_sql_file(conn, seed_data_sql):
            return False

        # 5. 验证初始化数据
        if not await verify_seed_data(conn):
            print("\n[FAIL] 初始化数据验证失败！")
            return False

        # 全部验证通过
        print(f"\n{'='*60}")
        print("[SUCCESS] 所有验证通过！DDL执行成功！")
        print(f"{'='*60}\n")

        print("下一步操作:")
        print("  1. 使用 psql 连接数据库查看表结构:")
        print(f"     psql -h {settings.DB_HOST} -U {settings.DB_USER} -d {settings.DB_NAME}")
        print("     \\dt - 查看所有表")
        print("     \\di - 查看所有索引")
        print("  2. 查询管理员账号:")
        print("     SELECT * FROM admin_users;")
        print("  3. 开始P1.3阶段（Pydantic模型设计）")

        return True

    except Exception as e:
        print(f"\n[ERROR] 验证过程出错：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()
        print(f"\n数据库连接已关闭。")


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
