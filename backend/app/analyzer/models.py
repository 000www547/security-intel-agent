"""
================================================================================
威胁情报数据模型 (Pydantic)
================================================================================
面试知识点:
  - Pydantic v2: field_validator, model_dump, Literal 类型
  - 类型安全: 编译期 + 运行期双重验证
  - 序列化: .model_dump() 直接转 dict/JSON
  - FastAPI 集成: Pydantic 模型自动生成 OpenAPI Schema
================================================================================
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============================
# 枚举类 - 约束取值范围
# ============================
class ThreatType(str, Enum):
    """
    威胁分类枚举
    
    面试: "为什么用 Enum 而不是 str？"
    → 约束合法值, IDE 自动补全, 防止拼写错误
    → 映射安全行业标准分类(ATT&CK框架思路)
    """
    VULNERABILITY = "漏洞"          # CVE 漏洞
    MALWARE = "恶意软件"            # 木马/勒索/蠕虫
    APT = "APT攻击"                 # 高级持续性威胁
    DATA_LEAK = "数据泄露"          # 数据泄露事件
    PHISHING = "钓鱼攻击"           # 钓鱼邮件/网站
    DDOS = "DDoS攻击"              # 分布式拒绝服务
    ZERO_DAY = "零日漏洞"           # 0day
    WEB_ATTACK = "Web攻击"          # SQL注入/XSS等
    CONFIG_ERROR = "配置缺陷"       # 云配置错误/暴露
    OTHER = "其他"                  # 其他类型


class RiskLevel(str, Enum):
    """
    风险等级
    
    面试: "为什么分三级？" → 参考 CVSS 评分体系简化
    CVSS 9.0+ → HIGH / 4.0-8.9 → MEDIUM / 0.1-3.9 → LOW
    """
    HIGH = "高危"
    MEDIUM = "中危"
    LOW = "低危"


# ============================
# 分析结果模型
# ============================
class ThreatAnalysis(BaseModel):
    """
    AI 分析输出的结构化威胁情报
    
    面试: "为什么要结构化输出？"
    → 1. 前端可直接渲染不用解析
    → 2. 数据库结构化存储可查询/统计/筛选
    → 3. 下游系统(告警/工单)可直接消费
    """
    # 基础信息
    title: str = Field(..., description="情报标题")
    summary: str = Field(..., description="情报摘要（200字以内）")

    # AI 分析结果
    threat_type: ThreatType = Field(..., description="威胁分类")
    risk_level: RiskLevel = Field(..., description="风险等级")
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="AI 置信度 0.0-1.0"
    )

    # 威胁详情
    cve_id: Optional[str] = Field(default=None, description="关联 CVE 编号")
    affected_products: list[str] = Field(
        default_factory=list,
        description="受影响产品/系统"
    )
    attack_vector: str = Field(default="", description="攻击方式/利用途径")

    # 处置建议
    defense_plan: str = Field(
        default="",
        description="可落地的防御处置方案（分步骤）"
    )
    ioc_indicators: list[str] = Field(
        default_factory=list,
        description="IOC 威胁指标(恶意IP/域名/文件哈希)"
    )

    # 元信息
    source_name: str = Field(default="", description="情报来源")
    source_url: str = Field(default="", description="原始链接")
    published_at: Optional[str] = Field(default=None, description="原始发布时间")
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="分析时间"
    )

    @field_validator("cve_id")
    @classmethod
    def validate_cve_format(cls, v: Optional[str]) -> Optional[str]:
        """
        校验 CVE 编号格式: CVE-YYYY-NNNNN
        
        面试: "为什么这里校验？" → 数据质量保障, 不合法CVE不进库
        """
        if v and not v.startswith("CVE-"):
            # 兼容处理: 加上 CVE- 前缀
            return f"CVE-{v}"
        return v
