# SuperBizAgent (Python / FastAPI)

> 基于 **FastAPI + LangChain/LangGraph + Milvus** 的智能问答与 AIOps 运维分析 Demo。

本仓库是对原 Java/Spring 版本的 Python 重构。当前实现包含：

- **聊天对话**（支持普通/流式 SSE）
- **文档上传 → 切分 → 向量化 → 入 Milvus**（知识库）
- **AIOps 分析**（普通/流式 SSE，输出 Markdown 报告）
- **静态前端**（`static/`，支持本地 vendor，避免 CDN 慢导致的首屏转圈）

---

## 技术栈

- **Backend**: FastAPI (async)
- **LLM**: 阿里云 DashScope（通义千问）
- **Agent**: LangChain / LangGraph（AIOps 多 Agent 方向）
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
    index.html              # 前端入口（API_BASE_URL + vendor 优先）
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

（注意：仓库默认 `.gitignore` 已忽略 `.env`，不要提交到 GitHub。）

### 3) 启动 Milvus（带持久化）

```bash
docker-compose up -d
```

说明：`docker-compose.yml` 已挂载本地目录：

- `./volumes/milvus:/var/lib/milvus`
- `./volumes/etcd:/etcd`
- `./volumes/minio:/minio_data`

因此 **正常重启容器不会丢数据**；只有删除 `volumes/` 或使用 `docker compose down -v` 才会清空。

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
- 或任意静态服务器打开：`http://127.0.0.1:<port>/static/index.html`

#### 前端如何配置后端地址（重要）

前端会从 `localStorage.API_BASE_URL` 读取后端前缀，默认写入：

```text
http://127.0.0.1:9900/api
```

如果你后端不是这个地址，可以在浏览器控制台执行：

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

SSE 格式：

```text
data: {"type":"content","data":"..."}
data: {"type":"done"}
data: {"type":"error","data":"..."}
```

### Upload

- `POST /api/upload`（multipart/form-data, field: `file`）

返回示例：

```json
{"filename":"a.md","chunks":12,"status":"success"}
```

### Session

- `DELETE /api/chat/clear/{session_id}`
- `GET /api/chat/sessions`

### AIOps

- `POST /api/ai_ops`
- `POST /api/ai_ops_stream`（SSE）

SSE `type`：`message` / `content` / `done` / `error`。

---

## Milvus 数据查看（推荐 Attu）

可视化管理工具建议使用 Attu：

```bash
docker run --rm -p 8000:3000 zilliz/attu:latest
```

打开 `http://127.0.0.1:8000`，连接：

- Host: `127.0.0.1`
- Port: `19530`

---

## 常见问题（Troubleshooting）

### 1) AIOps / Chat 调用 DashScope 报 SSL 错误

如果日志出现类似：

`SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol`

通常不是代码问题，而是网络/代理/安全软件中间人导致：

- 尝试切换网络（如手机热点）
- 检查终端环境变量 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`
- 如果在公司网络，可能需要放行 `dashscope.aliyuncs.com:443`

### 2) 前端打开很慢、Network 里出现大量 `content_script`

这通常来自浏览器插件/安全模块注入脚本，建议：

- 使用 Chrome/Edge 新 Profile（无扩展）对照
- 禁用所有扩展后再打开

### 3) Milvus 重启后数据是否会消失？

不会（本项目 compose 已做 volumes 持久化）。

会丢数据的操作：

- 删除 `volumes/`
- `docker compose down -v`

---

## 参考文档

- `docs/design.md`：总体架构与迁移设计
- `docs/PHASE3_PLAN.md`：Phase 3 规划（AIOps 多 Agent）
- `docs/requirements.md`：需求与验收标准
- `docs/TOOL_EXPLANATION.md`：LangChain Tool 机制解释

