from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from app.agents.chat_agent import ChatAgent
from app.agents.tools.datetime_tool import get_current_datetime
from app.agents.tools.internal_docs_tool import create_docs_tool
from app.agents.tools.log_tool import query_log
from app.agents.tools.prometheus_tool import query_prometheus_alerts
from app.agents.tools.tavily_tool import create_tavily_search_tool
from app.clients.milvus_client import MilvusClient
from app.core.settings import Settings
from app.rag.embeddings import EmbeddingService
from app.rag.reranker import BGEReranker
from app.rag.vector_store import VectorStore
from app.services.rag_service import RAGService
from app.services.session_store import SessionStore


class ChatService:
    def __init__(self, settings: Settings, session_store: SessionStore):
        self.settings = settings
        self.session_store = session_store
        self.llm = ChatTongyi(
            dashscope_api_key=settings.dashscope_api_key,
            model_name=settings.chat_model,
            streaming=True,
        )
        self.summary_llm = ChatTongyi(
            dashscope_api_key=settings.dashscope_api_key,
            model_name=settings.chat_model,
            streaming=False,
            temperature=0.0,
        )
        self.rag_service = None
        self.chat_agent = None

    def _get_session_summary(self, session_id: str) -> str:
        get_summary = getattr(self.session_store, "get_summary", None)
        if callable(get_summary):
            return get_summary(session_id)
        return ""

    @staticmethod
    def _format_messages_for_summary(messages: list) -> str:
        lines = []
        for msg in messages:
            role = "用户" if msg.get("role") == "user" else "助手"
            content = str(msg.get("content", "")).strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "无新增对话"

    async def _compact_session_history(self, session_id: str) -> None:
        get_messages_to_summarize = getattr(self.session_store, "get_messages_to_summarize", None)
        apply_summary_and_trim = getattr(self.session_store, "apply_summary_and_trim", None)
        if not callable(get_messages_to_summarize) or not callable(apply_summary_and_trim):
            return

        messages_to_summarize = get_messages_to_summarize(session_id)
        if not messages_to_summarize:
            return

        existing_summary = self._get_session_summary(session_id)
        formatted_messages = self._format_messages_for_summary(messages_to_summarize)
        prompt = f"""你是一个会话摘要助手。请把“已有摘要”和“新增对话”合并成新的会话摘要。

要求：
1. 只保留后续回答和检索真正需要的信息。
2. 优先保留用户目标、关键实体、已确认事实、已做过的排查、已有结论和未解决问题。
3. 保持简洁，不要编造。
4. 直接输出合并后的摘要。

已有摘要：
{existing_summary or "无"}

新增对话：
{formatted_messages}

新的会话摘要："""

        try:
            response = await self.summary_llm.ainvoke(
                [
                    SystemMessage(content="你是一个严谨的会话摘要助手，只输出更新后的摘要。"),
                    HumanMessage(content=prompt),
                ]
            )
            new_summary = (response.content or "").strip()
            if not new_summary:
                logger.warning(f"会话 {session_id} 摘要生成结果为空，跳过压缩")
                return
            apply_summary_and_trim(session_id, new_summary)
            logger.info(f"会话 {session_id} 已完成历史压缩，摘要长度: {len(new_summary)}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"会话 {session_id} 摘要压缩失败，保留原始 history: {e}")

    async def _rewrite_question_with_history(
        self,
        question: str,
        history: list,
        summary: str = "",
    ) -> str:
        await self._ensure_rag_service()
        if self.rag_service is None or self.rag_service.query_rewriter is None:
            return question

        try:
            rewritten_question = await self.rag_service.query_rewriter.process(
                question,
                history=history,
                summary=summary,
            )
            if rewritten_question != question:
                logger.info(f"会话问题已改写为自包含查询: {rewritten_question}")
            return rewritten_question
        except Exception as e:  # noqa: BLE001
            logger.warning(f"history-aware rewrite 失败，回退原问题: {e}")
            return question

    async def _ensure_agent(self):
        if self.chat_agent is not None:
            return

        try:
            logger.info("开始初始化 ChatAgent...")
            await self._ensure_rag_service()

            tools = [get_current_datetime]
            if self.settings.tavily_api_key:
                tavily_tool = create_tavily_search_tool(
                    api_key=self.settings.tavily_api_key,
                    base_url=self.settings.tavily_base_url,
                )
                tools.append(tavily_tool)
                logger.info("Added Tavily search tool")
            else:
                logger.warning("TAVILY_API_KEY not configured, skip Tavily tool")

            tools.append(query_prometheus_alerts)
            tools.append(query_log)

            if self.rag_service is not None:
                docs_tool = create_docs_tool(self.rag_service)
                tools.append(docs_tool)
                logger.info("添加文档检索工具")

            self.chat_agent = ChatAgent(
                api_key=self.settings.dashscope_api_key,
                model=self.settings.chat_model,
                tools=tools,
            )
            logger.info("ChatAgent 初始化完成")
        except Exception as e:  # noqa: BLE001
            logger.error(f"ChatAgent 初始化失败: {str(e)}")
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            self.chat_agent = None

    async def _ensure_rag_service(self):
        if self.rag_service is not None:
            return

        try:
            logger.info("开始初始化 RAG 服务...")

            logger.info("Step 1: 创建 MilvusClient")
            milvus_client = MilvusClient(self.settings)

            logger.info("Step 2: 连接 Milvus")
            await milvus_client.connect()

            logger.info("Step 3: 确保 collection 存在")
            await milvus_client.ensure_collection()

            logger.info("Step 4: 创建 EmbeddingService")
            embedding_service = EmbeddingService(self.settings)

            logger.info("Step 4.5: 创建 BGE Reranker")
            try:
                reranker = BGEReranker("BAAI/bge-reranker-base")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"BGE Reranker 初始化失败，回退到 LLM 重排: {e}")
                reranker = None

            reranker_llm = ChatTongyi(
                dashscope_api_key=self.settings.dashscope_api_key,
                model_name="qwen-turbo",
                streaming=False,
                temperature=0.0,
            )

            logger.info("Step 5: 创建 VectorStore")
            vector_store = VectorStore(
                milvus_client,
                embedding_service,
                reranker_llm=reranker_llm,
                reranker=reranker,
                dense_top_k=10,
                enable_rerank=True,
            )

            logger.info("Step 6: 创建 RAGService")
            self.rag_service = RAGService(vector_store, self.llm)

            logger.info("RAG 服务初始化完成")
        except Exception as e:  # noqa: BLE001
            logger.error(f"RAG 服务初始化失败: {str(e)}")
            import traceback

            logger.error(f"详细错误: {traceback.format_exc()}")
            self.rag_service = None

    async def chat(self, session_id: str, question: str, metadata_filters: dict = None) -> dict:
        try:
            sources = []
            history = self.session_store.get_history(session_id)
            session_summary = self._get_session_summary(session_id)

            if metadata_filters:
                await self._ensure_rag_service()
                if self.rag_service is None:
                    raise Exception("RAG 服务不可用，无法执行 metadata 过滤检索")
                result = await self.rag_service.generate_answer(
                    question,
                    metadata_filters=metadata_filters,
                    history=history,
                    session_summary=session_summary,
                )
                sources = result["sources"]
                answer = result["answer"]
                logger.info(f"会话 {session_id} 使用 metadata 过滤 RAG 回复")
            else:
                await self._ensure_agent()

            if not metadata_filters and self.chat_agent is not None:
                rewritten_question = await self._rewrite_question_with_history(
                    question,
                    history,
                    summary=session_summary,
                )
                answer = await self.chat_agent.chat(rewritten_question, history, summary=session_summary)
                logger.info(f"会话 {session_id} 使用 ChatAgent 回复")
            elif not metadata_filters and self.rag_service is not None:
                result = await self.rag_service.generate_answer(
                    question,
                    history=history,
                    session_summary=session_summary,
                )
                sources = result["sources"]
                answer = result["answer"]
                logger.info(f"会话 {session_id} 使用 RAG 回复")
            elif not metadata_filters:
                rewritten_question = await self._rewrite_question_with_history(
                    question,
                    history,
                    summary=session_summary,
                )
                messages = []
                if session_summary:
                    messages.append(
                        SystemMessage(content=f"以下是当前会话较早轮次的摘要，请参考：\n{session_summary}")
                    )
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
                messages.append(HumanMessage(content=rewritten_question))
                response = await self.llm.ainvoke(messages)
                answer = response.content
                logger.info(f"会话 {session_id} 使用普通对话回复")

            self.session_store.add_message(session_id, "user", question)
            self.session_store.add_message(session_id, "assistant", answer)
            await self._compact_session_history(session_id)

            logger.info(f"会话 {session_id} AI 回复: {answer[:50]}...")
            return {"answer": answer, "sources": sources}
        except Exception as e:  # noqa: BLE001
            logger.error(f"对话出现异常 {e}")
            raise Exception(f"对话失败: {str(e)}")

    async def chat_stream(self, session_id: str, question: str, metadata_filters: dict = None):
        """流式对话。"""

        try:
            full_answer = ""
            history = self.session_store.get_history(session_id)
            session_summary = self._get_session_summary(session_id)

            if metadata_filters:
                await self._ensure_rag_service()
                if self.rag_service is None:
                    raise Exception("RAG 服务不可用，无法执行 metadata 过滤检索")
                async for chunk in self.rag_service.generate_answer_stream(
                    question,
                    metadata_filters=metadata_filters,
                    history=history,
                    session_summary=session_summary,
                ):
                    full_answer += chunk
                    yield chunk
                logger.info(f"会话 {session_id} 使用 metadata 过滤 RAG 流式回复")
            else:
                await self._ensure_agent()

            if not metadata_filters and self.chat_agent is not None:
                rewritten_question = await self._rewrite_question_with_history(
                    question,
                    history,
                    summary=session_summary,
                )
                answer = await self.chat_agent.chat(rewritten_question, history, summary=session_summary)
                full_answer = answer
                yield answer
                logger.info(f"Session {session_id} streamed via ChatAgent")
            elif not metadata_filters and self.rag_service is not None:
                async for chunk in self.rag_service.generate_answer_stream(
                    question,
                    history=history,
                    session_summary=session_summary,
                ):
                    full_answer += chunk
                    yield chunk
                logger.info(f"会话 {session_id} 使用 RAG 流式回复")
            elif not metadata_filters:
                rewritten_question = await self._rewrite_question_with_history(
                    question,
                    history,
                    summary=session_summary,
                )
                messages = []
                if session_summary:
                    messages.append(
                        SystemMessage(content=f"以下是当前会话较早轮次的摘要，请参考：\n{session_summary}")
                    )
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
                messages.append(HumanMessage(content=rewritten_question))
                async for chunk in self.llm.astream(messages):
                    content = chunk.content
                    full_answer += content
                    yield content
                logger.info(f"会话 {session_id} 使用普通流式回复")

            self.session_store.add_message(session_id, "user", question)
            self.session_store.add_message(session_id, "assistant", full_answer)
            await self._compact_session_history(session_id)

            logger.info(f"会话 {session_id} 流式回复完成")
        except Exception as e:  # noqa: BLE001
            logger.error(f"流式对话失败: {str(e)}")
            raise Exception(f"流式对话失败: {str(e)}")
