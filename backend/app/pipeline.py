"""
================================================================================
情报采集 → 分析 → 存储 自动化流水线
================================================================================
面试知识点:
  - 流水线模式(Pipeline Pattern): 串联多个处理阶段
  - 单一职责: 每个阶段独立可测试
  - 容错设计: 任一步骤失败不阻塞后续
================================================================================
"""
import logging
from datetime import datetime

import yaml

from app.collector.rss_collector import RSSCollector, CollectResult
from app.analyzer.threat_analyzer import ThreatAnalyzer
from app.analyzer.models import ThreatAnalysis
from app.db.database import Database
from app.notifier.feishu import FeishuNotifier

logger = logging.getLogger(__name__)


class SecurityPipeline:
    """
    安全情报处理流水线
    
    流程:
    collect() → analyze() → store() → notify()
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.collector = RSSCollector(
            sources=self.config["collect"]["rss_sources"],
            timeout=self.config["collect"].get("request_timeout", 15),
            max_items=self.config["collect"].get("max_items_per_source", 10),
        )
        self.analyzer = ThreatAnalyzer(llm_config=self.config["llm"])
        self.database = Database(db_path=self.config["database"]["path"])
        self._notifier = None  # 懒加载（没有 webhook 则不初始化）

    @property
    def notifier(self) -> FeishuNotifier | None:
        if self._notifier is None:
            webhook = self.config["notify"].get("feishu_webhook", "")
            if webhook:
                self._notifier = FeishuNotifier(webhook)
        return self._notifier

    def run(self) -> dict:
        """
        执行完整流水线
        
        Returns:
            {
                "collected": int,      # 采集数量
                "analyzed": int,       # 分析成功数量
                "stored": int,         # 入库数量(去重后)
                "errors": list[str],   # 错误列表
                "high_risk": int,      # 高危数量
                "medium_risk": int,    # 中危数量
                "low_risk": int,       # 低危数量
            }
        """
        result = {
            "collected": 0, "analyzed": 0, "stored": 0,
            "errors": [], "high_risk": 0, "medium_risk": 0, "low_risk": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # ---- 阶段1: 采集 ----
        logger.info("=" * 50)
        logger.info("[流水线] 阶段1/4: 情报采集")
        collect_result = self.collector.collect()
        result["collected"] = collect_result.total_collected
        result["errors"].extend(collect_result.errors)

        if not collect_result.items:
            logger.warning("[流水线] 没有采集到任何情报, 结束")
            return result

        # ---- 阶段2: AI 分析 ----
        logger.info("[流水线] 阶段2/4: AI 威胁分析")
        analyses = self.analyzer.analyze_batch(collect_result.items)
        result["analyzed"] = len(analyses)

        # ---- 阶段3: 入库 ----
        logger.info("[流水线] 阶段3/4: 数据持久化")
        stored_count = self.database.insert_batch(analyses)
        result["stored"] = stored_count

        # 统计风险分布
        result["high_risk"] = sum(1 for a in analyses if a.risk_level.value == "高危")
        result["medium_risk"] = sum(1 for a in analyses if a.risk_level.value == "中危")
        result["low_risk"] = sum(1 for a in analyses if a.risk_level.value == "低危")

        # ---- 阶段4: 推送 ----
        logger.info("[流水线] 阶段4/4: 消息推送")
        if self.notifier:
            sent = self.notifier.send_high_risk_alerts(analyses)
            self.notifier.send_daily_report(
                result["stored"],
                result["high_risk"],
                result["medium_risk"],
                result["low_risk"],
                datetime.now().strftime("%Y-%m-%d"),
            )
            result["notified"] = sent
        else:
            logger.info("[流水线] 未配置推送渠道, 跳过推送")

        logger.info(f"[流水线] 完成! 采集{result['collected']} → "
                     f"分析{result['analyzed']} → 入库{result['stored']}")
        return result

    @staticmethod
    def _load_config(path: str) -> dict:
        """加载 YAML 配置"""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
