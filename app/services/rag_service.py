from typing import List, Dict  # Python 类型提示
from app.rag.vector_store import VectorStore  # 你之前实现的向量存储
from langchain_core.prompts import ChatPromptTemplate  # LangChain 的 Prompt 模板
from langchain_core.output_parsers import StrOutputParser  # 输出解析器
from langchain_core.runnables import RunnablePassthrough  # 数据传递工具
from loguru import logger  # 日志工具


class RAGService:
    def __init__(self, vector_store, llm):
        # 初始化，创建 Prompt 模板
        self.vector_store = vector_store
        self.llm = llm

        self.prompt = ChatPromptTemplate.from_template("""
        你是一个专业严谨的知识助手，你的任务是结合搜索到的文档信息，来回答用户的问题。
        如果文档里没有对于问题的解答，请你如实告知。
        文档信息：{context}
        用户问题：{question}
        回答：
        """)
        logger.info("RAG 服务初始化完成")

    async def retrieve(self, question, top_k: int = 3) -> List[Dict]:
        # 检索相关文档
        res = await self.vector_store.search(question, top_k)
        logger.info(f"文档检索到{len(res)}个文档")
        return res

    def format_docs(self, docs: List[Dict]) -> str:
        # 格式化文档为字符串
        if not docs:
            return "没有找到相关文档"
        formatted = []
        for i, chunk in enumerate(docs, 1):
            content = chunk.get("content", "")
            source = chunk.get("metadata", {}).get("source", "未知来源")
            formatted.append(f"文档{i} (来源: {source}):\n{content}")
        return "\n\n".join(formatted)

    async def generate_answer(self, question):
        # 生成完整回答
        docs = await self.retrieve(question)
        formatted = self.format_docs(docs)
        chain = self.prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke(
            {
                "context": formatted,
                "question": question
            }
        )
        sources = list(set([doc.get("metadata", {}).get("source", "未知来源") for doc in docs]))
        return {
            "answer": result,
            "sources": sources
        }

    async def generate_answer_stream(self, question):
        try:
            docs = await self.retrieve(question)
            formatted = self.format_docs(docs)
            chain = self.prompt | self.llm | StrOutputParser()
            async for chunk in chain.astream(
                    {
                        "context": formatted,
                        "question": question
                    }
            ):
                yield chunk
            logger.info(f"流式回答完成")
        except Exception as e:
            logger.error(f"流式生成失败: {str(e)}")
            raise Exception(f"流式生成失败: {str(e)}")

# 流式生成回答
