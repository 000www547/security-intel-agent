"""
================================================================================
FastAPI 应用入口
================================================================================
面试知识点:
  - FastAPI: Python 最快的 Web 框架之一(基于 Starlette + Pydantic)
  - lifespan: 应用生命周期管理(启动时初始化, 关闭时清理)
  - CORS 中间件: 解决前后端分离的跨域问题
  - uvicorn: ASGI 服务器, 支持异步(面试常考 WSGI vs ASGI)
================================================================================
"""
import logging
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.routes import router, init_router
from app.pipeline import SecurityPipeline
from app.db.database import Database

# ============================
# 日志配置
# ============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================
# 全局实例
# ============================
pipeline: SecurityPipeline = None
database: Database = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    面试: "lifespan vs @app.on_event？"
    → lifespan 是 FastAPI 推荐的新方式(取代已废弃的 on_event)
    → async context manager: yield 前是 startup, yield 后是 shutdown
    """
    global pipeline, database

    logger.info("=" * 50)
    logger.info("Security-Intel-Agent 启动中...")

    # 确定配置文件路径
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    if not os.path.isabs(config_path):
        # 相对路径 → 相对于 backend 目录
        config_path = str(Path(__file__).parent.parent / config_path)
    logger.info(f"配置文件: {config_path}")

    # 初始化
    pipeline = SecurityPipeline(config_path)
    database = pipeline.database
    init_router(pipeline, database)

    logger.info("Security-Intel-Agent 启动完成!")
    logger.info("API 文档: http://localhost:8000/docs")
    logger.info("=" * 50)

    yield  # 服务运行中...

    # 清理
    logger.info("Security-Intel-Agent 关闭中...")


# ============================
# 创建 FastAPI 应用
# ============================
app = FastAPI(
    title="Security-Intel-Agent",
    description="AI 驱动的网络安全威胁情报分析平台",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",         # Swagger UI
    redoc_url="/redoc",       # ReDoc
)

# ============================
# CORS 中间件
# ============================
# 面试: "什么是 CORS？" → 浏览器同源策略的限制, 需服务端设置允许跨域头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],               # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


# ============================
# 直接运行入口
# ============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,          # 开发模式热重载
    )
