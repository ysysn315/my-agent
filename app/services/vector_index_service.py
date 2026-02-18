# 向量索引服务
# TODO: 任务 13.2 - 实现 VectorIndexService 类
# 向量索引服务
# TODO: 任务 13.2 - 实现 VectorIndexService 类

from typing import Dict
from app.rag.chunking import DocumentChunker
from app.rag.vector_store import VectorStore
from loguru import logger
from app.rag.load import DocumentLoader


class VectorIndexService:
    def __init__(self, chunker: DocumentChunker, vector_store: VectorStore):
        self.chunker = chunker
        self.vector_store = vector_store
        logger.info("向量索引服务初始化完成")

    async def index_document(self, file_path: str, filename: str) -> Dict:
        try:
            text=DocumentLoader.load(file_path)
        
            if not text or not text.strip():
                logger.warning(f"文件{filename}为空")
                return {"filename": filename, "chunks": 0, "status": "failed"}
            chunks = self.chunker.chunk_text(text, filename)
            if not chunks:
                logger.warning(f"文件{filename}切分后无内容")
                return {"filename": filename, "chunks": 0, "status": "failed"}
            
            # 直接插入，不删除旧数据
            await self.vector_store.insert(chunks)
            logger.info(f"文档 {filename} 索引完成，共 {len(chunks)} 个 chunks")
            return {
                "filename": filename,
                "chunks": len(chunks),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"索引文档 {filename} 失败: {str(e)}")
            return {
                "filename": filename,
                "chunks": 0,
                "status": "failed"
            }
