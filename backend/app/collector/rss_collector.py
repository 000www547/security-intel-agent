"""
================================================================================
RSS 情报采集模块
================================================================================
面试知识点:
  - feedparser: Python 最流行的 RSS/Atom 解析库
  - HTTP 请求: httpx (比 requests 更快, 支持异步)
  - 数据清洗: HTML标签过滤, 空白字符处理, 日期格式化
  - 去重策略: 基于 URL 的集合去重 (O(1) 查找)
  - 异常处理: try/except 保证单个源失败不影响整体
================================================================================
"""
import logging
from datetime import datetime
from typing import Optional

import feedparser
import httpx
from dateutil import parser as date_parser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================
# 数据模型 - 定义采集结果的统一格式
# ============================
class RawIntelItem(BaseModel):
    """
    从 RSS 源采集来的原始情报条目
    Pydantic BaseModel: 自动类型校验 + 序列化
    面试: "为什么用 Pydantic？" → 类型安全, 自动校验, FastAPI 原生支持
    """
    title: str = Field(..., description="情报标题")
    summary: str = Field(default="", description="情报摘要")
    source_name: str = Field(default="", description="来源名称")
    source_url: str = Field(..., description="原始链接")
    published_at: Optional[str] = Field(default=None, description="发布时间")


class CollectResult(BaseModel):
    """采集结果汇总"""
    total_collected: int = Field(default=0, description="采集总数")
    items: list[RawIntelItem] = Field(default_factory=list, description="情报列表")
    sources: list[str] = Field(default_factory=list, description="成功的来源")
    errors: list[str] = Field(default_factory=list, description="失败的来源")


# ============================
# 核心采集函数
# ============================
class RSSCollector:
    """
    RSS 采集器
    
    面试: "为什么用类而不是函数？"
    → 状态管理(config), 可测试性(可 mock), 可扩展(子类化)
    """

    def __init__(self, sources: list[dict], timeout: int = 15, max_items: int = 10):
        """
        Args:
            sources: RSS源配置列表 [{"name": "FreeBuf", "url": "..."}]
            timeout: 请求超时秒数
            max_items: 每个源最多取多少条
        """
        self.sources = sources
        self.timeout = timeout
        self.max_items = max_items

    def collect(self) -> CollectResult:
        """
        执行全量采集
        
        面试: "为什么不并发请求？"
        → feedparser 本身是同步的, 用 threading 或 asyncio 可提速
          这里保持简单先用同步, 面试时可提到优化方向
        """
        result = CollectResult()
        seen_urls: set[str] = set()  # URL 去重集合 - 面试: "如何去重？" → 用 set

        for source in self.sources:
            try:
                items = self._fetch_source(source)
                for item in items:
                    # 去重: 基于 source_url
                    if item.source_url not in seen_urls:
                        seen_urls.add(item.source_url)
                        result.items.append(item)
                result.sources.append(source["name"])
                logger.info(f"[采集] {source['name']}: 获取 {len(items)} 条")

            except Exception as e:
                # 面试: "为什么单个源失败不影响整体？" → 容错设计, 降级策略
                error_msg = f"{source['name']}: {str(e)}"
                result.errors.append(error_msg)
                logger.error(f"[采集失败] {error_msg}")

        result.total_collected = len(result.items)
        logger.info(f"[采集完成] 共 {result.total_collected} 条, "
                     f"成功 {len(result.sources)} 个源, "
                     f"失败 {len(result.errors)} 个源")
        return result

    def _fetch_source(self, source: dict) -> list[RawIntelItem]:
        """抓取单个 RSS 源"""
        resp = httpx.get(
            source["url"],
            timeout=self.timeout,
            headers={
                "User-Agent": "Security-Intel-Agent/1.0 (Threat Intelligence Collector)"
            }
        )
        resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        items: list[RawIntelItem] = []

        for entry in feed.entries[: self.max_items]:
            item = RawIntelItem(
                title=self._clean_text(entry.get("title", "")),
                summary=self._extract_summary(entry),
                source_name=source["name"],
                source_url=entry.get("link", ""),
                published_at=self._parse_date(entry),
            )
            items.append(item)

        return items

    # ============================
    # 数据清洗辅助方法
    # ============================
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        清洗文本: HTML标签 + 空白字符
        
        面试: "为什么不用 re.sub(r'<[^>]+>', '', text)？"
        → 正则处理 HTML 有隐患(嵌套标签), 用 HTMLParser 更安全
        """
        import re
        from html import unescape
        # 去除 HTML 标签
        clean = re.sub(r"<[^>]+>", "", text)
        # HTML 实体解码
        clean = unescape(clean)
        # 合并空白
        clean = " ".join(clean.split())
        return clean.strip()

    @staticmethod
    def _extract_summary(entry: dict) -> str:
        """从 RSS entry 中提取摘要"""
        summary = entry.get("summary", "") or entry.get("description", "")
        return RSSCollector._clean_text(summary)[:500]  # 截断过长摘要

    @staticmethod
    def _parse_date(entry: dict) -> Optional[str]:
        """
        日期解析与标准化
        
        面试: "不同 RSS 源的日期格式不一样怎么办？"
        → dateutil.parser 自动识别多种格式
        → 统一输出 ISO 8601 标准格式
        """
        date_str = entry.get("published", "") or entry.get("updated", "")
        if not date_str:
            return None
        try:
            dt = date_parser.parse(date_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OverflowError):
            return date_str  # 解析失败则返回原始值
