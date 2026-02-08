# DashScope API 客户端
# TODO: 任务 4.1 - 实现 DashScopeClient 类
# - __init__(self, settings: Settings)
# - async def chat(self, messages: list[dict]) -> str
# - 使用 httpx.AsyncClient 进行 HTTP 请求
# - 处理 API 错误和超时
# - API 端点: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
import httpx
from app.core.settings import Settings
from dashscope import Generation
import dashscope
class DashScopeClient():
    api_key:str
    model_name:str
    base_url:str
    def __init__(self,settings:Settings):
        self.api_key=settings.dashscope_api_key
        self.model_name=settings.chat_model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.client=httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization":f"Bearer {self.api_key}",
                "Content-Type":"application/json"
            }
        )
    async def chat(self,messages:list[dict])->str:
        """发送消息到dashscope API"""
        try:
            payload={
                "model":self.model_name,
                "input":{
                    "messages":messages
                },
                "parameters":{
                    "result_format":"message"
                }
            }
            response=await self.client.post(
                url=self.base_url,
                json=payload
            )
            response.raise_for_status()
            result=response.json()
            content=result["output"]["choices"][0]["message"]["content"]
            return content
        except httpx.TimeoutException:
            raise Exception("DashScope API 请求超时")
        except httpx.HTTPError as e:
            raise Exception(f"DashScope API HTTP 错误: {str(e)}")
        except KeyError as e:
            raise Exception(f"DashScope API 响应格式错误: {str(e)}")
        except Exception as e:
            raise Exception(f"DashScope API 调用失败: {str(e)}")
    async def close(self):
        await self.client.aclose()
       



