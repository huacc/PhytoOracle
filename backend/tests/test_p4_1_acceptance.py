"""
P4.1阶段验收测试脚本

验收标准（G4.1）：
1. FastAPI服务启动成功（uvicorn apps.api.main:app --reload）
2. /docs 可访问（Swagger UI自动生成API文档）
3. 依赖注入测试通过（数据库连接池、Redis、VLM客户端可正常获取）
4. 配置管理测试通过（从 .env 读取配置）
5. CORS配置正确（前端可跨域调用）

实现阶段：P4.1

作者：AI Python Architect
日期：2025-11-15
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入核心模块
from backend.core.config import settings
from backend.apps.api.deps import (
    get_db_pool,
    get_redis_client,
    get_vlm_client,
    get_knowledge_service,
    get_diagnosis_service,
    get_image_service,
    cleanup_resources,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 验收测试类 ====================

class P41AcceptanceTest:
    """
    P4.1阶段验收测试类

    测试项：
    1. 配置管理测试
    2. 依赖注入测试
    3. FastAPI服务测试（需手动启动服务器）
    4. CORS配置测试（需手动验证）
    """

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name: str, passed: bool, message: str = "", details: Any = None):
        """
        记录测试结果

        Args:
            test_name: 测试名称
            passed: 是否通过
            message: 附加消息
            details: 详细信息
        """
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "details": details,
        }
        self.results.append(result)

        if passed:
            self.passed += 1
            logger.info(f"✅ {test_name}: 通过 - {message}")
        else:
            self.failed += 1
            logger.error(f"❌ {test_name}: 失败 - {message}")

    async def test_config_management(self):
        """
        G4.1.4: 配置管理测试

        验证点：
        - settings对象可正常导入
        - 从.env读取配置成功
        - 所有必需配置项存在
        """
        logger.info("\n" + "="*60)
        logger.info("📋 G4.1.4: 配置管理测试")
        logger.info("="*60)

        try:
            # 验证核心配置项
            required_configs = {
                "PROJECT_NAME": settings.PROJECT_NAME,
                "VERSION": settings.VERSION,
                "ENVIRONMENT": settings.ENVIRONMENT,
                "DB_HOST": settings.DB_HOST,
                "DB_PORT": settings.DB_PORT,
                "DB_NAME": settings.DB_NAME,
                "REDIS_HOST": settings.REDIS_HOST,
                "REDIS_PORT": settings.REDIS_PORT,
                "VLM_PROVIDER": settings.VLM_PROVIDER,
                "STORAGE_BASE_PATH": str(settings.STORAGE_BASE_PATH),
                "KNOWLEDGE_BASE_PATH": str(settings.KNOWLEDGE_BASE_PATH),
            }

            logger.info(f"项目名称: {settings.PROJECT_NAME}")
            logger.info(f"版本号: {settings.VERSION}")
            logger.info(f"运行环境: {settings.ENVIRONMENT}")
            logger.info(f"数据库URL: {settings.DATABASE_URL}")
            logger.info(f"Redis URL: {settings.REDIS_URL}")
            logger.info(f"VLM提供商: {settings.VLM_PROVIDER}")

            self.log_result(
                "G4.1.4 配置管理测试",
                True,
                "所有配置项加载成功",
                required_configs
            )

        except Exception as e:
            self.log_result(
                "G4.1.4 配置管理测试",
                False,
                f"配置加载失败: {e}"
            )

    async def test_dependency_injection(self):
        """
        G4.1.3: 依赖注入测试

        验证点：
        - PostgreSQL连接池可正常获取
        - Redis客户端可正常获取
        - VLM客户端可正常初始化
        - 知识库服务可正常初始化
        - 诊断服务可正常初始化
        - 图片服务可正常初始化
        """
        logger.info("\n" + "="*60)
        logger.info("📋 G4.1.3: 依赖注入测试")
        logger.info("="*60)

        # 1. 测试PostgreSQL连接池
        try:
            db_pool = await get_db_pool()
            if db_pool:
                async with db_pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    self.log_result(
                        "G4.1.3.1 PostgreSQL连接池",
                        result == 1,
                        f"数据库连接测试成功: SELECT 1 = {result}",
                        {"db_host": settings.DB_HOST, "db_name": settings.DB_NAME}
                    )
            else:
                self.log_result(
                    "G4.1.3.1 PostgreSQL连接池",
                    False,
                    "数据库连接池不可用（可能未安装asyncpg或连接失败）"
                )
        except Exception as e:
            self.log_result(
                "G4.1.3.1 PostgreSQL连接池",
                False,
                f"数据库连接测试失败: {e}"
            )

        # 2. 测试Redis客户端
        try:
            redis_client = await get_redis_client()
            if redis_client:
                await redis_client.set("p4_1_test_key", "test_value")
                value = await redis_client.get("p4_1_test_key")
                await redis_client.delete("p4_1_test_key")
                self.log_result(
                    "G4.1.3.2 Redis客户端",
                    value == "test_value",
                    f"Redis连接测试成功: test_key = {value}",
                    {"redis_host": settings.REDIS_HOST, "redis_port": settings.REDIS_PORT}
                )
            else:
                self.log_result(
                    "G4.1.3.2 Redis客户端",
                    False,
                    "Redis客户端不可用（可能未安装redis或连接失败）"
                )
        except Exception as e:
            self.log_result(
                "G4.1.3.2 Redis客户端",
                False,
                f"Redis连接测试失败: {e}"
            )

        # 3. 测试VLM客户端
        try:
            vlm_client = await get_vlm_client()
            providers = list(vlm_client.providers.keys())
            self.log_result(
                "G4.1.3.3 VLM客户端",
                len(providers) > 0,
                f"VLM客户端初始化成功，已配置 {len(providers)} 个提供商",
                {"providers": providers}
            )
        except Exception as e:
            self.log_result(
                "G4.1.3.3 VLM客户端",
                False,
                f"VLM客户端初始化失败: {e}"
            )

        # 4. 测试知识库服务
        try:
            kb_service = await get_knowledge_service()
            diseases = kb_service.get_all_diseases()
            self.log_result(
                "G4.1.3.4 知识库服务",
                len(diseases) > 0,
                f"知识库服务初始化成功，已加载 {len(diseases)} 个疾病",
                {
                    "disease_count": len(diseases),
                    "first_disease": diseases[0].disease_id if diseases else None
                }
            )
        except Exception as e:
            self.log_result(
                "G4.1.3.4 知识库服务",
                False,
                f"知识库服务初始化失败: {e}"
            )

        # 5. 测试诊断服务
        try:
            diagnosis_service = await get_diagnosis_service()
            self.log_result(
                "G4.1.3.5 诊断服务",
                diagnosis_service is not None,
                "诊断服务初始化成功"
            )
        except Exception as e:
            self.log_result(
                "G4.1.3.5 诊断服务",
                False,
                f"诊断服务初始化失败: {e}"
            )

        # 6. 测试图片服务
        try:
            image_service = await get_image_service()
            self.log_result(
                "G4.1.3.6 图片服务",
                image_service is not None,
                "图片服务初始化成功",
                {"storage_path": str(image_service.storage.base_path)}
            )
        except Exception as e:
            self.log_result(
                "G4.1.3.6 图片服务",
                False,
                f"图片服务初始化失败: {e}"
            )

    def print_manual_tests(self):
        """
        打印需要手动验证的测试项
        """
        logger.info("\n" + "="*60)
        logger.info("📋 手动验收测试项")
        logger.info("="*60)

        logger.info("\n✋ G4.1.1: FastAPI服务启动测试")
        logger.info("   请执行以下命令启动服务器：")
        logger.info("   ```bash")
        logger.info(f"   cd {PROJECT_ROOT}")
        logger.info("   python -m backend.apps.api.main")
        logger.info("   ```")
        logger.info("   验证点：")
        logger.info("   - 服务器成功启动在 http://0.0.0.0:8000")
        logger.info("   - 控制台输出启动日志")
        logger.info("   - 没有异常错误")

        logger.info("\n✋ G4.1.2: /docs 访问测试")
        logger.info("   请在浏览器访问以下URL：")
        logger.info("   - Swagger UI: http://localhost:8000/docs")
        logger.info("   - ReDoc: http://localhost:8000/redoc")
        logger.info("   验证点：")
        logger.info("   - Swagger UI正常显示")
        logger.info("   - 包含 Health 标签下的3个接口（/, /health, /ping）")
        logger.info("   - API文档描述完整")

        logger.info("\n✋ G4.1.5: CORS配置测试")
        logger.info("   请执行以下命令测试CORS：")
        logger.info("   ```bash")
        logger.info("   curl -H \"Origin: http://localhost:3000\" \\")
        logger.info("        -H \"Access-Control-Request-Method: GET\" \\")
        logger.info("        -X OPTIONS http://localhost:8000/health")
        logger.info("   ```")
        logger.info("   验证点：")
        logger.info("   - 响应包含 Access-Control-Allow-Origin 头")
        logger.info("   - 允许的源包括 http://localhost:3000")

    def print_summary(self):
        """
        打印验收测试汇总
        """
        logger.info("\n" + "="*60)
        logger.info("📊 P4.1阶段验收测试汇总")
        logger.info("="*60)

        logger.info(f"\n总测试项: {len(self.results)}")
        logger.info(f"✅ 通过: {self.passed}")
        logger.info(f"❌ 失败: {self.failed}")
        logger.info(f"通过率: {self.passed / len(self.results) * 100:.1f}%")

        logger.info("\n详细结果：")
        for i, result in enumerate(self.results, 1):
            status = "✅" if result["passed"] else "❌"
            logger.info(f"{i}. {status} {result['test_name']}")
            if result["message"]:
                logger.info(f"   {result['message']}")

        if self.failed == 0:
            logger.info("\n🎉 所有自动化测试通过！")
            logger.info("请继续完成手动验收测试项")
        else:
            logger.info(f"\n⚠️  有 {self.failed} 项测试失败，请检查！")

    async def run_all_tests(self):
        """
        运行所有自动化验收测试
        """
        logger.info("="*60)
        logger.info("🚀 开始P4.1阶段验收测试")
        logger.info("="*60)

        # 自动化测试
        await self.test_config_management()
        await self.test_dependency_injection()

        # 手动测试提示
        self.print_manual_tests()

        # 打印汇总
        self.print_summary()

        # 清理资源
        await cleanup_resources()


# ==================== 主函数 ====================

async def main():
    """
    验收测试主函数
    """
    tester = P41AcceptanceTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    """
    运行验收测试

    运行方式：
    ```bash
    cd D:\项目管理\PhytoOracle\backend
    python backend/tests/test_p4_1_acceptance.py
    ```
    """
    asyncio.run(main())
