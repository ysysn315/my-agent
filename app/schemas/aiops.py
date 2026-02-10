# AIOps 请求/响应模型
from pydantic import BaseModel


class AIOpsRequest(BaseModel):
    """AIOps 分析请求
    
    注意：Java 版本不需要输入（自动读取告警），但 Python 版本支持手动输入问题描述
    """
    problem: str = "请分析当前系统告警"  # 默认值，可以自定义问题


class AIOpsResponse(BaseModel):
    """AIOps 分析响应"""
    report: str  # 分析报告
