import asyncio
from app.clients.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.core.settings import get_settings

async def test():
    settings = get_settings()

    # 初始化
    milvus = MilvusClient(settings)
    await milvus.connect()
    await milvus.ensure_collection()

    embedding = EmbeddingService(settings)
    vector_store = VectorStore(milvus, embedding)

    # 测试插入
    chunks = [
        {"content": "这是第一段测试文本", "metadata": {"source": "test.txt", "chunk_index": 0}},
        {"content": "这是第二段测试文本", "metadata": {"source": "test.txt", "chunk_index": 1}}
    ]
    await vector_store.insert(chunks)

    # 测试检索
    docs = await vector_store.search("测试", top_k=2)
    print(f"找到 {len(docs)} 个文档")
    print(docs[0])

asyncio.run(test())







