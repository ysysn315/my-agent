# # AIOps Agent - 自动化运维故障排查
# # 使用 Planner-Operation-Reflection 模式
#
# from langchain_community.chat_models import ChatTongyi
# from typing import List, TypedDict, Annotated, Literal
# from loguru import logger
# from langgraph.graph import StateGraph, END
# from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# import operator
# import json
#
#
# # ==================== State 定义 ====================
#
# class AIOpsState(TypedDict):
#     """AIOps Agent 状态定义
#
#     State 在 Planner-Operation-Reflection 循环中传递，保存所有必要信息
#     """
#     # 用户输入
#     input: str  # 用户的问题或告警描述
#
#     # 排查计划
#     plan: str  # Planner 生成的排查计划（步骤列表）
#
#     # 执行历史（使用 operator.add 自动合并）
#     past_steps: Annotated[List[str], operator.add]  # 已执行的步骤和结果
#
#     # 循环控制
#     iteration: int  # 当前循环次数（防止无限循环，最大3次）
#
#     # 最终输出
#     response: str  # 最终的分析报告
#
#
# # ==================== AIOps Agent 类 ====================
#
# class AIOpsAgent:
#     """AIOps Agent - 自动化故障排查和根因分析
#
#     使用 Planner-Operation-Reflection 模式:
#     - Planner: 制定排查计划
#     - Operation: 执行操作（调用工具）
#     - Reflection: 反思评估，决定是否继续
#     """
#
#     def __init__(self, api_key: str, model: str, tools: List):
#         """
#         初始化 AIOps Agent
#
#         参数:
#             api_key: DashScope API Key
#             model: 模型名称，如 "qwen-max"
#             tools: 工具列表 [query_prometheus_alerts, query_log, query_internal_docs, get_current_datetime]
#         """
#         # 初始化 LLM 并绑定工具
#         self.llm = ChatTongyi(
#             dashscope_api_key=api_key,
#             model_name=model,
#             streaming=False
#         ).bind_tools(tools)
#
#         # 保存工具字典（方便后续调用）
#         self.tools = {tool.name: tool for tool in tools}
#
#         # 创建 Graph
#         self.graph = self._create_graph()
#
#         logger.info("AIOpsAgent 初始化成功")
#
#     def _create_graph(self):
#         """创建 LangGraph 工作流
#
#         工作流: Planner → Operation → Reflection → (继续 or 结束)
#         """
#         # TODO: 定义节点函数
#         # TODO: 构建图
#         workflow = StateGraph(AIOpsState)
#         workflow.add_node("planner", self.planner_node)
#         workflow.add_node("operation", self.operation_node)
#         workflow.add_node("reflection", self.reflection_node)
#         workflow.set_entry_point("planner")
#         workflow.add_edge("planner", "operation")
#         workflow.add_edge("operation", "reflection")
#         workflow.add_conditional_edges(
#             "reflection",
#             self.should_continue,
#             {
#                 "continue": "planner",
#                 "end": END
#             }
#         )
#         return workflow.compile()
#
#     # ==================== 节点函数 ====================
#
#     async def planner_node(self, state: AIOpsState):
#         """Planner - 制定排查计划
#
#         功能:
#         - 分析问题
#         - 制定排查步骤
#         - 决定调用哪些工具
#         """
#         logger.info("🧠 Planner: 开始制定排查计划")
#
#         # 1. 获取当前状态
#         user_input = state["input"]
#         past_steps = state.get("past_steps", [])
#         iteration = state.get("iteration", 0)
#
#         # 2. 构建 Prompt
#         if iteration == 0:
#             # 第一次规划
#             prompt = f"""你是一个 AIOps 专家，负责制定故障排查计划。
#
# 用户问题：{user_input}
#
# 请根据已知信息，**仅制定下一步**最关键的 1-2 个排查动作。
# - 如果已经查询过告警且没有明确线索，**必须**转向查询日志(query_log)或知识库(query_internal_docs)。
# **决策逻辑**：
# 1. 【关键】如果之前的日志查询结果中已经包含了 **Error, Exception, Timeout** 等明确报错：
#    - 下一步必须是：调用 `query_internal_docs` 查询该报错的解决方案，或者直接说明“信息充足”。
#    - **严禁**再回头去查监控/告警。
#
# 2. 如果日志没问题，但告警还在：
#    - 尝试扩大日志查询的时间范围，或查询关联服务的日志。
#
# 3. **绝对禁止**：
#    - 严禁重复调用 `query_prometheus_alerts`（除非你认为告警状态发生了剧烈变化，但这很少见）。
#    - 严禁重复执行完全相同的 query_log 参数。
#
# 可用工具：
# - query_prometheus_alerts: 查询 Prometheus 告警
# - query_log: 查询系统日志（参数：query, time_range）
# - query_internal_docs: 查询运维知识库（参数：query）
# - get_current_datetime: 获取当前时间
#
# 请以清晰的步骤列表形式输出计划。"""
#         else:
#             # 重新规划（Replan）
#             past_steps_str = "\n".join(past_steps)
#             prompt = f"""你是一个 AIOps 专家，负责制定故障排查计划。
#
# 用户问题：{user_input}
#
# 已执行的步骤：
# {past_steps_str}
#
# 请根据已知信息，**仅制定下一步**最关键的 1-2 个排查动作。
# - 如果已经查询过告警且没有明确线索，**必须**转向查询日志(query_log)或知识库(query_internal_docs)。
# **决策逻辑**：
# 1. 【关键】如果之前的日志查询结果中已经包含了 **Error, Exception, Timeout** 等明确报错：
#    - 下一步必须是：调用 `query_internal_docs` 查询该报错的解决方案，或者直接说明“信息充足”。
#    - **严禁**再回头去查监控/告警。
#
# 2. 如果日志没问题，但告警还在：
#    - 尝试扩大日志查询的时间范围，或查询关联服务的日志。
#
# 3. **绝对禁止**：
#    - 严禁重复调用 `query_prometheus_alerts`（除非你认为告警状态发生了剧烈变化，但这很少见）。
#    - 严禁重复执行完全相同的 query_log 参数。
#
# 可用工具：
# - query_prometheus_alerts: 查询 Prometheus 告警
# - query_log: 查询系统日志（参数：query, time_range）
# - query_internal_docs: 查询运维知识库（参数：query）
# - get_current_datetime: 获取当前时间
#
# 请以清晰的步骤列表形式输出计划。"""
#
#         # 3. 调用 LLM 生成计划
#         messages = [
#             SystemMessage(content="你是一个专业的 AIOps 故障排查专家。"),
#             HumanMessage(content=prompt)
#         ]
#
#         response = await self.llm.ainvoke(messages)
#         plan = response.content
#
#         logger.info(f"📋 Planner 生成计划:\n{plan}")
#
#         # 4. 更新 State
#         return {
#             "plan": plan,
#             "iteration": iteration + 1
#         }
#
#     async def operation_node(self, state: AIOpsState):
#         """Operation - 执行操作
#
#         功能:
#         - 执行计划中的步骤
#         - 调用工具收集信息
#         - 记录执行结果
#         """
#         logger.info("⚙️ Operation: 开始执行操作")
#
#         # 1. 获取计划
#         plan = state["plan"]
#         user_input = state["input"]
#         past_steps = state.get("past_steps", [])
#         context_str = "\n".join(past_steps[-3:]) if past_steps else "无（首次执行）"
#         # 2. 构建 Prompt（让 LLM 根据计划调用工具）
#         prompt = f"""你是一个精准的执行助手。
#
# 用户问题：{user_input}
#
# 【重要参考上下文】
# (这是之前工具调用的结果，请从中提取 Pod名称、时间、错误信息等用于后续工具的参数)，尽量不重复执行之前的工具，除非参数不同:
# {context_str}
#
# 排查计划：
# {plan}
#
# 请根据计划调用相应的工具。你必须调用以下工具之一：
# - query_prometheus_alerts (): 查询当前告警（无需参数）
# - get_current_datetime (): 获取当前时间（无需参数）
# - query_prometheus_alerts (无参数)
# - query_log (query: str, time_range: str):查询日志
# - query_internal_docs (query: str)：查询知识库
# **重要**：请**严格按照上述计划**调用对应的工具。
# - 如果计划中提到查询日志，请务必调用 `query_log` 并填入合理的 query 参数和time_range参数。
# - 如果计划中提到查知识库，请务必调用 `query_internal_docs`并填入合理的query参数。
# - 不要自行决定跳过任何步骤。"""
#
#         messages = [
#             SystemMessage(content="你是一个 AIOps 执行助手，负责调用工具收集信息。"),
#             HumanMessage(content=prompt)
#         ]
#
#         # 3. 调用 LLM
#         response = await self.llm.ainvoke(messages)
#
#         # 4. 检查是否有工具调用
#         if not hasattr(response, 'tool_calls') or not response.tool_calls:
#             # 没有工具调用，直接返回 LLM 的回答
#             logger.warning("⚠️ Operation: LLM 没有调用任何工具")
#             return {
#                 "past_steps": [f"执行结果: {response.content}"]
#             }
#
#         # 5. 执行所有工具
#         logger.info(f"🔧 Operation: 执行 {len(response.tool_calls)} 个工具")
#
#         results = []
#         for tool_call in response.tool_calls:
#             tool_name = tool_call["name"]
#             tool_args = tool_call["args"]
#
#             logger.info(f"  - 调用工具: {tool_name}, 参数: {tool_args}")
#
#             try:
#                 # 获取工具并执行
#                 tool = self.tools[tool_name]
#                 result = await tool.ainvoke(tool_args)  # ← 关键：需要 await
#
#                 # 记录结果（截断过长结果）
#                 step_result = f"工具: {tool_name}\n参数: {json.dumps(tool_args, ensure_ascii=False)}\n结果: {result[:500]}..."
#                 results.append(step_result)
#
#                 logger.info(f"  ✅ {tool_name} 执行成功")
#             except Exception as e:
#                 error_msg = f"工具: {tool_name}\n错误: {str(e)}"
#                 results.append(error_msg)
#                 logger.error(f"  ❌ {tool_name} 执行失败: {e}")
#
#         # 6. 返回结果（会自动添加到 past_steps）
#         return {
#             "past_steps": results
#         }
#
#     async def reflection_node(self, state: AIOpsState):
#         """Reflection - 反思评估
#
#         功能:
#         - 评估执行结果
#         - 判断信息是否充足
#         - 如果充足，生成最终报告
#         - 如果不足，不做任何操作（让 should_continue 决定）
#         """
#         logger.info("🤔 Reflection: 开始评估结果")
#
#         # 1. 获取状态
#         user_input = state["input"]
#         past_steps = state.get("past_steps", [])
#         iteration = state.get("iteration", 0)
#
#         # 2. 构建 Prompt
#         past_steps_str = "\n\n".join(past_steps)
#         prompt = f"""你是一个 AIOps 专家，负责评估故障排查结果。
#
# 用户问题：{user_input}
#
# 已收集的信息：
# {past_steps_str}
#
# **判定标准（重要）**：
# 1. **只要**在日志中发现了明确的**错误堆栈、异常类名（Exception）或超时（Timeout）信息**，就视为**根因已找到**。此时**必须**生成最终报告。
# 2. 不需要等待所有细节都完美，只要能解释告警原因（例如：CPU高是因为数据库连接池卡死）即可。
#
# 请评估当前信息是否足够进行根因分析：
#
# 1. 如果信息充足(符合上述“根因已找到”的标准)：
#    - 请生成详细的故障分析报告
#    - 报告格式：问题描述、根因分析、解决建议
#    - 以"【最终报告】"开头
#
# 2. 如果信息不足：
#    - 简单说明"信息不足，需要继续排查"
#    - 不要给出具体建议（Planner 会重新规划）
#    **重要**：如果发现最近的步骤一直在重复查询相同内容（例如重复查告警），请在评估中明确指出‘需要尝试新的排查方向，如查询日志/知识库/时间’，以便引导 Planner。
#    """
#
#         # 3. 调用 LLM
#         messages = [
#             SystemMessage(content="你是一个专业的 AIOps 故障分析专家。"),
#             HumanMessage(content=prompt)
#         ]
#
#         response = await self.llm.ainvoke(messages)
#         evaluation = response.content
#
#         logger.info(f"📊 Reflection 评估:\n{evaluation[:200]}...")
#
#         # 4. 如果生成了最终报告，保存到 response
#         if "【最终报告】" in evaluation:
#             logger.info("✅ Reflection: 生成最终报告")
#             return {
#                 "response": evaluation
#             }
#         else:
#             # 信息不足，不更新 response（保持为空）
#             logger.info("🔄 Reflection: 信息不足")
#             return {}  # 返回空字典，不更新任何字段
#
#     # ==================== 条件判断函数 ====================
#
#     def should_continue(self, state: AIOpsState) -> Literal["continue", "end"]:
#         """判断是否继续循环
#
#         决策逻辑：
#         1. 如果 response 不为空 → 已生成报告 → end
#         2. 如果 iteration >= 6 → 达到上限 → end（强制）
#         3. 否则 → continue
#
#         返回:
#             "continue": 回到 Planner 继续排查
#             "end": 结束流程
#         """
#         response = state.get("response", "")
#         iteration = state.get("iteration", 0)
#
#         # 1. 如果已经生成最终报告，结束
#         if response:
#             logger.info("🎯 决策: 已生成报告，结束流程")
#             return "end"
#
#         # 2. 如果达到最大循环次数，强制结束
#         if iteration >= 6:
#             logger.warning("⚠️ 决策: 达到最大循环次数(6次)，强制结束")
#             return "end"
#
#         # 3. 否则继续
#         logger.info(f"🔄 决策: 继续排查（当前第 {iteration} 轮）")
#         return "continue"
#
#     # ==================== 对外接口 ====================
#
#     async def analyze(self, problem: str) -> str:
#         """
#         分析故障并生成报告
#
#         参数:
#             problem: 故障描述或告警信息
#
#         返回:
#             分析报告
#         """
#         try:
#             logger.info(f"🚀 AIOps Agent 开始分析问题: {problem[:100]}...")
#             initial_state = {
#                 "input": problem,
#                 "plan": "",
#                 "past_steps": [],
#                 "iteration": 0,
#                 "response": ""
#             }
#             result = await self.graph.ainvoke(initial_state)
#
#             final_report = result.get("response", "")
#
#             if not final_report:
#                 # 如果没有生成报告（达到最大循环次数），生成一个简单报告
#                 logger.warning("⚠️ 未生成最终报告，可能达到最大循环次数")
#                 past_steps_str = "\n\n".join(result.get("past_steps", []))
#                 final_report = f"""【分析报告】
#                 问题描述：{problem}
#
# 已收集的信息：
# {past_steps_str}
#
# 注意：由于达到最大排查次数限制，分析可能不完整。建议人工介入进一步排查。"""
#             logger.info("✅ AIOps Agent 分析完成")
#             return final_report
#         except Exception as e:
#             logger.error(f"❌ AIOps Agent 分析失败: {str(e)}")
#             import traceback
#             logger.error(f"详细错误: {traceback.format_exc()}")
#             raise
# AIOps Agent - 自动化运维故障排查
# 架构模式: Planner (计数器状态机) -> Operation (直通车优化) -> Reflection (验收)

from langchain_community.chat_models import ChatTongyi
from typing import List, TypedDict, Annotated, Literal
from loguru import logger
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import operator
import json


# ==================== State 定义 ====================

class AIOpsState(TypedDict):
    """AIOps Agent 状态定义"""
    input: str
    plan: str
    past_steps: Annotated[List[str], operator.add]
    iteration: int
    response: str


# ==================== AIOps Agent 类 ====================

class AIOpsAgent:
    """AIOps Agent - 自动化故障排查专家"""

    def __init__(self, api_key: str, model: str, tools: List):
        self.base_llm = ChatTongyi(
            dashscope_api_key=api_key,
            model_name=model,
            streaming=False,
            temperature=0.1
        )
        self.tool_llm = self.base_llm.bind_tools(tools)
        self.tools = {tool.name: tool for tool in tools}
        self.graph = self._create_graph()
        logger.info("AIOpsAgent 初始化成功 (显示修复版)")

    def _create_graph(self):
        workflow = StateGraph(AIOpsState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("operation", self.operation_node)
        workflow.add_node("reflection", self.reflection_node)

        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "operation")
        workflow.add_edge("operation", "reflection")
        workflow.add_conditional_edges(
            "reflection",
            self.should_continue,
            {
                "continue": "planner",
                "end": END
            }
        )
        return workflow.compile()

    # ==================== 1. Planner 节点 ====================

    async def planner_node(self, state: AIOpsState):
        logger.info("🧠 Planner: 开始制定计划")
        user_input = state["input"]
        past_steps = state.get("past_steps", [])
        iteration = state.get("iteration", 0)

        # --- 1. 关键状态统计 ---
        has_checked_alerts = any("query_prometheus_alerts" in step for step in past_steps)
        log_query_count = sum(1 for step in past_steps if "query_log" in step)
        has_checked_docs = any("query_internal_docs" in step for step in past_steps)

        # --- 2. 强制状态机逻辑 ---
        if not has_checked_alerts:
            # 【阶段 0】：查告警
            plan_instruction = "1. 优先调用 `query_prometheus_alerts` 查询当前告警。"

        elif log_query_count == 0:
            # 【阶段 1】：查日志
            plan_instruction = """1. ✅ 已获取告警信息。
2. **下一步必须查询日志**。
3. 请根据告警名称，严格对照以下映射调用 `query_log`：
   - HighCPU -> query="cpu"
   - HighMemory/OOM -> query="memory"
   - SlowResponse -> query="slow"
   - Error/Crash -> query="error" """

        elif log_query_count == 1:
            # 【阶段 2】：日志重试
            plan_instruction = """1. ⚠️ 上一次日志查询可能未命中。
2. **请尝试更换关键词**再次调用 `query_log`。
   - 如 "cpu" -> "thread" 或 "stack trace"。
   - 如 "error" -> "exception" 或 "fatal"。"""

        elif log_query_count >= 3 and not has_checked_docs:
            # 【阶段 3】：强制查知识库
            plan_instruction = """1. 🛑 日志查询结束。
2. **必须**调用 `query_internal_docs` 查询知识库。
   - 提取之前的告警名（如 HighCPU）作为参数查询排查手册。"""

        else:
            # 【阶段 4】：最终总结 (这里加了一句关键指令，确保格式统一)
            plan_instruction = """1. 已收集全量信息。
2. 请基于所有信息生成最终分析。
3. **必须以 '【最终报告】' 开头** (这很重要，否则系统无法识别)。"""

        prompt = f"""你是一个 AIOps 专家。
用户问题：{user_input}
进度：告警({has_checked_alerts}) -> 日志({log_query_count}) -> 知识库({has_checked_docs})
历史：
{chr(10).join(past_steps[-6:])}

【指令】
{plan_instruction}

请输出下一步计划。"""

        messages = [
            SystemMessage(content="你是一个严格遵守排查流程的专家。"),
            HumanMessage(content=prompt)
        ]
        response = await self.base_llm.ainvoke(messages)
        plan = response.content

        # 兜底
        if not plan: plan = "1. 调用 query_internal_docs 查询知识库。"

        logger.info(f"📋 Planner 指令:\n{plan}")
        return {"plan": plan, "iteration": iteration + 1}

    # ==================== 2. Operation 节点 (关键修复点) ====================

    async def operation_node(self, state: AIOpsState):
        """Operation - 执行操作"""
        logger.info("⚙️ Operation: 执行操作")
        plan = state["plan"]

        # 【核心修复】：如果 Planner 已经生成了最终报告，直接透传！
        # 不要让 Tool LLM 再处理一遍，否则它会把报告内容吞掉，导致 Reflection 没东西看。
        if "【最终报告】" in plan:
            logger.info("🚀 检测到最终报告，直通 Reflection")
            return {"past_steps": [plan]}

        past_steps = state.get("past_steps", [])
        context_str = "\n".join(past_steps[-3:]) if past_steps else "无"

        prompt = f"""你是一个执行助手。
【排查计划】
{plan}
【上下文】
{context_str}
请根据计划调用工具。如果计划是纯文本分析，请不要调用工具。"""

        messages = [
            SystemMessage(content="严格按计划执行。"),
            HumanMessage(content=prompt)
        ]

        response = await self.tool_llm.ainvoke(messages)

        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            return {"past_steps": [f"执行结果(无工具): {response.content}"]}

        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            logger.info(f"  🔧 调用: {tool_name} | 参数: {tool_args}")
            try:
                tool = self.tools[tool_name]
                result = await tool.ainvoke(tool_args)
                step_result = f"### 🛠️ 工具: {tool_name}\n参数: {json.dumps(tool_args, ensure_ascii=False)}\n结果: {str(result)[:600]}..."
                results.append(step_result)
            except Exception as e:
                results.append(f"工具 {tool_name} 执行失败: {e}")

        return {"past_steps": results}

    # ==================== 3. Reflection 节点 (显示逻辑修复) ====================

    async def reflection_node(self, state: AIOpsState):
        """Reflection - 评估结果"""
        logger.info("🤔 Reflection: 评估中...")

        past_steps = state.get("past_steps", [])
        past_steps_str = "\n\n".join(past_steps)
        last_step = past_steps[-1] if past_steps else ""

        has_logs = any("query_log" in s for s in past_steps)

        # 【核心修复】：优先检查是否是 Operation 直通过来的最终报告
        if "【最终报告】" in last_step:
            # 依然保留防早退检查（虽然走到这一步通常都是安全的）
            if not has_logs:
                return {}
            # 直接把这份报告作为最终 response 返回！
            return {"response": last_step}

        # 下面是常规的 LLM 评估逻辑 (用于中间步骤)
        prompt = f"""评估当前进度。
已执行步骤：
{past_steps_str}

逻辑：
1. 没查日志 -> 回复 "需查日志"。
2. 没查知识库 -> 回复 "需查知识库"。
3. 看到 "【最终报告】" -> 重复输出该报告内容。
"""
        messages = [HumanMessage(content=prompt)]
        response = await self.base_llm.ainvoke(messages)
        evaluation = response.content

        # 这里的防早退是为了防止 LLM 幻觉
        if "【最终报告】" in evaluation and not has_logs:
            return {}

        if "【最终报告】" in evaluation:
            return {"response": evaluation}

        return {}

    # ==================== 控制与入口 ====================

    def should_continue(self, state: AIOpsState) -> Literal["continue", "end"]:
        if state.get("response"): return "end"
        if state.get("iteration", 0) >= 6: return "end"
        return "continue"

    async def analyze(self, problem: str) -> str:
        try:
            res = await self.graph.ainvoke({
                "input": problem, "plan": "", "past_steps": [], "iteration": 0, "response": ""
            })
            # 如果 response 有值，说明正常结束，直接显示
            return res.get("response") or "【最终报告】\n达到最大尝试次数，建议人工介入。"
        except Exception as e:
            return f"Error: {e}"
