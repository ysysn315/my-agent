from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

class QueryRewriter:
    """查询改写器"""
    def __init__(self,llm,enable_expansion:bool=True,enable_rewrite:bool=True):
        self.llm=llm
        self.enable_expansion=enable_expansion
        self.enable_rewrite=enable_rewrite
    async def rewrite(self,query:str)->str:
        """改写查询"""
        if not self.enable_rewrite:
            return query
        prompt = f"""你是一个查询优化专家。请将用户的查询改写为更清晰、更具体的搜索查询。

规则：
1. 保持原意，但使查询更明确
2. 添加必要的上下文词
3. 只输出改写后的查询，不要解释

原始查询：{query}

改写后的查询："""
        try:
            messages=[
                SystemMessage(content="你是一个查询优化专家，只输出改写结果。"),
                HumanMessage(content=prompt)
            ]
            response=await self.llm.ainvoke(messages)
            rewritten=response.content.strip()
            logger.info(f"[QueryRewriter]改写：'{query}'->'{rewritten}'")
            return rewritten
        except Exception as e:
            logger.warning(f"查询改写失败：{e}")
            return query
    async def expand(self,query:str,num_expansions:int=3)->List[str]:
        """拓展查询"""
        if not self.enable_expansion:
            return [query]
        prompt = f"""你是一个搜索专家。请根据原始查询生成 {num_expansions} 个相关的搜索查询。

规则：
1. 添加同义词、相关词
2. 从不同角度表达相同意图
3. 每行一个查询，不要编号

原始查询：{query}

相关查询："""
        try:
            messages = [
                SystemMessage(content="你是一个搜索专家，每行输出一个查询。"),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            expansions=[line.strip() for line in response.content.strip().split('\n') if line.strip()]
            all_queries=[query]+expansions
            all_queries=list(dict.fromkeys(all_queries))
            logger.info(f"[QueryRewriter] 扩展: '{query}' → {all_queries}")
            return all_queries[:num_expansions+1]
        except Exception as e:
            logger.warning(f"查询拓展失败：{e}")
            return [query]
    async def process(self, query: str) -> str:
        """完整处理：改写 + 扩展，返回合并后的查询"""
        # Step 1: 改写
        rewritten = await self.rewrite(query)
        
        # Step 2: 扩展（可选，这里返回改写后的单个查询）
        return rewritten
    async def process_with_expansions(self,query:str)->List[str]:
        rewritten=await self.rewrite(query)
        expansions=await self.expand(rewritten)
        return expansions



        
        
        