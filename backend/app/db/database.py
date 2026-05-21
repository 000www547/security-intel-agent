"""
================================================================================
SQLite 数据持久化模块
================================================================================
面试知识点:
  - SQLite: 零配置嵌入式数据库, 适合中小型应用
  - sqlite3 标准库: Python 内置，无需额外安装
  - 唯一索引去重: INSERT OR IGNORE + UNIQUE 约束
  - 分页查询: LIMIT + OFFSET 实现
  - 统计聚合: COUNT + GROUP BY 做数据统计
  - 为什么不用 ORM？轻型项目 sqlite3 足够，避免过度工程
================================================================================
"""
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from contextlib import contextmanager

from app.analyzer.models import ThreatAnalysis, ThreatType, RiskLevel

logger = logging.getLogger(__name__)


# ============================
# 建表 SQL
# ============================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS threat_intel (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    summary         TEXT    DEFAULT '',
    threat_type     TEXT    NOT NULL DEFAULT '其他',
    risk_level      TEXT    NOT NULL DEFAULT '低危',
    confidence      REAL    DEFAULT 0.8,
    cve_id          TEXT    DEFAULT NULL,
    affected_products TEXT  DEFAULT '[]',
    attack_vector   TEXT    DEFAULT '',
    defense_plan    TEXT    DEFAULT '',
    ioc_indicators  TEXT    DEFAULT '[]',
    source_name     TEXT    DEFAULT '',
    source_url      TEXT    NOT NULL UNIQUE,  -- 唯一约束, 防止重复入库
    published_at    TEXT    DEFAULT NULL,
    analyzed_at     TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_risk_level   ON threat_intel(risk_level);
CREATE INDEX IF NOT EXISTS idx_threat_type  ON threat_intel(threat_type);
CREATE INDEX IF NOT EXISTS idx_published_at ON threat_intel(published_at);
"""


class Database:
    """
    SQLite 数据库管理类

    面试: "为什么用 contextmanager？"
    → 自动管理连接和事务, with 语句保证 commit/close
    → 异常时自动 rollback
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库: 建表 + 索引"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_conn() as conn:
            conn.executescript(CREATE_TABLE_SQL)
            logger.info(f"[数据库] 初始化完成: {self.db_path}")

    @contextmanager
    def _get_conn(self):
        """
        获取数据库连接 (上下文管理器)
        
        面试: "sqlite3 的隔离级别是什么？"
        → 默认 DEFERRED, 写操作升级为 IMMEDIATE
        → WAL 模式适合并发读写
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典式行对象
        conn.execute("PRAGMA journal_mode=WAL")  # WAL 模式提高并发
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ============================
    # 写入操作
    # ============================
    def insert(self, item: ThreatAnalysis) -> bool:
        """
        插入一条情报（自动去重）

        面试: "INSERT OR IGNORE 的去重原理？"
        → UNIQUE 约束冲突时不报错不插入, 返回 0 行
        → 比先 SELECT 再 INSERT 少一次 DB 交互

        Returns:
            True 表示插入成功，False 表示已存在（去重跳过）
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO threat_intel
                    (title, summary, threat_type, risk_level, confidence,
                     cve_id, affected_products, attack_vector, defense_plan,
                     ioc_indicators, source_name, source_url,
                     published_at, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.title,
                    item.summary,
                    item.threat_type.value,
                    item.risk_level.value,
                    item.confidence,
                    item.cve_id,
                    json.dumps(item.affected_products, ensure_ascii=False),
                    item.attack_vector,
                    item.defense_plan,
                    json.dumps(item.ioc_indicators, ensure_ascii=False),
                    item.source_name,
                    item.source_url,
                    item.published_at,
                    item.analyzed_at,
                ),
            )
            inserted = cursor.rowcount > 0
            if inserted:
                logger.debug(f"[入库] {item.title[:30]}")
            return inserted

    def insert_batch(self, items: list[ThreatAnalysis]) -> int:
        """
        批量插入

        Returns:
            成功插入的数量
        """
        count = 0
        for item in items:
            if self.insert(item):
                count += 1
        logger.info(f"[批量入库] {count}/{len(items)} 条新增")
        return count

    # ============================
    # 查询操作
    # ============================
    def query_all(
        self,
        page: int = 1,
        page_size: int = 20,
        risk_level: Optional[str] = None,
        threat_type: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict:
        """
        分页查询情报列表

        面试: "SQL 注入怎么防？"
        → 参数化查询(占位符 ?)，不是字符串拼接
        → 但动态 ORDER BY / LIKE 需要白名单校验

        面试: "分页怎么实现？"
        → LIMIT + OFFSET, 前端传 page + page_size
        → 返回 total 让前端计算总页数
        """
        conditions = []
        params = []

        if risk_level:
            conditions.append("risk_level = ?")
            params.append(risk_level)
        if threat_type:
            conditions.append("threat_type = ?")
            params.append(threat_type)
        if keyword:
            conditions.append("(title LIKE ? OR summary LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        offset = (page - 1) * page_size

        with self._get_conn() as conn:
            # 查询总数
            total_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM threat_intel WHERE {where_clause}",
                params,
            ).fetchone()
            total = total_row["cnt"]

            # 分页查询
            rows = conn.execute(
                f"""
                SELECT * FROM threat_intel
                WHERE {where_clause}
                ORDER BY analyzed_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [page_size, offset],
            ).fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "items": [self._row_to_dict(row) for row in rows],
        }

    def query_by_id(self, intel_id: int) -> Optional[dict]:
        """根据 ID 查询单条情报"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM threat_intel WHERE id = ?", (intel_id,)
            ).fetchone()
            return self._row_to_dict(row) if row else None

    def get_stats(self) -> dict:
        """
        获取统计概览

        面试: "SQL GROUP BY 的执行顺序？"
        → FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY
        """
        with self._get_conn() as conn:
            # 总数
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM threat_intel"
            ).fetchone()["cnt"]

            # 按风险等级
            risk_stats = conn.execute(
                """
                SELECT risk_level, COUNT(*) as cnt
                FROM threat_intel
                GROUP BY risk_level
                ORDER BY cnt DESC
                """
            ).fetchall()

            # 按威胁类型
            type_stats = conn.execute(
                """
                SELECT threat_type, COUNT(*) as cnt
                FROM threat_intel
                GROUP BY threat_type
                ORDER BY cnt DESC
                """
            ).fetchall()

            # 近7天趋势
            seven_days_ago = (
                datetime.now() - timedelta(days=7)
            ).strftime("%Y-%m-%d")
            daily_trend = conn.execute(
                """
                SELECT DATE(analyzed_at) as day, COUNT(*) as cnt
                FROM threat_intel
                WHERE analyzed_at >= ?
                GROUP BY day
                ORDER BY day
                """,
                (seven_days_ago,),
            ).fetchall()

        return {
            "total": total,
            "risk_distribution": [
                {"level": r["risk_level"], "count": r["cnt"]}
                for r in risk_stats
            ],
            "type_distribution": [
                {"type": r["threat_type"], "count": r["cnt"]}
                for r in type_stats
            ],
            "daily_trend": [
                {"date": r["day"], "count": r["cnt"]}
                for r in daily_trend
            ],
        }

    # ============================
    # 辅助方法
    # ============================
    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """将 sqlite3.Row 转为 dict, 同时解析 JSON 字段"""
        d = dict(row)
        # 解析 JSON 数组字段(不影响 SQLite 原生查询)
        for field in ["affected_products", "ioc_indicators"]:
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    d[field] = []
        return d


# 标准库 json 导入
import json
