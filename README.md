# SuperBizAgent - Python Version

> 基于 FastAPI + LangChain + Milvus 的智能问答与运维系统

## 项目状态

🚧 **当前阶段**: Phase 1 - 简单框架搭建中

## 项目简介

这是 SuperBizAgent 的 Python 重构版本，采用渐进式开发策略：

- **Phase 1**: 简单框架 - 基础 AI 对话功能
- **Phase 2**: 核心功能 - RAG + 工具调用 + 会话管理
- **Phase 3**: 完整功能 - AIOps 多 Agent 协作

## 技术栈

- **Web 框架**: FastAPI
- **AI 框架**: LangChain + LangGraph
- **LLM 服务**: 阿里云 DashScope (通义千问)
- **向量数据库**: Milvus
- **数据验证**: Pydantic v2
- **日志**: loguru

## 快速开始

### 1. 环境准备

#### 方式一：使用 Conda (推荐)

```bash
# 使用 environment.yml 创建环境
conda env create -f environment.yml

# 激活环境
conda activate langchain-agent
```

#### 方式二：使用 pip + venv

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 方式三：使用 pyproject.toml (开发模式)

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 DASHSCOPE_API_KEY
```

### 3. 启动 Milvus (Phase 2 需要)

```bash
# 使用 docker-compose 启动 Milvus
docker-compose up -d
```

### 4. 启动应用

```bash
# 开发模式
uvicorn app.main:app --reload --port 9900
```

### 5. 访问 API

- API 文档: http://localhost:9900/docs
- 健康检查: http://localhost:9900/health

## 项目结构

```
my-agent/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 核心配置
│   │   ├── settings.py      # 配置管理
│   │   ├── logging.py       # 日志配置
│   │   └── dependencies.py  # 依赖注入
│   ├── api/                 # API 路由
│   │   ├── routes_chat.py   # 对话路由
│   │   └── routes_milvus.py # Milvus 健康检查
│   ├── schemas/             # Pydantic 模型
│   │   └── chat.py          # 对话模型
│   ├── services/            # 业务逻辑
│   │   └── chat_service.py  # 对话服务
│   └── clients/             # 外部服务客户端
│       ├── dashscope_client.py  # DashScope 客户端
│       └── milvus_client.py     # Milvus 客户端
├── tests/                   # 测试
├── .env.example             # 环境变量模板
├── pyproject.toml           # 项目配置
└── README.md                # 项目文档
```

## 开发指南

### Phase 1 任务清单

参考 `.kiro/specs/python-agent-migration/tasks.md` 中的任务列表。

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并查看覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/unit/test_chat_service.py
```

### 代码格式化

```bash
# 使用 black 格式化代码
black app/ tests/

# 使用 ruff 检查代码
ruff check app/ tests/
```

## API 文档

### Phase 1 可用接口

#### 健康检查

```bash
GET /health
```

响应:
```json
{
  "status": "ok"
}
```

#### 基础对话

```bash
POST /api/chat
Content-Type: application/json

{
  "Id": "session-123",
  "Question": "你好"
}
```

响应:
```json
{
  "answer": "你好！有什么我可以帮助你的吗？"
}
```

## 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://docs.langchain.com/)
- [Milvus 文档](https://milvus.io/docs/)
- [DashScope API 文档](https://help.aliyun.com/zh/model-studio/)

## 许可证

MIT
