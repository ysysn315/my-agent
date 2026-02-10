# Prometheus 告警查询工具
# TODO: 实现 query_prometheus_alerts 工具
from langchain.tools import tool
import json
from datetime import datetime, timedelta


@tool
def query_prometheus_alerts() -> str:
    """查询 Prometheus 活动告警

    该工具从 Prometheus 告警系统检索所有当前活动的告警。
    返回告警名称、描述、状态和持续时间。
     使用场景：
    - 查看当前有哪些告警在触发
    - 了解告警的详细信息和持续时间
    - 作为故障排查的第一步
    """
    now=datetime.now()
    alerts=[
        {
            "alert_name": "HighCPUUsage",
            "description": (
                "服务 payment-service 的 CPU 使用率持续超过 80%，当前值为 92%。"
                "实例: pod-payment-service-7d8f9c6b5-x2k4m，命名空间: production"
            ),
            "state": "firing",
            "active_at": (now - timedelta(minutes=25)).isoformat() + "Z",
            "duration": "25m30s"
        },
        {
            "alert_name": "HighMemoryUsage",
            "description": (
                "服务 order-service 的内存使用率持续超过 85%，当前值为 91%。"
                "JVM堆内存使用: 3.8GB/4GB，可能存在内存泄漏风险。"
                "实例: pod-order-service-5c7d8e9f1-m3n2p，命名空间: production"
            ),
            "state": "firing",
            "active_at": (now - timedelta(minutes=15)).isoformat() + "Z",
            "duration": "15m20s"
        },
        {
            "alert_name": "SlowResponse",
            "description": (
                "服务 user-service 的 P99 响应时间持续超过 3 秒，当前值为 4.2 秒。"
                "受影响接口: /api/v1/users/profile, /api/v1/users/orders。"
                "可能原因：数据库慢查询或下游服务延迟"
            ),
            "state": "firing",
            "active_at": (now - timedelta(minutes=10)).isoformat() + "Z",
            "duration": "10m15s"
        }
    ]
    result={
        "success": True,
        "alerts":alerts,
        "message":f"成功检索到{len(alerts)}个活动告警"
    }
    return json.dumps(result,ensure_ascii=False,indent=2)
