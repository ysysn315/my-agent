import asyncio
from statistics import mean
from typing import Dict, List

from app.clients.milvus_client import MilvusClient
from app.rag.bm25 import BM25Retriever
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from evals.rag.common import load_json, save_json
from evals.rag.kb_tools import (
    batch_index_documents,
    clear_current_knowledge_base,
    collect_test_documents,
)
from evals.rag.metrics import (
    hit_at_k,
    mean_average_precision,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from evals.rag.run_embedding_compare import (
    RETRIEVAL_DATASET_PATH,
    build_chunk_cache,
    build_eval_rerankers,
    clone_settings,
)
from app.core.settings import get_settings


REPORT_PATH = "evals/rag/reports/retrieval_same_conditions_latest.json"

CONFIGS = [
    {"name": "baseline", "top_k": 3, "enable_hybrid": False, "enable_rerank": False},
    {"name": "hybrid_only", "top_k": 3, "enable_hybrid": True, "enable_rerank": False},
    {"name": "rerank_only", "top_k": 3, "enable_hybrid": False, "enable_rerank": True},
    {"name": "hybrid_rerank", "top_k": 3, "enable_hybrid": True, "enable_rerank": True},
    {"name": "hybrid_rerank_k5", "top_k": 5, "enable_hybrid": True, "enable_rerank": True},
]


async def build_vector_store(
    settings,
    chunk_cache: List[Dict],
    enable_hybrid: bool,
    enable_rerank: bool,
    dense_top_k: int,
):
    milvus_client = MilvusClient(settings)
    await milvus_client.connect()
    await milvus_client.ensure_collection()

    embedding_service = EmbeddingService(settings)
    reranker, reranker_llm = build_eval_rerankers(settings)

    vector_store = VectorStore(
        milvus_client=milvus_client,
        embedding_service=embedding_service,
        reranker_llm=reranker_llm,
        reranker=reranker,
        dense_top_k=dense_top_k,
        enable_rerank=enable_rerank,
        enable_hybrid=enable_hybrid,
    )

    # 同条件复跑时，把 BM25 内存索引也补齐。
    if enable_hybrid and chunk_cache:
        vector_store.all_chunks = list(chunk_cache)
        vector_store.bm25_retriever = BM25Retriever()
        vector_store.bm25_retriever.index(vector_store.all_chunks)

    return vector_store, milvus_client


async def run_one_config(settings, chunk_cache: List[Dict], cases: List[Dict], cfg: Dict):
    vector_store = None
    milvus_client = None
    try:
        vector_store, milvus_client = await build_vector_store(
            settings=settings,
            chunk_cache=chunk_cache,
            enable_hybrid=cfg["enable_hybrid"],
            enable_rerank=cfg["enable_rerank"],
            dense_top_k=max(10, cfg["top_k"]),
        )

        per_case = []
        h1_list, h3_list, r3_list, mrr_list = [], [], [], []
        p3_list, ndcg3_list = [], []
        all_pred, all_gold = [], []

        for case in cases:
            gold = set(case["gold_sources"])
            docs = await vector_store.search(case["query"], top_k=cfg["top_k"])
            pred = [
                (doc.get("metadata") or {}).get("source", "")
                for doc in docs
                if (doc.get("metadata") or {}).get("source", "")
            ]

            h1 = hit_at_k(pred, gold, 1)
            h3 = hit_at_k(pred, gold, min(3, cfg["top_k"]))
            r3 = recall_at_k(pred, gold, min(3, cfg["top_k"]))
            mrr_value = mrr(pred, gold)
            p3 = precision_at_k(pred, gold, min(3, cfg["top_k"]))
            ndcg3 = ndcg_at_k(pred, gold, min(3, cfg["top_k"]))

            h1_list.append(h1)
            h3_list.append(h3)
            r3_list.append(r3)
            mrr_list.append(mrr_value)
            p3_list.append(p3)
            ndcg3_list.append(ndcg3)
            all_pred.append(pred)
            all_gold.append(gold)

            per_case.append(
                {
                    "id": case["id"],
                    "query": case["query"],
                    "gold_sources": sorted(gold),
                    "pred_sources": pred,
                    "hit@1": h1,
                    "hit@3": h3,
                    "recall@3": r3,
                    "mrr": mrr_value,
                    "precision@3": p3,
                    "ndcg@3": ndcg3,
                }
            )

        return {
            "config": cfg,
            "metrics": {
                "num_cases": len(cases),
                "hit@1": round(mean(h1_list), 4) if h1_list else 0.0,
                "hit@3": round(mean(h3_list), 4) if h3_list else 0.0,
                "recall@3": round(mean(r3_list), 4) if r3_list else 0.0,
                "mrr": round(mean(mrr_list), 4) if mrr_list else 0.0,
                "precision@3": round(mean(p3_list), 4) if p3_list else 0.0,
                "ndcg@3": round(mean(ndcg3_list), 4) if ndcg3_list else 0.0,
                "map": round(mean_average_precision(all_pred, all_gold), 4)
                if all_pred
                else 0.0,
            },
            "cases": per_case,
        }
    finally:
        if milvus_client is not None:
            await milvus_client.close()


async def main():
    base_settings = get_settings()
    settings = clone_settings(
        base_settings,
        embedding_provider="dashscope",
        embedding_model="text-embedding-v4",
        milvus_collection=base_settings.milvus_collection,
    )
    doc_paths = collect_test_documents()
    cases = load_json(RETRIEVAL_DATASET_PATH)

    clear_result = await clear_current_knowledge_base(settings)
    index_result = await batch_index_documents(settings, doc_paths)
    chunk_cache = build_chunk_cache(settings, doc_paths)

    results = []
    for cfg in CONFIGS:
        result = await run_one_config(settings, chunk_cache, cases, cfg)
        results.append(result)
        print(cfg["name"], result["metrics"])

    leaderboard = sorted(
        results,
        key=lambda item: (
            item["metrics"]["map"],
            item["metrics"]["ndcg@3"],
            item["metrics"]["mrr"],
        ),
        reverse=True,
    )

    report = {
        "dataset_path": RETRIEVAL_DATASET_PATH,
        "doc_dirs": ["aiops-docs", "aiops-docs-noise"],
        "fixed_config": {
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "milvus_collection": settings.milvus_collection,
            "rerank_runtime": "BGE rerank first, fallback to qwen-turbo",
            "hybrid_runtime": "Milvus dense + in-memory BM25",
        },
        "clear_result": clear_result,
        "index_result": index_result,
        "chunk_cache_size": len(chunk_cache),
        "leaderboard": leaderboard,
        "best": leaderboard[0] if leaderboard else None,
    }

    save_json(REPORT_PATH, report)
    print("saved:", REPORT_PATH)


if __name__ == "__main__":
    asyncio.run(main())
