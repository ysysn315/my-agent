# LangChain Tool 机制详解

## 目录
1. [Tool 是什么](#1-tool-是什么)
2. [Tool 的定义方式](#2-tool-的定义方式)
3. [Tool 如何绑定到 LLM](#3-tool-如何绑定到-llm)
4. [LLM 如何调用 Tool](#4-llm-如何调用-tool)
5. [chat_agent.py 中的 Tool 流程](#5-chat_agentpy-中的-tool-流程)
6. [完整示例](#6-完整示例)

---

## 1. Tool 是什么？

**Tool（工具）** 是 Agent 可以调用的函数，用于执行特定任务。

### 类比理解
想象你是一个助手（Agent），老板（用户）问你："现在几点了？"

- **没有 Tool**：你只能猜测或编造答案
- **有 Tool**：你可以调用 `get_current_time()` 函数获取准确时间

### Tool 的组成
```python
@tool
def get_current_datetime() -> str:
    """获取当前日期和时间
    
    返回:
        当前的日期和时间，格式为 YYYY-MM-DD HH:MM:SS
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

一个 Tool 包含：
1. **函数名**：`get_current_datetime`（LLM 会看到这个名字）
2. **描述**：docstring 中的内容（LLM 根据这个决定是否调用）
3. **参数**：函数的参数（LLM 会根据参数类型和描述传值）
4. **返回值**：函数的返回结果（会返回给 LLM）

---

## 2. Tool 的定义方式

### 方式 1：使用 `@tool` 装饰器（推荐）

```python
from langchain.tools import tool

@tool
def query_log(query: str, time_range: str = "5m") -> str:
    """查询系统日志
    
    参数:
        query: 查询关键词（如 "cpu", "error"）
        time_range: 时间范围（默认 "5m"）
    
    返回:
        JSON格式的日志列表
    """
    # 实现逻辑
    return json.dumps({"logs": [...]})
```

**LLM 看到的信息：**
```json
{
  "name": "query_log",
  "description": "查询系统日志\n\n参数:\n    query: 查询关键词...",
  "parameters": {
    "query": {"type": "string", "description": "查询关键词"},
    "time_range": {"type": "string", "default": "5m"}
  }
}
```

### 方式 2：使用 `Tool` 类

```python
from langchain.tools import Tool

def my_function(input: str) -> str:
    return f"处理: {input}"

tool = Tool(
    name="my_tool",
    description="这是一个示例工具",
    func=my_function
)
```

---

## 3. Tool 如何绑定到 LLM？

### 在 chat_agent.py 中的绑定

```python
# 步骤 1: 创建 LLM
llm = ChatTongyi(
    dashscope_api_key=api_key,
    model_name=model,
    streaming=False
)

# 步骤 2: 绑定工具
self.llm = llm.bind_tools(tools)
```

### `bind_tools()` 做了什么？

1. **转换工具定义**：将 Python 函数转换为 LLM 能理解的 JSON Schema
2. **注入到 LLM**：告诉 LLM "你可以调用这些工具"
3. **返回新的 LLM**：返回一个增强版的 LLM，它知道如何请求工具调用

### 示例：LLM 收到的工具信息

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "query_log",
        "description": "查询系统日志...",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "查询关键词"},
            "time_range": {"type": "string", "default": "5m"}
          },
          "required": ["query"]
        }
      }
    }
  ]
}
```

---

## 4. LLM 如何调用 Tool？

### 完整流程图

```
用户问题: "查询最近的 CPU 日志"
    ↓
┌─────────────────────────────────────────┐
│  LLM 分析问题                            │
│  - 需要查询日志                          │
│  - 应该调用 query_log 工具               │
│  - 参数: query="cpu", time_range="5m"   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  LLM 返回 tool_calls                     │
│  [                                       │
│    {                                     │
│      "id": "call_abc123",               │
│      "name": "query_log",               │
│      "args": {                          │
│        "query": "cpu",                  │
│        "time_range": "5m"               │
│      }                                   │
│    }                                     │
│  ]                                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Agent 执行工具                          │
│  result = query_log.invoke({            │
│    "query": "cpu",                      │
│    "time_range": "5m"                   │
│  })                                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  构造 ToolMessage                        │
│  ToolMessage(                            │
│    content=result,                      │
│    tool_call_id="call_abc123"           │
│  )                                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  将结果返回给 LLM                        │
│  LLM 根据工具结果生成最终答案            │
└─────────────────────────────────────────┘
    ↓
最终答案: "根据日志显示，CPU 使用率为 92%..."
```

---

## 5. chat_agent.py 中的 Tool 流程

### 代码逐行解析

#### 5.1 初始化：绑定工具

```python
def __init__(self, api_key: str, model: str, tools: List):
    # 创建 LLM 并绑定工具
    self.llm = ChatTongyi(
        dashscope_api_key=api_key,
        model_name=model,
        streaming=False
    ).bind_tools(tools)  # ← 关键：绑定工具
    
    # 保存工具字典（方便后续调用）
    self.tools = {tool.name: tool for tool in tools}
    # 结果: {"query_log": <Tool>, "query_prometheus_alerts": <Tool>}
```

#### 5.2 LLM 节点：调用模型

```python
async def call_model(state: AgentState):
    """调用 LLM"""
    messages = state["messages"]
    # 调用 LLM（LLM 可能返回普通回答或 tool_calls）
    response = await self.llm.ainvoke(messages)
    
    # response 可能是：
    # 1. 普通回答: AIMessage(content="你好！")
    # 2. 工具调用: AIMessage(content="", tool_calls=[{...}])
    
    return {"messages": [response]}
```

#### 5.3 工具节点：执行工具

```python
async def call_tools(state: AgentState):
    """调用工具"""
    # 获取最后一条消息（LLM 的响应）
    last_message = state["messages"][-1]
    
    # 提取 tool_calls
    tool_calls = last_message.tool_calls
    # tool_calls 示例:
    # [
    #   {
    #     "id": "call_abc123",
    #     "name": "query_log",
    #     "args": {"query": "cpu", "time_range": "5m"}
    #   }
    # ]
    
    results = []
    for tool_call in tool_calls:
        # 1. 提取工具信息
        tool_name = tool_call["name"]        # "query_log"
        tool_args = tool_call["args"]        # {"query": "cpu", ...}
        
        # 2. 获取工具对象
        tool = self.tools[tool_name]         # 从字典中获取工具
        
        # 3. 执行工具
        result = await tool.ainvoke(tool_args)
        # result = '{"success": true, "logs": [...]}'
        
        # 4. 构造 ToolMessage
        from langchain_core.messages import ToolMessage
        results.append(ToolMessage(
            content=str(result),              # 工具返回的结果
            tool_call_id=tool_call["id"]     # 关联到原始调用
        ))
    
    # 返回所有工具结果
    return {"messages": results}
```

#### 5.4 条件判断：是否需要调用工具

```python
def should_continue(state: AgentState):
    """判断是否继续"""
    last_message = state["messages"][-1]
    
    # 检查最后一条消息是否包含 tool_calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"  # 需要调用工具
    return "end"        # 不需要，结束
```

---

## 6. 完整示例

### 示例对话：查询 CPU 日志

#### 输入
```python
question = "帮我查询最近的 CPU 相关日志"
```

#### 执行流程

**第 1 轮：Agent 节点**
```python
# 输入消息
messages = [
    SystemMessage(content="你是一个有用的助手..."),
    HumanMessage(content="帮我查询最近的 CPU 相关日志")
]

# LLM 响应
response = AIMessage(
    content="",
    tool_calls=[
        {
            "id": "call_xyz789",
            "name": "query_log",
            "args": {"query": "cpu", "time_range": "5m"}
        }
    ]
)
```

**第 2 轮：Tools 节点**
```python
# 执行工具
tool = self.tools["query_log"]
result = await tool.ainvoke({"query": "cpu", "time_range": "5m"})
# result = '{"success": true, "logs": [...]}'

# 构造 ToolMessage
tool_message = ToolMessage(
    content=result,
    tool_call_id="call_xyz789"
)
```

**第 3 轮：Agent 节点（再次）**
```python
# 输入消息（包含工具结果）
messages = [
    SystemMessage(...),
    HumanMessage("帮我查询最近的 CPU 相关日志"),
    AIMessage(tool_calls=[...]),
    ToolMessage(content='{"success": true, "logs": [...]}')
]

# LLM 根据工具结果生成最终答案
response = AIMessage(
    content="根据日志显示，最近 5 分钟内 payment-service 的 CPU 使用率持续在 90% 以上..."
)
```

**结束**
```python
# 没有 tool_calls，返回 "end"
return response.content
```

---

## 关键概念总结

### 1. `bind_tools(tools)`
- **作用**：告诉 LLM 可以调用哪些工具
- **输入**：工具列表 `[tool1, tool2, ...]`
- **输出**：增强版 LLM（知道如何请求工具调用）

### 2. `tool_calls`
- **定义**：LLM 返回的工具调用请求
- **格式**：`[{"id": "...", "name": "...", "args": {...}}]`
- **作用**：告诉 Agent 需要调用哪个工具、传什么参数

### 3. `ToolMessage`
- **定义**：工具执行结果的消息
- **格式**：`ToolMessage(content="...", tool_call_id="...")`
- **作用**：将工具结果返回给 LLM

### 4. 工具字典 `self.tools`
- **定义**：`{tool.name: tool}` 的映射
- **作用**：根据工具名快速找到工具对象
- **示例**：`self.tools["query_log"]` → `<Tool query_log>`

---

## 常见问题

### Q1: 为什么要用 `tool_call_id`？
**A:** 关联工具调用和结果。如果 LLM 同时调用多个工具，需要知道哪个结果对应哪个调用。

### Q2: 工具可以返回什么类型？
**A:** 通常返回字符串（`str`），因为 LLM 只能理解文本。复杂数据用 JSON 字符串。

### Q3: 如果工具执行失败怎么办？
**A:** 可以在 `call_tools` 中添加 try-except，返回错误信息给 LLM。

```python
try:
    result = await tool.ainvoke(tool_args)
except Exception as e:
    result = f"工具执行失败: {str(e)}"
```

### Q4: LLM 如何知道该调用哪个工具？
**A:** 根据工具的 `description`（docstring）。所以工具描述要清晰准确！

---

## 下一步学习

1. ✅ 理解 Tool 的基本概念
2. ✅ 理解 `bind_tools()` 的作用
3. ✅ 理解 `tool_calls` 和 `ToolMessage`
4. 📝 动手：修改 `query_log` 的描述，看 LLM 是否会调用
5. 📝 动手：添加一个新工具 `get_current_time`
6. 📝 动手：测试多工具调用（一次调用多个工具）

---

## 参考资料

- LangChain Tools 文档: https://python.langchain.com/docs/how_to/custom_tools/
- LangGraph Tool Calling: https://langchain-ai.github.io/langgraph/how-tos/tool-calling/
