# 文档检索工具 - 查询内部知识库

from langchain.tools import tool
from app.rag.vector_store import VectorStore


def create_docs_tool(vector_store: VectorStore):
    """
    创建文档检索工具的工厂函数
    
    参数:
        vector_store: VectorStore 实例
    
    返回:
        配置好的文档检索工具
    """
    
    @tool
    async def query_internal_docs(query: str) -> str:
        """查询内部文档知识库"""
        docs = await vector_store.search(query, top_k=3)
        if not docs:
            return "未找到相关文档"

        result = []
        for i, doc in enumerate(docs, 1):
            result.append(f"【文档 {i}】\n{doc['content']}\n")
        
        return "\n".join(result)
    
    return query_internal_docs
