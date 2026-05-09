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

## RAG 评测结果（最新）

### 1）历史基线评测（2026-02-21）

#### 检索评测总览

| 指标 | 数值 |
|---|---:|
| num_cases | 40 |
| hit@1 | 0.6500 |
| hit@3 | 0.8750 |
| recall@3 | 0.8000 |
| mrr | 0.7458 |
| precision@3 | 0.2917 |
| ndcg@3 | 0.7364 |
| map | 0.6979 |

#### 生成评测总览（8 条冒烟集）

| 指标 | 数值 |
|---|---:|
| num_cases | 8 |
| keyword_recall | 0.9750 |
| source_hit | 0.9375 |

#### 检索配置对比（Leaderboard）

| 配置 | hit@3 | recall@3 | mrr | precision@3 | ndcg@3 | map |
|---|---:|---:|---:|---:|---:|---:|
| hybrid_rerank_k5 | 0.8500 | 0.7875 | 0.7508 | 0.2833 | 0.7506 | 0.7281 |
| rerank_only | 0.8750 | 0.8000 | 0.7625 | 0.2917 | 0.7489 | 0.7146 |
| hybrid_rerank | 0.8500 | 0.8000 | 0.7500 | 0.2917 | 0.7420 | 0.7083 |
| baseline | 0.8250 | 0.7625 | 0.6708 | 0.2750 | 0.6776 | 0.6354 |
| hybrid_only | 0.8250 | 0.7625 | 0.6708 | 0.2750 | 0.6776 | 0.6354 |

#### 基线结论

- 引入 rerank 的配置在排序质量（MRR/NDCG/MAP）上明显优于 baseline，说明在强干扰语料下 rerank 有效。
- 当时综合表现最均衡的配置是 `hybrid_rerank_k5`。
- 8 条生成集更适合做早期冒烟，不再单独作为主模型选型依据。

### 2）正式主模型对比（2026-04-21）

#### 本轮配置

- 数据集：`evals/rag/datasets/rag_generation_cases_formal_template.json`（60 条正式生成集）
- 主模型：`qwen3-max`、`qwen3.6-plus`、`qwen3.5-plus`
- Embedding：`dashscope / text-embedding-v4`
- 向量库：`knowledge_base`
- 检索参数：`enable_hybrid=True`、`enable_rerank=True`、`dense_top_k=10`
- Query Rewrite：`qwen-turbo`
- Rerank：实际运行使用 `BGE rerank (BAAI/bge-reranker-base, CPU)`
- 结果文件：`evals/rag/reports/main_model_compare_latest.json`

#### 主模型对比结果（按 `strict_score` 排序）

| 模型 | strict_score | fact_recall | source_recall_strict | source_precision_strict | hallucination_score | 平均延迟 | P95 延迟 | 总 Token | 总费用（CNY） | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3-max` | 0.7751 | 0.7444 | 0.8917 | 0.5139 | 0.9333 | 19.52s | 29.20s | 68,522 | 0.254550 | 0.0000 |
| `qwen3.6-plus` | 0.7720 | 0.7264 | 0.8917 | 0.5306 | 0.9500 | 42.97s | 59.38s | 149,964 | 1.247448 | 0.0000 |
| `qwen3.5-plus` | 0.7501 | 0.7042 | 0.8667 | 0.5028 | 0.9333 | 60.48s | 104.48s | 199,859 | 0.739978 | 0.0167 |

#### 主模型结论

- 默认主模型选择 `qwen3-max`。它在 60 条正式集上拿到最高 `strict_score`，同时延迟和费用显著优于另外两个模型。
- `qwen3.6-plus` 更偏“质量优先”备选。它的 `source_precision_strict` 和 `hallucination_score` 略好，但整体收益不足以覆盖 2 倍以上时延和接近 5 倍费用。
- `qwen3.5-plus` 不建议作为默认模型。它这轮严格得分最低，且出现了 `1/60` 的失败样本。

### 3）Embedding 对比（2026-04-21）
#### 本轮配置

- 检索测试集：`evals/rag/datasets/rag_retrieval_cases.json`，40 条检索用例
- 生成测试集：`evals/rag/datasets/rag_generation_cases_formal_template.json`，60 条正式生成集
- 导入语料：`aiops-docs` + `aiops-docs-noise`
- 语料规模：15 个文件，164 个 chunks
- 主模型：`qwen3-max`
- Query Rewrite：`qwen-turbo`
- 检索参数：`enable_hybrid=True`、`enable_rerank=True`、`dense_top_k=10`
- Hybrid：`Milvus dense + in-memory BM25`
- Rerank：实际运行使用 `BGE rerank (BAAI/bge-reranker-base, CPU)`
- Embedding A：`dashscope / text-embedding-v4`，collection=`knowledge_base`
- Embedding B：`bge / bge-large-zh`，collection=`knowledge_base_bge_large_zh`
- 结果文件：`evals/rag/reports/embedding_compare_latest.json`

#### 检索侧对比

| Embedding | Collection | hit@1 | hit@3 | recall@3 | mrr | precision@3 | ndcg@3 | map |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `text-embedding-v4` | `knowledge_base` | 0.4750 | 0.7750 | 0.7500 | 0.6000 | 0.2750 | 0.6317 | 0.5833 |
| `bge-large-zh` | `knowledge_base_bge_large_zh` | 0.5000 | 0.8250 | 0.7750 | 0.6333 | 0.2750 | 0.6551 | 0.6021 |

#### 生成侧对比（主模型固定 `qwen3-max`）

| Embedding | strict_score | fact_recall | source_recall_strict | source_precision_strict | hallucination_score | source_hit | keyword_recall | error_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `text-embedding-v4` | 0.6959 | 0.5847 | 0.8667 | 0.5111 | 0.9333 | 0.8667 | 0.3792 | 0.0000 |
| `bge-large-zh` | 0.6764 | 0.5431 | 0.8750 | 0.4972 | 0.9333 | 0.8750 | 0.3708 | 0.0000 |

#### Embedding 结论

- 只看检索侧，`bge-large-zh` 在 `hit@1 / hit@3 / recall@3 / mrr / ndcg@3 / map` 上都略优于 `text-embedding-v4`。
- 但看端到端生成质量，`text-embedding-v4` 的 `strict_score` 和 `fact_recall` 更高，当前整条 RAG 链路里整体表现更稳。
- 因此当前默认 embedding 仍选择 `text-embedding-v4`，`bge-large-zh` 作为后续继续调优的备选。

### 4）同条件检索配置复跑（2026-04-21）
#### 本轮配置

- 检索测试集：`evals/rag/datasets/rag_retrieval_cases.json`，40 条检索用例
- 导入语料：`aiops-docs` + `aiops-docs-noise`
- 语料规模：15 个文件，164 个 chunks
- 固定 Embedding：`dashscope / text-embedding-v4`
- 固定向量库：`knowledge_base`
- Hybrid：`Milvus dense + in-memory BM25`
- Rerank：实际运行使用 `BGE rerank (BAAI/bge-reranker-base, CPU)`，失败才回退 `qwen-turbo`
- 结果文件：`evals/rag/reports/retrieval_same_conditions_latest.json`

#### 配置对比（同条件复跑）

| 配置 | hit@1 | hit@3 | recall@3 | mrr | precision@3 | ndcg@3 | map |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 0.6000 | 0.8500 | 0.8375 | 0.7125 | 0.3167 | 0.7498 | 0.7167 |
| `hybrid_only` | 0.5250 | 0.8750 | 0.8500 | 0.6792 | 0.3167 | 0.7231 | 0.6708 |
| `rerank_only` | 0.5000 | 0.9250 | 0.8625 | 0.6833 | 0.3167 | 0.7170 | 0.6542 |
| `hybrid_rerank_k5` | 0.4750 | 0.7750 | 0.7500 | 0.6425 | 0.2750 | 0.6394 | 0.6219 |
| `hybrid_rerank` | 0.4750 | 0.7750 | 0.7500 | 0.6000 | 0.2750 | 0.6317 | 0.5833 |

#### 同条件复跑结论

- 在“同一份 15 文件 / 164 chunks 语料、同一份 40 条检索集、同一个 `text-embedding-v4` collection、实际启用 BM25 和 BGE rerank”的条件下，当前最优配置是 `baseline`。
- `hybrid_only` 和 `rerank_only` 抬高了 `hit@3 / recall@3`，但把第一命中位置往后推了，所以 `MRR / NDCG / MAP` 反而不如 `baseline`。
- `hybrid_rerank` 与 `hybrid_rerank_k5` 在当前噪声语料上表现更差，说明“混合检索 + 重排”并不天然更优，仍然要看语料结构和重排质量。
- 这也解释了为什么本轮 `MRR / NDCG` 会低于 2 月历史结果：更大的差异来自实验条件和运行链路变化，而不是测试集本身变难。

### 5）本地复现实验命令

```bash
conda activate langchain-agent
cd D:\AI编程\kiro-place\JAVA-agent\my-agent

python -m evals.rag.run_generation_eval
python -m evals.rag.run_main_model_compare
python -m evals.rag.run_generation_eval_strict
python -m evals.rag.run_embedding_compare
python -m evals.rag.run_retrieval_eval
python -m evals.rag.run_experiments
python -m evals.rag.run_retrieval_config_same_conditions
python -m pytest tests/test_rag_regression.py -q
```

## 参考文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://docs.langchain.com/)
- [Milvus 文档](https://milvus.io/docs/)
- [DashScope API 文档](https://help.aliyun.com/zh/model-studio/)

## 许可证

MIT
