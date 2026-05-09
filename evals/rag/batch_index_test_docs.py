import asyncio

from evals.rag.kb_tools import batch_index_documents, collect_test_documents, load_settings, to_pretty_json


async def main() -> None:
    doc_paths = collect_test_documents()
    if not doc_paths:
        raise RuntimeError("未找到可导入的测试文档，请检查 aiops-docs 和 aiops-docs-noise 目录。")

    result = await batch_index_documents(load_settings(), doc_paths)
    print(to_pretty_json(result))


if __name__ == "__main__":
    asyncio.run(main())
