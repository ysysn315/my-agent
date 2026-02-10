"""
测试 AIOps API 端点
测试 2 个端点：
1. /api/ai_ops - 非流式
2. /api/ai_ops_stream - 流式
"""
import asyncio
import httpx
import json
from loguru import logger

# 配置日志
logger.add("test_aiops_api.log", rotation="10 MB")

BASE_URL = "http://localhost:8000"


async def test_ai_ops_non_stream():
    """测试非流式 AIOps 端点"""
    logger.info("=" * 60)
    logger.info("测试 1: /api/ai_ops (非流式)")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 准备请求
        request_data = {
            "problem": "系统出现 CPU 使用率过高告警，请帮我分析原因"
        }
        
        logger.info(f"发送请求: {request_data}")
        
        try:
            # 发送 POST 请求
            response = await client.post(
                f"{BASE_URL}/api/ai_ops",
                json=request_data
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ 请求成功")
                logger.info(f"报告长度: {len(result['report'])} 字符")
                logger.info(f"\n报告内容:\n{result['report']}")
            else:
                logger.error(f"❌ 请求失败: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")


async def test_ai_ops_stream():
    """测试流式 AIOps 端点"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: /api/ai_ops_stream (流式)")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 准备请求
        request_data = {
            "problem": "请分析当前系统告警"  # 使用默认问题
        }
        
        logger.info(f"发送流式请求: {request_data}")
        
        try:
            # 发送流式请求
            async with client.stream(
                "POST",
                f"{BASE_URL}/api/ai_ops_stream",
                json=request_data
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"❌ 请求失败: {response.status_code}")
                    return
                
                logger.info("✅ 开始接收流式数据...")
                
                # 逐行读取 SSE 数据
                full_content = []
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # 去掉 "data: " 前缀
                        
                        try:
                            data = json.loads(data_str)
                            msg_type = data.get("type")
                            msg_data = data.get("data")
                            
                            if msg_type == "message":
                                # 系统消息（开始、分隔线等）
                                logger.info(f"[系统消息] {msg_data}")
                            elif msg_type == "content":
                                # 报告内容
                                print(msg_data, end="", flush=True)
                                full_content.append(msg_data)
                            elif msg_type == "done":
                                # 完成
                                logger.info("\n✅ 流式传输完成")
                            elif msg_type == "error":
                                # 错误
                                logger.error(f"❌ 错误: {msg_data}")
                        
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ 无法解析 JSON: {data_str}")
                
                logger.info(f"\n总共接收内容长度: {len(''.join(full_content))} 字符")
        
        except Exception as e:
            logger.error(f"❌ 流式请求异常: {str(e)}")


async def test_ai_ops_with_custom_problem():
    """测试自定义问题"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: 自定义问题")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 自定义问题
        request_data = {
            "problem": "订单服务响应缓慢，用户反馈下单失败，请帮我排查问题"
        }
        
        logger.info(f"发送请求: {request_data}")
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/ai_ops",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ 请求成功")
                logger.info(f"\n报告内容:\n{result['report'][:500]}...")  # 只显示前 500 字符
            else:
                logger.error(f"❌ 请求失败: {response.status_code}")
        
        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")


async def main():
    """运行所有测试"""
    logger.info("🚀 开始测试 AIOps API")
    logger.info("请确保服务已启动: uvicorn app.main:app --reload")
    logger.info("")
    
    # 测试 1: 非流式
    await test_ai_ops_non_stream()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试 2: 流式
    await test_ai_ops_stream()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试 3: 自定义问题
    await test_ai_ops_with_custom_problem()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
