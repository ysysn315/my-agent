# 文件上传路由
# TODO: 任务 13.3 - 实现文件上传 API
# 文件上传路由
# TODO: 任务 13.3 - 实现文件上传 API

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.schemas.upload import UploadResponse
from app.services.vector_index_service import VectorIndexService
from app.core.settings import Settings, get_settings
from app.clients.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.chunking import DocumentChunker
from app.rag.vector_store import VectorStore
from loguru import logger
import os
router = APIRouter()

async def get_index_service(
        settings:Settings=Depends(get_settings)
)->VectorIndexService:
    milvus_client=MilvusClient(settings)
    await milvus_client.connect()
    await  milvus_client.ensure_collection()

    embedding_service=EmbeddingService(settings)
    vector_store=VectorStore(milvus_client,embedding_service)
    chunker=DocumentChunker(
        max_size=settings.doc_chunk_max_size,
        overlap= settings.doc_chunk_overlap
    )
    index_service=VectorIndexService(chunker,vector_store)
    return index_service

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
        file: UploadFile = File(...),
        settings: Settings = Depends(get_settings),
        index_service: VectorIndexService = Depends(get_index_service)
):
    try:
        allowed_extensions=[".txt",".md"]
        file_ext=os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}，仅支持 .txt 和 .md 文件"
            )
        logger.info(f"接收到文件上传请求: {file.filename}")

        # 2. 确保 uploads 目录存在
        os.makedirs(settings.upload_dir, exist_ok=True)

        file_path=os.path.join(settings.upload_dir,file.filename)
        with open(file_path,"wb") as f:
            content=await file.read()
            f.write(content)
        logger.info(f"文件{file.filename}保存成功:{file_path}")
        result=await index_service.index_document(file_path,file.filename)
        return UploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

















