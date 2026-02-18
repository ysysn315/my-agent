import os
# 设置模型缓存目录（必须在导入 FlagEmbedding 之前）
os.environ["HF_HOME"] = "D:/AI编程/kiro-place/JAVA-agent/my-agent/models"
os.environ["TRANSFORMERS_CACHE"] = "D:/AI编程/kiro-place/JAVA-agent/my-agent/models"

from typing import List, Dict
from FlagEmbedding import FlagReranker
from loguru import logger
class BGEReranker:
    """BGE Rerank模型"""
    def __init__(self,model_name:str="BAAI/bge-reranker-base"):
        self.reranker=FlagReranker(model_name,use_fp16=True)
        logger.info(f"BGE Reranker 初始化完成: {model_name}")
    def rerank(self,query:str,documents:List[Dict],top_k:int=None)->List[Dict]:
        """
        重排文档
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档包含 content 字段
            top_k: 返回前K个结果
        
        Returns:
            重排后的文档列表
        """
        if not documents:
            return []
        pairs=[[query,doc["content"]] for doc in documents]

        raw_scores = self.reranker.compute_score(pairs)
        # 处理返回值格式（可能是嵌套列表）
        if raw_scores and isinstance(raw_scores[0], list):
            scores = [s[0] for s in raw_scores]
        else:
            scores = raw_scores if isinstance(raw_scores, list) else [raw_scores]


        scores_docs=list(zip(documents,scores))
        scores_docs.sort(key=lambda x:x[1],reverse=True)
        result=[doc for doc,scores in scores_docs[:top_k]]
        logger.info(f"BGE Rerank 完成，返回 {len(result)} 个文档")
        
        return result
