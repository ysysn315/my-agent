"""
测试文档检索工具是否正常工作
"""
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from app.agents.tools.internal_docs_tool import create_docs_tool
from app.rag.vector_store import VectorStore
from app.clients.milvus_client import MilvusClient
from app.core.settings import get_settings

# 加载环境变量
load_dotenv()


async def test_docs_tool():
    """测试文档检索工具"""
    logger.info("=" * 60)
    logger.info("测试文档检索工具")
    logger.info("=" * 60)
    
    settings = get_settings()
    
    try:
        # 初始化 Milvus 和 VectorStore
        logger.info("初始化 Milvus 客户端...")
        milvus_client = MilvusClient(settings)
        
        logger.info("初始化 VectorStore...")
        vector_store = VectorStore(milvus_client, settings)
        
        logger.info("创建文档检索工具...")
        docs_tool = create_docs_tool(vector_store)
        
        logger.info(f"✅ 工具创建成功: {docs_tool.name}")
        logger.info(f"工具描述: {docs_tool.description}")
        
        # 测试查询
        query = "CPU 使用率过高"
        logger.info(f"\n测试查询: {query}")
        
        result = await docs_tool.ainvoke({"query": query})
        
        logger.info(f"\n查询结果:\n{result}")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        logger.info("\n提示:")
        logger.info("- 如果 Milvus 未启动，请运行: docker-compose up -d")
        logger.info("- 如果知识库为空，请先上传文档")


if __name__ == "__main__":
    asyncio.run(test_docs_tool())
