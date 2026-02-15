# AIOps API 路由
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.aiops import AIOpsRequest, AIOpsResponse
from app.services.aiops_service import AIOpsService
from app.core.settings import Settings, get_settings
from loguru import logger
import json

router = APIRouter(tags=["aiops"])


def get_aiops_service(settings: Settings = Depends(get_settings)) -> AIOpsService:
    """依赖注入：获取 AIOps 服务实例"""
    return AIOpsService(settings)


@router.post("/ai_ops", response_model=AIOpsResponse)
async def ai_ops(
        request: AIOpsRequest,
        aiops_service: AIOpsService = Depends(get_aiops_service)
):
    """AIOps 故障分析端点（非流式）
    
    功能：
    - 接收问题描述
    - 执行 Planner-Operation-Reflection 循环
    - 返回完整分析报告
    
    参数:
        request: AIOps 请求（包含问题描述）
    
    返回:
        AIOpsResponse: 包含分析报告
    """
    try:
        logger.info(f"收到 AIOps 分析请求: {request.problem[:100]}...")

        # 执行分析
        report = await aiops_service.analyze(request.problem)

        return AIOpsResponse(report=report)

    except Exception as e:
        logger.error(f"AIOps 分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"AIOps 分析失败: {str(e)}"
        )


@router.post("/ai_ops_stream")
async def ai_ops_stream(
        request: AIOpsRequest,
        aiops_service: AIOpsService = Depends(get_aiops_service)
):
    """AIOps 故障分析端点（真正的流式）"""

    async def generate():
        try:
            logger.info(f"收到流式 AIOps 分析请求: {request.problem[:100]}...")

            # 直接转发 Agent 的流式输出
            async for chunk in aiops_service.analyze_stream(request.problem):
                # chunk 已经是 JSON 字符串，直接包装成 SSE 格式
                yield f"data: {chunk}\n\n"

        except Exception as e:
            logger.error(f"流式 AIOps 分析失败: {str(e)}")
            error_msg = json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
