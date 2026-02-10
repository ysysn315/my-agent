"""
演示 Tool 调用的完整流程
"""
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


# 1. 定义一个简单的工具
@tool
def get_weather(city: str) -> str:
    """获取城市天气
    
    参数:
        city: 城市名称
    
    返回:
        天气信息
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天，15°C",
        "上海": "多云，18°C",
        "广州": "小雨，22°C"
    }
    return weather_data.get(city, "未知城市")


def main():
    print("=" * 80)
    print("Tool 调用流程演示")
    print("=" * 80)
    
    # 2. 查看工具信息
    print("\n【步骤 1】工具定义")
    print(f"工具名称: {get_weather.name}")
    print(f"工具描述: {get_weather.description}")
    print(f"工具参数: {get_weather.args}")
    
    # 3. 模拟 LLM 返回 tool_calls
    print("\n【步骤 2】LLM 决定调用工具")
    print("用户问题: '北京天气怎么样？'")
    print("\nLLM 分析后返回:")
    
    # 这是 LLM 返回的消息（包含 tool_calls）
    llm_response = AIMessage(
        content="",  # 内容为空，因为需要先调用工具
        tool_calls=[
            {
                "id": "call_weather_001",
                "name": "get_weather",
                "args": {"city": "北京"}
            }
        ]
    )
    
    print(f"  tool_calls: {llm_response.tool_calls}")
    
    # 4. 执行工具
    print("\n【步骤 3】执行工具")
    tool_call = llm_response.tool_calls[0]
    print(f"  调用工具: {tool_call['name']}")
    print(f"  传入参数: {tool_call['args']}")
    
    # 实际调用工具
    result = get_weather.invoke(tool_call['args'])
    print(f"  工具返回: {result}")
    
    # 5. 构造 ToolMessage
    print("\n【步骤 4】构造 ToolMessage")
    tool_message = ToolMessage(
        content=result,
        tool_call_id=tool_call['id']
    )
    print(f"  ToolMessage:")
    print(f"    - content: {tool_message.content}")
    print(f"    - tool_call_id: {tool_message.tool_call_id}")
    
    # 6. 模拟 LLM 根据工具结果生成最终答案
    print("\n【步骤 5】LLM 根据工具结果生成答案")
    print("  LLM 收到的消息历史:")
    print(f"    1. HumanMessage: '北京天气怎么样？'")
    print(f"    2. AIMessage: tool_calls=[...]")
    print(f"    3. ToolMessage: '{result}'")
    print("\n  LLM 生成最终答案:")
    final_answer = f"根据查询结果，北京今天{result}"
    print(f"    '{final_answer}'")
    
    print("\n" + "=" * 80)
    print("流程完成！")
    print("=" * 80)
    
    # 7. 演示多工具调用
    print("\n\n" + "=" * 80)
    print("多工具调用演示")
    print("=" * 80)
    
    print("\n用户问题: '北京和上海的天气怎么样？'")
    print("\nLLM 返回多个 tool_calls:")
    
    multi_tool_calls = [
        {"id": "call_001", "name": "get_weather", "args": {"city": "北京"}},
        {"id": "call_002", "name": "get_weather", "args": {"city": "上海"}}
    ]
    
    print(f"  tool_calls: {multi_tool_calls}")
    
    print("\n执行所有工具:")
    tool_messages = []
    for tc in multi_tool_calls:
        result = get_weather.invoke(tc['args'])
        print(f"  - {tc['args']['city']}: {result}")
        tool_messages.append(ToolMessage(
            content=result,
            tool_call_id=tc['id']
        ))
    
    print(f"\n生成 {len(tool_messages)} 个 ToolMessage")
    print("LLM 会根据这些结果生成综合答案")


if __name__ == "__main__":
    main()
