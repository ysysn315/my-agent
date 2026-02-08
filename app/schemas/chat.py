# 对话请求/响应模型
# TODO: 任务 5.1 - 使用 Pydantic 定义 ChatRequest 和 ChatResponse
# ChatRequest: Id (str), Question (str)
# ChatResponse: answer (str), sources (list, 可选)
from typing import List

from pydantic import BaseModel
class ChatRequest(BaseModel):
    Id:str
    Question:str
class ChatResponse(BaseModel):
    answer:str
    sources:List[str]=[]
