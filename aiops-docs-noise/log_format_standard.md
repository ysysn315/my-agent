# 日志格式规范

统一日志字段：
- trace_id
- span_id
- service
- level
- timestamp
- message

示例：
{"level":"INFO","service":"api-gateway","trace_id":"xxx","message":"request ok"}

本文是格式规范，不提供 CPU、内存或慢响应的排障结论。

## 字段定义与约束

- `trace_id`: 全链路请求唯一标识，跨服务透传
- `span_id`: 当前处理节点标识，用于链路拓扑还原
- `service`: 服务名，建议使用部署单元名
- `level`: 日志级别，统一 INFO/WARN/ERROR
- `timestamp`: ISO8601 格式，统一 UTC+0 存储
- `message`: 主文本，禁止拼接敏感信息

## 推荐扩展字段

- `env`: 环境标识（prod/stage/dev）
- `region`: 机房或地域标识
- `http_path`: 请求路径
- `latency_ms`: 处理耗时
- `error_code`: 业务错误码
- `user_id_hash`: 脱敏后的用户标识

## 采样策略

1. INFO 默认采样 10%
2. WARN/ERROR 全量采集
3. 高并发路径支持动态采样

## 检索示例

- 按 trace_id 检索单次请求全链路日志
- 按 service + error_code 聚合故障分布
- 按 latency_ms 过滤慢请求区间

注：该文档用于日志格式统一，不是故障分析手册；出现 latency、error 等字段仅为规范示例。
