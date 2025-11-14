"""
依赖注入模块 (Dependency Injection)

功能：
- 为FastAPI路由提供统一的依赖注入
- 管理数据库连接池、Redis客户端、VLM客户端等资源
- 实现单例模式，避免重复初始化

实现阶段：P4.1

架构说明：
- 所有依赖项都是FastAPI的Depends()依赖
- 使用全局变量缓存单例对象
- 提供优雅的资源清理接口

作者：AI Python Architect
日期：2025-11-15
"""

import logging
from pathlib import Path
from typing import Optional, Generator
from contextlib import asynccontextmanager

# asyncpg for PostgreSQL
try:
    import asyncpg
except ImportError:
    asyncpg = None

# redis for Redis
try:
    import redis.asyncio as redis
except ImportError:
    redis = None

# 核心配置
from backend.core.config import settings

# VLM客户端
from backend.infrastructure.llm.vlm_client import MultiProviderVLMClient
from backend.infrastructure.llm.llm_config import load_llm_config

# 知识库服务
from backend.services.knowledge_service import KnowledgeService

# 诊断服务
from backend.services.diagnosis_service import DiagnosisService

# 加权评分器
from backend.infrastructure.ontology.weighted_scorer import WeightedDiagnosisScorer

# 图片服务
from backend.services.image_service import ImageService
from backend.infrastructure.persistence.repositories.image_repo import ImageRepository
from backend.infrastructure.storage.local_storage import LocalImageStorage


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 全局单例对象缓存 ====================
# 用于缓存全局单例对象，避免重复初始化

_db_pool: Optional[asyncpg.Pool] = None
_redis_client: Optional[redis.Redis] = None
_vlm_client: Optional[MultiProviderVLMClient] = None
_knowledge_service: Optional[KnowledgeService] = None
_diagnosis_service: Optional[DiagnosisService] = None
_image_service: Optional[ImageService] = None


# ==================== 依赖注入函数 ====================

async def get_db_pool() -> Optional[asyncpg.Pool]:
    """
    获取PostgreSQL数据库连接池（依赖注入）

    Returns:
        asyncpg.Pool: PostgreSQL连接池对象
        None: 如果asyncpg未安装或连接失败

    注意：
    - 使用全局单例模式，避免重复创建连接池
    - 首次调用时创建连接池，后续调用返回已缓存的连接池
    - 如果连接失败，返回None（允许降级运行）

    使用示例：
    ```python
    from fastapi import Depends

    @app.get("/api/v1/test")
    async def test_db(pool: asyncpg.Pool = Depends(get_db_pool)):
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return {"result": result}
    ```
    """
    global _db_pool

    if _db_pool is not None:
        return _db_pool

    # 检查asyncpg是否已安装
    if asyncpg is None:
        logger.warning("asyncpg未安装，数据库连接池不可用")
        return None

    try:
        # 创建数据库连接池
        _db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=settings.DB_POOL_MIN_SIZE,
            max_size=settings.DB_POOL_MAX_SIZE,
        )
        logger.info(f"✅ PostgreSQL连接池初始化成功: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        return _db_pool
    except Exception as e:
        logger.error(f"❌ PostgreSQL连接池初始化失败: {e}")
        return None


async def get_redis_client() -> Optional[redis.Redis]:
    """
    获取Redis客户端（依赖注入）

    Returns:
        redis.Redis: Redis异步客户端对象
        None: 如果redis未安装或连接失败

    注意：
    - 使用全局单例模式
    - 首次调用时创建Redis客户端
    - 如果连接失败，返回None（允许降级运行）

    使用示例：
    ```python
    from fastapi import Depends

    @app.get("/api/v1/test")
    async def test_redis(r: redis.Redis = Depends(get_redis_client)):
        await r.set("test_key", "test_value")
        value = await r.get("test_key")
        return {"value": value.decode()}
    ```
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    # 检查redis是否已安装
    if redis is None:
        logger.warning("redis未安装，Redis客户端不可用")
        return None

    try:
        # 创建Redis客户端
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

        # 测试连接
        await _redis_client.ping()
        logger.info(f"✅ Redis客户端初始化成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return _redis_client
    except Exception as e:
        logger.error(f"❌ Redis客户端初始化失败: {e}")
        return None


async def get_vlm_client() -> MultiProviderVLMClient:
    """
    获取VLM客户端（依赖注入）

    Returns:
        MultiProviderVLMClient: VLM多提供商客户端对象

    注意：
    - 使用全局单例模式
    - 首次调用时创建VLM客户端
    - 从llm_config.json读取API密钥和配置

    使用示例：
    ```python
    from fastapi import Depends

    @app.post("/api/v1/test")
    async def test_vlm(vlm: MultiProviderVLMClient = Depends(get_vlm_client)):
        response = await vlm.call_with_fallback(
            prompt="识别图片内容",
            image_bytes=image_bytes,
            response_model=Q00Response
        )
        return response
    ```
    """
    global _vlm_client

    if _vlm_client is not None:
        return _vlm_client

    try:
        # 获取项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent
        config_path = project_root / "llm_config.json"

        # 创建VLM客户端（使用已有的初始化方式）
        _vlm_client = MultiProviderVLMClient(
            config_path=config_path,
            enable_cache=True,
        )

        logger.info(f"✅ VLM客户端初始化成功，默认提供商: {settings.VLM_PROVIDER}")
        return _vlm_client
    except Exception as e:
        logger.error(f"❌ VLM客户端初始化失败: {e}")
        raise


async def get_knowledge_service() -> KnowledgeService:
    """
    获取知识库服务（依赖注入）

    Returns:
        KnowledgeService: 知识库服务对象

    注意：
    - 使用全局单例模式
    - 首次调用时创建知识库服务并自动初始化
    - 读取knowledge_base目录下的JSON文件

    使用示例：
    ```python
    from fastapi import Depends

    @app.get("/api/v1/diseases")
    async def list_diseases(kb: KnowledgeService = Depends(get_knowledge_service)):
        diseases = kb.get_all_diseases()
        return {"diseases": diseases}
    ```
    """
    global _knowledge_service

    if _knowledge_service is not None:
        return _knowledge_service

    try:
        # 获取项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent
        kb_path = settings.KNOWLEDGE_BASE_PATH

        # 如果配置路径不是绝对路径，则相对于项目根目录
        if not kb_path.is_absolute():
            kb_path = project_root / kb_path

        # 创建知识库服务（auto_initialize=False，手动初始化）
        _knowledge_service = KnowledgeService(
            kb_path=kb_path,
            auto_initialize=False,  # 先不自动初始化
        )

        # 手动初始化知识库（同步方法）
        _knowledge_service.initialize()  # 注意：这是同步方法

        logger.info(f"✅ 知识库服务初始化成功，路径: {kb_path}")
        logger.info(f"   - 疾病数量: {len(_knowledge_service.get_all_diseases())}")
        return _knowledge_service
    except Exception as e:
        logger.error(f"❌ 知识库服务初始化失败: {e}")
        raise


async def get_diagnosis_service(
    vlm_client: MultiProviderVLMClient = None,
    knowledge_service: KnowledgeService = None,
) -> DiagnosisService:
    """
    获取诊断服务（依赖注入）

    Args:
        vlm_client: VLM客户端（可选，默认从依赖注入获取）
        knowledge_service: 知识库服务（可选，默认从依赖注入获取）

    Returns:
        DiagnosisService: 诊断服务对象

    注意：
    - 使用全局单例模式
    - 首次调用时创建诊断服务
    - 自动注入VLM客户端和知识库服务

    使用示例：
    ```python
    from fastapi import Depends

    @app.post("/api/v1/diagnose")
    async def diagnose(
        image: UploadFile,
        service: DiagnosisService = Depends(get_diagnosis_service)
    ):
        result = await service.diagnose(image_bytes=await image.read())
        return result
    ```
    """
    global _diagnosis_service

    if _diagnosis_service is not None:
        return _diagnosis_service

    try:
        # 注入依赖
        if vlm_client is None:
            vlm_client = await get_vlm_client()
        if knowledge_service is None:
            knowledge_service = await get_knowledge_service()

        # 创建加权评分器
        scorer = WeightedDiagnosisScorer()

        # 创建诊断服务
        _diagnosis_service = DiagnosisService(
            vlm_client=vlm_client,
            knowledge_service=knowledge_service,
            scorer=scorer,
        )

        logger.info("✅ 诊断服务初始化成功")
        return _diagnosis_service
    except Exception as e:
        logger.error(f"❌ 诊断服务初始化失败: {e}")
        raise


async def get_image_service() -> ImageService:
    """
    获取图片服务（依赖注入）

    Returns:
        ImageService: 图片服务对象

    注意：
    - 使用全局单例模式
    - 首次调用时创建图片服务
    - 自动注入存储路径和数据库路径

    使用示例：
    ```python
    from fastapi import Depends

    @app.post("/api/v1/images")
    async def upload_image(
        image: UploadFile,
        service: ImageService = Depends(get_image_service)
    ):
        result = service.save_image(
            image_bytes=await image.read(),
            flower_genus="Rosa"
        )
        return result
    ```
    """
    global _image_service

    if _image_service is not None:
        return _image_service

    try:
        # 获取项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent
        storage_path = settings.STORAGE_BASE_PATH

        # 如果配置路径不是绝对路径，则相对于项目根目录
        if not storage_path.is_absolute():
            storage_path = project_root / storage_path

        # 数据库路径
        db_path = project_root / "data" / "images.db"

        # 创建图片服务（使用storage_path和db_path参数）
        _image_service = ImageService(
            storage_path=storage_path,
            db_path=db_path,
        )

        logger.info(f"✅ 图片服务初始化成功，存储路径: {storage_path}")
        return _image_service
    except Exception as e:
        logger.error(f"❌ 图片服务初始化失败: {e}")
        raise


# ==================== 资源清理函数 ====================

async def cleanup_resources():
    """
    清理所有全局资源

    注意：
    - 应该在应用关闭时调用（FastAPI的lifespan事件）
    - 关闭数据库连接池、Redis客户端等资源

    使用示例（在main.py中）：
    ```python
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 启动时初始化资源
        yield
        # 关闭时清理资源
        await cleanup_resources()

    app = FastAPI(lifespan=lifespan)
    ```
    """
    global _db_pool, _redis_client, _vlm_client
    global _knowledge_service, _diagnosis_service, _image_service

    logger.info("🔄 开始清理全局资源...")

    # 关闭数据库连接池
    if _db_pool is not None:
        await _db_pool.close()
        logger.info("✅ PostgreSQL连接池已关闭")
        _db_pool = None

    # 关闭Redis客户端
    if _redis_client is not None:
        await _redis_client.close()
        logger.info("✅ Redis客户端已关闭")
        _redis_client = None

    # 清理其他单例对象
    _vlm_client = None
    _knowledge_service = None
    _diagnosis_service = None
    _image_service = None

    logger.info("✅ 全局资源清理完成")


# ==================== 测试函数 ====================

async def test_all_dependencies():
    """
    测试所有依赖注入是否正常工作

    测试项：
    1. 数据库连接池
    2. Redis客户端
    3. VLM客户端
    4. 知识库服务
    5. 诊断服务
    6. 图片服务

    使用示例：
    ```python
    import asyncio
    from backend.apps.api.deps import test_all_dependencies

    asyncio.run(test_all_dependencies())
    ```
    """
    print("\n" + "="*60)
    print("🧪 开始测试所有依赖注入...")
    print("="*60 + "\n")

    # 1. 测试数据库连接池
    print("1️⃣ 测试PostgreSQL连接池...")
    try:
        db_pool = await get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                print(f"   ✅ 数据库连接测试成功: SELECT 1 = {result}")
        else:
            print("   ⚠️  数据库连接池不可用（可能未安装asyncpg）")
    except Exception as e:
        print(f"   ❌ 数据库连接测试失败: {e}")

    # 2. 测试Redis客户端
    print("\n2️⃣ 测试Redis客户端...")
    try:
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.set("test_key", "test_value")
            value = await redis_client.get("test_key")
            print(f"   ✅ Redis连接测试成功: test_key = {value}")
        else:
            print("   ⚠️  Redis客户端不可用（可能未安装redis）")
    except Exception as e:
        print(f"   ❌ Redis连接测试失败: {e}")

    # 3. 测试VLM客户端
    print("\n3️⃣ 测试VLM客户端...")
    try:
        vlm_client = await get_vlm_client()
        print(f"   ✅ VLM客户端初始化成功")
        print(f"   - 已配置提供商: {list(vlm_client.providers.keys())}")
    except Exception as e:
        print(f"   ❌ VLM客户端初始化失败: {e}")

    # 4. 测试知识库服务
    print("\n4️⃣ 测试知识库服务...")
    try:
        kb_service = await get_knowledge_service()
        diseases = kb_service.get_all_diseases()
        print(f"   ✅ 知识库服务初始化成功")
        print(f"   - 疾病总数: {len(diseases)}")
        if diseases:
            print(f"   - 第一个疾病: {diseases[0].disease_id}")
    except Exception as e:
        print(f"   ❌ 知识库服务初始化失败: {e}")

    # 5. 测试诊断服务
    print("\n5️⃣ 测试诊断服务...")
    try:
        diagnosis_service = await get_diagnosis_service()
        print(f"   ✅ 诊断服务初始化成功")
    except Exception as e:
        print(f"   ❌ 诊断服务初始化失败: {e}")

    # 6. 测试图片服务
    print("\n6️⃣ 测试图片服务...")
    try:
        image_service = await get_image_service()
        print(f"   ✅ 图片服务初始化成功")
        print(f"   - 存储路径: {image_service.storage.base_path}")
    except Exception as e:
        print(f"   ❌ 图片服务初始化失败: {e}")

    print("\n" + "="*60)
    print("✅ 依赖注入测试完成！")
    print("="*60 + "\n")

    # 清理资源
    await cleanup_resources()


# ==================== 主函数 ====================

if __name__ == "__main__":
    """
    依赖注入测试主函数

    运行方式：
    ```bash
    cd D:\项目管理\PhytoOracle\backend
    python -m apps.api.deps
    ```
    """
    import asyncio
    asyncio.run(test_all_dependencies())
