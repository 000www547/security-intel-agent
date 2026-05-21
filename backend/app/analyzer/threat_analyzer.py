"""
================================================================================
AI 威胁分析引擎 - LangChain + DeepSeek
================================================================================
面试知识点:
  - LangChain ChatModel: 统一大模型调用接口
  - ChatPromptTemplate: 模板化 prompt 管理
  - PydanticOutputParser: 结构化输出解析
  - Chain: prompt → llm → parser 流水线
  - 失败处理: 重试 + 降级策略
================================================================================
"""
import json
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError

from .models import ThreatAnalysis, ThreatType, RiskLevel
from .prompts import SECURITY_ANALYST_SYSTEM, SECURITY_ANALYST_USER_TEMPLATE
from app.collector.rss_collector import RawIntelItem

logger = logging.getLogger(__name__)


class ThreatAnalyzer:
    """
    威胁情报 AI 分析器
    
    面试: "LangChain 在你的项目中做了什么？"
    → 1. 统一大模型调用(ChatOpenAI 兼容 DeepSeek)
    → 2. Prompt 模板管理(复用+可维护)
    → 3. 结构化输出解析(PydanticOutputParser 直接输出对象)
    → 4. Chain 编排(prompt | model | parser)
    """

    def __init__(self, llm_config: dict):
        """
        Args:
            llm_config: 大模型配置
                {
                    "api_key": "sk-xxx",
                    "base_url": "https://api.deepseek.com/v1",
                    "model_name": "deepseek-chat",
                    "temperature": 0.3,
                    "max_tokens": 2048
                }
        """
        self.llm_config = llm_config
        self._model = None  # 懒加载
        self._parser = PydanticOutputParser(pydantic_object=ThreatAnalysis)

    @property
    def model(self) -> ChatOpenAI:
        """
        懒加载 ChatOpenAI 实例
        
        面试: "为什么 DeepSeek 用 ChatOpenAI？"
        → DeepSeek API 兼容 OpenAI SDK 格式
        → LangChain 的 ChatOpenAI 通过 base_url 可指向任意兼容服务
        → 这就是设计模式的"适配器模式"
        """
        if self._model is None:
            self._model = ChatOpenAI(
                api_key=self.llm_config["api_key"],
                base_url=self.llm_config["base_url"],
                model=self.llm_config.get("model_name", "deepseek-chat"),
                temperature=self.llm_config.get("temperature", 0.3),
                max_tokens=self.llm_config.get("max_tokens", 2048),
            )
        return self._model

    def analyze(self, raw_item: RawIntelItem) -> Optional[ThreatAnalysis]:
        """
        分析单条情报

        面试: "这条 Chain 的流程是什么？"
        → RawIntelItem → 构造 prompt → 调用 LLM → 解析 JSON → ThreatAnalysis

        Args:
            raw_item: 原始情报条目

        Returns:
            分析结果，失败返回 None（不中断整体流程）
        """
        try:
            # 1. 构造消息模板
            prompt = ChatPromptTemplate.from_messages([
                ("system", SECURITY_ANALYST_SYSTEM),
                ("human", SECURITY_ANALYST_USER_TEMPLATE),
            ])

            # 2. 填充模板变量
            messages = prompt.format_messages(
                source_name=raw_item.source_name,
                published_at=raw_item.published_at or "未知",
                source_url=raw_item.source_url,
                title=raw_item.title,
                summary=raw_item.summary,
            )

            # 3. 调用 LLM
            response = self.model.invoke(messages)
            content = response.content

            logger.debug(f"[分析] LLM 原始输出: {content[:200]}...")

            # 4. 解析 JSON 输出
            analysis = self._parse_response(content, raw_item)
            return analysis

        except ValidationError as e:
            logger.warning(f"[分析失败-校验] {raw_item.title[:30]}: {e}")
            return None
        except Exception as e:
            logger.error(f"[分析失败-异常] {raw_item.title[:30]}: {e}")
            return None

    def analyze_batch(self, items: list[RawIntelItem]) -> list[ThreatAnalysis]:
        """
        批量分析

        面试: "为什么不并发调用？"
        → 当前同步版本保持简单, 生产环境可用 asyncio.gather 并发
        → 注意 API rate limit, 加 Semaphore 控制并发数

        Returns:
            分析成功的列表（失败的自动过滤）
        """
        results = []
        total = len(items)

        for i, item in enumerate(items, 1):
            logger.info(f"[分析进度] {i}/{total} - {item.title[:30]}...")
            analysis = self.analyze(item)
            if analysis:
                results.append(analysis)

        logger.info(f"[分析完成] {len(results)}/{total} 条成功")
        return results

    def _parse_response(
        self, content: str, raw_item: RawIntelItem
    ) -> ThreatAnalysis:
        """
        解析 LLM 输出的 JSON

        面试: "LLM 输出的 JSON 可能有格式问题怎么办？"
        → 1. 提取 JSON 块(处理 markdown ```json ... ``` 包裹)
        → 2. json.loads 解析
        → 3. Pydantic 校验
        → 4. 补充原始信息
        """
        # 提取 JSON 块 - 处理 markdown 代码块包裹
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content)

        # 补全元信息
        data["source_name"] = data.get("source_name", raw_item.source_name)
        data["source_url"] = data.get("source_url", raw_item.source_url)
        data["published_at"] = data.get("published_at", raw_item.published_at)

        # Pydantic 校验
        return ThreatAnalysis(**data)
