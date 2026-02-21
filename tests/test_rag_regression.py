import json
from pathlib import Path


def _load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_retrieval_regression_not_drop():
    cur = _load("evals/rag/reports/retrieval_latest.json")
    base = _load("evals/rag/baselines/retrieval_baseline.json")
    assert cur["summary"]["hit@3"] >= base["summary"]["hit@3"] - 0.03
    assert cur["summary"]["mrr"] >= base["summary"]["mrr"] - 0.03
    assert cur["summary"]["ndcg@3"] >= base["summary"]["ndcg@3"] - 0.03
    assert cur["summary"]["map"] >= base["summary"]["map"] - 0.03


def test_generation_regression_not_drop():
    cur = _load("evals/rag/reports/generation_latest.json")
    base = _load("evals/rag/baselines/generation_baseline.json")
    assert cur["summary"]["keyword_recall"] >= base["summary"]["keyword_recall"] - 0.05
    assert cur["summary"]["source_hit"] >= base["summary"]["source_hit"] - 0.05
