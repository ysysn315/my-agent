# Design Document

## Overview

本设计文档描述了将 SuperBizAgent 从 Java/Spring 技术栈迁移到 Python/FastAPI 技术栈的架构设计。设计遵循渐进式开发原则，分为三个阶段：

1. **Phase 1 - 简单框架**：建立基础架构，实现最小可用的 AI 对话功能
2. **Phase 2 - 核心功能**：补充 RAG、工具调用、会话管理等核心能力
3. **Phase 3 - 完整功能**：实现 AIOps 多 Agent 协作和生产级特性

### 技术栈选择

- **Web 框架**: FastAPI（异步、高性能、自动文档生成）
- **AI 框架**: LangChain（工具封装、Prompt 管理）+ LangGraph（多 Agent 编排）
- **LLM 服务**: 阿里云 DashScope（通义千问 Qwen）
- **向量数据库**: Milvus（高性能向量检索）
- **数据验证**: Pydantic v2（类型安全、自动验证）
- **异步 HTTP**: httpx（调用外部 API）
- **日志**: loguru（简洁、强大）
- **配置管理**: pydantic-settings（类型安全的配置）
- **容器化**: Docker + docker-compose

### 设计原则

1. **简单优先**：Phase 1 只实现最核心的功能，避免过度设计
2. **可扩展性**：架构设计支持后续功能的平滑添加
3. **类型安全**：全面使用 Python 类型提示和 Pydantic 验证
4. **异步优先**：所有 I/O 操作使用 async/await
5. **清晰分层**：API → Service → Client，职责明确
6. **配置外部化**：所有配置通过环境变量管理

## Architecture

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                              │
│                    (Web / API Consumer)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/SSE
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Application                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (routes)                      │  │
│  │  /api/chat  /api/chat_stream  /api/upload           │  │
│  │  /api/ai_ops  /api/chat/clear  /milvus/health       │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │            Service Layer                             │  │
│  │  ChatService  RagService  AiOpsService               │  │
│  │  SessionStore  VectorIndexService                    │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │         Agent Layer (LangChain/LangGraph)            │  │
│  │  ChatAgent  AiOpsGraph (Planner/Executor/Supervisor)│  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │              Tool Layer                              │  │
│  │  DateTimeTool  InternalDocsTool                      │  │
│  │  PrometheusTool  LogsTool                            │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │            Client Layer                              │  │
│  │  DashScopeClient  MilvusClient  PrometheusClient     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
│  DashScope   │  │   Milvus    │  │ Prometheus │
│   (Qwen)     │  │  (Vector)   │  │  (Metrics) │
└──────────────┘  └─────────────┘  └────────────┘
```



### 目录结构

```
my-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   │
│   ├── api/                       # API 路由层
│   │   ├── __init__.py
│   │   ├── routes_chat.py         # 对话相关路由
│   │   ├── routes_upload.py       # 文件上传路由
│   │   ├── routes_session.py      # 会话管理路由
│   │   └── routes_aiops.py        # AIOps 路由
│   │
│   ├── core/                      # 核心配置和依赖
│   │   ├── __init__.py
│   │   ├── settings.py            # 配置管理
│   │   ├── logging.py             # 日志配置
│   │   └── dependencies.py        # FastAPI 依赖注入
│   │
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── chat.py                # 对话请求/响应模型
│   │   ├── upload.py              # 上传请求/响应模型
│   │   ├── session.py             # 会话模型
│   │   └── aiops.py               # AIOps 模型
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── chat_service.py        # 对话服务
│   │   ├── rag_service.py         # RAG 服务
│   │   ├── aiops_service.py       # AIOps 服务
│   │   ├── session_store.py       # 会话存储
│   │   └── vector_index_service.py # 向量索引服务
│   │
│   ├── agents/                    # Agent 层
│   │   ├── __init__.py
│   │   ├── chat_agent.py          # 基础对话 Agent
│   │   ├── aiops_graph.py         # AIOps LangGraph
│   │   └── tools/                 # Agent 工具
│   │       ├── __init__.py
│   │       ├── datetime_tool.py   # 时间工具
│   │       ├── internal_docs_tool.py # 文档检索工具
│   │       ├── prometheus_tool.py # Prometheus 工具
│   │       └── logs_tool.py       # 日志查询工具
│   │
│   ├── rag/                       # RAG 组件
│   │   ├── __init__.py
│   │   ├── chunking.py            # 文档切分
│   │   ├── embeddings.py          # 向量化
│   │   ├── vector_store.py        # 向量存储
│   │   └── indexing.py            # 索引管理
│   │
│   └── clients/                   # 外部服务客户端
│       ├── __init__.py
│       ├── dashscope_client.py    # DashScope 客户端
│       ├── milvus_client.py       # Milvus 客户端
│       └── prometheus_client.py   # Prometheus 客户端
│
├── tests/                         # 测试目录
│   ├── __init__.py
│   ├── test_api/                  # API 测试
│   ├── test_services/             # 服务测试
│   └── test_agents/               # Agent 测试
│
├── uploads/                       # 文件上传目录
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量示例
├── pyproject.toml                 # 项目依赖和配置
├── docker-compose.yml             # Docker 编排
├── Dockerfile                     # 应用容器镜像
└── README.md                      # 项目文档
```

## Components and Interfaces

### Phase 1 - 简单框架组件

#### 1.1 FastAPI Application (main.py)

**职责**: 应用入口，注册路由和中间件

```python
from fastapi import FastAPI
from app.api import routes_chat
from app.core.logging import setup_logging

app = FastAPI(title="SuperBizAgent", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    setup_logging()
    # 初始化 Milvus 连接

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(routes_chat.router, prefix="/api")
```

#### 1.2 Settings (core/settings.py)

**职责**: 配置管理，使用 pydantic-settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用配置
    app_port: int = 9900
    upload_dir: str = "./uploads"
    
    # DashScope 配置
    dashscope_api_key: str
    chat_model: str = "qwen-max"
    embedding_model: str = "text-embedding-v4"
    
    # Milvus 配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "knowledge_base"
    
    # RAG 配置
    doc_chunk_max_size: int = 800
    doc_chunk_overlap: int = 100
    rag_top_k: int = 3
    
    class Config:
        env_file = ".env"
```



#### 1.3 Chat API (api/routes_chat.py)

**职责**: 处理对话请求

```python
from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends()
):
    """基础对话接口（Phase 1）"""
    answer = await chat_service.chat(request.Question)
    return ChatResponse(answer=answer)
```

#### 1.4 Chat Service (services/chat_service.py)

**职责**: 对话业务逻辑

```python
from app.clients.dashscope_client import DashScopeClient

class ChatService:
    def __init__(self, dashscope_client: DashScopeClient):
        self.client = dashscope_client
    
    async def chat(self, question: str) -> str:
        """Phase 1: 简单对话，无工具、无历史"""
        response = await self.client.chat(
            messages=[{"role": "user", "content": question}]
        )
        return response
```

#### 1.5 DashScope Client (clients/dashscope_client.py)

**职责**: 封装 DashScope API 调用

```python
import httpx
from app.core.settings import Settings

class DashScopeClient:
    def __init__(self, settings: Settings):
        self.api_key = settings.dashscope_api_key
        self.model = settings.chat_model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
    
    async def chat(self, messages: list[dict]) -> str:
        """调用 DashScope Chat API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "input": {"messages": messages}
                }
            )
            data = response.json()
            return data["output"]["text"]
```

#### 1.6 Milvus Client (clients/milvus_client.py)

**职责**: 管理 Milvus 连接和操作

```python
from pymilvus import connections, Collection, utility
from app.core.settings import Settings

class MilvusClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.collection = None
    
    async def connect(self):
        """连接 Milvus"""
        connections.connect(
            host=self.settings.milvus_host,
            port=self.settings.milvus_port
        )
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return connections.has_connection("default")
        except:
            return False
    
    async def ensure_collection(self):
        """确保 collection 存在"""
        if not utility.has_collection(self.settings.milvus_collection):
            # Phase 2 会实现创建 collection 的逻辑
            pass
```

### Phase 2 - 核心功能组件

#### 2.1 Session Store (services/session_store.py)

**职责**: 管理会话和对话历史

```python
from collections import defaultdict
from typing import Dict, List

class SessionStore:
    def __init__(self, max_history: int = 6):
        self.sessions: Dict[str, List[dict]] = defaultdict(list)
        self.max_history = max_history  # 最多保留 6 轮对话（12 条消息）
    
    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话历史"""
        self.sessions[session_id].append({
            "role": role,
            "content": content
        })
        # 保持历史长度限制
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][-(self.max_history * 2):]
    
    def get_history(self, session_id: str) -> List[dict]:
        """获取会话历史"""
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str):
        """清空会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
```

#### 2.2 RAG Service (services/rag_service.py)

**职责**: RAG 检索增强生成

```python
from app.rag.vector_store import VectorStore
from app.clients.dashscope_client import DashScopeClient

class RagService:
    def __init__(
        self,
        vector_store: VectorStore,
        dashscope_client: DashScopeClient,
        top_k: int = 3
    ):
        self.vector_store = vector_store
        self.client = dashscope_client
        self.top_k = top_k
    
    async def query(self, question: str, history: List[dict] = None) -> dict:
        """RAG 查询"""
        # 1. 检索相关文档
        docs = await self.vector_store.search(question, self.top_k)
        
        if not docs:
            return {
                "answer": "抱歉，知识库中未找到相关信息。",
                "sources": []
            }
        
        # 2. 构建上下文
        context = self._build_context(docs)
        
        # 3. 构建 prompt
        prompt = self._build_prompt(question, context)
        
        # 4. 调用 LLM
        messages = (history or []) + [{"role": "user", "content": prompt}]
        answer = await self.client.chat(messages)
        
        return {
            "answer": answer,
            "sources": [{"content": doc["content"], "score": doc["score"]} for doc in docs]
        }
    
    def _build_context(self, docs: List[dict]) -> str:
        """构建上下文"""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"【参考资料 {i}】\n{doc['content']}\n")
        return "\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """构建 prompt"""
        return f"""你是一个专业的AI助手。请根据以下参考资料回答用户的问题。

参考资料：
{context}

用户问题：{question}

请基于上述参考资料给出准确、详细的回答。如果参考资料中没有相关信息，请明确说明。"""
```



#### 2.3 Vector Store (rag/vector_store.py)

**职责**: 向量存储和检索

```python
from pymilvus import Collection
from app.clients.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService

class VectorStore:
    def __init__(
        self,
        milvus_client: MilvusClient,
        embedding_service: EmbeddingService
    ):
        self.milvus = milvus_client
        self.embedding = embedding_service
    
    async def search(self, query: str, top_k: int) -> List[dict]:
        """向量检索"""
        # 1. 生成查询向量
        query_vector = await self.embedding.embed_text(query)
        
        # 2. 在 Milvus 中检索
        collection = self.milvus.collection
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["content", "metadata"]
        )
        
        # 3. 格式化结果
        docs = []
        for hit in results[0]:
            docs.append({
                "content": hit.entity.get("content"),
                "metadata": hit.entity.get("metadata"),
                "score": hit.score
            })
        
        return docs
    
    async def insert(self, texts: List[str], metadatas: List[dict]):
        """插入文档"""
        # 1. 生成向量
        vectors = await self.embedding.embed_texts(texts)
        
        # 2. 插入 Milvus
        collection = self.milvus.collection
        collection.insert([
            list(range(len(texts))),  # ids
            vectors,                   # vectors
            texts,                     # content
            metadatas                  # metadata
        ])
        collection.flush()
```

#### 2.4 Document Chunking (rag/chunking.py)

**职责**: 文档切分

```python
from typing import List

class DocumentChunker:
    def __init__(self, max_size: int = 800, overlap: int = 100):
        self.max_size = max_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, source: str) -> List[dict]:
        """切分文本为 chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_size
            chunk_text = text[start:end]
            
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "source": source,
                    "start": start,
                    "end": end
                }
            })
            
            start = end - self.overlap
        
        return chunks
```

#### 2.5 Streaming Response (api/routes_chat.py)

**职责**: SSE 流式响应

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

@router.post("/chat_stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口"""
    
    async def generate():
        try:
            # 获取流式响应
            async for chunk in chat_service.chat_stream(
                request.Id,
                request.Question
            ):
                # 发送内容块
                yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        except Exception as e:
            # 发送错误信号
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### Phase 3 - 完整功能组件

#### 3.1 Agent Tools (agents/tools/)

**职责**: 封装 Agent 可调用的工具

```python
# agents/tools/datetime_tool.py
from langchain.tools import tool
from datetime import datetime

@tool
def get_current_datetime() -> str:
    """获取当前日期和时间"""
    return datetime.now().isoformat()

# agents/tools/internal_docs_tool.py
from langchain.tools import tool
from app.rag.vector_store import VectorStore

@tool
async def query_internal_docs(query: str, vector_store: VectorStore) -> str:
    """查询内部文档知识库"""
    docs = await vector_store.search(query, top_k=3)
    if not docs:
        return "未找到相关文档"
    
    result = []
    for i, doc in enumerate(docs, 1):
        result.append(f"【文档 {i}】\n{doc['content']}\n")
    
    return "\n".join(result)

# agents/tools/prometheus_tool.py
from langchain.tools import tool
from app.clients.prometheus_client import PrometheusClient

@tool
async def query_prometheus_alerts(prom_client: PrometheusClient) -> str:
    """查询 Prometheus 活跃告警"""
    alerts = await prom_client.get_alerts()
    if not alerts:
        return "当前无活跃告警"
    
    result = []
    for alert in alerts:
        result.append(
            f"- {alert['labels']['alertname']}: "
            f"{alert['labels'].get('severity', 'unknown')}"
        )
    
    return "\n".join(result)
```

#### 3.2 Chat Agent (agents/chat_agent.py)

**职责**: 基础对话 Agent，支持工具调用

```python
from langchain.agents import create_react_agent
from langchain_community.chat_models import ChatTongyi
from langchain.prompts import ChatPromptTemplate

class ChatAgent:
    def __init__(
        self,
        api_key: str,
        model: str,
        tools: List
    ):
        self.llm = ChatTongyi(
            dashscope_api_key=api_key,
            model_name=model
        )
        self.tools = tools
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """创建 ReAct Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的智能助手，可以使用工具获取信息。"),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        return create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    async def chat(self, question: str, history: List[dict] = None) -> str:
        """执行对话"""
        result = await self.agent.ainvoke({
            "input": question,
            "chat_history": history or []
        })
        return result["output"]
```



#### 3.3 AIOps Graph (agents/aiops_graph.py)

**职责**: AIOps 多 Agent 协作，使用 LangGraph

```python
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatTongyi
from typing import TypedDict, Annotated
import operator

class AIOpsState(TypedDict):
    """AIOps 状态"""
    input: str
    planner_plan: str
    executor_feedback: str
    decision: str  # PLAN, EXECUTE, FINISH
    final_report: str
    iteration: int

class AIOpsGraph:
    def __init__(self, api_key: str, model: str, tools: List):
        self.llm = ChatTongyi(dashscope_api_key=api_key, model_name=model)
        self.tools = tools
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建 LangGraph"""
        workflow = StateGraph(AIOpsState)
        
        # 添加节点
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("supervisor", self._supervisor_node)
        
        # 添加边
        workflow.set_entry_point("supervisor")
        workflow.add_edge("supervisor", "planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "supervisor")
        
        # 条件边：根据 decision 决定下一步
        workflow.add_conditional_edges(
            "supervisor",
            self._should_continue,
            {
                "continue": "planner",
                "finish": END
            }
        )
        
        return workflow.compile()
    
    async def _planner_node(self, state: AIOpsState) -> AIOpsState:
        """Planner Agent 节点"""
        prompt = f"""你是 Planner Agent，负责分析告警并制定执行计划。

当前任务：{state['input']}
Executor 反馈：{state.get('executor_feedback', '无')}

请输出 JSON 格式的计划：
{{
  "decision": "PLAN|EXECUTE|FINISH",
  "step": "下一步要执行的操作",
  "tool": "需要调用的工具",
  "context": "相关上下文"
}}

如果已完成分析，decision 设为 FINISH，并输出完整的 Markdown 告警分析报告。
"""
        
        response = await self.llm.ainvoke(prompt)
        state["planner_plan"] = response.content
        
        # 解析 decision
        try:
            import json
            plan = json.loads(response.content)
            state["decision"] = plan.get("decision", "EXECUTE")
        except:
            state["decision"] = "EXECUTE"
        
        return state
    
    async def _executor_node(self, state: AIOpsState) -> AIOpsState:
        """Executor Agent 节点"""
        prompt = f"""你是 Executor Agent，负责执行 Planner 的计划。

Planner 计划：{state['planner_plan']}

请执行计划中的第一步，调用相应的工具，并返回执行结果。
输出 JSON 格式：
{{
  "status": "SUCCESS|FAILED",
  "summary": "执行摘要",
  "evidence": "工具返回的证据",
  "nextHint": "给 Planner 的建议"
}}
"""
        
        # 这里应该实际调用工具，简化示例
        response = await self.llm.ainvoke(prompt)
        state["executor_feedback"] = response.content
        state["iteration"] = state.get("iteration", 0) + 1
        
        return state
    
    async def _supervisor_node(self, state: AIOpsState) -> AIOpsState:
        """Supervisor Agent 节点"""
        # Supervisor 决定是否继续循环
        if state.get("decision") == "FINISH":
            # 提取最终报告
            state["final_report"] = state["planner_plan"]
        
        return state
    
    def _should_continue(self, state: AIOpsState) -> str:
        """判断是否继续"""
        if state.get("decision") == "FINISH":
            return "finish"
        if state.get("iteration", 0) > 10:  # 最多 10 轮
            return "finish"
        return "continue"
    
    async def run(self, task: str) -> str:
        """运行 AIOps 分析"""
        initial_state = {
            "input": task,
            "planner_plan": "",
            "executor_feedback": "",
            "decision": "PLAN",
            "final_report": "",
            "iteration": 0
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_report"]
```

## Data Models

### Pydantic Schemas

```python
# schemas/chat.py
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    Id: str = Field(..., description="会话 ID")
    Question: str = Field(..., description="用户问题")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="AI 回答")
    sources: List[dict] = Field(default=[], description="参考来源")

# schemas/upload.py
class UploadResponse(BaseModel):
    filename: str
    chunks: int
    status: str

# schemas/session.py
class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    last_updated: str
```

### Milvus Schema

```python
# Collection: knowledge_base
{
    "fields": [
        {"name": "id", "type": "INT64", "is_primary": True, "auto_id": True},
        {"name": "vector", "type": "FLOAT_VECTOR", "dim": 1536},  # text-embedding-v4 维度
        {"name": "content", "type": "VARCHAR", "max_length": 65535},
        {"name": "metadata", "type": "JSON"}
    ],
    "index": {
        "field": "vector",
        "metric_type": "IP",  # 内积
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
}
```



## Correctness Properties

*属性（Property）是系统在所有有效执行中都应该保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性是人类可读规范和机器可验证正确性保证之间的桥梁。*

### Property 1: API 请求数据验证
*对于任何* 发送到 `/api/chat` 的 POST 请求，如果请求体包含有效的 `Id` 和 `Question` 字段，系统应该接受请求并返回 200 状态码；如果缺少必需字段或类型错误，应该返回 422 状态码和验证错误信息。

**Validates: Requirements 1.3, 2.1**

### Property 2: 对话响应格式一致性
*对于任何* 成功的对话请求，系统返回的 JSON 响应必须包含 `answer` 字段，且该字段为非空字符串。

**Validates: Requirements 2.3**

### Property 3: 会话隔离性
*对于任何* 两个不同的会话 ID（session_id_1 和 session_id_2），在 session_id_1 中添加的消息不应该出现在 session_id_2 的历史记录中。

**Validates: Requirements 4.1**

### Property 4: 会话历史长度限制
*对于任何* 会话，无论添加多少条消息，系统维护的历史记录长度不应该超过 12 条消息（6 轮对话）。

**Validates: Requirements 4.2**

### Property 5: 流式响应格式正确性
*对于任何* 流式对话请求，系统返回的每个 SSE 事件都应该是有效的 JSON 格式，包含 `type` 字段，且 `type` 的值为 `content`、`done` 或 `error` 之一。

**Validates: Requirements 5.3**

### Property 6: 流式响应完成信号
*对于任何* 成功的流式对话请求，系统最后发送的事件必须是 `{"type":"done"}`。

**Validates: Requirements 5.4**

### Property 7: 文档切分覆盖性
*对于任何* 上传的文档，切分后的所有 chunks 拼接起来应该覆盖原文档的全部内容（考虑 overlap 重叠部分）。

**Validates: Requirements 6.4**

### Property 8: 文档存储检索一致性（Round Trip）
*对于任何* 上传并向量化的文档，使用文档中的原文进行检索，应该能够在 top-k 结果中找到该文档的至少一个 chunk。

**Validates: Requirements 6.6**

### Property 9: 上传响应完整性
*对于任何* 成功的文件上传请求，系统返回的响应必须包含 `filename`、`chunks` 和 `status` 三个字段。

**Validates: Requirements 6.8**

### Property 10: RAG 检索数量限制
*对于任何* RAG 查询，系统返回的文档数量不应该超过配置的 top-k 值。

**Validates: Requirements 7.2**

### Property 11: RAG 响应来源信息
*对于任何* RAG 查询（知识库非空），系统返回的响应必须包含 `sources` 字段，且该字段为列表类型。

**Validates: Requirements 7.5**

### Property 12: AIOps 报告格式完整性
*对于任何* 完成的 AIOps 分析，生成的 Markdown 报告必须包含以下章节标题：`# 告警分析报告`、`## 活跃告警清单`、`## 告警根因分析`、`## 处理方案执行`、`## 结论`。

**Validates: Requirements 10.8, 10.10**

## Error Handling

### 错误处理策略

1. **API 层错误处理**
   - 使用 FastAPI 的异常处理器统一处理错误
   - 返回标准化的错误响应格式：`{"error": "错误类型", "message": "错误详情"}`
   - 记录所有错误到日志

2. **外部服务调用错误**
   - DashScope API 调用失败：返回友好错误信息，不暴露 API 密钥
   - Milvus 连接失败：应用仍可启动，但 RAG 功能不可用
   - Prometheus 不可用：工具调用返回错误信息，不阻塞其他功能

3. **工具调用错误**
   - 单个工具失败不影响其他工具
   - 同一工具连续失败 3 次后，停止调用并记录
   - 在 AIOps 报告中如实说明工具失败原因

4. **数据验证错误**
   - 使用 Pydantic 自动验证请求数据
   - 返回 422 状态码和详细的验证错误信息

### 错误响应示例

```python
# 成功响应
{
    "answer": "这是回答",
    "sources": [...]
}

# 错误响应
{
    "error": "ValidationError",
    "message": "Question field is required"
}

# 外部服务错误
{
    "error": "ServiceUnavailable",
    "message": "Unable to connect to Milvus"
}
```

## Testing Strategy

### 测试方法论

本项目采用**双重测试策略**：单元测试 + 属性测试，两者互补，共同确保系统正确性。

- **单元测试**：验证具体示例、边界情况和错误条件
- **属性测试**：验证通用属性在所有输入下都成立
- **集成测试**：验证组件间的协作和端到端流程

### 测试框架和工具

- **测试框架**: pytest
- **属性测试**: Hypothesis（Python 的 PBT 库）
- **Mock**: pytest-mock
- **异步测试**: pytest-asyncio
- **覆盖率**: pytest-cov

### 属性测试配置

每个属性测试应该：
- 运行至少 100 次迭代（Hypothesis 默认配置）
- 使用注释标记对应的设计属性
- 格式：`# Feature: python-agent-migration, Property N: [property_text]`

### 测试组织

```
tests/
├── unit/                          # 单元测试
│   ├── test_chat_service.py
│   ├── test_rag_service.py
│   ├── test_session_store.py
│   └── test_chunking.py
│
├── properties/                    # 属性测试
│   ├── test_api_properties.py     # API 层属性
│   ├── test_session_properties.py # 会话管理属性
│   ├── test_rag_properties.py     # RAG 属性
│   └── test_streaming_properties.py # 流式响应属性
│
└── integration/                   # 集成测试
    ├── test_chat_flow.py          # 对话流程
    ├── test_upload_flow.py        # 上传流程
    └── test_aiops_flow.py         # AIOps 流程
```

### 属性测试示例

```python
# tests/properties/test_api_properties.py
from hypothesis import given, strategies as st
import pytest

# Feature: python-agent-migration, Property 1: API 请求数据验证
@given(
    session_id=st.text(min_size=1),
    question=st.text(min_size=1)
)
@pytest.mark.asyncio
async def test_valid_chat_request_accepted(client, session_id, question):
    """对于任何有效的 Id 和 Question，API 应该接受请求"""
    response = await client.post(
        "/api/chat",
        json={"Id": session_id, "Question": question}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data

# Feature: python-agent-migration, Property 4: 会话历史长度限制
@given(
    session_id=st.text(min_size=1),
    messages=st.lists(st.text(min_size=1), min_size=20, max_size=50)
)
@pytest.mark.asyncio
async def test_session_history_length_limit(session_store, session_id, messages):
    """无论添加多少消息，历史长度不超过 12 条"""
    for msg in messages:
        session_store.add_message(session_id, "user", msg)
        session_store.add_message(session_id, "assistant", f"reply to {msg}")
    
    history = session_store.get_history(session_id)
    assert len(history) <= 12
```

### 单元测试示例

```python
# tests/unit/test_chat_service.py
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_chat_service_basic_response():
    """测试基础对话功能"""
    # Arrange
    mock_client = AsyncMock()
    mock_client.chat.return_value = "这是回答"
    service = ChatService(mock_client)
    
    # Act
    result = await service.chat("你好")
    
    # Assert
    assert result == "这是回答"
    mock_client.chat.assert_called_once()

@pytest.mark.asyncio
async def test_chat_service_handles_api_error():
    """测试 API 错误处理"""
    # Arrange
    mock_client = AsyncMock()
    mock_client.chat.side_effect = Exception("API Error")
    service = ChatService(mock_client)
    
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await service.chat("你好")
    assert "API Error" in str(exc_info.value)
```

### 集成测试示例

```python
# tests/integration/test_upload_flow.py
import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_upload_and_query_flow(client, test_file):
    """测试上传文档后能够检索到内容"""
    # 1. 上传文档
    with open(test_file, "rb") as f:
        upload_response = await client.post(
            "/api/upload",
            files={"file": f}
        )
    assert upload_response.status_code == 200
    
    # 2. 查询文档内容
    query_response = await client.post(
        "/api/chat",
        json={
            "Id": "test-session",
            "Question": "文档中说了什么？"
        }
    )
    assert query_response.status_code == 200
    data = query_response.json()
    assert "sources" in data
    assert len(data["sources"]) > 0
```

### 测试覆盖目标

- **Phase 1**: 核心 API 和服务层单元测试，覆盖率 > 70%
- **Phase 2**: 添加属性测试和集成测试，覆盖率 > 80%
- **Phase 3**: 完整测试套件，覆盖率 > 85%

### CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```



## Implementation Phases

### Phase 1: 简单框架（1-2 天）

**目标**: 建立最小可用系统，能够进行基础 AI 对话

**核心功能**:
- FastAPI 应用骨架
- 配置管理（Settings）
- 日志系统
- `/health` 健康检查
- `/api/chat` 基础对话（无工具、无历史）
- DashScope 客户端
- Milvus 连接（仅连接，不使用）

**验收标准**:
- 应用能够启动并监听 9900 端口
- 能够通过 `/api/chat` 与 AI 对话
- 日志正常输出
- Milvus 连接成功

**技术债务**:
- 会话管理暂未实现
- 工具调用暂未实现
- RAG 功能暂未实现

### Phase 2: 核心功能（3-5 天）

**目标**: 补充 RAG 和工具调用能力，实现完整的智能问答

**核心功能**:
- 会话管理（SessionStore）
- 流式对话（SSE）
- 文件上传与向量化
- RAG 检索和生成
- 基础工具（时间、文档检索）
- LangChain Agent 集成

**验收标准**:
- 支持多轮对话，历史记录正确
- 流式响应正常工作
- 能够上传文档并向量化
- RAG 查询返回相关文档
- Agent 能够调用工具

**技术债务**:
- AIOps 功能暂未实现
- Prometheus 集成暂未实现

### Phase 3: 完整功能（4-6 天）

**目标**: 实现 AIOps 多 Agent 协作和生产级特性

**核心功能**:
- Prometheus 客户端和工具
- AIOps LangGraph（Planner-Executor-Supervisor）
- 告警分析报告生成
- Docker 容器化
- 完整测试套件
- 性能优化

**验收标准**:
- AIOps 分析能够生成完整报告
- Docker 一键启动
- 测试覆盖率 > 85%
- 性能满足要求（响应时间 < 2s）

## Deployment

### 开发环境

```bash
# 1. 克隆项目
cd my-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY

# 5. 启动 Milvus
docker-compose up -d milvus

# 6. 启动应用
uvicorn app.main:app --reload --port 9900
```

### 生产环境（Docker）

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Milvus 向量数据库
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - ./volumes/etcd:/etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - ./volumes/minio:/minio_data
    command: minio server /minio_data

  milvus:
    image: milvusdb/milvus:v2.3.0
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ./volumes/milvus:/var/lib/milvus
    ports:
      - "19530:19530"
    depends_on:
      - etcd
      - minio

  # Python 应用
  app:
    build: .
    ports:
      - "9900:9900"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - milvus
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml .
RUN pip install -e .

# 复制代码
COPY app/ ./app/

# 暴露端口
EXPOSE 9900

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9900"]
```

### 环境变量配置

```bash
# .env.example
# 应用配置
APP_PORT=9900
UPLOAD_DIR=./uploads

# DashScope 配置
DASHSCOPE_API_KEY=your-api-key-here
CHAT_MODEL=qwen-max
EMBEDDING_MODEL=text-embedding-v4

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=knowledge_base

# RAG 配置
DOC_CHUNK_MAX_SIZE=800
DOC_CHUNK_OVERLAP=100
RAG_TOP_K=3

# Prometheus 配置（Phase 3）
PROMETHEUS_BASE_URL=http://localhost:9090
```

## Dependencies

### 核心依赖

```toml
# pyproject.toml
[project]
name = "superbiz-agent"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    # Web 框架
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-multipart>=0.0.6",  # 文件上传
    
    # 数据验证
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    
    # AI 框架
    "langchain>=0.1.0",
    "langchain-community>=0.0.10",
    "langgraph>=0.0.20",
    
    # LLM 服务
    "dashscope>=1.14.0",  # 阿里云 DashScope SDK
    
    # 向量数据库
    "pymilvus>=2.3.0",
    
    # HTTP 客户端
    "httpx>=0.25.0",
    
    # 日志
    "loguru>=0.7.0",
    
    # 工具
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    # 测试
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "hypothesis>=6.92.0",  # 属性测试
    
    # 代码质量
    "ruff>=0.1.0",
    "black>=23.11.0",
    "mypy>=1.7.0",
]
```

### 依赖说明

- **fastapi**: 现代、高性能的 Web 框架
- **langchain**: AI 应用开发框架，提供工具封装和 Prompt 管理
- **langgraph**: 多 Agent 编排框架，用于 AIOps
- **dashscope**: 阿里云通义千问 SDK
- **pymilvus**: Milvus 向量数据库客户端
- **httpx**: 异步 HTTP 客户端
- **loguru**: 简洁强大的日志库
- **hypothesis**: 属性测试框架

## Performance Considerations

### 性能目标

- **API 响应时间**: < 2s（不含 LLM 生成时间）
- **RAG 检索时间**: < 500ms
- **文件上传处理**: < 5s（1MB 文件）
- **并发支持**: 100 并发请求

### 优化策略

1. **异步 I/O**
   - 所有外部调用使用 async/await
   - 使用 httpx 异步 HTTP 客户端
   - Milvus 操作使用异步接口

2. **连接池**
   - 复用 HTTP 连接
   - Milvus 连接池管理

3. **缓存**
   - 向量化结果缓存（可选）
   - 会话数据使用 Redis（Phase 3）

4. **批处理**
   - 文档批量向量化
   - 批量插入 Milvus

5. **流式响应**
   - 使用 SSE 减少首字节时间
   - 提升用户体验

## Security Considerations

### 安全措施

1. **API 密钥保护**
   - 使用环境变量存储密钥
   - 不在日志中输出密钥
   - 错误信息不暴露密钥

2. **输入验证**
   - 使用 Pydantic 验证所有输入
   - 文件上传大小限制（10MB）
   - 文件类型白名单

3. **SQL/NoSQL 注入防护**
   - 使用参数化查询
   - Milvus 表达式过滤

4. **CORS 配置**
   - 生产环境限制允许的源
   - 开发环境可配置

5. **速率限制**（Phase 3）
   - 使用 slowapi 限制请求频率
   - 防止滥用

## Monitoring and Observability

### 日志策略

```python
# app/core/logging.py
from loguru import logger
import sys

def setup_logging():
    """配置日志"""
    logger.remove()  # 移除默认处理器
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 文件输出
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # 每天轮转
        retention="30 days",  # 保留 30 天
        level="DEBUG"
    )
```

### 关键指标

- API 请求数和响应时间
- LLM 调用次数和耗时
- 向量检索次数和耗时
- 工具调用成功/失败率
- 错误率和错误类型

### 可观测性（Phase 3）

- OpenTelemetry 集成
- Prometheus metrics 导出
- 分布式追踪

## Migration from Java

### 对照表

| Java 组件 | Python 组件 | 说明 |
|----------|------------|------|
| Spring Boot | FastAPI | Web 框架 |
| Spring AI | LangChain/LangGraph | AI 框架 |
| @Service | Service 类 | 业务逻辑层 |
| @RestController | APIRouter | API 路由 |
| @Value | Settings | 配置管理 |
| @Autowired | Depends() | 依赖注入 |
| application.yml | .env + Settings | 配置文件 |
| SLF4J | loguru | 日志 |
| Maven | pip + pyproject.toml | 依赖管理 |

### 迁移注意事项

1. **类型系统**
   - Java 的强类型 → Python 的类型提示 + Pydantic
   - 运行时验证更重要

2. **异步模型**
   - Java 的线程模型 → Python 的 async/await
   - 注意 GIL 限制

3. **依赖注入**
   - Spring 的 DI 容器 → FastAPI 的 Depends()
   - 更轻量，但需要手动管理

4. **错误处理**
   - Java 的受检异常 → Python 的异常处理
   - 需要更明确的错误处理

5. **测试**
   - JUnit → pytest
   - 测试风格更灵活

## Conclusion

本设计文档提供了从 Java/Spring 到 Python/FastAPI 的完整迁移方案，采用渐进式开发策略：

1. **Phase 1** 快速建立简单框架，验证技术选型
2. **Phase 2** 补充核心功能，实现完整的 RAG 和工具调用
3. **Phase 3** 实现高级特性，达到生产级别

设计强调：
- **简单性**：避免过度设计，优先实现核心功能
- **可扩展性**：架构支持后续功能的平滑添加
- **类型安全**：全面使用类型提示和 Pydantic 验证
- **测试驱动**：双重测试策略确保正确性

通过这个设计，你将能够：
- 快速看到一个能运行的 Agent（Phase 1）
- 逐步掌握 LangChain/LangGraph 的使用（Phase 2）
- 最终实现完整的 AIOps 功能（Phase 3）
