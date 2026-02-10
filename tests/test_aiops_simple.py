"""
简单测试 AIOps Agent - 只测试初始化和基本结构
"""
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv()

logger.info("=" * 60)
logger.info("测试 1: 导入模块")
logger.info("=" * 60)

try:
    from app.agents.aiops_agent import AIOpsAgent
    from app.agents.tools.prometheus_tool import query_prometheus_alerts
    from app.agents.tools.log_tool import query_log
    from app.agents.tools.datetime_tool import get_current_datetime
    from langchain.tools import tool
    logger.info("✅ 所有模块导入成功")
except Exception as e:
    logger.error(f"❌ 模块导入失败: {e}")
    exit(1)

logger.info("\n" + "=" * 60)
logger.info("测试 2: 创建工具")
logger.info("=" * 60)

# 创建 Mock 文档检索工具
@tool
async def query_internal_docs(query: str) -> str:
    """查询内部文档知识库（Mock 模式）"""
    return "Mock 知识库内容"

tools = [
    query_prometheus_alerts,
    query_log,
    query_internal_docs,
    get_current_datetime
]

logger.info(f"✅ 创建了 {len(tools)} 个工具:")
for t in tools:
    logger.info(f"  - {t.name}: {t.description[:50]}...")

logger.info("\n" + "=" * 60)
logger.info("测试 3: 初始化 AIOps Agent")
logger.info("=" * 60)

api_key = os.getenv("DASHSCOPE_API_KEY")
model = os.getenv("DASHSCOPE_MODEL", "qwen-max")

if not api_key:
    logger.error("❌ 未找到 DASHSCOPE_API_KEY")
    exit(1)

logger.info(f"API Key: {api_key[:10]}...")
logger.info(f"Model: {model}")

try:
    agent = AIOpsAgent(
        api_key=api_key,
        model=model,
        tools=tools
    )
    logger.info("✅ AIOps Agent 初始化成功")
    logger.info(f"  - Graph 节点数: {len(agent.graph.nodes)}")
    logger.info(f"  - 工具数量: {len(agent.tools)}")
except Exception as e:
    logger.error(f"❌ 初始化失败: {e}")
    import traceback
    logger.error(traceback.format_exc())
    exit(1)

logger.info("\n" + "=" * 60)
logger.info("✅ 所有基础测试通过")
logger.info("=" * 60)
logger.info("\n提示: 如果要测试完整分析流程，请运行 test_aiops_agent.py")
