# Implementation Plan: Python Agent Migration

## Overview

本任务列表将 SuperBizAgent 从 Java/Spring 迁移到 Python/FastAPI 的设计转换为可执行的开发任务。采用渐进式开发策略，分三个阶段实施：

- **Phase 1**: 简单框架（快速启动，建立信心）
- **Phase 2**: 核心功能（RAG + 工具调用）
- **Phase 3**: 完整功能（AIOps + 生产级特性）

每个任务都是独立的、可测试的代码变更，确保开发过程平滑且易于掌握。

## Tasks

### Phase 1: 简单框架（1-2 天）

- [ ] 1. 项目初始化和基础配置
  - 创建 `my-agent/` 项目目录结构
  - 创建 `pyproject.toml` 定义项目依赖
  - 创建 `.env.example` 环境变量模板
  - 创建 `.gitignore` 文件
  - 初始化 Git 仓库
  - _Requirements: 1.1, 1.4, 13.1, 13.2_

- [ ] 2. 配置管理和日志系统
  - [ ] 2.1 实现 `app/core/settings.py` 配置类
    - 使用 pydantic-settings 定义 Settings 类
    - 包含 DashScope、Milvus、RAG 等配置项
    - 支持从 .env 文件和环境变量读取
    - _Requirements: 1.4, 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [ ] 2.2 实现 `app/core/logging.py` 日志配置
    - 使用 loguru 配置结构化日志
    - 控制台输出彩色日志
    - 文件输出按日期轮转
    - _Requirements: 1.5, 12.1, 12.5_

- [ ] 3. FastAPI 应用骨架
  - [ ] 3.1 创建 `app/main.py` 应用入口
    - 初始化 FastAPI 应用
    - 配置 CORS 中间件
    - 添加启动和关闭事件处理
    - _Requirements: 1.1, 1.2_
  
  - [ ] 3.2 实现健康检查端点
    - 添加 `GET /health` 端点
    - 返回 `{"status": "ok"}`
    - _Requirements: 1.7_

- [ ] 4. DashScope 客户端实现
  - [ ] 4.1 创建 `app/clients/dashscope_client.py`
    - 实现 DashScopeClient 类
    - 封装 chat() 方法调用 DashScope API
    - 使用 httpx 异步 HTTP 客户端
    - 处理 API 错误和超时
    - _Requirements: 1.6, 2.2, 2.5, 12.3_
  
  - [ ]*4.2 编写 DashScope 客户端单元测试
    - 测试成功调用场景
    - 测试 API 错误处理
    - 使用 mock 隔离外部依赖
    - _Requirements: 2.2, 2.5_

- [ ] 5. 基础对话 API
  - [ ] 5.1 创建 `app/schemas/chat.py` 数据模型
    - 定义 ChatRequest（Id, Question）
    - 定义 ChatResponse（answer）
    - 使用 Pydantic 验证
    - _Requirements: 1.3, 2.1, 2.3_
  
  - [ ] 5.2 创建 `app/services/chat_service.py` 对话服务
    - 实现 ChatService 类
    - 实现 chat() 方法（简单版，无工具、无历史）
    - 调用 DashScopeClient
    - _Requirements: 2.2, 2.3_
  
  - [ ] 5.3 创建 `app/api/routes_chat.py` 对话路由
    - 实现 `POST /api/chat` 端点
    - 使用 FastAPI Depends 注入服务
    - 处理请求和响应
    - _Requirements: 2.1, 2.3_
  
  - [ ]*5.4 编写对话 API 属性测试
    - **Property 1: API 请求数据验证**
    - **Validates: Requirements 1.3, 2.1**
    - 使用 Hypothesis 生成随机 Id 和 Question
    - 验证有效请求返回 200 和 answer 字段
    - 验证无效请求返回 422 和错误信息
  
  - [ ]*5.5 编写对话 API 单元测试
    - 测试成功对话场景
    - 测试 API 错误处理
    - 测试数据验证
    - _Requirements: 2.1, 2.3, 2.5_

- [ ] 6. Milvus 客户端实现
  - [ ] 6.1 创建 `app/clients/milvus_client.py`
    - 实现 MilvusClient 类
    - 实现 connect() 连接方法
    - 实现 health_check() 健康检查
    - 实现 ensure_collection() 确保 collection 存在
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 6.2 添加 Milvus 健康检查端点
    - 创建 `app/api/routes_milvus.py`
    - 实现 `GET /milvus/health` 端点
    - 返回 Milvus 连接状态
    - _Requirements: 3.3_
  
  - [ ]*6.3 编写 Milvus 客户端单元测试
    - 测试连接成功场景
    - 测试连接失败场景
    - 测试健康检查
    - _Requirements: 3.1, 3.3, 3.4_

- [ ] 7. Phase 1 集成测试和验收
  - [ ]*7.1 编写端到端集成测试
    - 测试应用启动
    - 测试健康检查端点
    - 测试基础对话流程
    - 测试 Milvus 连接
  
  - [ ] 7.2 创建启动脚本和文档
    - 编写 README.md 快速开始指南
    - 创建 .env.example 配置示例
    - 测试本地启动流程
  
  - [ ] 7.3 Checkpoint - Phase 1 验收
    - 确保所有 Phase 1 测试通过
    - 验证应用能够启动并响应请求
    - 询问用户是否有问题或需要调整

### Phase 2: 核心功能（3-5 天）

- [ ] 8. 会话管理实现
  - [ ] 8.1 创建 `app/services/session_store.py`
    - 实现 SessionStore 类
    - 实现 add_message() 添加消息
    - 实现 get_history() 获取历史
    - 实现 clear_session() 清空会话
    - 实现历史长度限制（最多 12 条消息）
    - _Requirements: 4.1, 4.2, 4.6_
  
  - [ ]*8.2 编写会话管理属性测试
    - **Property 3: 会话隔离性**
    - **Validates: Requirements 4.1**
    - 验证不同会话的消息不会混淆
    - **Property 4: 会话历史长度限制**
    - **Validates: Requirements 4.2**
    - 验证历史长度不超过 12 条
  
  - [ ]*8.3 编写会话管理单元测试
    - 测试添加消息
    - 测试获取历史
    - 测试清空会话
    - 测试历史长度限制
    - _Requirements: 4.1, 4.2_

- [ ] 9. 会话管理 API
  - [ ] 9.1 创建 `app/schemas/session.py` 会话数据模型
    - 定义 SessionInfo 模型
    - _Requirements: 4.5_
  
  - [ ] 9.2 创建 `app/api/routes_session.py` 会话路由
    - 实现 `POST /api/chat/clear` 清空会话
    - 实现 `GET /api/chat/session/{sessionId}` 查询会话
    - _Requirements: 4.4, 4.5_
  
  - [ ] 9.3 更新对话服务支持会话历史
    - 修改 ChatService.chat() 方法
    - 添加 session_id 参数
    - 从 SessionStore 获取历史
    - 将历史包含在 LLM 调用中
    - 保存新消息到历史
    - _Requirements: 4.1, 4.3_
  
  - [ ]*9.4 编写会话 API 单元测试
    - 测试清空会话
    - 测试查询会话
    - 测试多轮对话
    - _Requirements: 4.3, 4.4, 4.5_

- [ ] 10. 流式对话实现
  - [ ] 10.1 更新 DashScopeClient 支持流式响应
    - 添加 chat_stream() 方法
    - 使用 httpx 流式请求
    - 返回异步生成器
    - _Requirements: 5.1, 5.2_
  
  - [ ] 10.2 更新 ChatService 支持流式对话
    - 添加 chat_stream() 方法
    - 处理流式响应
    - 保存完整对话到历史
    - _Requirements: 5.1, 5.6_
  
  - [ ] 10.3 实现流式对话 API 端点
    - 在 routes_chat.py 添加 `POST /api/chat_stream`
    - 使用 StreamingResponse 返回 SSE
    - 发送 content、done、error 事件
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]*10.4 编写流式响应属性测试
    - **Property 5: 流式响应格式正确性**
    - **Validates: Requirements 5.3**
    - 验证每个 SSE 事件是有效 JSON
    - **Property 6: 流式响应完成信号**
    - **Validates: Requirements 5.4**
    - 验证最后发送 done 事件
  
  - [ ]*10.5 编写流式对话单元测试
    - 测试流式响应格式
    - 测试错误处理
    - 测试历史保存
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 11. 文档切分和向量化
  - [ ] 11.1 创建 `app/rag/chunking.py` 文档切分
    - 实现 DocumentChunker 类
    - 实现 chunk_text() 方法
    - 支持 max_size 和 overlap 配置
    - _Requirements: 6.4_
  
  - [ ]*11.2 编写文档切分属性测试
    - **Property 7: 文档切分覆盖性**
    - **Validates: Requirements 6.4**
    - 验证 chunks 拼接覆盖原文档
  
  - [ ] 11.3 创建 `app/rag/embeddings.py` 向量化服务
    - 实现 EmbeddingService 类
    - 实现 embed_text() 单个文本向量化
    - 实现 embed_texts() 批量向量化
    - 调用 DashScope embedding API
    - _Requirements: 6.5_
  
  - [ ]*11.4 编写向量化服务单元测试
    - 测试单个文本向量化
    - 测试批量向量化
    - 测试 API 错误处理
    - _Requirements: 6.5_

- [ ] 12. 向量存储实现
  - [ ] 12.1 创建 Milvus collection schema
    - 在 MilvusClient 中实现 create_collection()
    - 定义 schema（id, vector, content, metadata）
    - 创建向量索引（IVF_FLAT, IP）
    - _Requirements: 3.5, 6.6_
  
  - [ ] 12.2 创建 `app/rag/vector_store.py` 向量存储
    - 实现 VectorStore 类
    - 实现 insert() 插入文档
    - 实现 search() 检索文档
    - 实现 delete_by_source() 删除旧文档
    - _Requirements: 6.6, 6.7, 7.2_
  
  - [ ]*12.3 编写向量存储属性测试
    - **Property 8: 文档存储检索一致性**
    - **Validates: Requirements 6.6**
    - 验证存储后能检索到文档
    - **Property 10: RAG 检索数量限制**
    - **Validates: Requirements 7.2**
    - 验证检索结果不超过 top-k
  
  - [ ]*12.4 编写向量存储单元测试
    - 测试插入文档
    - 测试检索文档
    - 测试删除文档
    - _Requirements: 6.6, 6.7, 7.2_

- [ ] 13. 文件上传 API
  - [ ] 13.1 创建 `app/schemas/upload.py` 上传数据模型
    - 定义 UploadResponse 模型
    - _Requirements: 6.8_
  
  - [ ] 13.2 创建 `app/services/vector_index_service.py` 索引服务
    - 实现 VectorIndexService 类
    - 实现 index_document() 索引文档
    - 整合 chunking、embedding、vector_store
    - 处理同名文件覆盖更新
    - _Requirements: 6.4, 6.5, 6.6, 6.7_
  
  - [ ] 13.3 创建 `app/api/routes_upload.py` 上传路由
    - 实现 `POST /api/upload` 端点
    - 接受文件上传
    - 验证文件格式（.txt, .md）
    - 保存文件到 uploads 目录
    - 调用索引服务处理文件
    - _Requirements: 6.1, 6.2, 6.3, 6.8_
  
  - [ ]*13.4 编写上传 API 属性测试
    - **Property 9: 上传响应完整性**
    - **Validates: Requirements 6.8**
    - 验证响应包含 filename、chunks、status
  
  - [ ]*13.5 编写上传 API 单元测试
    - 测试上传 .txt 文件
    - 测试上传 .md 文件
    - 测试上传不支持的格式
    - 测试同名文件覆盖
    - _Requirements: 6.1, 6.2, 6.3, 6.7, 6.8_

- [ ] 14. RAG 服务实现
  - [ ] 14.1 创建 `app/services/rag_service.py` RAG 服务
    - 实现 RagService 类
    - 实现 query() 方法
    - 整合检索和生成
    - 构建 RAG prompt 模板
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ] 14.2 更新对话 API 支持 RAG
    - 修改 routes_chat.py
    - 根据请求决定使用 RAG 或普通对话
    - _Requirements: 7.1, 7.5_
  
  - [ ]*14.3 编写 RAG 服务属性测试
    - **Property 11: RAG 响应来源信息**
    - **Validates: Requirements 7.5**
    - 验证响应包含 sources 字段
  
  - [ ]*14.4 编写 RAG 服务单元测试
    - 测试 RAG 查询流程
    - 测试空知识库场景
    - 测试 prompt 构建
    - _Requirements: 7.1, 7.3, 7.4, 7.5, 7.6_

- [ ] 15. 基础工具实现
  - [ ] 15.1 创建 `app/agents/tools/datetime_tool.py`
    - 使用 @tool 装饰器定义工具
    - 实现 get_current_datetime() 函数
    - _Requirements: 8.1_
  
  - [ ] 15.2 创建 `app/agents/tools/internal_docs_tool.py`
    - 实现 query_internal_docs() 工具
    - 调用 VectorStore 检索文档
    - 格式化返回结果
    - _Requirements: 8.2_
  
  - [ ]*15.3 编写工具单元测试
    - 测试时间工具
    - 测试文档检索工具
    - _Requirements: 8.1, 8.2_

- [ ] 16. LangChain Agent 集成
  - [ ] 16.1 创建 `app/agents/chat_agent.py` 对话 Agent
    - 实现 ChatAgent 类
    - 使用 LangChain create_react_agent
    - 配置 ChatTongyi LLM
    - 注册工具
    - _Requirements: 8.3, 8.4_
  
  - [ ] 16.2 更新 ChatService 使用 Agent
    - 修改 chat() 方法使用 ChatAgent
    - 支持工具调用
    - 记录工具调用日志
    - _Requirements: 8.4, 8.5_
  
  - [ ]*16.3 编写 Agent 集成测试
    - 测试工具调用流程
    - 测试工具失败处理
    - _Requirements: 8.4, 8.6_

- [ ] 17. Phase 2 集成测试和验收
  - [ ]*17.1 编写完整的上传-查询流程测试
    - 测试上传文档
    - 测试 RAG 查询
    - 测试多轮对话
    - 测试流式响应
  
  - [ ] 17.2 更新文档和示例
    - 更新 README.md
    - 添加 API 使用示例
    - 添加配置说明
  
  - [ ] 17.3 Checkpoint - Phase 2 验收
    - 确保所有 Phase 2 测试通过
    - 验证 RAG 和工具调用正常工作
    - 询问用户是否有问题或需要调整

### Phase 3: 完整功能（4-6 天）

- [ ] 18. Prometheus 客户端实现
  - [ ] 18.1 创建 `app/clients/prometheus_client.py`
    - 实现 PrometheusClient 类
    - 实现 get_alerts() 查询告警
    - 实现 query() 执行 PromQL
    - 使用 httpx 异步调用
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ]*18.2 编写 Prometheus 客户端单元测试
    - 测试查询告警
    - 测试执行 PromQL
    - 测试连接失败处理
    - _Requirements: 9.1, 9.2, 9.5_

- [ ] 19. Prometheus 工具实现
  - [ ] 19.1 创建 `app/agents/tools/prometheus_tool.py`
    - 实现 query_prometheus_alerts() 工具
    - 实现 query_prometheus_metrics() 工具
    - 格式化返回结果
    - _Requirements: 9.1, 9.2_
  
  - [ ]*19.2 编写 Prometheus 工具单元测试
    - 测试告警查询工具
    - 测试指标查询工具
    - _Requirements: 9.1, 9.2_

- [ ] 20. AIOps LangGraph 实现
  - [ ] 20.1 创建 `app/agents/aiops_graph.py` - 状态定义
    - 定义 AIOpsState TypedDict
    - 包含 input、planner_plan、executor_feedback 等字段
    - _Requirements: 10.1, 10.2_
  
  - [ ] 20.2 实现 Planner Agent 节点
    - 实现 _planner_node() 方法
    - 构建 Planner prompt
    - 解析 decision（PLAN/EXECUTE/FINISH）
    - _Requirements: 10.2, 10.3, 10.7_
  
  - [ ] 20.3 实现 Executor Agent 节点
    - 实现 _executor_node() 方法
    - 构建 Executor prompt
    - 执行工具调用
    - 返回执行结果
    - _Requirements: 10.2, 10.4_
  
  - [ ] 20.4 实现 Supervisor Agent 节点
    - 实现 _supervisor_node() 方法
    - 协调 Planner 和 Executor
    - 判断是否继续循环
    - _Requirements: 10.2, 10.5_
  
  - [ ] 20.5 构建 LangGraph 工作流
    - 使用 StateGraph 构建图
    - 添加节点和边
    - 添加条件边（根据 decision）
    - 实现 run() 方法
    - _Requirements: 10.2, 10.6_
  
  - [ ]*20.6 编写 AIOps Graph 单元测试
    - 测试 Planner 节点
    - 测试 Executor 节点
    - 测试 Supervisor 节点
    - 测试工作流循环
    - _Requirements: 10.2, 10.3, 10.4, 10.5_

- [ ] 21. AIOps 服务和 API
  - [ ] 21.1 创建 `app/schemas/aiops.py` AIOps 数据模型
    - 定义 AIOpsRequest 模型
    - 定义 AIOpsResponse 模型
    - _Requirements: 10.1_
  
  - [ ] 21.2 创建 `app/services/aiops_service.py` AIOps 服务
    - 实现 AiOpsService 类
    - 实现 analyze() 方法
    - 调用 AIOpsGraph
    - 提取最终报告
    - _Requirements: 10.1, 10.8_
  
  - [ ] 21.3 创建 `app/api/routes_aiops.py` AIOps 路由
    - 实现 `POST /api/ai_ops` 端点
    - 使用 StreamingResponse 返回 SSE
    - 流式输出报告生成过程
    - _Requirements: 10.1, 10.9_
  
  - [ ]*21.4 编写 AIOps API 属性测试
    - **Property 12: AIOps 报告格式完整性**
    - **Validates: Requirements 10.8, 10.10**
    - 验证报告包含必需章节
  
  - [ ]*21.5 编写 AIOps API 单元测试
    - 测试 AIOps 分析流程
    - 测试报告生成
    - 测试流式输出
    - _Requirements: 10.1, 10.8, 10.9, 10.10_

- [ ] 22. Docker 容器化
  - [ ] 22.1 创建 Dockerfile
    - 使用 Python 3.11 基础镜像
    - 安装依赖
    - 复制代码
    - 配置启动命令
    - _Requirements: 11.3_
  
  - [ ] 22.2 创建 docker-compose.yml
    - 定义 Milvus 服务（etcd, minio, milvus）
    - 定义应用服务
    - 配置网络和卷
    - _Requirements: 11.1, 11.2, 11.4, 11.5_
  
  - [ ] 22.3 测试 Docker 部署
    - 测试 docker-compose up 启动
    - 测试服务间通信
    - 测试数据持久化
    - _Requirements: 11.4, 11.5, 11.6_

- [ ] 23. 完整测试套件
  - [ ]*23.1 补充缺失的单元测试
    - 确保核心模块测试覆盖率 > 80%
    - _Requirements: 14.1_
  
  - [ ]*23.2 补充集成测试
    - 测试完整的 AIOps 流程
    - 测试错误场景
    - _Requirements: 14.2_
  
  - [ ]*23.3 配置测试覆盖率报告
    - 配置 pytest-cov
    - 生成覆盖率报告
    - _Requirements: 14.5_

- [ ] 24. 文档和示例
  - [ ] 24.1 完善 README.md
    - 添加项目介绍
    - 添加快速开始指南
    - 添加 API 文档
    - 添加配置说明
    - 添加部署指南
  
  - [ ] 24.2 创建 API 使用示例
    - 创建 examples/ 目录
    - 添加对话示例
    - 添加上传示例
    - 添加 AIOps 示例
  
  - [ ] 24.3 创建开发者文档
    - 添加架构说明
    - 添加开发指南
    - 添加测试指南

- [ ] 25. Phase 3 验收和优化
  - [ ] 25.1 性能测试和优化
    - 测试 API 响应时间
    - 测试并发性能
    - 优化慢查询
  
  - [ ] 25.2 安全审查
    - 检查 API 密钥保护
    - 检查输入验证
    - 检查错误信息泄露
  
  - [ ] 25.3 最终验收
    - 确保所有测试通过
    - 验证 Docker 部署正常
    - 验证文档完整
    - 询问用户反馈和改进建议

## Notes

- 标记 `*` 的任务为可选任务（主要是测试相关），可以根据时间和需求决定是否实施
- 每个 Checkpoint 任务是暂停点，确保当前阶段完成并征求用户反馈
- 任务按照依赖关系排序，建议按顺序执行
- 每个任务都引用了对应的需求编号，便于追溯
- 属性测试任务明确标注了对应的设计属性编号
