"""
测试 AIOps 工具（Prometheus 和 Log 查询工具）
"""
from app.agents.tools.prometheus_tool import query_prometheus_alerts
from app.agents.tools.log_tool import query_log
import json


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_prometheus_tool():
    """测试 Prometheus 告警查询工具"""
    print_section("测试 1: Prometheus 告警查询")
    
    try:
        # 调用工具
        result = query_prometheus_alerts.invoke({})
        
        # 解析 JSON
        data = json.loads(result)
        
        print(f"✅ 查询成功: {data['message']}")
        print(f"📊 告警数量: {len(data['alerts'])}")
        print("\n告警详情:")
        
        for i, alert in enumerate(data['alerts'], 1):
            print(f"\n  {i}. {alert['alert_name']} ({alert['state']})")
            print(f"     持续时间: {alert['duration']}")
            print(f"     描述: {alert['description'][:80]}...")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_log_tool_cpu():
    """测试日志查询工具 - CPU 相关"""
    print_section("测试 2: 日志查询 - CPU 相关")
    
    try:
        result = query_log.invoke({"query": "cpu", "time_range": "5m"})
        data = json.loads(result)
        
        print(f"✅ 查询成功")
        print(f"📝 查询条件: {data['query']}")
        print(f"⏰ 时间范围: {data['time_range']}")
        print(f"📊 日志数量: {data['count']}")
        
        if data['logs']:
            print("\n前3条日志:")
            for i, log in enumerate(data['logs'][:3], 1):
                print(f"\n  {i}. [{log['level']}] {log['service']} - {log['instance']}")
                print(f"     时间: {log['timestamp']}")
                print(f"     消息: {log['message'][:80]}...")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_log_tool_error():
    """测试日志查询工具 - 错误日志"""
    print_section("测试 3: 日志查询 - 错误日志")
    
    try:
        result = query_log.invoke({"query": "error"})
        data = json.loads(result)
        
        print(f"✅ 查询成功")
        print(f"📊 日志数量: {data['count']}")
        
        if data['logs']:
            print("\n错误类型统计:")
            error_types = {}
            for log in data['logs']:
                level = log['level']
                error_types[level] = error_types.get(level, 0) + 1
            
            for level, count in error_types.items():
                print(f"  - {level}: {count} 条")
            
            print("\n示例错误日志:")
            for log in data['logs'][:2]:
                if log['level'] in ['ERROR', 'FATAL']:
                    print(f"\n  [{log['level']}] {log['service']}")
                    print(f"  消息: {log['message'][:100]}...")
                    if 'error_type' in log['metrics']:
                        print(f"  错误类型: {log['metrics']['error_type']}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_log_tool_slow_query():
    """测试日志查询工具 - 数据库慢查询"""
    print_section("测试 4: 日志查询 - 数据库慢查询")
    
    try:
        result = query_log.invoke({"query": "slow query"})
        data = json.loads(result)
        
        print(f"✅ 查询成功")
        print(f"📊 慢查询数量: {data['count']}")
        
        if data['logs']:
            print("\n慢查询详情:")
            for i, log in enumerate(data['logs'][:3], 1):
                print(f"\n  {i}. {log['service']} - {log['instance']}")
                print(f"     时间: {log['timestamp']}")
                if 'query_time_sec' in log['metrics']:
                    print(f"     执行时间: {log['metrics']['query_time_sec']}s")
                if 'table' in log['metrics']:
                    print(f"     表: {log['metrics']['table']}")
                print(f"     SQL: {log['message'][:80]}...")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_log_tool_system_events():
    """测试日志查询工具 - 系统事件"""
    print_section("测试 5: 日志查询 - 系统事件（重启/崩溃）")
    
    try:
        result = query_log.invoke({"query": "restart"})
        data = json.loads(result)
        
        print(f"✅ 查询成功")
        print(f"📊 事件数量: {data['count']}")
        
        if data['logs']:
            print("\n系统事件:")
            for log in data['logs']:
                print(f"\n  [{log['level']}] {log['service']}")
                print(f"  时间: {log['timestamp']}")
                print(f"  消息: {log['message']}")
                if 'event_type' in log['metrics']:
                    print(f"  事件类型: {log['metrics']['event_type']}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 40)
    print("  AIOps 工具测试套件")
    print("🚀" * 40)
    
    results = []
    
    # 运行所有测试
    results.append(("Prometheus 告警查询", test_prometheus_tool()))
    results.append(("日志查询 - CPU", test_log_tool_cpu()))
    results.append(("日志查询 - 错误", test_log_tool_error()))
    results.append(("日志查询 - 慢查询", test_log_tool_slow_query()))
    results.append(("日志查询 - 系统事件", test_log_tool_system_events()))
    
    # 打印测试总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！工具运行正常！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息")


if __name__ == "__main__":
    main()
