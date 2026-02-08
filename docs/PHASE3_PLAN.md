# Phase 3 完整功能规划

## 📋 Phase 3 概述

**目标**: 实现 AIOps 多 Agent 协作和生产级特性

**预计时间**: 4-6 天

**核心价值**: 
- 实现智能运维告警分析
- 多 Agent 协作（Planner-Executor-Supervisor）
- 生产级部署和监控

---

## 🎯 Phase 3 需要完成的功能

### 1. Prometheus 集成 (1 天)

#### 1.1 Prometheus 客户端
**文件**: `app/clients/prometheus_client.py`

**功能**:
- 查询活跃告警 (`get_alerts()`)
- 执行 PromQL 查询 (`query()`)
- 异步 HTTP 调用
- 错误处理和超时控制

**技术要点**:
- 使用 `httpx.AsyncClient`
- Prometheus HTTP API: `/api/v1/alerts`, `/api/v1/query`
- 10 秒超时
- 友好的错误信息

**预计时间**: 2-3 小时

---

#### 1.2 Prometheus 工具
**文件**: `app/agents/tools/prometheus_tool.py`

**功能**:
- `query_prometheus_alerts()`: 查询告警工具
- `query_prometheus_metrics()`: 查询指标工具
- 格式化返回结果供 Agent 使用

**技术要点**:
- 使用 LangChain `@tool` 装饰器
- 返回结构化的字符串结果
- 处理空结果情况

**预计时间**: 1-2 小时

---

### 2. AIOps LangGraph 实现 (2-3 天) ⭐ 核心

#### 2.1 状态定义
**文件**: `app/agents/aiops_graph.py`

**AIOpsState 结构**:
```python
class AIOpsState(TypedDict):
    input: str                  # 用户输入的任务
    planner_plan: str           # Planner 的计划
    executor_feedback: str      # Executor 的执行反馈
    decision: str               # PLAN/EXECUTE/FINISH
    final_report: str           # 最终报告
    iteration: int              # 当前迭代次数
```

**预计时间**: 1 小时

---

#### 2.2 Planner Agent 节点
**职责**: 分析告警，制定执行计划

**输入**:
- 当前任务
- Executor 的反馈（如果有）

**输出**:
- JSON 格式的计划
- decision: PLAN/EXECUTE/FINISH
- 下一步要执行的操作
- 需要调用的工具

**Prompt 设计**:
```
你是 Planner Agent，负责分析告警并制定执行计划。

当前任务：{input}
Executor 反馈：{executor_feedback}

请输出 JSON 格式的计划：
{
  "decision": "PLAN|EXECUTE|FINISH",
  "step": "下一步要执行的操作",
  "tool": "需要调用的工具",
  "context": "相关上下文"
}

如果已完成分析，decision 设为 FINISH，并输出完整的 Markdown 告警分析报告。
```

**预计时间**: 3-4 小时

---

#### 2.3 Executor Agent 节点
**职责**: 执行 Planner 的计划，调用工具

**输入**:
- Planner 的计划

**输出**:
- JSON 格式的执行结果
- status: SUCCESS/FAILED
- 工具返回的证据
- 给 Planner 的建议

**关键逻辑**:
- 解析 Planner 的计划
- 调用相应的工具（Prometheus、文档检索等）
- 返回真实的工具执行结果
- **禁止编造数据**

**预计时间**: 3-4 小时

---

#### 2.4 Supervisor Agent 节点
**职责**: 协调 Planner 和 Executor，决定是否继续

**判断逻辑**:
- 如果 decision == "FINISH" → 结束
- 如果 iteration > 10 → 强制结束（防止死循环）
- 如果同一工具连续失败 3 次 → 结束
- 否则 → 继续循环

**预计时间**: 2-3 小时

---

#### 2.5 LangGraph 工作流构建
**核心**: 使用 `StateGraph` 构建多 Agent 协作流程

**图结构**:
```
START → Supervisor → Planner → Executor → Supervisor → ...
                                              ↓
                                            END (decision == FINISH)
```

**条件边**:
- Supervisor 根据 decision 决定下一步
- "continue" → 回到 Planner
- "finish" → END

**预计时间**: 2-3 小时

---

### 3. AIOps 服务和 API (1 天)

#### 3.1 AIOps 服务
**文件**: `app/services/aiops_service.py`

**功能**:
- 封装 AIOpsGraph
- 提供 `analyze()` 方法
- 提取最终报告

**预计时间**: 1-2 小时

---

#### 3.2 AIOps API
**文件**: `app/api/routes_aiops.py`

**端点**: `POST /api/ai_ops`

**功能**:
- 接受 AIOps 分析请求
- 使用 SSE 流式输出报告生成过程
- 返回最终的 Markdown 报告

**报告格式**:
```markdown
# 告警分析报告

## 活跃告警清单
- 告警 1: ...
- 告警 2: ...

## 告警根因分析
...

## 处理方案执行
...

## 结论
...
```

**预计时间**: 2-3 小时

---

### 4. Docker 容器化 (0.5 天)

#### 4.1 Dockerfile
**功能**:
- Python 3.11 基础镜像
- 安装依赖
- 复制代码
- 配置启动命令

**预计时间**: 1 小时

---

#### 4.2 docker-compose.yml
**服务**:
- etcd (Milvus 依赖)
- minio (Milvus 依赖)
- milvus (向量数据库)
- app (Python 应用)

**功能**:
- 一键启动所有服务
- 数据持久化
- 网络配置

**预计时间**: 1-2 小时

---

### 5. 测试和文档 (1 天)

#### 5.1 单元测试
- Prometheus 客户端测试
- Prometheus 工具测试
- AIOps Graph 节点测试

**预计时间**: 2-3 小时

---

#### 5.2 集成测试
- 完整的 AIOps 分析流程测试
- Docker 部署测试

**预计时间**: 2-3 小时

---

#### 5.3 文档
- 更新 README.md
- 添加 AIOps 使用示例
- 添加部署指南

**预计时间**: 1-2 小时

---

## 🛠️ 技术栈总结

### 新增技术栈 (Phase 3)

| 技术 | 用途 | 难度 |
|------|------|------|
| **LangGraph** | 多 Agent 编排 | ⭐⭐⭐⭐ |
| **Prometheus API** | 告警和指标查询 | ⭐⭐ |
| **Docker Compose** | 容器编排 | ⭐⭐ |
| **SSE (Server-Sent Events)** | 流式输出 | ⭐⭐ |

### 已有技术栈 (Phase 1-2)

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| LangChain | AI 框架 |
| DashScope | LLM 服务 |
| Milvus | 向量数据库 |
| Pydantic | 数据验证 |
| httpx | HTTP 客户端 |
| loguru | 日志 |

---

## ⏱️ 时间估算

### 详细时间分配

| 任务 | 预计时间 | 难度 |
|------|---------|------|
| **1. Prometheus 集成** | 0.5-1 天 | ⭐⭐ |
| - Prometheus 客户端 | 2-3 小时 | ⭐⭐ |
| - Prometheus 工具 | 1-2 小时 | ⭐ |
| **2. AIOps LangGraph** | 2-3 天 | ⭐⭐⭐⭐⭐ |
| - 状态定义 | 1 小时 | ⭐ |
| - Planner Agent | 3-4 小时 | ⭐⭐⭐⭐ |
| - Executor Agent | 3-4 小时 | ⭐⭐⭐⭐ |
| - Supervisor Agent | 2-3 小时 | ⭐⭐⭐ |
| - LangGraph 构建 | 2-3 小时 | ⭐⭐⭐⭐ |
| - 调试和优化 | 4-6 小时 | ⭐⭐⭐⭐ |
| **3. AIOps 服务和 API** | 0.5-1 天 | ⭐⭐⭐ |
| - AIOps 服务 | 1-2 小时 | ⭐⭐ |
| - AIOps API | 2-3 小时 | ⭐⭐⭐ |
| **4. Docker 容器化** | 0.5 天 | ⭐⭐ |
| - Dockerfile | 1 小时 | ⭐ |
| - docker-compose.yml | 1-2 小时 | ⭐⭐ |
| **5. 测试和文档** | 1 天 | ⭐⭐⭐ |
| - 单元测试 | 2-3 小时 | ⭐⭐ |
| - 集成测试 | 2-3 小时 | ⭐⭐⭐ |
| - 文档 | 1-2 小时 | ⭐ |
| **总计** | **4-6 天** | |

### 关键路径

1. **LangGraph 实现** (最复杂，2-3 天)
2. Prometheus 集成 (0.5-1 天)
3. AIOps API (0.5-1 天)
4. Docker 和测试 (1-1.5 天)

---

## 🎓 LangGraph 学习重点

### 核心概念 (必须掌握)

#### 1. StateGraph - 状态图 ⭐⭐⭐⭐⭐
**最重要的概念**

**作用**: 定义 Agent 工作流的状态机

**关键 API**:
```python
from langgraph.graph import StateGraph, END

# 创建状态图
workflow = StateGraph(StateType)

# 添加节点
workflow.add_node("node_name", node_function)

# 设置入口
workflow.set_entry_point("start_node")

# 添加边（固定路径）
workflow.add_edge("node_a", "node_b")

# 添加条件边（动态路径）
workflow.add_conditional_edges(
    "node_a",
    condition_function,
    {
        "path1": "node_b",
        "path2": "node_c",
        "end": END
    }
)

# 编译图
graph = workflow.compile()

# 执行图
result = await graph.ainvoke(initial_state)
```

**学习重点**:
- 如何定义状态（TypedDict）
- 如何添加节点和边
- 如何使用条件边实现动态路由
- 如何编译和执行图

---

#### 2. State Management - 状态管理 ⭐⭐⭐⭐
**作用**: 在节点间传递和更新状态

**关键概念**:
```python
from typing import TypedDict, Annotated
import operator

class MyState(TypedDict):
    # 普通字段：每次更新会覆盖
    current_step: str
    
    # 累加字段：使用 operator.add 累加
    messages: Annotated[List, operator.add]
    
    # 计数字段
    iteration: int
```

**状态更新规则**:
- 节点函数返回的字典会**合并**到当前状态
- 使用 `Annotated[List, operator.add]` 可以累加列表
- 状态在整个图执行过程中持久化

**学习重点**:
- 如何定义状态结构
- 如何在节点中更新状态
- 如何使用 Annotated 实现累加

---

#### 3. Nodes - 节点函数 ⭐⭐⭐⭐
**作用**: 执行具体的逻辑

**节点函数签名**:
```python
async def my_node(state: MyState) -> MyState:
    # 1. 读取当前状态
    current_value = state["some_field"]
    
    # 2. 执行逻辑（调用 LLM、工具等）
    result = await some_operation(current_value)
    
    # 3. 返回状态更新
    return {
        "some_field": result,
        "iteration": state.get("iteration", 0) + 1
    }
```

**学习重点**:
- 节点函数必须接受 state 参数
- 节点函数返回字典（部分状态更新）
- 节点可以是同步或异步函数

---

#### 4. Conditional Edges - 条件边 ⭐⭐⭐⭐⭐
**作用**: 根据状态动态决定下一步

**示例**:
```python
def should_continue(state: MyState) -> str:
    """决定下一步走哪条路径"""
    if state["decision"] == "FINISH":
        return "end"
    if state["iteration"] > 10:
        return "end"
    return "continue"

workflow.add_conditional_edges(
    "supervisor",
    should_continue,
    {
        "continue": "planner",
        "end": END
    }
)
```

**学习重点**:
- 条件函数返回字符串（路径名）
- 路径名必须在映射字典中定义
- 使用 `END` 表示结束

---

#### 5. Cycles - 循环 ⭐⭐⭐⭐
**作用**: 实现多轮迭代

**示例**:
```python
# Planner → Executor → Supervisor → Planner (循环)
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    should_continue,
    {
        "continue": "planner",  # 回到 Planner，形成循环
        "end": END
    }
)
```

**学习重点**:
- 如何构建循环结构
- 如何设置循环终止条件
- 如何防止死循环

---

### 进阶概念 (可选)

#### 6. Checkpointing - 检查点 ⭐⭐⭐
**作用**: 保存中间状态，支持暂停和恢复

**使用场景**:
- 长时间运行的任务
- 需要人工审核的流程
- 错误恢复

**学习优先级**: 中（Phase 3 可选）

---

#### 7. Streaming - 流式输出 ⭐⭐⭐
**作用**: 实时输出中间结果

**使用场景**:
- 实时显示 Agent 思考过程
- 流式生成报告

**学习优先级**: 高（Phase 3 需要）

---

#### 8. Human-in-the-Loop - 人工介入 ⭐⭐
**作用**: 在流程中加入人工审核

**学习优先级**: 低（Phase 3 不需要）

---

### 学习资源

#### 官方文档 (必读)
1. **Quick Start**: https://langchain-ai.github.io/langgraph/tutorials/introduction/
   - 15-30 分钟快速入门
   - 理解基本概念

2. **State Management**: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
   - 理解状态如何传递和更新

3. **Conditional Edges**: https://langchain-ai.github.io/langgraph/how-tos/branching/
   - 学习动态路由

4. **Multi-Agent**: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/
   - 多 Agent 协作示例（与 Phase 3 最相关）

#### 示例代码 (推荐)
1. **ReAct Agent**: 简单的工具调用 Agent
2. **Multi-Agent Collaboration**: Planner-Executor 模式
3. **Supervisor Pattern**: 监督者模式

---

### 学习计划建议

#### Day 1 上午 (2-3 小时)
- 阅读 Quick Start
- 运行官方示例
- 理解 StateGraph 基本用法

#### Day 1 下午 (2-3 小时)
- 阅读 Multi-Agent 教程
- 理解 Planner-Executor 模式
- 尝试修改示例代码

#### Day 2 (根据需要)
- 深入学习条件边和循环
- 学习流式输出
- 开始实现 Phase 3

---

## 🎯 Phase 3 成功标准

### 功能验收
- [ ] Prometheus 能够查询告警和指标
- [ ] AIOps 能够生成完整的 Markdown 报告
- [ ] 报告包含：告警清单、根因分析、处理方案、结论
- [ ] 使用 SSE 流式输出报告生成过程
- [ ] Docker 一键启动所有服务
- [ ] 测试覆盖率 > 85%

### 性能标准
- [ ] AIOps 分析完成时间 < 2 分钟
- [ ] Prometheus 查询响应时间 < 1 秒
- [ ] 支持 10 轮以内的 Planner-Executor 循环

### 质量标准
- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 代码符合 PEP 8 规范
- [ ] 文档完整清晰

---

## 💡 开发建议

### 1. 先简单后复杂
- 先实现单个 Agent 节点
- 再连接成简单的线性流程
- 最后添加循环和条件判断

### 2. 充分测试
- 每个节点单独测试
- 测试各种边界情况
- 测试循环终止条件

### 3. 日志和调试
- 在每个节点打印状态
- 记录 LLM 的输入输出
- 使用 LangSmith 调试（可选）

### 4. 错误处理
- 工具调用失败的处理
- LLM 返回格式错误的处理
- 循环超时的处理

---

## 📚 参考资料

### LangGraph 官方文档
- 官网: https://langchain-ai.github.io/langgraph/
- GitHub: https://github.com/langchain-ai/langgraph
- 示例: https://github.com/langchain-ai/langgraph/tree/main/examples

### 相关技术文档
- Prometheus API: https://prometheus.io/docs/prometheus/latest/querying/api/
- Docker Compose: https://docs.docker.com/compose/
- FastAPI SSE: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

---

## 🚀 开始 Phase 3

准备好了吗？建议按以下顺序开始：

1. **明天上午**: 学习 LangGraph 官方文档 (2-3 小时)
2. **明天下午**: 实现 Prometheus 集成 (简单，建立信心)
3. **Day 2-3**: 实现 AIOps LangGraph (核心，最复杂)
4. **Day 4**: 实现 AIOps API 和测试
5. **Day 5**: Docker 容器化和文档

祝你学习顺利！有任何问题随时问我 😊
