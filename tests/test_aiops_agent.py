"""
测试 AIOps Agent 核心功能
不需要启动 FastAPI 服务器，直接测试 Agent
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

# 配置日志
logger.add("tests/test_aiops_agent.log", rotation="10 MB")


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


async def test_aiops_agent():
    """测试 AIOps Agent 完整流程"""
    logger.info("=" * 60)
    logger.info("测试 AIOps Agent")
    logger.info("=" * 60)
    
    # 1. 准备工具
    tools = [
        query_prometheus_alerts,
        query_log,
        query_internal_docs,
        get_current_datetime
    ]
    
    logger.info(f"✅ 准备了 {len(tools)} 个工具")
    
    # 2. 初始化 Agent
    api_key = os.getenv("DASHSCOPE_API_KEY")
    model = os.getenv("DASHSCOPE_MODEL", "qwen-max")
    
    if not api_key:
        logger.error("❌ 未找到 DASHSCOPE_API_KEY，请检查 .env 文件")
        return
    
    logger.info(f"使用模型: {model}")
    
    agent = AIOpsAgent(
        api_key=api_key,
        model=model,
        tools=tools
    )
    
    logger.info("✅ AIOps Agent 初始化成功")
    
    # 3. 测试分析
    problem = "系统出现 CPU 使用率过高告警，请帮我分析原因并给出解决方案"
    
    logger.info(f"\n问题: {problem}")
    logger.info("\n开始分析...\n")
    
    try:
        # 执行分析
        report = await agent.analyze(problem)
        
        logger.info("\n" + "=" * 60)
        logger.info("📋 分析报告")
        logger.info("=" * 60)
        logger.info(f"\n{report}\n")
        logger.info("=" * 60)
        logger.info(f"✅ 分析完成，报告长度: {len(report)} 字符")
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


async def test_aiops_agent_simple():
    """测试简单问题"""
    logger.info("\n" + "=" * 60)
    logger.info("测试简单问题")
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
    
    # 简单问题
    problem = "请分析当前系统告警"
    
    logger.info(f"问题: {problem}")
    
    try:
        report = await agent.analyze(problem)
        logger.info(f"\n报告:\n{report[:500]}...")  # 只显示前 500 字符
        logger.info(f"\n✅ 完成，总长度: {len(report)} 字符")
    
    except Exception as e:
        logger.error(f"❌ 失败: {str(e)}")


async def main():
    """运行所有测试"""
    logger.info("🚀 开始测试 AIOps Agent")
    logger.info("")
    
    # 测试 1: 完整流程
    await test_aiops_agent()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试 2: 简单问题
    await test_aiops_agent_simple()
    
    logger.info("\n✅ 所有测试完成")


if __name__ == "__main__":
    asyncio.run(main())
