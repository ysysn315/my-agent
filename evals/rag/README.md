# RAG Evaluation

## What is evaluated

1. Retrieval:
- Hit@k
- Recall@k
- MRR

2. Generation:
- keyword_recall
- source_hit

3. Experiment loop:
- Compare top_k / enable_hybrid / enable_rerank

## Run

Use your conda env:

```bash
D:\Anaconda\envs\langchain-agent\python.exe evals/rag/run_retrieval_eval.py
D:\Anaconda\envs\langchain-agent\python.exe evals/rag/run_generation_eval.py
D:\Anaconda\envs\langchain-agent\python.exe evals/rag/run_experiments.py
