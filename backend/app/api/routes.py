"""
================================================================================
FastAPI RESTful API 路由
================================================================================
面试知识点:
  - RESTful 设计: GET/POST/PUT/DELETE 语义化
  - 异步接口: async def + await 非阻塞 I/O
  - Pydantic + FastAPI: 自动参数校验 + OpenAPI 文档
  - CORS: 跨域资源共享, 前端独立部署时必需
  - 依赖注入: Depends() 注入共享资源(数据库连接)
================================================================================
"""
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from app.pipeline import SecurityPipeline
from app.db.database import Database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["安全情报"])

# 全局实例(由 main.py 初始化)
_pipeline: Optional[SecurityPipeline] = None
_database: Optional[Database] = None


def init_router(pipeline: SecurityPipeline, database: Database):
    """初始化路由依赖"""
    global _pipeline, _database
    _pipeline = pipeline
    _database = database


# ============================
# 情报查询 API
# ============================
@router.get("/intel", summary="获取情报列表（分页+筛选）")
async def list_intel(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    threat_type: Optional[str] = Query(None, description="威胁类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
):
    """
    分页查询情报列表
    
    面试: "FastAPI 的 Query 做什么？" → 自动校验 + 生成 OpenAPI 文档
    """
    return _database.query_all(
        page=page,
        page_size=page_size,
        risk_level=risk_level,
        threat_type=threat_type,
        keyword=keyword,
    )


@router.get("/intel/{intel_id}", summary="获取情报详情")
async def get_intel(intel_id: int):
    """获取单条情报详情"""
    result = _database.query_by_id(intel_id)
    if not result:
        raise HTTPException(status_code=404, detail="情报不存在")
    return result


# ============================
# 统计概览 API
# ============================
@router.get("/stats", summary="获取统计概览")
async def get_stats():
    """获取全局统计: 总数、风险分布、类型分布、近7天趋势"""
    return _database.get_stats()


# ============================
# 采集触发 API
# ============================
@router.post("/pipeline/run", summary="手动触发情报采集分析")
async def trigger_pipeline():
    """
    手动触发一次完整流水线
    
    面试: "为什么用 POST 而不是 GET？" → POST 有副作用(写入数据库)
    """
    logger.info("[API] 手动触发情报采集流水线")
    try:
        result = _pipeline.run()
        return JSONResponse(content={
            "code": 0,
            "message": "流水线执行完成",
            "data": result,
        })
    except Exception as e:
        logger.error(f"[API] 流水线执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================
# 健康检查 API
# ============================
@router.get("/health", summary="服务健康检查")
async def health_check():
    """
    健康检查端点
    
    面试: "为什么需要健康检查？"
    → K8s/Docker 用 liveness/readiness probe 判断服务状态
    """
    return {"status": "ok", "service": "security-intel-agent"}
