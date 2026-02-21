# Kubernetes Ingress TLS 配置指南

本文介绍如何在集群中配置 HTTPS 证书与 Ingress 路由。

常用命令：
- kubectl create secret tls ...
- kubectl apply -f ingress.yaml

排障重点：
- 检查证书 CN 是否匹配域名
- 检查 Ingress Controller 是否加载规则
- 检查 Service 端口映射是否一致

## 场景说明

在多环境集群中，常见的入口流量路径为：CDN -> WAF -> Ingress -> Service -> Pod。
TLS 证书一般终止在 Ingress 层，也可由云负载均衡完成终止后转发到集群。

## 标准配置流程

1. 生成或导入证书文件（fullchain + private key）
2. 创建命名空间下的 TLS Secret
3. 在 Ingress 中绑定 `tls.hosts` 与 `secretName`
4. 配置后端 Service 端口与 path 路由
5. 通过 `kubectl describe ingress` 与浏览器握手结果双向验证

## 排障步骤细化

### 证书问题
- 检查证书有效期与签发链是否完整
- 检查 SAN 列表是否包含目标域名
- 检查中间证书是否缺失导致握手失败

### 控制器问题
- 检查 IngressClass 是否匹配控制器
- 检查控制器日志中是否有配置加载错误
- 检查 ConfigMap 是否限制了大请求头或超时

### 路由问题
- 检查 pathType 是否为预期值
- 检查 rewrite 规则是否导致 404
- 检查上游 Service selector 是否正确命中 Pod

## 验证命令

- `kubectl get ingress -A`
- `kubectl describe ingress <name>`
- `kubectl logs <ingress-controller-pod>`
- `curl -vk https://your.domain/path`

注：本文是入口网关与证书配置文档，不用于应用层性能故障根因分析。
