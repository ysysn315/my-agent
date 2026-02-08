# 依赖版本说明

## 核心依赖版本

本项目使用以下核心依赖版本，已在生产环境验证可用。

### LangChain 生态系统

**重要说明**: 项目已从 LangChain 0.3.x 升级到 1.2.9，以解决 `create_react_agent` 的 StopIteration bug。

| 包名 | 版本 | 说明 |
|------|------|------|
| langchain | 1.2.9 | LangChain 核心框架 |
| langchain-core | 1.2.9 | LangChain 核心组件 |
| langchain-community | 0.4.1 | 社区集成（包含 ChatTongyi） |
| langchain-text-splitters | 1.1.0 | 文本分割工具 |
| langchain-milvus | 0.3.3 | Milvus 向量存储集成 |
| langgraph | 1.0.7 | Agent 工作流编排 |
| langgraph-checkpoint | 4.0.0 | 状态检查点 |
| langgraph-prebuilt | 1.0.7 | 预构建组件 |
| langgraph-sdk | 0.3.3 | SDK 工具 |
| langsmith | 0.6.9 | 调试和监控工具 |

### Web 框架

| 包名 | 版本 | 说明 |
|------|------|------|
| fastapi | 0.128.0 | Web 框架 |
| uvicorn | 0.40.0 | ASGI 服务器 |
| starlette | 0.50.0 | ASGI 工具包 |
| python-multipart | 0.0.22 | 文件上传支持 |

### 数据验证

| 包名 | 版本 | 说明 |
|------|------|------|
| pydantic | 2.12.5 | 数据验证 |
| pydantic-core | 2.41.5 | Pydantic 核心 |
| pydantic-settings | 2.12.0 | 配置管理 |

### 向量数据库

| 包名 | 版本 | 说明 |
|------|------|------|
| pymilvus | 2.6.8 | Milvus Python SDK |

### AI 服务

| 包名 | 版本 | 说明 |
|------|------|------|
| dashscope | 1.25.11 | 阿里云通义千问 SDK |

### HTTP 客户端

| 包名 | 版本 | 说明 |
|------|------|------|
| httpx | 0.28.1 | 异步 HTTP 客户端 |
| httpcore | 1.0.9 | HTTP 核心 |
| httpx-sse | 0.4.3 | SSE 支持 |
| requests | 2.32.5 | 同步 HTTP 客户端 |
| aiohttp | 3.13.3 | 异步 HTTP 框架 |

### 工具库

| 包名 | 版本 | 说明 |
|------|------|------|
| loguru | 0.7.3 | 日志库 |
| python-dotenv | 1.2.1 | 环境变量管理 |
| tenacity | 8.5.0 | 重试机制 |
| PyYAML | 6.0.3 | YAML 解析 |

### 数据处理

| 包名 | 版本 | 说明 |
|------|------|------|
| numpy | 1.26.4 | 数值计算 |
| pandas | 3.0.0 | 数据分析 |
| SQLAlchemy | 2.0.46 | ORM 框架 |

### 开发工具

| 包名 | 版本 | 说明 |
|------|------|------|
| pytest | 9.0.2 | 测试框架 |
| pytest-asyncio | 1.3.0 | 异步测试支持 |
| black | 26.1.0 | 代码格式化 |
| ruff | 0.14.14 | 代码检查 |

## 版本升级记录

### 2026-02-08: LangChain 升级到 1.2.9

**原因**: 解决 `create_react_agent` 的 StopIteration bug

**变更**:
- langchain: 0.3.13 → 1.2.9
- langchain-core: 0.3.26 → 1.2.9
- langchain-community: 0.3.12 → 0.4.1

**影响**:
- 使用 LangGraph 重写了 ChatAgent
- 不再使用 `create_react_agent`，改用 `StateGraph` 手动构建工作流
- 工具调用功能正常，无 StopIteration 错误

**实现细节**:
```python
# 旧方式 (有 bug)
from langchain.agents import create_react_agent

# 新方式 (使用 LangGraph)
from langgraph.graph import StateGraph, END
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
```

## Python 版本要求

- **最低版本**: Python 3.10
- **推荐版本**: Python 3.10 或 3.11
- **测试版本**: Python 3.10

## 环境配置方式

### 方式一：使用 Conda (推荐)

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate langchain-agent
```

### 方式二：使用 pip

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 常见问题

### Q1: 为什么要升级到 LangChain 1.2.9？

A: LangChain 0.3.x 版本的 `create_react_agent` 存在 StopIteration bug，导致工具调用失败。升级到 1.2.9 并使用 LangGraph 可以完全解决这个问题。

### Q2: 升级后有什么不兼容的地方吗？

A: 主要变化是 ChatAgent 的实现方式，从 `create_react_agent` 改为 LangGraph 的 `StateGraph`。对外接口保持不变，业务代码无需修改。

### Q3: 如何验证环境配置正确？

A: 运行以下命令测试：

```bash
# 启动服务
conda run -n langchain-agent python -m uvicorn app.main:app --reload --port 8000

# 测试工具调用
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"Id": "test-session", "Question": "现在几点了？"}'
```

如果返回当前时间，说明环境配置正确。

### Q4: 在其他设备上如何快速部署？

A: 使用以下步骤：

```bash
# 1. 克隆项目
git clone <your-repo>
cd my-agent

# 2. 创建 conda 环境
conda env create -f environment.yml
conda activate langchain-agent

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY

# 4. 启动 Milvus (如果需要 RAG 功能)
docker-compose up -d

# 5. 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

## 更新日志

- **2026-02-08**: 初始版本，LangChain 1.2.9，LangGraph 1.0.7
