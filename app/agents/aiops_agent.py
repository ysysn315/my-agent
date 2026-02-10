# AIOps Agent - 自动化运维故障排查
# 使用 Planner-Operation-Reflection 模式

from langchain_community.chat_models import ChatTongyi
from typing import List, TypedDict, Annotated, Literal
from loguru import logger
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import operator
import json


# ==================== State 定义 ====================

class AIOpsState(TypedDict):
    """AIOps Agent 状态定义
    
    State 在 Planner-Operation-Reflection 循环中传递，保存所有必要信息
    """
    # 用户输入
    input: str  # 用户的问题或告警描述

    # 排查计划
    plan: str  # Planner 生成的排查计划（步骤列表）

    # 执行历史（使用 operator.add 自动合并）
    past_steps: Annotated[List[str], operator.add]  # 已执行的步骤和结果

    # 循环控制
    iteration: int  # 当前循环次数（防止无限循环，最大3次）

    # 最终输出
    response: str  # 最终的分析报告


# ==================== AIOps Agent 类 ====================

class AIOpsAgent:
    """AIOps Agent - 自动化故障排查和根因分析
    
    使用 Planner-Operation-Reflection 模式:
    - Planner: 制定排查计划
    - Operation: 执行操作（调用工具）
    - Reflection: 反思评估，决定是否继续
    """

    def __init__(self, api_key: str, model: str, tools: List):
        """
        初始化 AIOps Agent
        
        参数:
            api_key: DashScope API Key
            model: 模型名称，如 "qwen-max"
            tools: 工具列表 [query_prometheus_alerts, query_log, query_internal_docs, get_current_datetime]
        """
        # 初始化 LLM 并绑定工具
        self.llm = ChatTongyi(
            dashscope_api_key=api_key,
            model_name=model,
            streaming=False
        ).bind_tools(tools)

        # 保存工具字典（方便后续调用）
        self.tools = {tool.name: tool for tool in tools}

        # 创建 Graph
        self.graph = self._create_graph()

        logger.info("AIOpsAgent 初始化成功")

    def _create_graph(self):
        """创建 LangGraph 工作流
        
        工作流: Planner → Operation → Reflection → (继续 or 结束)
        """
        # TODO: 定义节点函数
        # TODO: 构建图
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

    # ==================== 节点函数 ====================

    async def planner_node(self, state: AIOpsState):
        """Planner - 制定排查计划
        
        功能:
        - 分析问题
        - 制定排查步骤
        - 决定调用哪些工具
        """
        logger.info("🧠 Planner: 开始制定排查计划")

        # 1. 获取当前状态
        user_input = state["input"]
        past_steps = state.get("past_steps", [])
        iteration = state.get("iteration", 0)

        # 2. 构建 Prompt
        if iteration == 0:
            # 第一次规划
            prompt = f"""你是一个 AIOps 专家，负责制定故障排查计划。

用户问题：{user_input}

请制定详细的排查计划，包括：
1. 需要调用哪些工具来收集信息
2. 每个工具的参数
3. 排查的理由

可用工具：
- query_prometheus_alerts: 查询 Prometheus 告警
- query_log: 查询系统日志（参数：query, time_range）
- query_internal_docs: 查询运维知识库（参数：query）
- get_current_datetime: 获取当前时间

请以清晰的步骤列表形式输出计划。"""
        else:
            # 重新规划（Replan）
            past_steps_str = "\n".join(past_steps)
            prompt = f"""你是一个 AIOps 专家，负责制定故障排查计划。

用户问题：{user_input}

已执行的步骤：
{past_steps_str}

根据已有信息，请制定下一步的排查计划。如果信息已经足够，请说明"信息充足，可以生成报告"。

可用工具：
- query_prometheus_alerts: 查询 Prometheus 告警
- query_log: 查询系统日志（参数：query, time_range）
- query_internal_docs: 查询运维知识库（参数：query）
- get_current_datetime: 获取当前时间

请以清晰的步骤列表形式输出计划。"""

        # 3. 调用 LLM 生成计划
        messages = [
            SystemMessage(content="你是一个专业的 AIOps 故障排查专家。"),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)
        plan = response.content

        logger.info(f"📋 Planner 生成计划:\n{plan}")

        # 4. 更新 State
        return {
            "plan": plan,
            "iteration": iteration + 1
        }

    async def operation_node(self, state: AIOpsState):
        """Operation - 执行操作
        
        功能:
        - 执行计划中的步骤
        - 调用工具收集信息
        - 记录执行结果
        """
        logger.info("⚙️ Operation: 开始执行操作")

        # 1. 获取计划
        plan = state["plan"]
        user_input = state["input"]

        # 2. 构建 Prompt（让 LLM 根据计划调用工具）
        prompt = f"""你是一个 AIOps 执行助手，负责调用工具收集信息。

用户问题：{user_input}

排查计划：
{plan}

请根据计划调用相应的工具。你必须调用以下工具之一：
- query_prometheus_alerts: 查询当前告警（无需参数）
- query_log: 查询日志（参数：query, time_range）
- query_internal_docs: 查询知识库（参数：query）
- get_current_datetime: 获取当前时间（无需参数）

重要：请根据计划调用合适的工具，不要只调用 get_current_datetime！"""

        messages = [
            SystemMessage(content="你是一个 AIOps 执行助手，负责调用工具收集信息。"),
            HumanMessage(content=prompt)
        ]

        # 3. 调用 LLM
        response = await self.llm.ainvoke(messages)

        # 4. 检查是否有工具调用
        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            # 没有工具调用，直接返回 LLM 的回答
            logger.warning("⚠️ Operation: LLM 没有调用任何工具")
            return {
                "past_steps": [f"执行结果: {response.content}"]
            }

        # 5. 执行所有工具
        logger.info(f"🔧 Operation: 执行 {len(response.tool_calls)} 个工具")

        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.info(f"  - 调用工具: {tool_name}, 参数: {tool_args}")

            try:
                # 获取工具并执行
                tool = self.tools[tool_name]
                result = await tool.ainvoke(tool_args)  # ← 关键：需要 await

                # 记录结果（截断过长结果）
                step_result = f"工具: {tool_name}\n参数: {json.dumps(tool_args, ensure_ascii=False)}\n结果: {result[:500]}..."
                results.append(step_result)

                logger.info(f"  ✅ {tool_name} 执行成功")
            except Exception as e:
                error_msg = f"工具: {tool_name}\n错误: {str(e)}"
                results.append(error_msg)
                logger.error(f"  ❌ {tool_name} 执行失败: {e}")

        # 6. 返回结果（会自动添加到 past_steps）
        return {
            "past_steps": results
        }

    async def reflection_node(self, state: AIOpsState):
        """Reflection - 反思评估
        
        功能:
        - 评估执行结果
        - 判断信息是否充足
        - 如果充足，生成最终报告
        - 如果不足，不做任何操作（让 should_continue 决定）
        """
        logger.info("🤔 Reflection: 开始评估结果")

        # 1. 获取状态
        user_input = state["input"]
        past_steps = state.get("past_steps", [])
        iteration = state.get("iteration", 0)

        # 2. 构建 Prompt
        past_steps_str = "\n\n".join(past_steps)
        prompt = f"""你是一个 AIOps 专家，负责评估故障排查结果。

用户问题：{user_input}

已收集的信息：
{past_steps_str}

请评估当前信息是否足够进行根因分析：

1. 如果信息充足：
   - 请生成详细的故障分析报告
   - 报告格式：问题描述、根因分析、解决建议
   - 以"【最终报告】"开头

2. 如果信息不足：
   - 简单说明"信息不足，需要继续排查"
   - 不要给出具体建议（Planner 会重新规划）"""

        # 3. 调用 LLM
        messages = [
            SystemMessage(content="你是一个专业的 AIOps 故障分析专家。"),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)
        evaluation = response.content

        logger.info(f"📊 Reflection 评估:\n{evaluation[:200]}...")

        # 4. 如果生成了最终报告，保存到 response
        if "【最终报告】" in evaluation:
            logger.info("✅ Reflection: 生成最终报告")
            return {
                "response": evaluation
            }
        else:
            # 信息不足，不更新 response（保持为空）
            logger.info("🔄 Reflection: 信息不足")
            return {}  # 返回空字典，不更新任何字段

    # ==================== 条件判断函数 ====================

    def should_continue(self, state: AIOpsState) -> Literal["continue", "end"]:
        """判断是否继续循环
        
        决策逻辑：
        1. 如果 response 不为空 → 已生成报告 → end
        2. 如果 iteration >= 3 → 达到上限 → end（强制）
        3. 否则 → continue
        
        返回:
            "continue": 回到 Planner 继续排查
            "end": 结束流程
        """
        response = state.get("response", "")
        iteration = state.get("iteration", 0)

        # 1. 如果已经生成最终报告，结束
        if response:
            logger.info("🎯 决策: 已生成报告，结束流程")
            return "end"

        # 2. 如果达到最大循环次数，强制结束
        if iteration >= 3:
            logger.warning("⚠️ 决策: 达到最大循环次数(3次)，强制结束")
            return "end"

        # 3. 否则继续
        logger.info(f"🔄 决策: 继续排查（当前第 {iteration} 轮）")
        return "continue"

    # ==================== 对外接口 ====================

    async def analyze(self, problem: str) -> str:
        """
        分析故障并生成报告
        
        参数:
            problem: 故障描述或告警信息
        
        返回:
            分析报告
        """
        try:
            logger.info(f"🚀 AIOps Agent 开始分析问题: {problem[:100]}...")
            initial_state = {
                "input": problem,
                "plan": "",
                "past_steps": [],
                "iteration": 0,
                "response": ""
            }
            result = await self.graph.ainvoke(initial_state)

            final_report = result.get("response", "")

            if not final_report:
                # 如果没有生成报告（达到最大循环次数），生成一个简单报告
                logger.warning("⚠️ 未生成最终报告，可能达到最大循环次数")
                past_steps_str = "\n\n".join(result.get("past_steps", []))
                final_report = f"""【分析报告】
                问题描述：{problem}

已收集的信息：
{past_steps_str}

注意：由于达到最大排查次数限制，分析可能不完整。建议人工介入进一步排查。"""
            logger.info("✅ AIOps Agent 分析完成")
            return final_report
        except Exception as e:
            logger.error(f"❌ AIOps Agent 分析失败: {str(e)}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            raise
