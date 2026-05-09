from langchain.tools import tool
from langchain_community.chat_models import ChatTongyi
from loguru import logger

from app.agents.aiops_agent import AIOpsAgent
from app.agents.tools.datetime_tool import get_current_datetime
from app.agents.tools.internal_docs_tool import create_docs_tool
from app.agents.tools.log_tool import query_log
from app.agents.tools.prometheus_tool import query_prometheus_alerts
from app.clients.milvus_client import MilvusClient
from app.core.settings import Settings
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.services.rag_service import RAGService


class AIOpsService:
    """AIOps service that wraps the AIOps agent and its tools."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.rag_service = None
        self._docs_ready = False

        @tool
        async def docs_tool(query: str) -> str:
            """Query the internal document knowledge base."""
            return "知识库当前不可用。请确认 Milvus 已启动并且已上传文档。"

        try:
            self.milvus_client = MilvusClient(settings)
            self.embedding_service = EmbeddingService(settings)
            self.vector_store = VectorStore(self.milvus_client, self.embedding_service)
            self.rag_service = self._build_rag_service()

            @tool
            async def docs_tool(query: str) -> str:
                """Query the internal document knowledge base."""
                return "知识库尚未完成初始化。请先确认 Milvus 已启动，然后重试。"

            logger.info("Document retrieval dependencies initialized")
        except Exception as e:
            logger.warning(f"Document retrieval initialization failed: {e}")
            logger.warning("AIOps can continue, but internal docs search is unavailable")

        self.tools = [
            query_prometheus_alerts,
            query_log,
            docs_tool,
            get_current_datetime,
        ]
        self.agent = AIOpsAgent(
            api_key=settings.dashscope_api_key,
            model=settings.chat_model,
            tools=self.tools,
        )
        logger.info("AIOpsService initialized")


    def _build_rag_service(self):
        try:
            retrieval_llm = ChatTongyi(
                dashscope_api_key=self.settings.dashscope_api_key,
                model_name=self.settings.chat_model,
                streaming=False,
                temperature=0.0,
            )
            return RAGService(self.vector_store, retrieval_llm)
        except Exception as e:
            logger.warning(f"RAG rewrite initialization failed, fallback to single-query docs tool: {e}")
            return None


    def _docs_retriever(self):
        return self.rag_service or self.vector_store


    async def _ensure_docs_tool(self):
        await self.milvus_client.connect()
        await self.milvus_client.ensure_collection()

        if self._docs_ready:
            return

        self.tools[2] = create_docs_tool(self._docs_retriever())
        self.agent = AIOpsAgent(
            api_key=self.settings.dashscope_api_key,
            model=self.settings.chat_model,
            tools=self.tools,
        )
        self._docs_ready = True


    async def analyze(self, problem: str) -> str:
        logger.info(f"AIOpsService analyzing: {problem[:100]}...")
        try:
            await self._ensure_docs_tool()
        except Exception as e:
            logger.warning(f"Knowledge base initialization failed, continue without docs retrieval: {e}")
        report = await self.agent.analyze(problem)
        logger.info("AIOpsService analyze completed")
        return report


    async def analyze_stream(self, problem: str):
        try:
            await self._ensure_docs_tool()
        except Exception as e:
            logger.warning(f"Knowledge base initialization failed, continue without docs retrieval: {e}")
        async for chunk in self.agent.analyze_stream(problem):
            yield chunk
