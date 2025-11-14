"""
PhytoOracle FastAPI 应用主入口 (P4.1升级版)

功能：
- FastAPI 应用初始化
- CORS 中间件配置
- 全局异常处理器
- 路由注册（占位）
- 生命周期管理（lifespan）

实现阶段：P4.1

架构说明：
- 使用lifespan管理应用生命周期
- 统一异常处理（VLM异常、数据库异常、验证异常）
- 支持Swagger UI和ReDoc文档

作者：AI Python Architect
日期：2025-11-15
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# 依赖注入资源清理
from backend.apps.api.deps import cleanup_resources

# VLM异常
from backend.infrastructure.llm.vlm_exceptions import (
    VLMException,
    AllProvidersFailedException,
    ValidationException,
    ProviderUnavailableException,
)

# 知识库异常
from backend.infrastructure.ontology.exceptions import (
    KnowledgeBaseNotFoundError,
    KnowledgeBaseLoadError,
)

# 存储异常
from backend.infrastructure.storage.storage_exceptions import (
    StorageException,
    ImageDeleteError,
    InvalidImageFormat,
)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 应用生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动阶段：
    - 初始化全局资源（数据库、Redis、VLM客户端等）
    - 打印启动信息

    关闭阶段：
    - 清理全局资源
    - 关闭数据库连接池、Redis客户端
    """
    # ========== 启动阶段 ==========
    logger.info("🚀 PhytoOracle API 启动中...")
    logger.info(f"📝 项目名称: {app.title}")
    logger.info(f"📌 版本号: {app.version}")
    logger.info(f"📚 Swagger UI: http://localhost:8000/docs")
    logger.info(f"📚 ReDoc: http://localhost:8000/redoc")

    # 依赖注入会在首次调用时自动初始化资源，无需显式初始化
    logger.info("✅ PhytoOracle API 启动完成！")

    yield

    # ========== 关闭阶段 ==========
    logger.info("🔄 PhytoOracle API 关闭中...")
    await cleanup_resources()
    logger.info("✅ PhytoOracle API 已关闭")


# ==================== 创建 FastAPI 应用实例 ====================

app = FastAPI(
    title="PhytoOracle API",
    description="""
    ## 基于本体建模的花卉疾病诊断系统 API

    ### 核心功能
    - 🌸 **疾病诊断**: 上传花卉图片，获取疾病诊断结果
    - 📚 **知识库管理**: CRUD操作疾病知识库
    - 🧬 **本体管理**: 查询特征本体定义
    - 🖼️ **图片管理**: 图片列表查询和准确性标注
    - 📊 **历史记录**: 查询诊断历史

    ### 技术栈
    - FastAPI: Web框架
    - PostgreSQL: 数据库
    - Redis: 缓存
    - Qwen VL / GPT-4V: VLM提供商

    ### 版本信息
    - 当前版本: v1.0.0
    - 最后更新: 2025-11-15
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,  # 生命周期管理
)


# ==================== CORS 中间件配置 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 开发服务器
        "http://localhost:8501",  # Streamlit 开发服务器
        "http://localhost:5173",  # Vite 开发服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法（GET, POST, PUT, DELETE等）
    allow_headers=["*"],  # 允许所有请求头
)


# ==================== 全局异常处理器 ====================

@app.exception_handler(VLMException)
async def vlm_exception_handler(request: Request, exc: VLMException):
    """
    VLM异常处理器

    处理VLM相关的所有异常：
    - AllProvidersFailedException: 所有VLM提供商都失败
    - ValidationException: VLM响应验证失败
    - ProviderUnavailableException: VLM提供商不可用
    """
    logger.error(f"VLM异常: {exc}")

    # 根据异常类型返回不同的状态码
    if isinstance(exc, AllProvidersFailedException):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_code = "VLM_SERVICE_UNAVAILABLE"
    elif isinstance(exc, ValidationException):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_code = "VLM_INVALID_RESPONSE"
    elif isinstance(exc, ProviderUnavailableException):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "VLM_PROVIDER_UNAVAILABLE"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "VLM_ERROR"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_code,
            "message": str(exc),
            "detail": "VLM服务暂时不可用，请稍后重试",
        },
    )


@app.exception_handler(KnowledgeBaseNotFoundError)
async def knowledge_base_not_found_handler(request: Request, exc: KnowledgeBaseNotFoundError):
    """
    知识库未找到异常处理器
    """
    logger.error(f"知识库异常: {exc}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "KNOWLEDGE_BASE_NOT_FOUND",
            "message": str(exc),
            "detail": "请检查知识库文件是否存在",
        },
    )


@app.exception_handler(KnowledgeBaseLoadError)
async def knowledge_base_load_error_handler(request: Request, exc: KnowledgeBaseLoadError):
    """
    知识库加载错误异常处理器
    """
    logger.error(f"知识库加载异常: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "KNOWLEDGE_BASE_LOAD_ERROR",
            "message": str(exc),
            "detail": "知识库加载失败，请联系管理员",
        },
    )


@app.exception_handler(StorageException)
async def storage_exception_handler(request: Request, exc: StorageException):
    """
    图片存储异常处理器

    处理图片存储相关的所有异常：
    - ImageDeleteError: 图片删除失败
    - InvalidImageFormat: 无效的图片格式
    """
    logger.error(f"图片存储异常: {exc}")

    # 根据异常类型返回不同的状态码
    if isinstance(exc, ImageDeleteError):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "IMAGE_DELETE_ERROR"
    elif isinstance(exc, InvalidImageFormat):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "INVALID_IMAGE_FORMAT"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "IMAGE_STORAGE_ERROR"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_code,
            "message": str(exc),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理器

    处理FastAPI的请求验证错误（Pydantic验证）
    """
    logger.error(f"请求验证异常: {exc}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Pydantic验证异常处理器

    处理Pydantic模型的验证错误
    """
    logger.error(f"Pydantic验证异常: {exc}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "数据验证失败",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器

    捕获所有未被其他处理器捕获的异常
    """
    logger.error(f"未知异常: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if app.debug else "请联系管理员",
        },
    )


# ==================== 基础路由 ====================

@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    """
    根路径 - API健康检查

    Returns:
        Dict: API基本信息
    """
    return {
        "message": "PhytoOracle API is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    健康检查接口

    用于负载均衡器、容器编排工具（如Kubernetes）检测服务健康状态

    Returns:
        Dict: 健康状态
    """
    return {
        "status": "ok",
        "message": "Service is healthy",
    }


@app.get("/ping", tags=["Health"])
async def ping() -> Dict[str, str]:
    """
    Ping接口

    用于简单的连通性测试

    Returns:
        Dict: Pong响应
    """
    return {"ping": "pong"}


# ==================== 路由注册（P4.2-P4.5实现） ====================

# 注意：以下路由将在P4.2-P4.5阶段实现
# from backend.apps.api.routers import diagnosis, knowledge, ontology, images

# app.include_router(diagnosis.router, prefix="/api/v1", tags=["Diagnosis"])
# app.include_router(knowledge.router, prefix="/api/v1", tags=["Knowledge"])
# app.include_router(ontology.router, prefix="/api/v1", tags=["Ontology"])
# app.include_router(images.router, prefix="/api/v1", tags=["Images"])


# ==================== 主函数 ====================

if __name__ == "__main__":
    """
    直接运行主函数启动服务器

    运行方式：
    ```bash
    cd D:\项目管理\PhytoOracle\backend
    python -m apps.api.main
    ```

    或使用uvicorn：
    ```bash
    cd D:\项目管理\PhytoOracle\backend
    uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
    ```
    """
    import uvicorn

    logger.info("🚀 启动FastAPI服务器...")
    logger.info("📝 运行方式: python -m apps.api.main")
    logger.info("📚 访问文档: http://localhost:8000/docs")

    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info",
    )
