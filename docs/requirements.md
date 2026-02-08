# Requirements Document

## Introduction

本文档定义了将 SuperBizAgent 从 Java/Spring 技术栈迁移到 Python/FastAPI 技术栈的需求。项目采用渐进式开发策略：首先建立简单但可扩展的核心框架，使 Agent 能够运行起来；然后逐步补充完整功能，确保开发过程平滑且易于掌握。

## Glossary

- **System**: Python 版本的 SuperBizAgent 应用
- **RAG**: Retrieval-Augmented Generation，检索增强生成
- **Agent**: 基于 LangChain/LangGraph 的智能代理
- **Milvus**: 向量数据库
- **DashScope**: 阿里云通义千问 AI 服务
- **Tool**: Agent 可调用的外部功能（如时间查询、文档检索等）
- **Session**: 用户会话，维护对话历史
- **Chunk**: 文档分片，用于向量化存储
- **SSE**: Server-Sent Events，服务器推送事件流
- **AIOps**: AI 运维，基于多 Agent 协作的智能运维系统
- **Planner**: 规划 Agent，负责拆解任务和制定执行计划
- **Executor**: 执行 Agent，负责执行具体的工具调用
- **Supervisor**: 监督 Agent，负责协调 Planner 和 Executor

## Requirements

### Requirement 1: 项目基础架构（Phase 1 - 简单框架）

**User Story:** 作为开发者，我希望建立一个简单但完整的 FastAPI 项目骨架，使得基础的 API 能够运行，便于后续功能扩展。

#### Acceptance Criteria

1. THE System SHALL 使用 FastAPI 框架提供 RESTful API 服务
2. THE System SHALL 在端口 9900 上启动 HTTP 服务
3. THE System SHALL 使用 Pydantic 进行请求和响应的数据验证
4. THE System SHALL 使用环境变量管理配置（DASHSCOPE_API_KEY、MILVUS_HOST 等）
5. THE System SHALL 提供结构化日志输出（使用 loguru 或 structlog）
6. THE System SHALL 使用 asyncio 实现异步 I/O 操作
7. THE System SHALL 提供健康检查端点 `/health`

### Requirement 2: 基础对话功能（Phase 1 - 简单框架）

**User Story:** 作为用户，我希望能够通过 API 与 AI 进行基础对话，即使没有工具调用和历史记忆，也能获得响应。

#### Acceptance Criteria

1. WHEN 用户发送 POST 请求到 `/api/chat`，THE System SHALL 接受包含 `Id` 和 `Question` 的 JSON 请求体
2. WHEN 收到对话请求，THE System SHALL 调用 DashScope API 获取 AI 响应
3. WHEN AI 响应完成，THE System SHALL 返回包含 `answer` 字段的 JSON 响应
4. THE System SHALL 使用 qwen-max 或 qwen-turbo 模型进行对话
5. IF API 调用失败，THEN THE System SHALL 返回包含错误信息的 JSON 响应，HTTP 状态码为 500

### Requirement 3: Milvus 向量数据库连接（Phase 1 - 简单框架）

**User Story:** 作为开发者，我希望系统能够连接到 Milvus 向量数据库，为后续的 RAG 功能做准备。

#### Acceptance Criteria

1. THE System SHALL 在启动时连接到 Milvus 数据库
2. THE System SHALL 使用配置的 host 和 port 连接 Milvus（默认 localhost:19530）
3. THE System SHALL 提供 `/milvus/health` 端点检查 Milvus 连接状态
4. WHEN Milvus 连接失败，THE System SHALL 记录错误日志但不阻止应用启动
5. THE System SHALL 创建或验证名为 `knowledge_base` 的 collection 存在

### Requirement 4: 会话管理（Phase 2 - 功能补充）

**User Story:** 作为用户，我希望系统能够记住我的对话历史，实现多轮对话。

#### Acceptance Criteria

1. WHEN 用户发送对话请求，THE System SHALL 根据 `Id` 字段识别会话
2. THE System SHALL 为每个会话维护最近 6 轮对话历史（12 条消息）
3. WHEN 生成 AI 响应，THE System SHALL 将对话历史包含在上下文中
4. THE System SHALL 提供 `POST /api/chat/clear` 端点清空指定会话的历史
5. THE System SHALL 提供 `GET /api/chat/session/{sessionId}` 端点查询会话信息
6. THE System SHALL 在内存中存储会话数据（可选：使用 Redis 持久化）

### Requirement 5: 流式对话（Phase 2 - 功能补充）

**User Story:** 作为用户，我希望能够实时看到 AI 的回复内容，而不是等待完整响应。

#### Acceptance Criteria

1. THE System SHALL 提供 `POST /api/chat_stream` 端点支持流式对话
2. WHEN 用户请求流式对话，THE System SHALL 使用 SSE（Server-Sent Events）协议返回数据
3. THE System SHALL 以 JSON 格式发送每个内容块：`{"type":"content","data":"..."}`
4. WHEN 响应完成，THE System SHALL 发送 `{"type":"done"}` 事件
5. IF 发生错误，THEN THE System SHALL 发送 `{"type":"error","data":"错误信息"}` 事件
6. THE System SHALL 在流式响应完成后将对话保存到会话历史

### Requirement 6: 文档上传与向量化（Phase 2 - 功能补充）

**User Story:** 作为用户，我希望能够上传文档到系统，系统自动将其向量化并存储到知识库。

#### Acceptance Criteria

1. THE System SHALL 提供 `POST /api/upload` 端点接受文件上传
2. THE System SHALL 支持 `.txt` 和 `.md` 文件格式
3. WHEN 文件上传，THE System SHALL 将文件保存到 `./uploads` 目录
4. THE System SHALL 将文档内容切分为 chunks（max_size=800, overlap=100）
5. THE System SHALL 使用 DashScope text-embedding-v4 模型生成向量
6. THE System SHALL 将向量和文本内容存储到 Milvus 的 `knowledge_base` collection
7. WHEN 上传同名文件，THE System SHALL 删除旧文档的所有 chunks 后再插入新 chunks
8. THE System SHALL 返回上传结果，包含文件名、chunk 数量和向量化状态

### Requirement 7: RAG 智能问答（Phase 2 - 功能补充）

**User Story:** 作为用户，我希望系统能够基于上传的文档回答我的问题，提供准确的知识库检索。

#### Acceptance Criteria

1. WHEN 用户提问，THE System SHALL 使用问题文本生成查询向量
2. THE System SHALL 从 Milvus 检索 top-k（默认 3）个最相似的文档 chunks
3. THE System SHALL 将检索到的文档内容作为上下文传递给 AI 模型
4. THE System SHALL 构建包含参考资料的 prompt 模板
5. THE System SHALL 在响应中包含检索到的文档来源信息
6. IF 未检索到相关文档，THEN THE System SHALL 返回"知识库中未找到相关信息"的提示

### Requirement 8: 基础工具集成（Phase 2 - 功能补充）

**User Story:** 作为 AI Agent，我希望能够调用外部工具获取实时信息，增强回答能力。

#### Acceptance Criteria

1. THE System SHALL 提供 `getCurrentDateTime` 工具获取当前时间
2. THE System SHALL 提供 `queryInternalDocs` 工具从知识库检索文档
3. THE System SHALL 使用 LangChain Tool 封装工具函数
4. WHEN AI 需要调用工具，THE System SHALL 自动执行工具并返回结果
5. THE System SHALL 在日志中记录所有工具调用及其参数
6. THE System SHALL 支持工具调用失败时的错误处理和重试

### Requirement 9: Prometheus 监控集成（Phase 3 - 完整功能）

**User Story:** 作为运维人员，我希望系统能够查询 Prometheus 告警和指标，用于智能运维分析。

#### Acceptance Criteria

1. THE System SHALL 提供 `queryPrometheusAlerts` 工具查询活跃告警
2. THE System SHALL 提供 `queryPrometheusMetrics` 工具执行 PromQL 查询
3. THE System SHALL 使用 httpx 异步调用 Prometheus HTTP API
4. THE System SHALL 支持配置 Prometheus base URL（默认 http://localhost:9090）
5. WHEN Prometheus 不可用，THE System SHALL 返回友好的错误信息
6. THE System SHALL 设置 10 秒的请求超时时间

### Requirement 10: AIOps 多 Agent 协作（Phase 3 - 完整功能）

**User Story:** 作为运维人员，我希望系统能够自动分析告警，生成详细的运维报告。

#### Acceptance Criteria

1. THE System SHALL 提供 `POST /api/ai_ops` 端点触发 AIOps 分析
2. THE System SHALL 使用 LangGraph 构建 Planner-Executor-Supervisor 工作流
3. THE Planner SHALL 分析告警并制定执行计划（输出 JSON 格式的步骤）
4. THE Executor SHALL 执行 Planner 的第一步并返回执行结果
5. THE Supervisor SHALL 协调 Planner 和 Executor 的循环执行
6. WHEN 同一工具连续失败 3 次，THE System SHALL 终止分析并在报告中说明原因
7. THE System SHALL 禁止编造数据，所有结论必须基于工具返回的真实证据
8. WHEN 分析完成，THE System SHALL 输出固定格式的 Markdown 告警分析报告
9. THE System SHALL 使用 SSE 流式输出报告生成过程
10. THE 报告 SHALL 包含：活跃告警清单、根因分析、处理方案、结论和建议

### Requirement 11: Docker 容器化部署（Phase 3 - 完整功能）

**User Story:** 作为开发者，我希望能够使用 Docker 一键启动整个系统，包括 Milvus 和应用服务。

#### Acceptance Criteria

1. THE System SHALL 提供 `docker-compose.yml` 文件定义所有服务
2. THE docker-compose SHALL 包含 Milvus、etcd、MinIO 服务
3. THE docker-compose SHALL 包含 Python 应用服务
4. THE System SHALL 支持通过 `docker-compose up` 一键启动所有服务
5. THE System SHALL 使用 volume 持久化 Milvus 数据
6. THE System SHALL 在容器内使用环境变量配置应用

### Requirement 12: 错误处理与日志（跨所有阶段）

**User Story:** 作为开发者，我希望系统能够提供清晰的错误信息和日志，便于调试和监控。

#### Acceptance Criteria

1. THE System SHALL 使用结构化日志记录所有 API 请求和响应
2. THE System SHALL 记录所有工具调用的输入参数和输出结果
3. THE System SHALL 记录所有外部 API 调用（DashScope、Milvus、Prometheus）
4. WHEN 发生异常，THE System SHALL 记录完整的堆栈跟踪
5. THE System SHALL 为不同日志级别使用不同的输出格式（DEBUG、INFO、WARNING、ERROR）
6. THE System SHALL 在生产环境中将日志输出到文件

### Requirement 13: 配置管理（跨所有阶段）

**User Story:** 作为开发者，我希望能够通过环境变量和配置文件灵活管理系统配置。

#### Acceptance Criteria

1. THE System SHALL 使用 pydantic-settings 管理配置
2. THE System SHALL 支持从 `.env` 文件读取配置（开发环境）
3. THE System SHALL 支持从环境变量读取配置（生产环境）
4. THE System SHALL 提供配置项的默认值
5. THE System SHALL 在启动时验证必需的配置项（如 DASHSCOPE_API_KEY）
6. THE System SHALL 提供配置项的类型检查和验证

### Requirement 14: 测试覆盖（Phase 3 - 完整功能）

**User Story:** 作为开发者，我希望有自动化测试确保系统功能正确性。

#### Acceptance Criteria

1. THE System SHALL 提供单元测试覆盖核心业务逻辑
2. THE System SHALL 提供集成测试验证 API 端点
3. THE System SHALL 使用 pytest 作为测试框架
4. THE System SHALL 使用 mock 隔离外部依赖（DashScope、Milvus）
5. THE System SHALL 提供测试覆盖率报告
6. THE System SHALL 在 CI/CD 流程中自动运行测试
