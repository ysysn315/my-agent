"""
调试 AIOps Agent - 查看 Planner 生成的计划
"""
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from app.agents.aiops_agent import AIOpsAgent
from app.agents.tools.prometheus_tool import query_prometheus_alerts
from app.agents.tools.log_tool import query_log
from app.agents.tools.datetime_tool import get_current_datetime
from langchain.tools import tool

# 加载环境变量
load_dotenv()

# 配置日志 - 显示更多细节
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG")


# 创建 Mock 文档检索工具
@tool
async def query_internal_docs(query: str) -> str:
    """查询内部文档知识库（Mock 模式）"""
    return """【运维知识库】
CPU 使用率过高的常见原因：
1. 应用程序存在死循环或计算密集型任务
2. 数据库查询效率低下，导致 CPU 占用高
3. 系统进程异常，如僵尸进程
4. 并发请求过多，超出系统处理能力

建议排查步骤：
1. 使用 top 命令查看占用 CPU 最高的进程
2. 检查应用日志，查找异常堆栈
3. 分析慢查询日志
4. 检查系统资源配置是否合理"""


async def test_aiops_debug():
    """测试并查看详细日志"""
    logger.info("=" * 60)
    logger.info("调试 AIOps Agent")
    logger.info("=" * 60)
    
    # 准备工具
    tools = [
        query_prometheus_alerts,
        query_log,
        query_internal_docs,
        get_current_datetime
    ]
    
    # 初始化 Agent
    api_key = os.getenv("DASHSCOPE_API_KEY")
    model = os.getenv("DASHSCOPE_MODEL", "qwen-max")
    
    agent = AIOpsAgent(
        api_key=api_key,
        model=model,
        tools=tools
    )
    
    # 测试问题
    problem = "系统出现 CPU 使用率过高告警，请分析原因"
    
    logger.info(f"\n问题: {problem}\n")
    
    try:
        report = await agent.analyze(problem)
        logger.info(f"\n\n最终报告:\n{report}")
    except Exception as e:
        logger.error(f"失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_aiops_debug())
