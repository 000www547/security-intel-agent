# 🛡️ Security-Intel-Agent 安全情报分析智能体

**AI 驱动的网络安全威胁情报采集、分析、预警平台** | 基于[硅基流动](https://cloud.siliconflow.cn) API + DeepSeek V3

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=chainlink)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 项目简介

Security-Intel-Agent 是一个**全栈 AI Agent 实战项目**，实现从全网安全情报自动采集 → 大模型智能分析 → 数据库持久化 → Web 可视化展示的完整链路。适合**网络安全求职、课程设计、毕业设计、简历项目**。

### 核心亮点

| 维度 | 说明 |
|------|------|
| 🤖 **AI Agent** | LangChain + DeepSeek 驱动, 非简单调用 API |
| 🏗️ **全栈架构** | Vue 3 前端 + FastAPI 后端 + SQLite 持久化 |
| 🔄 **自动化** | GitHub Actions 无服务器定时采集 |
| 🐳 **容器化** | Docker Compose 一键部署 |
| 📊 **可视化** | Web Dashboard 展示风险趋势与分布 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    用户浏览器                          │
│              Vue 3 + Naive UI Dashboard               │
└─────────────────┬───────────────────────────────────┘
                  │  HTTP REST API
┌─────────────────▼───────────────────────────────────┐
│                FastAPI 后端服务                       │
│  ┌──────────┬──────────┬──────────┬─────────────┐  │
│  │ Collector│ Analyzer │ Database │  Notifier   │  │
│  │ (RSS采集)│(LangChain)│(SQLite) │  (飞书推送)   │  │
│  └──────────┴──────────┴──────────┴─────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
     ┌────────────▼────────────┐
     │   GitHub Actions        │
     │   每日 16:00 定时执行     │
     └─────────────────────────┘
```

### 数据流

```
RSS Feeds → feedparser 抓取 → 数据清洗去重
    → LangChain + DeepSeek 威胁分析 → Pydantic 结构化输出
    → SQLite 持久化(自动去重) → RESTful API
    → Vue 3 前端展示 ← 飞书/钉钉推送
```

---

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- [硅基流动 API Key](https://cloud.siliconflow.cn)（注册即送免费额度，支持 DeepSeek V3）

### 方式一: 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/000www547/security-intel-agent.git
cd security-intel-agent

# 2. 后端
cd backend
pip install -r requirements.txt
# 编辑 config.yaml, 填入你的 DeepSeek API Key
python -m app.main

# 3. 前端 (新终端)
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:3000` 即可看到 Dashboard。

### 方式二: Docker Compose 一键部署

```bash
# 1. 编辑 backend/config.yaml, 填入 API Key
docker-compose up -d

# 2. 访问
# 前端: http://localhost
# API 文档: http://localhost:8000/docs
```

---

## 📂 项目结构

```
security-intel-agent/
├── backend/                       # 后端 (Python FastAPI)
│   ├── app/
│   │   ├── main.py                # FastAPI 入口 (lifespan + CORS)
│   │   ├── pipeline.py            # 采集→分析→存储 流水线
│   │   ├── api/routes.py          # RESTful API 路由
│   │   ├── collector/
│   │   │   └── rss_collector.py   # RSS 多源采集 + 数据清洗
│   │   ├── analyzer/
│   │   │   ├── threat_analyzer.py # LangChain + DeepSeek 分析引擎
│   │   │   ├── prompts.py         # 安全分析师 System Prompt
│   │   │   └── models.py          # Pydantic 数据模型
│   │   ├── notifier/
│   │   │   └── feishu.py          # 飞书卡片消息推送
│   │   └── db/
│   │       └── database.py        # SQLite CRUD + 统计查询
│   ├── requirements.txt
│   ├── config.yaml                # 全局配置
│   └── Dockerfile
├── frontend/                      # 前端 (Vue 3 + Naive UI)
│   ├── src/
│   │   ├── App.vue                # 主布局 (导航 + 路由)
│   │   ├── views/
│   │   │   ├── Dashboard.vue      # 仪表盘 (统计+趋势)
│   │   │   ├── IntelList.vue      # 情报列表 (分页+筛选)
│   │   │   └── IntelDetail.vue    # 情报详情
│   │   ├── components/
│   │   │   ├── IntelCard.vue      # 情报卡片
│   │   │   └── RiskBadge.vue      # 风险标签
│   │   └── api/index.js           # API 请求封装
│   ├── vite.config.js
│   └── Dockerfile
├── .github/workflows/
│   └── daily_run.yml              # GitHub Actions 定时任务
├── docker-compose.yml             # 容器编排
└── README.md
```

---

## 📚 面试知识体系

### 🐍 Python 工程化
| 知识点 | 在本项目中如何体现 |
|--------|-------------------|
| **包管理** | `requirements.txt` 依赖声明, 虚拟环境隔离 |
| **类型注解** | `def analyze(self, raw_item: RawIntelItem) -> Optional[ThreatAnalysis]` |
| **异常处理** | try/except 保证单个源失败不影响整体, 分级日志 |
| **上下文管理器** | `@contextmanager` 管理数据库连接, 自动 commit/rollback |
| **懒加载** | `@property` 延迟初始化 ChatOpenAI 实例 |
| **环境变量** | `os.environ.get("CONFIG_PATH")` 配置注入 |

### 🕷️ 网络爬虫 & RSS
| 知识点 | 实现 |
|--------|------|
| **feedparser** | 解析 RSS/Atom 标准格式 |
| **httpx** | 比 requests 更快, 支持 async |
| **User-Agent** | 模拟浏览器, 避免被反爬 |
| **数据清洗** | HTML 标签去除 + HTML 实体解码 + 空白合并 |
| **日期标准化** | `dateutil.parser` 自动识别多种日期格式 → ISO 8601 |
| **去重策略** | 用 `set` 按 URL O(1) 去重 + DB 层 UNIQUE 约束 |

### 🤖 LangChain 框架
| 知识点 | 代码体现 |
|--------|---------|
| **ChatOpenAI** | 通过 `base_url` 指向 DeepSeek API (适配器模式) |
| **ChatPromptTemplate** | System + Human 双消息模板 |
| **PydanticOutputParser** | 解析 LLM 输出 → Pydantic 对象 |
| **Chain 编排** | prompt → model → parser 流水线 |
| **Temperature** | 0.3 低温度保证分析稳定性和一致性 |

### 🧠 Prompt Engineering
| 技巧 | 实践 |
|------|------|
| **角色设定** | "你是一名资深网络安全威胁情报分析师, 拥有 10 年以上经验" |
| **约束规则** | 明确定义威胁分类标准 + 风险定级规则 |
| **格式要求** | 要求输出严格 JSON, 定义每个字段含义 |
| **幻觉控制** | "无法确定的信息标注为'暂无相关信息'" |

### 📐 Pydantic 数据验证
| 知识点 | 代码 |
|--------|------|
| **BaseModel** | 所有数据模型继承, 自动类型校验 |
| **Field** | 添加描述、默认值、约束 (ge/le) |
| **Enum 约束** | ThreatType / RiskLevel 枚举约束取值范围 |
| **field_validator** | 校验 CVE 格式 `CVE-YYYY-NNNNN` |
| **model_dump** | 序列化为 dict/JSON |

### 🗄️ SQLite 数据库
| 知识点 | 实现 |
|--------|------|
| **建表** | `CREATE TABLE IF NOT EXISTS` 幂等初始化 |
| **唯一索引** | `source_url UNIQUE` 防止重复入库 |
| **INSERT OR IGNORE** | 原子去重, 无需先 SELECT |
| **分页查询** | `LIMIT ? OFFSET ?` 参数化查询防注入 |
| **GROUP BY** | 风险/类型分布 + 每日趋势聚合 |
| **WAL 模式** | `PRAGMA journal_mode=WAL` 提高并发 |

### 🌐 FastAPI Web 框架
| 知识点 | 代码 |
|--------|------|
| **异步支持** | `async def` + `await` 非阻塞 I/O |
| **RESTful 设计** | GET 查询 / POST 触发 / 路径参数 |
| **Query 参数** | 自动校验 + OpenAPI 文档生成 |
| **lifespan** | 启动初始化 / 关闭清理 |
| **CORS 中间件** | 前后端分离必需 |
| **HTTPException** | 统一错误响应 |

### 🎨 Vue 3 前端
| 知识点 | 体现 |
|--------|------|
| **Composition API** | `<script setup>` + ref/reactive/computed |
| **Vue Router** | SPA 路由, history 模式 |
| **组件化** | IntelCard / RiskBadge 可复用组件 |
| **响应式数据** | ref 驱动视图自动更新 |
| **Vite** | 极速开发服务器 + 构建优化 |
| **Naive UI** | Tree Shaking 按需加载组件 |
| **axios 拦截器** | 统一错误处理 + 响应数据提取 |

### 🔄 GitHub Actions CI/CD
| 知识点 | 配置 |
|--------|------|
| **Cron 定时** | `0 8 * * *` = UTC 8:00 = 北京时间 16:00 |
| **workflow_dispatch** | 页面手动触发 |
| **Secrets 管理** | `${{ secrets.LLM_API_KEY }}` 不暴露明文 |
| **artifact 上传** | 数据库 + 报告自动归档 |
| **cache** | `cache: "pip"` 加速依赖安装 |

### 🐳 Docker 容器化
| 知识点 | 实现 |
|--------|------|
| **多阶段构建** | 前端 build → nginx 两阶段, 镜像仅 ~20MB |
| **docker-compose** | 一键编排 frontend + backend |
| **volume 持久化** | 数据库文件挂载到宿主机 |
| **nginx 代理** | SPA try_files + API 反向代理 |

### 🔐 安全领域知识
| 概念 | 说明 |
|------|------|
| **CVE** | Common Vulnerabilities and Exposures, 通用漏洞编号 |
| **CVSS** | 漏洞评分系统 (0-10分), 高分→高危 |
| **IOC** | Indicators of Compromise, 失陷指标 (IP/域名/哈希) |
| **ATT&CK** | MITRE 攻击框架, 威胁分类标准参考 |
| **威胁分类** | 漏洞/恶意软件/APT/数据泄露/钓鱼/DDoS/0day/Web攻击 |

---

## 🔧 配置说明

编辑 `backend/config.yaml`:

```yaml
llm:
  api_key: "sk-xxxxxxxx"       # DeepSeek API Key (必填)
  model_name: "deepseek-chat"  # 模型名称
  temperature: 0.3             # 0=确定性, 1=创造性

collect:
  rss_sources:                 # RSS 情报源 (可自行增减)
    - name: "FreeBuf"
      url: "https://www.freebuf.com/feed"

notify:
  feishu_webhook: ""           # 飞书机器人 Webhook (可选)
```

### GitHub Actions Secrets 配置

在仓库 Settings → Secrets and variables → Actions 中添加:

| Secret 名称 | 说明 |
|------------|------|
| `LLM_API_KEY` | DeepSeek API 密钥 |
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook (可选) |

---

## 🚢 部署方案

### 方案一: Docker Compose (推荐)

```bash
docker-compose up -d
```

### 方案二: 手动部署

后端使用 `uvicorn` + `supervisor` / `systemd` 守护进程化。
前端 `npm run build` 产物部署到 Nginx / CDN。

### 方案三: EdgeOne Pages / Vercel (仅前端)

```bash
cd frontend && npm run build
# 将 dist/ 目录部署到 EdgeOne Pages
```

---

## 🧪 扩展方向

- [ ] 接入 CVE/NVD 官方漏洞库实时比对
- [ ] 加入 RAG 安全知识库 (向量检索增强分析)
- [ ] 多 Agent 分工: 采集 Agent → 研判 Agent → 处置 Agent
- [ ] 恶意域名/IP 威胁情报识别
- [ ] 用户登录 + 订阅推送

---

## 📄 License

MIT License - 自由学习、二次开发、商用均可。

---

## 🤝 关于本项目

本项目是 **AI Agent + 网络安全 + 全栈开发** 的综合实战项目。

**面试官可能会问的问题:**

1. "LangChain 在你的项目中起什么作用？" → 统一 LLM 调用、Prompt 管理、结构化输出
2. "如何保证分析结果的准确性？" → Temperature 低参数 + Pydantic 校验 + 安全专家 Prompt
3. "如何处理不同 RSS 源的数据格式差异？" → 统一采集模型 RawIntelItem + dateutil 日期解析
4. "系统如何扩展？" → 分层架构, 新增情报源/推送渠道/分析维度只需加配置
5. "数据库为什么选 SQLite 而不是 MySQL?" → 轻量无运维, 适合初期, 可无缝迁移
