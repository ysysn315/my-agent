import asyncio
from collections import defaultdict
from statistics import mean

from evals.rag.common import build_rag, load_json, save_json
from evals.rag.metrics import (
    fact_recall_strict,
    forbidden_source_score,
    hallucination_score,
    keyword_recall,
    source_hit,
    source_precision_strict,
    source_recall_strict,
    strict_generation_score,
)


DATASET_PATH = "evals/rag/datasets/rag_generation_cases_formal_template.json"
REPORT_PATH = "evals/rag/reports/generation_strict_latest.json"


def _build_type_summary(case_results):
    """按题型聚合，方便看哪些题型更脆弱。"""
    grouped = defaultdict(list)
    for item in case_results:
        grouped[item["question_type"]].append(item)

    summary = {}
    for question_type, items in grouped.items():
        summary[question_type] = {
            "num_cases": len(items),
            "fact_recall": round(mean(x["fact_recall"] for x in items), 4),
            "source_recall_strict": round(
                mean(x["source_recall_strict"] for x in items), 4
            ),
            "source_precision_strict": round(
                mean(x["source_precision_strict"] for x in items), 4
            ),
            "hallucination_score": round(
                mean(x["hallucination_score"] for x in items), 4
            ),
            "strict_score": round(mean(x["strict_score"] for x in items), 4),
        }
    return summary


async def main():
    cases = load_json(DATASET_PATH)
    rag_service, _ = await build_rag(
        enable_hybrid=True,
        enable_rerank=True,
        dense_top_k=10,
    )

    per_case = []
    keyword_scores = []
    legacy_source_scores = []
    fact_scores = []
    source_recall_scores = []
    source_precision_scores = []
    hallucination_scores = []
    forbidden_source_scores = []
    strict_scores = []

    for c in cases:
        question = c["question"]
        expected_keywords = c.get("expected_keywords", [])
        expected_sources = c.get("expected_sources", [])
        expected_sources_all = c.get("expected_sources_all", expected_sources)
        expected_sources_any = c.get("expected_sources_any", [])
        expected_facts = c.get("expected_facts", [])
        forbidden_claims = c.get("forbidden_claims", [])
        forbidden_sources = c.get("forbidden_sources", [])

        out = await rag_service.generate_answer(question)
        answer = out.get("answer", "")
        sources = out.get("sources", [])

        keyword_score = keyword_recall(answer, expected_keywords)
        legacy_source_score = source_hit(
            sources,
            expected_sources_all + expected_sources_any,
        )
        fact_score = fact_recall_strict(answer, expected_facts)
        source_recall_score = source_recall_strict(
            sources,
            expected_sources_all=expected_sources_all,
            expected_sources_any=expected_sources_any,
        )
        source_precision_score = source_precision_strict(
            sources,
            expected_sources_all=expected_sources_all,
            expected_sources_any=expected_sources_any,
        )
        hallucination_score_value = hallucination_score(answer, forbidden_claims)
        forbidden_source_score_value = forbidden_source_score(
            sources,
            forbidden_sources=forbidden_sources,
        )
        strict_score = strict_generation_score(
            fact_score=fact_score,
            source_recall_score=source_recall_score,
            source_precision_score=source_precision_score,
            hallucination_score_value=hallucination_score_value,
            forbidden_source_score_value=forbidden_source_score_value,
        )

        keyword_scores.append(keyword_score)
        legacy_source_scores.append(legacy_source_score)
        fact_scores.append(fact_score)
        source_recall_scores.append(source_recall_score)
        source_precision_scores.append(source_precision_score)
        hallucination_scores.append(hallucination_score_value)
        forbidden_source_scores.append(forbidden_source_score_value)
        strict_scores.append(strict_score)

        per_case.append(
            {
                "id": c["id"],
                "question": question,
                "question_type": c.get("question_type", "unknown"),
                "difficulty": c.get("difficulty", "unknown"),
                "expected_keywords": expected_keywords,
                "expected_sources_all": expected_sources_all,
                "expected_sources_any": expected_sources_any,
                "forbidden_sources": forbidden_sources,
                "pred_sources": sources,
                "keyword_recall": round(keyword_score, 4),
                "source_hit": round(legacy_source_score, 4),
                "fact_recall": round(fact_score, 4),
                "source_recall_strict": round(source_recall_score, 4),
                "source_precision_strict": round(source_precision_score, 4),
                "hallucination_score": round(hallucination_score_value, 4),
                "forbidden_source_score": round(forbidden_source_score_value, 4),
                "strict_score": round(strict_score, 4),
                "answer_preview": answer[:300],
            }
        )

    report = {
        "dataset_path": DATASET_PATH,
        "summary": {
            "num_cases": len(cases),
            "keyword_recall": round(mean(keyword_scores), 4) if keyword_scores else 0.0,
            "source_hit": round(mean(legacy_source_scores), 4)
            if legacy_source_scores
            else 0.0,
            "fact_recall": round(mean(fact_scores), 4) if fact_scores else 0.0,
            "source_recall_strict": round(mean(source_recall_scores), 4)
            if source_recall_scores
            else 0.0,
            "source_precision_strict": round(mean(source_precision_scores), 4)
            if source_precision_scores
            else 0.0,
            "hallucination_score": round(mean(hallucination_scores), 4)
            if hallucination_scores
            else 0.0,
            "forbidden_source_score": round(mean(forbidden_source_scores), 4)
            if forbidden_source_scores
            else 0.0,
            "strict_score": round(mean(strict_scores), 4) if strict_scores else 0.0,
        },
        "by_question_type": _build_type_summary(per_case),
        "cases": per_case,
    }

    save_json(REPORT_PATH, report)
    print("saved:", REPORT_PATH)
    print(report["summary"])


if __name__ == "__main__":
    asyncio.run(main())
