# 向量存储模块
# TODO: 任务 12.2 - 实现 VectorStore 类
# 向量存储模块
# TODO: 任务 12.2 - 实现 VectorStore 类

from typing import List, Dict
from app.clients.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from loguru import logger


class VectorStore:
    def __init__(self, milvus_client: MilvusClient, embedding_service: EmbeddingService):
        self.milvus = milvus_client
        self.embedding = embedding_service
        logger.info("向量存储初始化完成")

    async def insert(self, chunks: List[Dict]) -> None:
        try:
            if not chunks:
                logger.warning("没有文档需要插入")
                return
            texts = [chunk["content"] for chunk in chunks]
            vectors = await self.embedding.embed_texts(texts)
            data = [
                vectors, texts, [chunk["metadata"] for chunk in chunks]
            ]
            self.milvus.collection.insert(data)
            self.milvus.collection.flush()
            logger.info(f"成功插入 {len(chunks)} 个文档块")

        except Exception as e:
            logger.error(f"插入文档失败: {str(e)}")
            raise Exception(f"插入文档失败: {str(e)}")

    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        try:
            query_vector = await self.embedding.embed_text(query)
            results = self.milvus.collection.search(
                data=[query_vector],
                anns_field="vector",
                param={"metric_type": "IP", "params": {"nprobe": 10}},
                limit=top_k,
                output_fields=["content", "metadata"]
            )
            docs = []
            for hit in results[0]:
                docs.append(
                    {
                        "content": hit.entity.get("content"),
                        "metadata": hit.entity.get("metadata"),
                        "score": hit.score
                    }
                )
            logger.info(f"检索到 {len(docs)} 个相关文档")
            return docs
        except Exception as e:
            logger.error(f"检索文档失败: {str(e)}")
            raise Exception(f"检索文档失败: {str(e)}")

    async def delete_by_source(self, source: str) -> None:
        """
        删除指定来源的所有文档

        Args:
            source: 文件名
        """
        try:
            # 先查询出所有匹配的文档 ID
            expr = f"metadata['source'] == '{source}'"

            # 查询匹配的文档
            results = self.milvus.collection.query(
                expr=expr,
                output_fields=["id"]
            )

            if not results:
                logger.info(f"没有找到来源为 {source} 的文档，跳过删除")
                return

            # 提取所有 ID
            ids = [result["id"] for result in results]

            # 按 ID 删除
            delete_expr = f"id in {ids}"
            self.milvus.collection.delete(delete_expr)

            logger.info(f"已删除来源为 {source} 的 {len(ids)} 个文档")

        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            raise Exception(f"删除文档失败: {str(e)}")
