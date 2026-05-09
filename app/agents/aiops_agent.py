from typing import Annotated, List, Literal, TypedDict

import json
import operator

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from loguru import logger

from app.agents.tool_runtime import safe_tool_execute


class AIOpsState(TypedDict):
    input: str
    plan: str
    past_steps: Annotated[List[str], operator.add]
    iteration: int
    response: str


class AIOpsAgent:
    def __init__(self, api_key: str, model: str, tools: List):
        self.base_llm = ChatTongyi(
            dashscope_api_key=api_key,
            model_name=model,
            streaming=False,
            temperature=0.1,
        )
        self.tool_llm = self.base_llm.bind_tools(tools)
        self.tools = {tool.name: tool for tool in tools}
        self.graph = self._create_graph()
        logger.info("AIOpsAgent initialized")

    @staticmethod
    def _has_successful_tool(past_steps: List[str], tool_name: str) -> bool:
        marker = f"tool={tool_name}"
        return any(marker in step and "status=success" in step for step in past_steps)

    @staticmethod
    def _count_successful_tool(past_steps: List[str], tool_name: str) -> int:
        marker = f"tool={tool_name}"
        return sum(1 for step in past_steps if marker in step and "status=success" in step)

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
                "end": END,
            },
        )
        return workflow.compile()

    async def planner_node(self, state: AIOpsState):
        logger.info("Planner evaluating next step")
        user_input = state["input"]
        past_steps = state.get("past_steps", [])
        iteration = state.get("iteration", 0)

        has_checked_alerts = self._has_successful_tool(past_steps, "query_prometheus_alerts")
        log_query_count = self._count_successful_tool(past_steps, "query_log")
        has_checked_docs = self._has_successful_tool(past_steps, "query_internal_docs")

        if not has_checked_alerts:
            plan_instruction = "1. 先调用 `query_prometheus_alerts` 查看当前告警。"
        elif log_query_count == 0:
            plan_instruction = (
                "1. 已经拿到告警信息。\n"
                "2. 根据告警内容映射关键词，调用 `query_log`。\n"
                "3. `HighCPU` 用 `cpu`，`HighMemory/OOM` 用 `memory`，`SlowResponse` 用 `slow`，"
                "`Error/Crash` 用 `error`。"
            )
        elif log_query_count == 1:
            plan_instruction = (
                "1. 上一次日志查询可能过窄。\n"
                "2. 请换一个更宽的关键词再次调用 `query_log`。\n"
                "3. 例如：`cpu -> thread`，`error -> exception` 或 `fatal`。"
            )
        elif log_query_count >= 3 and not has_checked_docs:
            plan_instruction = (
                "1. 当前日志采样已经足够宽。\n"
                "2. 调用 `query_internal_docs` 查询已知修复方案或排障步骤。"
            )
        else:
            plan_instruction = (
                "1. 当前证据已经比较充分。\n"
                "2. 输出最终诊断结论和可执行的下一步动作。"
            )

        prompt = f"""
你是一个 AIOps 规划助手。
用户问题：
{user_input}

当前进展：
- alerts_checked={has_checked_alerts}
- successful_log_queries={log_query_count}
- docs_checked={has_checked_docs}

最近步骤：
{chr(10).join(past_steps[-6:]) or "无"}

当前必须执行的下一步：
{plan_instruction}

请用 1 到 3 行给出简短执行计划。
""".strip()

        messages = [
            SystemMessage(content="你是一个严格的 AIOps 规划助手。"),
            HumanMessage(content=prompt),
        ]
        response = await self.base_llm.ainvoke(messages)
        plan = response.content or "1. 调用 `query_internal_docs` 补充更多证据。"
        logger.info(f"Planner output: {plan}")
        return {"plan": plan, "iteration": iteration + 1}

    async def operation_node(self, state: AIOpsState):
        logger.info("Operation executing plan")
        plan = state["plan"]
        past_steps = state.get("past_steps", [])
        context_str = "\n".join(past_steps[-3:]) if past_steps else "无"

        prompt = f"""
你是一个执行助手。
请使用可用工具执行当前计划。

计划：
{plan}

最近步骤：
{context_str}

规则：
- 当计划要求补充证据时，优先调用工具，而不是只写叙述。
- 不要编造工具结果。
- 如果现有证据已经足够且不需要调用工具，请简要说明原因。
""".strip()

        messages = [
            SystemMessage(content="请在合适的时候使用工具执行计划。"),
            HumanMessage(content=prompt),
        ]
        response = await self.tool_llm.ainvoke(messages)

        if not hasattr(response, "tool_calls") or not response.tool_calls:
            return {"past_steps": [f"tool=none\nstatus=no_tool\nattempts=0\nargs={{}}\nresult={response.content}"]}

        results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            logger.info(f"Operation calling tool={tool_name} args={tool_args}")
            try:
                tool = self.tools[tool_name]
                execution = await safe_tool_execute(tool_name, tool, tool_args)
                step_result = (
                    f"tool={tool_name}\n"
                    f"status={execution.status}\n"
                    f"attempts={execution.attempts}\n"
                    f"args={json.dumps(tool_args, ensure_ascii=False)}\n"
                    f"result={execution.content[:600]}..."
                )
                results.append(step_result)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Operation tool execution failed: tool={tool_name} error={e}")
                results.append(
                    f"tool={tool_name}\n"
                    f"status=error\n"
                    f"attempts=1\n"
                    f"args={json.dumps(tool_args, ensure_ascii=False)}\n"
                    f"result={str(e)}"
                )

        return {"past_steps": results}

    async def reflection_node(self, state: AIOpsState):
        logger.info("Reflection evaluating progress")
        past_steps = state.get("past_steps", [])
        past_steps_str = "\n\n".join(past_steps)
        has_logs = self._has_successful_tool(past_steps, "query_log")
        has_docs = self._has_successful_tool(past_steps, "query_internal_docs")
        has_alerts = self._has_successful_tool(past_steps, "query_prometheus_alerts")
        iteration = state.get("iteration", 0)

        if iteration < 2 and not has_logs and not has_docs:
            return {}

        prompt = f"""
你是一个 AIOps 复盘助手。
请判断当前调查是否已经有足够证据生成最终报告。

当前证据：
{past_steps_str or "无"}

规则：
- 如果证据仍然不足，只回复“继续”。
- 如果证据已经足够，请输出简洁的最终报告，包含：
  1. 可能的根因
  2. 支撑证据
  3. 下一步动作
- 如果部分工具降级或失败，但现有证据已经足够，仍然输出最终报告。
- alerts_collected={has_alerts}, logs_collected={has_logs}, docs_collected={has_docs}
""".strip()

        messages = [HumanMessage(content=prompt)]
        response = await self.base_llm.ainvoke(messages)
        evaluation = (response.content or "").strip()

        if evaluation in {"继续", "CONTINUE"} or evaluation.upper() == "CONTINUE":
            return {}

        if evaluation:
            return {"response": evaluation}

        return {}

    def should_continue(self, state: AIOpsState) -> Literal["continue", "end"]:
        if state.get("response"):
            return "end"
        if state.get("iteration", 0) >= 6:
            return "end"
        return "continue"

    async def analyze(self, problem: str) -> str:
        try:
            result = await self.graph.ainvoke(
                {
                    "input": problem,
                    "plan": "",
                    "past_steps": [],
                    "iteration": 0,
                    "response": "",
                }
            )
            return result.get("response") or "【最终报告】\n达到最大尝试次数，建议人工介入。"
        except Exception as e:  # noqa: BLE001
            return f"Error: {e}"

    async def analyze_stream(self, problem: str):
        state = {
            "input": problem,
            "plan": "",
            "past_steps": [],
            "iteration": 0,
            "response": "",
        }
        yield json.dumps({"type": "start", "data": "开始 AIOps 分析"}, ensure_ascii=False)

        while True:
            planner_result = await self.planner_node(state)
            state.update(planner_result)
            yield json.dumps({"type": "plan", "data": f"计划:\n{state['plan']}"}, ensure_ascii=False)

            yield json.dumps({"type": "step", "data": "Operation: 执行中..."}, ensure_ascii=False)
            operation_result = await self.operation_node(state)
            state.update(operation_result)

            if state["past_steps"]:
                last_result = state["past_steps"][-1]
                preview = last_result[:300] + "..." if len(last_result) > 300 else last_result
                yield json.dumps({"type": "tool_result", "data": f"结果:\n{preview}"}, ensure_ascii=False)

            yield json.dumps({"type": "step", "data": "Reflection: 评估中..."}, ensure_ascii=False)
            reflection_result = await self.reflection_node(state)
            state.update(reflection_result)

            if self.should_continue(state) == "end":
                final_response = state.get("response") or "【最终报告】\n达到最大尝试次数，建议人工介入。"
                yield json.dumps({"type": "report", "data": final_response}, ensure_ascii=False)
                yield json.dumps({"type": "done"}, ensure_ascii=False)
                break

            yield json.dumps({"type": "step", "data": "信息不足，继续排查..."}, ensure_ascii=False)
