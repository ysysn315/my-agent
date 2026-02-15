# SuperBizAgent - Python Version

> 基于 FastAPI + LangChain + Milvus 的智能运维问答与故障分析系统

## 项目简介

这是一个智能运维助手系统，具备以下核心功能：

- 💬 **智能对话** - RAG 增强的运维知识问答
- 🔧 **故障分析** - AIOps 自动根因分析（Planner-Operation-Reflection 架构）
- 📁 **知识库管理** - 文档上传与向量化检索
- 📊 **系统监控** - 服务健康状态检查

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| AI 框架 | LangChain + LangGraph |
| LLM 服务 | 阿里云 DashScope (通义千问) |
| 向量数据库 | Milvus |
| 缓存数据库 | Redis |
| 前端框架 | Vue 3 + Vite |
| 容器化 | Docker + Docker Compose |

## 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd my-agent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY

# 3. 一键启动所有服务
docker-compose up -d

# 4. 访问应用
# 前端界面: http://localhost
# API 文档: http://localhost:9900/docs
```

**服务端口说明：**

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 (Nginx) | 80 | Web 界面 |
| 后端 API | 9900 | FastAPI 服务 |
| Milvus | 19530 | 向量数据库 |
| Redis | 6379 | 缓存数据库 |

### 方式二：本地开发

#### 1. 环境准备

```bash
# 使用 Conda 创建环境
conda env create -f environment.yml
conda activate langchain-agent

# 或使用 pip
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. 启动基础设施

```bash
# 启动 Milvus 和 Redis
docker-compose up -d etcd minio milvus redis
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY
```

#### 4. 启动后端

```bash
uvicorn app.main:app --reload --port 9900
```

#### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

## 项目结构

```
my-agent/
├── app/                        # 后端应用
│   ├── main.py                 # FastAPI 入口
│   ├── agents/                 # Agent 实现
│   │   ├── aiops_agent.py      # AIOps 故障分析 Agent
│   │   └── tools/              # 工具集
│   ├── api/                    # API 路由
│   ├── services/               # 业务逻辑
│   ├── clients/                # 外部服务客户端
│   ├── rag/                    # RAG 相关模块
│   └── schemas/                # 数据模型
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   └── styles/             # 样式文件
│   └── Dockerfile
├── aiops-docs/                 # 运维知识文档
├── tests/                      # 测试文件
├── docker-compose.yml          # Docker 编排
├── Dockerfile                  # 后端 Dockerfile
└── .env.example                # 环境变量模板
```

## API 文档

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/chat` | POST | 普通对话 |
| `/api/chat_stream` | POST | 流式对话 |
| `/api/ai_ops` | POST | 故障分析（非流式） |
| `/api/ai_ops_stream` | POST | 故障分析（流式） |
| `/api/upload` | POST | 上传文档 |
| `/milvus/health` | GET | Milvus 健康检查 |

### 示例请求

**故障分析（流式）：**

```bash
curl -X POST http://localhost:9900/api/ai_ops_stream \
  -H "Content-Type: application/json" \
  -d '{"problem": "CPU使用率过高"}'
```

**对话（流式）：**

```bash
curl -X POST http://localhost:9900/api/chat_stream \
  -H "Content-Type: application/json" \
  -d '{"Id": "session-1", "Question": "如何排查内存泄漏？"}'
```

## 开发指南

### 运行测试

```bash
pytest

# 带覆盖率报告
pytest --cov=app --cov-report=html
```

### 代码格式化

```bash
black app/ tests/
ruff check app/ tests/
```

## 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DASHSCOPE_API_KEY` | ✅ | 阿里云 DashScope API Key |
| `MILVUS_HOST` | ❌ | Milvus 主机地址（默认：localhost） |
| `MILVUS_PORT` | ❌ | Milvus 端口（默认：19530） |
| `REDIS_HOST` | ❌ | Redis 主机地址（默认：localhost） |
| `REDIS_PORT` | ❌ | Redis 端口（默认：6379） |

## 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://docs.langchain.com/)
- [Milvus 文档](https://milvus.io/docs/)
- [DashScope API 文档](https://help.aliyun.com/zh/model-studio/)

## 许可证

MIT
