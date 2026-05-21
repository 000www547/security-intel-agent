"""
================================================================================
飞书/钉钉消息推送模块
================================================================================
面试知识点:
  - Webhook 推送: 服务端主动推送消息到 IM
  - 飞书卡片消息: JSON Schema 定义交互式卡片
  - 消息模板: 提取高威胁情报, 精简展示
  - 扩展性: 新增推送渠道只需实现相同接口
================================================================================
"""
import logging
from typing import Optional

import httpx

from app.analyzer.models import ThreatAnalysis, RiskLevel

logger = logging.getLogger(__name__)


# ============================
# 飞书卡片消息模板
# ============================
def build_feishu_card(analysis: ThreatAnalysis) -> dict:
    """
    构建飞书交互式卡片消息
    
    飞书卡片 JSON Schema:
    - header: 标题区 (颜色按风险等级区分)
    - elements: 内容区 (markdown/fields)
    - config: 配置(是否可更新)
    """
    # 风险等级颜色映射
    color_map = {
        RiskLevel.HIGH: "red",
        RiskLevel.MEDIUM: "orange",
        RiskLevel.LOW: "green",
    }

    # 威胁类型图标
    icon_map = {
        "漏洞": "🔴", "恶意软件": "🦠", "APT攻击": "🎯",
        "数据泄露": "💾", "钓鱼攻击": "🎣", "DDoS攻击": "🌊",
        "零日漏洞": "☠️", "Web攻击": "🌐", "配置缺陷": "⚙️",
    }

    color = color_map.get(analysis.risk_level, "grey")
    icon = icon_map.get(analysis.threat_type.value, "📌")

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"{icon} [{analysis.risk_level.value}] {analysis.title[:50]}"
            },
            "template": color,
        },
        "elements": [
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**威胁类型**\n{analysis.threat_type.value}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**风险等级**\n{analysis.risk_level.value}"}},
                ],
            },
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**CVE编号**\n{analysis.cve_id or '暂无'}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**AI置信度**\n{analysis.confidence:.0%}"}},
                ],
            },
            {
                "tag": "markdown",
                "content": f"**📝 摘要**\n{analysis.summary[:200]}"
            },
        ],
    }

    # 高危情报增加防御方案
    if analysis.risk_level == RiskLevel.HIGH and analysis.defense_plan:
        card["elements"].append({
            "tag": "markdown",
            "content": f"**🛡️ 防御方案**\n{analysis.defense_plan[:300]}"
        })

    # 添加来源链接
    if analysis.source_url:
        card["elements"].append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查看原文"},
                "type": "primary",
                "url": analysis.source_url,
            }],
        })

    return card


def build_daily_summary_card(
    total: int, high_count: int, medium_count: int, low_count: int,
    date_str: str,
) -> dict:
    """构建每日汇总卡片"""
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📊 安全情报日报 - {date_str}"},
            "template": "blue",
        },
        "elements": [
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**今日采集**\n{total} 条"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**🔴 高危**\n{high_count} 条"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**🟠 中危**\n{medium_count} 条"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**🟢 低危**\n{low_count} 条"}},
                ],
            }
        ],
    }


# ============================
# 推送引擎
# ============================
class FeishuNotifier:
    """飞书推送器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_card(self, card: dict) -> bool:
        """
        发送飞书卡片消息
        
        面试: "飞书 Webhook 怎么发？"
        → POST JSON { "msg_type": "interactive", "card": {...} }
        → 签名校验(加签模式需 HMAC-SHA256)
        """
        try:
            resp = httpx.post(
                self.webhook_url,
                json={"msg_type": "interactive", "card": card},
                timeout=10,
            )
            result = resp.json()
            if result.get("code") == 0:
                logger.info("[飞书] 推送成功")
                return True
            else:
                logger.error(f"[飞书] 推送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"[飞书] 异常: {e}")
            return False

    def send_high_risk_alerts(self, analyses: list[ThreatAnalysis]) -> int:
        """
        推送高危情报告警

        Returns:
            成功推送的条数
        """
        high_risk = [a for a in analyses if a.risk_level == RiskLevel.HIGH]
        sent = 0
        for analysis in high_risk[:5]:  # 最多推送5条，避免消息轰炸
            card = build_feishu_card(analysis)
            if self.send_card(card):
                sent += 1
        return sent

    def send_daily_report(
        self, total: int, high: int, medium: int, low: int, date_str: str
    ) -> bool:
        """发送每日汇总报告"""
        card = build_daily_summary_card(total, high, medium, low, date_str)
        return self.send_card(card)
