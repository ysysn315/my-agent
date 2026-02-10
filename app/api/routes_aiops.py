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
    """AIOps 故障分析端点（流式，类似 Java 版本）
    
    功能：
    - 使用 SSE (Server-Sent Events) 流式返回分析过程
    - 实时展示分析进度
    
    参数:
        request: AIOps 请求（包含问题描述）
    
    返回:
        StreamingResponse: SSE 流
    """
    async def generate():
        try:
            logger.info(f"收到流式 AIOps 分析请求: {request.problem[:100]}...")
            
            # 发送开始消息
            start_msg = json.dumps({'type': 'message', 'data': '🚀 开始 AIOps 分析...\n'}, ensure_ascii=False)
            yield f"data: {start_msg}\n\n"
            
            # 执行分析
            report = await aiops_service.analyze(request.problem)
            
            # 发送分隔线
            separator = json.dumps({'type': 'message', 'data': '\n' + '='*60 + '\n'}, ensure_ascii=False)
            yield f"data: {separator}\n\n"
            
            # 发送报告标题
            title = json.dumps({'type': 'message', 'data': '📋 **告警分析报告**\n\n'}, ensure_ascii=False)
            yield f"data: {title}\n\n"
            
            # 分块发送报告（模拟流式输出）
            chunk_size = 50
            for i in range(0, len(report), chunk_size):
                chunk = report[i:i + chunk_size]
                chunk_data = json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
            
            # 发送结束分隔线
            end_separator = json.dumps({'type': 'message', 'data': '\n' + '='*60 + '\n\n'}, ensure_ascii=False)
            yield f"data: {end_separator}\n\n"
            
            # 发送完成消息
            done_msg = json.dumps({'type': 'done'})
            yield f"data: {done_msg}\n\n"
            
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
