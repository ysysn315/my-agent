# AIOps 服务
from app.agents.aiops_agent import AIOpsAgent
from app.agents.tools.prometheus_tool import query_prometheus_alerts
from app.agents.tools.log_tool import query_log
from app.agents.tools.datetime_tool import get_current_datetime
from app.agents.tools.internal_docs_tool import create_docs_tool
from app.rag.vector_store import VectorStore
from app.rag.embeddings import EmbeddingService
from app.clients.milvus_client import MilvusClient
from app.core.settings import Settings
from loguru import logger
from langchain.tools import tool


class AIOpsService:
    """AIOps 服务 - 封装 AIOps Agent"""

    def __init__(self, settings: Settings):
        """初始化 AIOps 服务
        
        参数:
            settings: 应用配置
        """

        # 初始化 Milvus 和 VectorStore（用于文档检索工具）
        try:
            self.settings = settings
            self.milvus_client = MilvusClient(settings)
            self.embedding_service = EmbeddingService(settings)
            self.vector_store = VectorStore(self.milvus_client, self.embedding_service)
            self._docs_ready = False
            logger.info("正在初始化文档检索工具...")

            @tool
            async def docs_tool(query: str) -> str:
                """查询内部文档知识库（初始化中/占位）"""
                return "知识库尚未初始化。请先确保 Milvus 已启动，然后重试。"

            logger.info("✅ 文档检索工具初始化成功（使用真实 VectorStore）")
        except Exception as e:
            logger.warning(f"⚠️ 文档检索工具初始化失败: {e}")
            logger.warning("这可能是因为 Milvus 未启动或知识库为空")
            logger.warning("AIOps 功能仍可正常使用，但无法查询知识库")

            # 如果初始化失败，创建一个返回提示信息的工具

            @tool
            async def docs_tool(query: str) -> str:
                """查询内部文档知识库（当前不可用）"""
                return "知识库当前不可用。请确保 Milvus 已启动并且已上传文档。"

        # 准备工具列表
        self.tools = [
            query_prometheus_alerts,
            query_log,
            docs_tool,
            get_current_datetime
        ]

        # 初始化 AIOps Agent
        self.agent = AIOpsAgent(
            api_key=settings.dashscope_api_key,
            model=settings.chat_model,
            tools=self.tools
        )

        logger.info("AIOpsService 初始化成功")

    async def analyze(self, problem: str) -> str:
        """执行 AIOps 分析
        
        参数:
            problem: 问题描述或告警信息
        
        返回:
            分析报告
        """
        logger.info(f"AIOpsService 开始分析: {problem[:100]}...")
        try:
            await self.milvus_client.connect()
            await self.milvus_client.ensure_collection()
            if not self._docs_ready:
                real_docs_tool = create_docs_tool(self.vector_store)
                self.tools[2] = real_docs_tool
                self.agent = AIOpsAgent(
                    api_key=self.settings.dashscope_api_key,
                    model=self.settings.chat_model,
                    tools=self.tools
                )
                self._docs_ready = True
        except Exception as e:
            logger.warning(f"⚠️ 知识库初始化失败，将继续执行但禁用知识库检索: {e}")
        report = await self.agent.analyze(problem)
        logger.info("AIOpsService 分析完成")
        return report
