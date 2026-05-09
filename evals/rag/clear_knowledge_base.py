import asyncio

from evals.rag.kb_tools import clear_current_knowledge_base, load_settings, to_pretty_json


async def main() -> None:
    result = await clear_current_knowledge_base(load_settings())
    print(to_pretty_json(result))


if __name__ == "__main__":
    asyncio.run(main())
