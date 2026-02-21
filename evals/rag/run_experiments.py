import asyncio
from statistics import mean

from evals.rag.common import load_json, save_json, build_rag
from evals.rag.metrics import hit_at_k, recall_at_k, mrr, precision_at_k, ndcg_at_k, mean_average_precision

DATASET_PATH = "evals/rag/datasets/rag_retrieval_cases.json"
REPORT_PATH = "evals/rag/reports/experiment_latest.json"

CONFIGS = [
    {"name": "baseline", "top_k": 3, "enable_hybrid": False, "enable_rerank": False},
    {"name": "hybrid_only", "top_k": 3, "enable_hybrid": True, "enable_rerank": False},
    {"name": "rerank_only", "top_k": 3, "enable_hybrid": False, "enable_rerank": True},
    {"name": "hybrid_rerank", "top_k": 3, "enable_hybrid": True, "enable_rerank": True},
    {"name": "hybrid_rerank_k5", "top_k": 5, "enable_hybrid": True, "enable_rerank": True},
]


async def run_one(cfg, cases):
    _, vector_store = await build_rag(
        enable_hybrid=cfg["enable_hybrid"],
        enable_rerank=cfg["enable_rerank"],
        dense_top_k=max(10, cfg["top_k"]),
    )

    h3_list, r3_list, mrr_list = [], [], []
    p3_list, ndcg3_list = [], []
    all_pred, all_gold = [], []

    for c in cases:
        gold = set(c["gold_sources"])
        docs = await vector_store.search(c["query"], top_k=cfg["top_k"])
        pred = [
            (d.get("metadata") or {}).get("source", "")
            for d in docs
            if (d.get("metadata") or {}).get("source", "")
        ]
        h3_list.append(hit_at_k(pred, gold, min(3, cfg["top_k"])))
        r3_list.append(recall_at_k(pred, gold, min(3, cfg["top_k"])))
        mrr_list.append(mrr(pred, gold))
        p3_list.append(precision_at_k(pred, gold, min(3, cfg["top_k"])))
        ndcg3_list.append(ndcg_at_k(pred, gold, min(3, cfg["top_k"])))
        all_pred.append(pred)
        all_gold.append(gold)

    return {
        "config": cfg,
        "metrics": {
            "hit@3": round(mean(h3_list), 4),
            "recall@3": round(mean(r3_list), 4),
            "mrr": round(mean(mrr_list), 4),
            "precision@3": round(mean(p3_list), 4),
            "ndcg@3": round(mean(ndcg3_list), 4),
            "map": round(mean_average_precision(all_pred, all_gold), 4),

        },
    }


async def main():
    cases = load_json(DATASET_PATH)
    results = []
    for cfg in CONFIGS:
        r = await run_one(cfg, cases)
        results.append(r)
        print(cfg["name"], r["metrics"])

    results_sorted = sorted(results,
                            key=lambda x: (x["metrics"]["map"], x["metrics"]["ndcg@3"], x["metrics"]["mrr"]),
                            reverse=True)
    report = {
        "leaderboard_by_mrr": results_sorted,
        "best": results_sorted[0] if results_sorted else None,
    }
    save_json(REPORT_PATH, report)
    print("saved:", REPORT_PATH)


if __name__ == "__main__":
    asyncio.run(main())
