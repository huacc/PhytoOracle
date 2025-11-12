"""
创建PhytoOracle数据库脚本

功能：
- 连接到PostgreSQL默认数据库（postgres）
- 创建phytooracle数据库
- 执行init_db.sql和seed_data.sql初始化表结构和数据
"""

import asyncio
import asyncpg
from pathlib import Path
import sys

# 添加backend到Python路径
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 数据库配置（直接硬编码，不从配置文件读取）
DB_CONFIG = {
    'host': '192.168.0.119',
    'port': 5432,
    'user': 'admin',
    'password': '123456',
    'database': 'phytooracle'  # 目标数据库名称
}


async def database_exists(host, port, user, password, db_name):
    """
    检查数据库是否存在

    Args:
        host: 数据库主机
        port: 数据库端口
        user: 用户名
        password: 密码
        db_name: 数据库名称

    Returns:
        bool: 数据库是否存在
    """
    try:
        # 连接到postgres默认数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database='postgres',
            user=user,
            password=password
        )

        # 查询数据库是否存在
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_name
        )

        await conn.close()
        return result is not None
    except Exception as e:
        print(f"[ERROR] 检查数据库失败：{e}")
        return False


async def create_database():
    """
    创建phytooracle数据库
    """
    print(f"\n{'='*60}")
    print("PhytoOracle 数据库创建")
    print(f"{'='*60}\n")

    print(f"数据库配置:")
    print(f"  Host: {DB_CONFIG['host']}")
    print(f"  Port: {DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    print(f"  User: {DB_CONFIG['user']}")

    # 检查数据库是否已存在
    print(f"\n正在检查数据库是否存在...")
    exists = await database_exists(
        DB_CONFIG['host'],
        DB_CONFIG['port'],
        DB_CONFIG['user'],
        DB_CONFIG['password'],
        DB_CONFIG['database']
    )

    if exists:
        print(f"[WARN] 数据库 '{DB_CONFIG['database']}' 已存在，跳过创建步骤")
        return True

    # 连接到postgres默认数据库
    print(f"\n正在连接到postgres默认数据库...")
    try:
        conn = await asyncpg.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        print(f"[SUCCESS] 连接成功！")
    except Exception as e:
        print(f"[FAILED] 连接失败：{e}")
        return False

    try:
        # 创建数据库（注意：CREATE DATABASE不能在事务中执行）
        print(f"\n正在创建数据库 '{DB_CONFIG['database']}'...")

        # asyncpg不支持CREATE DATABASE在事务中，需要使用execute
        await conn.execute(f"""
            CREATE DATABASE {DB_CONFIG['database']}
                WITH
                TEMPLATE = template0
                OWNER = {DB_CONFIG['user']}
                ENCODING = 'UTF8'
                LC_COLLATE = 'C'
                LC_CTYPE = 'C'
                TABLESPACE = pg_default
                CONNECTION LIMIT = -1;
        """)

        print(f"[SUCCESS] 数据库 '{DB_CONFIG['database']}' 创建成功！")
        return True

    except Exception as e:
        print(f"[FAILED] 创建数据库失败：{e}")
        return False
    finally:
        await conn.close()


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

    # 执行SQL
    try:
        await conn.execute(sql_content)
        print(f"[SUCCESS] {sql_file.name} 执行成功！\n")
        return True
    except Exception as e:
        print(f"[FAILED] {sql_file.name} 执行失败：{e}\n")
        return False


async def init_database():
    """
    初始化数据库（执行DDL脚本）
    """
    print(f"\n{'='*60}")
    print("初始化数据库表结构和数据")
    print(f"{'='*60}\n")

    # 连接到phytooracle数据库
    print(f"正在连接到 '{DB_CONFIG['database']}' 数据库...")
    try:
        conn = await asyncpg.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        print(f"[SUCCESS] 连接成功！")
    except Exception as e:
        print(f"[FAILED] 连接失败：{e}")
        return False

    try:
        # SQL文件路径
        scripts_dir = BACKEND_DIR / "scripts"
        init_db_sql = scripts_dir / "init_db.sql"
        seed_data_sql = scripts_dir / "seed_data.sql"

        # 1. 执行init_db.sql
        if not await execute_sql_file(conn, init_db_sql):
            return False

        # 2. 执行seed_data.sql
        if not await execute_sql_file(conn, seed_data_sql):
            return False

        print(f"\n{'='*60}")
        print("[SUCCESS] 数据库初始化完成！")
        print(f"{'='*60}\n")

        print("下一步操作:")
        print(f"  1. 使用Navicat连接数据库:")
        print(f"     主机: {DB_CONFIG['host']}")
        print(f"     端口: {DB_CONFIG['port']}")
        print(f"     数据库: {DB_CONFIG['database']}")
        print(f"     用户名: {DB_CONFIG['user']}")
        print(f"     密码: {DB_CONFIG['password']}")
        print(f"  2. 查看5张核心表: diagnoses, images, api_keys, admin_users, knowledge_versions")
        print(f"  3. 查询管理员账号: SELECT * FROM admin_users;")

        return True

    except Exception as e:
        print(f"\n[ERROR] 初始化过程出错：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()
        print(f"\n数据库连接已关闭。")


async def main():
    """
    主函数
    """
    # 1. 创建数据库
    if not await create_database():
        print("\n[FAILED] 数据库创建失败！")
        return False

    # 2. 初始化数据库
    if not await init_database():
        print("\n[FAILED] 数据库初始化失败！")
        return False

    print(f"\n{'='*60}")
    print("[SUCCESS] 全部完成！您现在可以使用Navicat连接查看了。")
    print(f"{'='*60}\n")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
