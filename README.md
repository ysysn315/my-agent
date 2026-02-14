# SuperBizAgent (Python / FastAPI)

> 基于 **FastAPI + LangChain/LangGraph + Milvus** 的智能问答与 AIOps 运维分析 Demo。

本仓库是对原 Java/Spring 版本的 Python 重构。当前实现包含：

- **聊天对话**（支持普通/流式 SSE）
- **文档上传 → 切分 → 向量化 → 入 Milvus**（知识库）
- **AIOps 分析**（普通/流式 SSE，输出 Markdown 报告）
- **静态前端**（`static/`，优先本地 vendor，避免外网资源导致页面一直加载）

---

## 技术栈

- **Backend**: FastAPI (async)
- **LLM**: 阿里云 DashScope（通义千问）
- **Agent**: LangChain / LangGraph
- **Vector DB**: Milvus（Docker Compose：Milvus + etcd + MinIO）
- **Frontend**: 纯静态页面 `static/`（内置 `marked` + `highlight.js` vendor）

---

## 目录结构（关键部分）

```text
my-agent/
  app/
    main.py                 # FastAPI 应用入口（端口默认 9900）
    api/
      routes_chat.py        # /api/chat, /api/chat_stream
      routes_upload.py      # /api/upload
      routes_session.py     # /api/chat/clear/{id}, /api/chat/sessions
      routes_aiops.py       # /api/ai_ops, /api/ai_ops_stream
      routes_milvus.py      # /milvus/health
    core/settings.py        # 配置（读取 .env）
  static/
    index.html              # 前端入口（API_BASE_URL）
    app.js                  # 前端逻辑（chat/upload/aiops）
    styles.css
    vendor/                 # 本地依赖：marked/highlight.js/github.css
  docker-compose.yml        # Milvus + etcd + minio（带 volumes 持久化）
  volumes/                  # 本地持久化数据（已在 .gitignore）
  uploads/                  # 上传文件目录（已在 .gitignore）
```

---

## 快速开始

### 0) 前置依赖

- Python 3.10+（建议 3.11）
- Docker Desktop（用于启动 Milvus）

### 1) 安装依赖

使用 venv（示例）：

```bash
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt
```

或使用 `pyproject.toml`（可选）：

```bash
pip install -e ".[dev]"
```

### 2) 配置环境变量（DashScope）

项目通过 `app/core/settings.py` 从 `.env` 读取配置。

至少需要：

```bash
# .env
DASHSCOPE_API_KEY=你的key
```

### 3) 启动 Milvus（带持久化）

```bash
docker-compose up -d
```

说明：`docker-compose.yml` 已挂载本地目录（重启容器不丢数据）：

- `./volumes/milvus:/var/lib/milvus`
- `./volumes/etcd:/etcd`
- `./volumes/minio:/minio_data`

### 4) 启动后端

```bash
uvicorn app.main:app --reload --port 9900
```

后端地址：

- 健康检查：`GET http://127.0.0.1:9900/health`
- Swagger：`http://127.0.0.1:9900/docs`

### 5) 启动前端（静态）

前端在 `static/` 目录，不需要打包。

- 用 VS Code Live Server 打开：`static/index.html`

#### 前端如何配置后端地址（重要）

前端从 `localStorage.API_BASE_URL` 读取后端前缀，默认写入：

```text
http://127.0.0.1:9900/api
```

如果你后端不是这个地址，在浏览器控制台执行：

```js
localStorage.setItem('API_BASE_URL', 'http://127.0.0.1:9900/api');
location.reload();
```

---

## API 一览

### Health

- `GET /health`

### Chat

- `POST /api/chat`
- `POST /api/chat_stream`（SSE）

SSE 事件格式：

```text
data: {"type":"content","data":"..."}
data: {"type":"done"}
data: {"type":"error","data":"..."}
```

### Upload

- `POST /api/upload`（multipart/form-data, field: `file`）

### Session

- `DELETE /api/chat/clear/{session_id}`
- `GET /api/chat/sessions`

### AIOps

- `POST /api/ai_ops`
- `POST /api/ai_ops_stream`（SSE）

---

## Milvus 数据查看（推荐 Attu）

```bash
docker run --rm -p 8000:3000 zilliz/attu:latest
```

打开 `http://127.0.0.1:8000` 连接：`127.0.0.1:19530`。

---

## 常见问题（Troubleshooting）

### 1) DashScope SSL EOF

通常是网络/代理/安全软件导致：

- 切换网络（如手机热点）
- 检查 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`
- 放行 `dashscope.aliyuncs.com:443`

### 2) Live Server 打开前端一直转圈

一般是外网资源/插件注入脚本导致。当前前端已优先使用本地 `static/vendor/`，若仍出现：

- 用无扩展浏览器 Profile 对照
- 禁用扩展

---

## 参考文档

- `docs/design.md`：总体架构与迁移设计
- `docs/PHASE3_PLAN.md`：Phase 3 规划
- `docs/requirements.md`：需求与验收标准
- `docs/TOOL_EXPLANATION.md`：Tool 机制解释

