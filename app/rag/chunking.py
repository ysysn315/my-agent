# 文档切分模块
# TODO: 任务 11.1 - 实现 DocumentChunker 类
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


class DocumentChunker:
    def __init__(self, max_size: int = 800, overlap: int = 100):
        self.max_size = max_size
        self.overlap = overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    def chunk_text(self, text: str, source: str) -> List[Dict]:
        if text is None or not text.strip():
            logger.warning(f"切分的{source}文本为空")
            return []
        else:
            response = self.splitter.split_text(text)
            chunks = []
            for i, chunk_text in enumerate(response):
                chunks.append(
                    {
                        "content": chunk_text,
                        "metadata": {"source": source, "chunk_index": i, "total_chunks": len(response)}
                    },
                )
            logger.info(f"文档 {source} 切分完成: {len(chunks)} 个 chunks")
            return chunks

