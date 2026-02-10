# 日志查询工具
from langchain.tools import tool
import json
from datetime import datetime, timedelta


@tool
def query_log(query: str, time_range: str = "5m") -> str:
    """查询系统日志

    该工具从日志系统检索匹配查询条件的日志记录。
    支持多种日志类型：系统指标、应用错误、数据库慢查询、系统事件等。
    
    参数:
        query: 查询关键词（如 "cpu", "error", "slow query", "memory", "oom"）
        time_range: 时间范围（默认 "5m"，表示最近5分钟）
    
    使用场景：
    - 查询 CPU/内存/磁盘相关日志：query="cpu" 或 "memory" 或 "disk"
    - 查询错误日志：query="error" 或 "fatal" 或 "500"
    - 查询慢查询日志：query="slow" 或 "database"
    - 查询系统事件：query="restart" 或 "crash" 或 "oom_kill"
    
    返回:
        JSON格式的日志列表，包含时间戳、级别、服务、实例、消息和指标
    """
    now = datetime.now()
    logs = []
    query_lower = query.lower()
    
    # 1. CPU 相关日志
    if "cpu" in query_lower or ">80" in query_lower:
        for i in range(5):
            logs.append({
                "timestamp": (now - timedelta(minutes=i * 2)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "WARN",
                "service": "payment-service",
                "instance": "pod-payment-service-7d8f9c6b5-x2k4m",
                "message": f"CPU使用率过高: {92.0 - i * 1.5:.1f}%, 进程: java (PID: 1), 线程数: 245",
                "metrics": {
                    "cpu_usage": f"{92.0 - i * 1.5:.1f}",
                    "cpu_cores": "4",
                    "load_average_1m": "3.82",
                    "load_average_5m": "3.65",
                    "top_process": "java",
                    "process_threads": "245"
                }
            })
    
    # 2. 内存相关日志
    if "memory" in query_lower or ">85" in query_lower or "oom" in query_lower:
        for i in range(5):
            logs.append({
                "timestamp": (now - timedelta(minutes=i * 3)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "WARN",
                "service": "order-service",
                "instance": "pod-order-service-5c7d8e9f1-m3n2p",
                "message": f"内存使用率过高: {91.0 - i * 1.2:.1f}%, JVM堆内存: {3.8 - i * 0.1:.1f}GB/4GB, GC次数: {128 - i * 5}",
                "metrics": {
                    "memory_usage": f"{91.0 - i * 1.2:.1f}",
                    "jvm_heap_used": f"{3.8 - i * 0.1:.1f}GB",
                    "jvm_heap_max": "4GB",
                    "gc_count": str(128 - i * 5),
                    "gc_time_ms": str(1250 + i * 50)
                }
            })
        
        # 添加 GC 警告日志
        logs.append({
            "timestamp": (now - timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARN",
            "service": "order-service",
            "instance": "pod-order-service-5c7d8e9f1-m3n2p",
            "message": "频繁 Full GC 警告: 过去10分钟内发生 15 次 Full GC, 平均耗时 850ms, 建议检查内存泄漏",
            "metrics": {
                "full_gc_count": "15",
                "avg_gc_time_ms": "850",
                "survivor_space": "95%",
                "old_gen": "89%"
            }
        })
    
    # 3. 磁盘相关日志
    if "disk" in query_lower or "filesystem" in query_lower:
        for i in range(3):
            logs.append({
                "timestamp": (now - timedelta(minutes=i * 5)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "WARN",
                "service": "log-collector",
                "instance": "node-worker-01",
                "message": f"磁盘使用率告警: /data 分区使用率 {85.0 + i * 2:.1f}%, 可用空间: {15.0 - i * 2:.1f}GB",
                "metrics": {
                    "disk_usage": f"{85.0 + i * 2:.1f}%",
                    "disk_available": f"{15.0 - i * 2:.1f}GB",
                    "disk_total": "100GB",
                    "mount_point": "/data",
                    "largest_dir": "/data/logs"
                }
            })
    
    # 4. ERROR 级别日志
    if "error" in query_lower or "fatal" in query_lower or "500" in query_lower:
        # 数据库连接错误
        logs.append({
            "timestamp": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "ERROR",
            "service": "order-service",
            "instance": "pod-order-service-5c7d8e9f1-m3n2p",
            "message": "数据库连接池耗尽: Cannot acquire connection from pool, active: 50/50, waiting: 23, timeout: 30000ms",
            "metrics": {
                "error_type": "ConnectionPoolExhaustedException",
                "pool_active": "50",
                "pool_max": "50",
                "waiting_threads": "23"
            }
        })
        
        # OOM 错误
        logs.append({
            "timestamp": (now - timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "FATAL",
            "service": "order-service",
            "instance": "pod-order-service-5c7d8e9f1-m3n2p",
            "message": "java.lang.OutOfMemoryError: Java heap space at com.example.order.service.OrderService.processLargeOrder(OrderService.java:156)",
            "metrics": {
                "error_type": "OutOfMemoryError",
                "heap_used": "3.9GB",
                "heap_max": "4GB",
                "stack_trace": "OrderService.processLargeOrder -> OrderRepository.findByCondition -> HikariPool.getConnection"
            }
        })
        
        # HTTP 500 错误
        for i in range(3):
            logs.append({
                "timestamp": (now - timedelta(minutes=3 + i)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "ERROR",
                "service": "user-service",
                "instance": "pod-user-service-8e9f0a1b2-k5j6h",
                "message": f"HTTP 500 Internal Server Error: /api/v1/users/profile, 耗时: {5200 + i * 300}ms, 错误: Database query timeout",
                "metrics": {
                    "http_status": "500",
                    "uri": "/api/v1/users/profile",
                    "method": "GET",
                    "duration_ms": str(5200 + i * 300),
                    "error_cause": "QueryTimeoutException"
                }
            })
    
    # 5. 慢响应相关日志
    if "response_time" in query_lower or "slow" in query_lower or ">3000" in query_lower:
        for i in range(5):
            uri = "/api/v1/users/profile" if i % 2 == 0 else "/api/v1/users/orders"
            logs.append({
                "timestamp": (now - timedelta(minutes=i * 2)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "WARN",
                "service": "user-service",
                "instance": "pod-user-service-8e9f0a1b2-k5j6h",
                "message": f"慢请求警告: {uri}, 响应时间: {4200 - i * 150}ms, 阈值: 3000ms",
                "metrics": {
                    "uri": uri,
                    "response_time_ms": str(4200 - i * 150),
                    "threshold_ms": "3000",
                    "db_time_ms": str(3800 - i * 100),
                    "cache_hit": "false"
                }
            })
    
    # 6. 下游服务依赖相关日志
    if "downstream" in query_lower or "redis" in query_lower or "database" in query_lower or "mq" in query_lower:
        # Redis 错误
        logs.append({
            "timestamp": (now - timedelta(minutes=7)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "ERROR",
            "service": "payment-service",
            "instance": "pod-payment-service-7d8f9c6b5-x2k4m",
            "message": "Redis 连接超时: 无法连接到 Redis 集群, 节点: redis-cluster-01:6379, 超时: 3000ms",
            "metrics": {
                "dependency": "redis",
                "host": "redis-cluster-01:6379",
                "timeout_ms": "3000",
                "retry_count": "3"
            }
        })
        
        # MQ 错误
        logs.append({
            "timestamp": (now - timedelta(minutes=9)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARN",
            "service": "order-service",
            "instance": "pod-order-service-5c7d8e9f1-m3n2p",
            "message": "消息队列积压警告: 队列 order-process-queue 积压消息数: 15823, 消费速率下降",
            "metrics": {
                "dependency": "rabbitmq",
                "queue": "order-process-queue",
                "pending_messages": "15823",
                "consumer_count": "3"
            }
        })
    
    # 7. 数据库慢查询日志
    if "database" in query_lower or "slow query" in query_lower or "mysql" in query_lower or "sql" in query_lower:
        logs.append({
            "timestamp": (now - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARN",
            "service": "mysql",
            "instance": "mysql-primary-01",
            "message": "慢查询: SELECT * FROM orders WHERE user_id = ? AND status IN (?, ?, ?) ORDER BY created_at DESC LIMIT 100, 执行时间: 3.2s, 扫描行数: 1,245,678",
            "metrics": {
                "query_time_sec": "3.2",
                "rows_examined": "1245678",
                "rows_returned": "100",
                "index_used": "idx_user_id",
                "table": "orders",
                "query_type": "SELECT"
            }
        })
        
        logs.append({
            "timestamp": (now - timedelta(minutes=6)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARN",
            "service": "mysql",
            "instance": "mysql-primary-01",
            "message": "慢查询: SELECT u.*, p.* FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id WHERE u.last_login > ?, 执行时间: 2.8s, 全表扫描",
            "metrics": {
                "query_time_sec": "2.8",
                "rows_examined": "856234",
                "rows_returned": "45678",
                "index_used": "NONE",
                "table": "users, user_profiles",
                "query_type": "SELECT",
                "warning": "Full table scan detected"
            }
        })
        
        logs.append({
            "timestamp": (now - timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARN",
            "service": "mysql",
            "instance": "mysql-primary-01",
            "message": "慢查询: UPDATE orders SET status = ? WHERE created_at < ? AND status = ?, 执行时间: 4.5s, 锁等待时间: 2.1s",
            "metrics": {
                "query_time_sec": "4.5",
                "lock_time_sec": "2.1",
                "rows_affected": "23456",
                "table": "orders",
                "query_type": "UPDATE",
                "warning": "High lock contention"
            }
        })
    
    # 8. 系统事件日志（重启、崩溃）
    if "restart" in query_lower or "crash" in query_lower or "oom_kill" in query_lower or "kubernetes" in query_lower:
        logs.append({
            "timestamp": (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARN",
            "service": "kubernetes",
            "instance": "kube-controller-manager",
            "message": "Pod 重启事件: pod-order-service-5c7d8e9f1-m3n2p, 原因: OOMKilled, 容器退出码: 137, 重启次数: 3",
            "metrics": {
                "event_type": "PodRestart",
                "pod": "pod-order-service-5c7d8e9f1-m3n2p",
                "reason": "OOMKilled",
                "exit_code": "137",
                "restart_count": "3",
                "namespace": "production"
            }
        })
        
        logs.append({
            "timestamp": (now - timedelta(minutes=16)).strftime("%Y-%m-%d %H:%M:%S"),
            "level": "ERROR",
            "service": "kernel",
            "instance": "node-worker-02",
            "message": "OOM Killer 触发: 进程 java (PID: 12345) 被杀死, 内存使用: 3.9GB, 内存限制: 4GB",
            "metrics": {
                "event_type": "OOMKill",
                "process": "java",
                "pid": "12345",
                "memory_used": "3.9GB",
                "memory_limit": "4GB",
                "cgroup": "/kubepods/pod-order-service"
            }
        })
    
    # 如果没有匹配到任何关键词，返回通用日志
    if not logs:
        for i in range(5):
            logs.append({
                "timestamp": (now - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "INFO" if i % 2 == 0 else "WARN",
                "service": "generic-service",
                "instance": f"instance-{i}",
                "message": f"通用日志消息 #{i}, 查询条件: {query}",
                "metrics": {}
            })
    
    result = {
        "success": True,
        "logs": logs,
        "query": query,
        "time_range": time_range,
        "count": len(logs)
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)
