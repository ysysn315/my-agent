# FastAPI 应用入口
# TODO: 任务 3.1 - 初始化 FastAPI 应用，配置 CORS，添加启动/关闭事件
# TODO: 任务 3.2 - 添加健康检查端点 GET /health
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_chat, routes_milvus, routes_session, routes_upload, routes_aiops
import os
os.environ["HF_HOME"] = "D:/AI编程/kiro-place/JAVA-agent/my-agent/models"
os.environ["TRANSFORMERS_CACHE"] = "D:/AI编程/kiro-place/JAVA-agent/my-agent/models"
app=FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动事件：应用启动时执行
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    print("Application starting...")
    # TODO: 这里后续会添加：
    # - 初始化日志系统
    # - 连接 Milvus 数据库
    # - 初始化其他资源
    print("Application startup complete")

# 关闭事件：应用关闭时执行
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    print("Application shutting down...")
    # TODO: 这里后续会添加：
    # - 断开 Milvus 连接
    # - 清理临时资源
    print("Application shutdown complete")


@app.get("/health")
async def health()->dict:
    return {"status":"ok"}

#注册路由
app.include_router(routes_chat.router,prefix="/api")
app.include_router(routes_milvus.router,prefix="/milvus")
app.include_router(routes_session.router,prefix="/api")
app.include_router(routes_upload.router,prefix="/api")
app.include_router(routes_aiops.router,prefix="/api")



