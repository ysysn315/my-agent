from typing import List, Set, Iterable


def hit_at_k(pred: List[str], gold: Set[str], k: int) -> float:
    topk = pred[:k]
    return 1.0 if any(x in gold for x in topk) else 0.0


def recall_at_k(pred: List[str], gold: Set[str], k: int) -> float:
    if not gold:
        return 1.0
    topk = set(pred[:k])
    return len(topk & gold) / len(gold)


def mrr(pred: List[str], gold: Set[str]) -> float:
    for i, x in enumerate(pred, start=1):
        if x in gold:
            return 1.0 / i
    return 0.0


def keyword_recall(answer: str, keywords: Iterable[str]) -> float:
    kws = [k.strip().lower() for k in keywords if k.strip()]
    if not kws:
        return 1.0
    ans = (answer or "").lower()
    hit = sum(1 for k in kws if k in ans)
    return hit / len(kws)


def source_hit(pred_sources: List[str], expected_sources: Iterable[str]) -> float:
    exp = [x.strip().lower() for x in expected_sources if x.strip()]
    if not exp:
        return 1.0
    p = " | ".join((pred_sources or [])).lower()
    hit = sum(1 for e in exp if e in p)
    return hit / len(exp)


import math


def _unique_keep_order(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def precision_at_k(pred, gold, k):
    topk = pred[:k]
    if k <= 0:
        return 0.0
    return len(set(topk) & set(gold)) / k


def average_precision(pred, gold):
    gold = set(gold)
    if not gold:
        return 1.0
    pred = _unique_keep_order(pred)
    hit = 0
    s = 0.0
    for i, d in enumerate(pred, start=1):
        if d in gold:
            hit += 1
            s += hit / i
    return s / len(gold)


def mean_average_precision(list_pred, list_gold):
    if not list_pred:
        return 0.0
    aps = [average_precision(p, g) for p, g in zip(list_pred, list_gold)]
    return sum(aps) / len(aps)


def ndcg_at_k(pred, gold, k):
    gold = set(gold)
    topk = _unique_keep_order(pred)[:k]

    dcg = 0.0
    for i, d in enumerate(topk, start=1):
        rel = 1.0 if d in gold else 0.0
        dcg += rel / math.log2(i + 1)

    ideal_hits = min(len(gold), k)
    idcg = 0.0
    for i in range(1, ideal_hits + 1):
        idcg += 1.0 / math.log2(i + 1)

    return (dcg / idcg) if idcg > 0 else 0.0
