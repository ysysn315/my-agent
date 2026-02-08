# 向量化服务模块
# TODO: 任务 11.3 - 实现 EmbeddingService 类
from typing import List
from langchain_community.embeddings import DashScopeEmbeddings
from app.core.settings import Settings
from loguru import logger


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.embeddings = DashScopeEmbeddings(
            model=settings.embedding_model,  # "text-embedding-v4"
            dashscope_api_key=settings.dashscope_api_key
        )

    async def embed_text(self, text: str) -> List[float]:
        try:
            result = await self.embeddings.aembed_query(text)
            logger.info(f"向量化单个文本成功，文本长度: {len(text)}, 向量维度: {len(result)}")

            return result
        except Exception as e:
            logger.error(f"向量化文本失败: {str(e)}")
            raise Exception(f"向量化失败: {str(e)}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            result = await self.embeddings.aembed_documents(texts)
            logger.info(f"批量向量化成功，文本数量: {len(texts)}, 向量维度: {len(result[0]) if result else 0}")
            return result
        except Exception as e:
            logger.error(f"批量向量化失败: {str(e)}")
            raise Exception(f"批量向量化失败: {str(e)}")
