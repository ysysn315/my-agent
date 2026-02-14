# 对话服务 - 业务逻辑
# TODO: 任务 5.2 - 实现 ChatService 类
# - __init__(self, dashscope_client: DashScopeClient)
# - async def chat(self, question: str) -> str
# Phase 1: 简单版本，不包含工具和历史记录
# Phase 2: 将添加 session_id、历史记录和工具支持
from app.clients.dashscope_client import DashScopeClient
from app.services.session_store import SessionStore
from loguru import logger
from langchain_community.chat_models import ChatTongyi
from app.core.settings import Settings
from langchain_core.messages import HumanMessage, AIMessage
from app.services.rag_service import RAGService
from app.rag.vector_store import VectorStore
from app.rag.embeddings import EmbeddingService
from app.clients.milvus_client import MilvusClient
from app.agents.chat_agent import ChatAgent
from app.agents.tools.datetime_tool import get_current_datetime
from app.agents.tools.internal_docs_tool import create_docs_tool
from app.agents.tools.prometheus_tool import query_prometheus_alerts
from app.agents.tools.log_tool import query_log


class ChatService:
    def __init__(self, settings: Settings, session_store: SessionStore):
        self.settings = settings
        self.session_store = session_store
        self.llm = ChatTongyi(
            dashscope_api_key=settings.dashscope_api_key,
            model_name=settings.chat_model,
            streaming=True
        )
        self.rag_service = None
        self.chat_agent = None

    async def _ensure_agent(self):
        if self.chat_agent is None:
            try:
                logger.info("开始初始化ChatAgent...")
                await self._ensure_rag_service()
                tools = [get_current_datetime]
                tools.append(query_prometheus_alerts)
                tools.append(query_log)
                if self.rag_service is not None:
                    # 使用工厂函数创建文档检索工具
                    vector_store = self.rag_service.vector_store
                    docs_tool = create_docs_tool(vector_store)
                    tools.append(docs_tool)
                    logger.info("添加文档检索工具")

                self.chat_agent = ChatAgent(
                    api_key=self.settings.dashscope_api_key,
                    model=self.settings.chat_model,
                    tools=tools
                )
                logger.info("ChatAgent 初始化完成")
            except Exception as e:
                logger.error(f"ChatAgent 初始化失败: {str(e)}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                self.chat_agent = None

    async def _ensure_rag_service(self):
        if self.rag_service is None:
            try:
                logger.info("开始初始化 RAG 服务...")

                # Step 1
                logger.info("Step 1: 创建 MilvusClient")
                milvus_client = MilvusClient(self.settings)

                # Step 2
                logger.info("Step 2: 连接 Milvus")
                await milvus_client.connect()

                # Step 3
                logger.info("Step 3: 确保 collection 存在")
                await milvus_client.ensure_collection()

                # Step 4
                logger.info("Step 4: 创建 EmbeddingService")
                embedding_service = EmbeddingService(self.settings)

                reranker_llm = ChatTongyi(
                    dashscope_api_key=self.settings.dashscope_api_key,
                    model_name="qwen-turbo",  # 写死
                    streaming=False,
                    temperature=0.0
                )

                # Step 5
                logger.info("Step 5: 创建 VectorStore")
                vector_store = VectorStore(milvus_client, embedding_service,
                                           reranker_llm=reranker_llm, dense_top_k=10, enable_rerank=True)

                # Step 6
                logger.info("Step 6: 创建 RAGService")
                self.rag_service = RAGService(vector_store, self.llm)

                logger.info("RAG 服务初始化完成")
            except Exception as e:
                logger.error(f"RAG 服务初始化失败: {str(e)}")
                import traceback
                logger.error(f"详细错误: {traceback.format_exc()}")
                self.rag_service = None

    async def chat(self, session_id: str, question: str) -> dict:
        try:
            await self._ensure_agent()
            sources = []
            if self.chat_agent is not None:
                history = self.session_store.get_history(session_id)
                answer = await self.chat_agent.chat(question, history)
                logger.info(f"会话 {session_id} 使用 ChatAgent 回复")
            elif self.rag_service is not None:
                result = await self.rag_service.generate_answer(question)
                sources = result["sources"]
                answer = result["answer"]
                logger.info(f"会话 {session_id} 使用 RAG 回复")
            else:
                history = self.session_store.get_history(session_id)
                message = []
                for msg in history:
                    if msg["role"] == "user":
                        message.append(HumanMessage(content=msg["content"]))
                    else:
                        message.append(AIMessage(content=msg["content"]))
                message.append(HumanMessage(content=question))
                response = await self.llm.ainvoke(message)
                answer = response.content
                logger.info(f"会话 {session_id} 使用普通对话回复")
            self.session_store.add_message(session_id, "user", question)
            self.session_store.add_message(session_id, "assistant", answer)

            logger.info(f"会话 {session_id} AI 回复: {answer[:50]}...")
            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"对话出现异常{e}")
            raise Exception(f"对话失败: {str(e)}")

    async def chat_stream(self, session_id: str, question: str):
        """流式对话"""
        try:
            await self._ensure_rag_service()
            full_answer = ""
            if self.rag_service is not None:
                async for chunk in self.rag_service.generate_answer_stream(question):
                    full_answer += chunk
                    yield chunk
                logger.info(f"会话 {session_id} 使用 RAG 流式回复")
            else:
                # 获取历史
                history = self.session_store.get_history(session_id)

                # 转换为 LangChain 格式

                messages = []
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
                # 添加当前问题
                messages.append(HumanMessage(content=question))
                async for chunk in self.llm.astream(messages):
                    content = chunk.content
                    full_answer += content
                    yield content
                logger.info(f"会话 {session_id} 使用普通流式回复")
            self.session_store.add_message(session_id, "user", question)
            self.session_store.add_message(session_id, "assistant", full_answer)

            logger.info(f"会话 {session_id} 流式回复完成")
        except Exception as e:
            logger.error(f"流式对话失败: {str(e)}")
            raise Exception(f"流式对话失败: {str(e)}")
