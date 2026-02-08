# 使用 pydantic-settings 进行配置管理
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    app_port: int = 9900
    upload_dir: str = "./uploads"

    # DashScope 配置
    dashscope_api_key: str
    chat_model: str = "qwen-flash"
    embedding_model: str = "text-embedding-v4"

    # Milvus 配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "knowledge_base"

    # RAG 配置
    doc_chunk_max_size: int = 800
    doc_chunk_overlap: int = 100
    rag_top_k: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
@lru_cache
def get_settings() -> Settings:
    return Settings()
