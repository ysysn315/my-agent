"""
快速测试 AIOps API - 只测试非流式端点
"""
import asyncio
import httpx
from loguru import logger

BASE_URL = "http://localhost:8000"


async def test_ai_ops():
    """测试非流式 AIOps 端点"""
    logger.info("=" * 60)
    logger.info("测试 /api/ai_ops (非流式)")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 准备请求
        request_data = {
            "problem": "系统出现 CPU 使用率过高告警"
        }
        
        logger.info(f"发送请求: {request_data}")
        
        try:
            # 发送 POST 请求
            response = await client.post(
                f"{BASE_URL}/api/ai_ops",
                json=request_data
            )
            
            # 检查响应
            logger.info(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ 请求成功")
                logger.info(f"报告长度: {len(result['report'])} 字符")
                logger.info(f"\n{'='*60}")
                logger.info("报告内容:")
                logger.info(f"{'='*60}")
                logger.info(result['report'])
                logger.info(f"{'='*60}")
            else:
                logger.error(f"❌ 请求失败: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ 请求异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_ai_ops())
