from copy import deepcopy

from evals.rag.common import save_json


DATASET_PATH = "evals/rag/datasets/rag_generation_cases_formal_template.json"


def fact(name: str, all_of=None, any_of=None, none_of=None):
    """事实点/禁忌说法统一用同一种规则描述，便于复用。"""
    return {
        "name": name,
        "all_of": list(all_of or []),
        "any_of": list(any_of or []),
        "none_of": list(none_of or []),
    }


PROFILES = {
    "cpu_high_usage.md": {
        "keywords": ["CPU", "80%", "5分钟", "system-metrics", "query_logs", "当前时间"],
        "forbidden_sources": [
            "monitoring_glossary_noise.md",
            "mock_incident_drill_script.md",
            "perf_capacity_planning_false_friend.md",
        ],
        "facts": {
            "alarm_name": fact("CPU 告警名", any_of=["HighCPUUsage", "CPU告警", "CPU 告警"]),
            "threshold": fact("CPU 阈值", all_of=["CPU", "80", "5分钟"]),
            "first_step": fact("先确认时间范围", any_of=["get_current_time", "获取当前时间", "当前时间"]),
            "log_topic": fact("系统指标日志主题", any_of=["system-metrics", "system metrics"]),
            "time_window": fact("默认回看窗口", all_of=["30分钟"]),
            "log_filter": fact(
                "CPU 查询条件",
                any_of=["cpu_usage > 80", "cpu_usage:>80", "cpuusage>80"],
            ),
            "impact": fact("CPU 影响", any_of=["响应变慢", "请求超时", "雪崩"]),
            "pid": fact("关注进程或 PID", any_of=["PID", "进程"]),
        },
        "forbidden_claims": {
            "wrong_threshold": fact("误把 CPU 阈值说成 85%", all_of=["CPU", "85"]),
            "glossary_only": fact("误把术语手册当排障方案", any_of=["术语手册", "术语词典"]),
        },
    },
    "memory_high_usage.md": {
        "keywords": ["内存", "85%", "OOM", "GC", "system-metrics", "application-logs"],
        "forbidden_sources": [
            "monitoring_glossary_noise.md",
            "mock_incident_drill_script.md",
            "perf_capacity_planning_false_friend.md",
        ],
        "facts": {
            "threshold": fact("内存阈值", all_of=["内存", "85", "5分钟"]),
            "first_step": fact("先确认时间范围", any_of=["get_current_time", "获取当前时间", "当前时间"]),
            "system_log": fact("系统指标日志主题", any_of=["system-metrics", "system metrics"]),
            "app_log": fact("应用日志主题", any_of=["application-logs", "application logs"]),
            "time_window": fact("默认回看窗口", all_of=["30分钟"]),
            "log_filter": fact(
                "内存查询条件",
                any_of=["memory_usage>85", "memory_usage:>85", "event:oom", "oom_kill:true"],
            ),
            "impact": fact("内存高的典型表现", any_of=["OOM", "GC", "swap"]),
            "restart": fact("可能导致重启或崩溃", any_of=["重启", "崩溃"]),
        },
        "forbidden_claims": {
            "wrong_threshold": fact("误把内存阈值说成 80%", all_of=["内存", "80"]),
            "slow_response_confusion": fact("误把 3 秒 P99 当内存阈值", all_of=["P99", "3秒"]),
        },
    },
    "slow_response.md": {
        "keywords": ["P99", "3秒", "慢响应", "application-logs", "slow_query", "数据库"],
        "forbidden_sources": [
            "monitoring_glossary_noise.md",
            "mock_incident_drill_script.md",
            "perf_capacity_planning_false_friend.md",
        ],
        "facts": {
            "threshold": fact("慢响应阈值", all_of=["P99", "3秒", "5分钟"]),
            "first_step": fact("先确认时间范围", any_of=["get_current_time", "获取当前时间", "当前时间"]),
            "app_log": fact("应用日志主题", any_of=["application-logs", "application logs"]),
            "time_window": fact("默认回看窗口", all_of=["30分钟"]),
            "log_filter": fact(
                "慢响应查询条件",
                any_of=["response_time>3000", "response_time:>3000", "slow_query:true"],
            ),
            "db_log": fact("要查数据库慢查询", any_of=["慢查询", "slow query", "数据库"]),
            "impact": fact("慢响应影响", any_of=["用户体验下降", "请求堆积", "超时"]),
        },
        "forbidden_claims": {
            "memory_threshold_confusion": fact("误把 85% 内存阈值说到慢响应", all_of=["85", "慢响应"]),
            "service_level_confusion": fact("误把慢响应说成紧急不可用", any_of=["紧急", "不可用"]),
        },
    },
    "disk_high_usage.md": {
        "keywords": ["磁盘", "80%", "90%", "disk_full", "system-metrics", "写入"],
        "forbidden_sources": [
            "monitoring_glossary_noise.md",
            "mock_incident_drill_script.md",
            "perf_capacity_planning_false_friend.md",
        ],
        "facts": {
            "threshold": fact("磁盘阈值", any_of=["80%", "90%", ">80", ">90"]),
            "first_step": fact("先确认时间范围", any_of=["get_current_time", "获取当前时间", "当前时间"]),
            "system_log": fact("系统指标日志主题", any_of=["system-metrics", "system metrics"]),
            "time_window": fact("默认回看窗口", all_of=["30分钟"]),
            "log_filter": fact(
                "磁盘查询条件",
                any_of=["disk_usage>80", "disk_usage:>80", "disk_full:true", "filesystem:full"],
            ),
            "impact": fact("磁盘高的影响", any_of=["无法写入", "日志无法记录", "数据库损坏"]),
            "levels": fact("区分 warning 和 critical", any_of=["警告", "严重", "warning", "critical"]),
        },
        "forbidden_claims": {
            "slow_threshold_confusion": fact("误把 P99 3 秒当磁盘阈值", all_of=["P99", "3秒"]),
            "memory_confusion": fact("误把 OOM 当磁盘直接阈值", all_of=["OOM", "磁盘"]),
        },
    },
    "service_unavailable.md": {
        "keywords": ["服务不可用", "健康检查", "错误率50%", "application-logs", "500", "ERROR"],
        "forbidden_sources": [
            "monitoring_glossary_noise.md",
            "mock_incident_drill_script.md",
            "perf_capacity_planning_false_friend.md",
        ],
        "facts": {
            "trigger": fact("不可用触发条件", any_of=["健康检查失败", "错误率超过50%", "error rate"]),
            "severity": fact("故障级别", any_of=["紧急", "P1"]),
            "first_step": fact("先确认故障时间", any_of=["get_current_time", "获取当前时间", "当前时间"]),
            "app_log": fact("应用日志主题", any_of=["application-logs", "application logs"]),
            "time_window": fact("默认回看窗口", all_of=["15分钟"]),
            "log_filter": fact(
                "服务不可用查询条件",
                any_of=["level:error", "level:fatal", "status:500", "500"],
            ),
            "impact": fact("不可用影响", any_of=["无法访问", "业务中断", "经济损失"]),
            "system_event": fact("还要看系统事件", any_of=["系统事件", "system event"]),
        },
        "forbidden_claims": {
            "slow_response_confusion": fact("误把 3 秒 P99 当不可用定义", all_of=["P99", "3秒"]),
            "warning_confusion": fact("误说只是警告级别", any_of=["只是警告", "warning 级别"]),
        },
    },
    "security_waf_playbook.md": {
        "keywords": ["WAF", "SQL注入", "XSS", "CC", "限流", "白名单"],
        "forbidden_sources": [
            "cpu_high_usage.md",
            "memory_high_usage.md",
            "slow_response.md",
            "disk_high_usage.md",
            "service_unavailable.md",
        ],
        "facts": {
            "attack_types": fact("WAF 防护对象", any_of=["SQL 注入", "XSS", "CC"]),
            "rate_limit": fact("速率限制", any_of=["按 IP", "限流", "请求频次"]),
            "scope": fact("不是 JVM/数据库故障手册", any_of=["与 JVM OOM 无直接关系", "与慢查询无直接关系"]),
            "workflow": fact("处置流程", any_of=["确认影响范围", "应用防护模板", "跟踪误拦截"]),
        },
        "forbidden_claims": {
            "oom_confusion": fact("误把 WAF 说成处理 OOM/GC", any_of=["OOM", "Full GC"]),
        },
    },
    "mysql_backup_restore.md": {
        "keywords": ["MySQL", "xtrabackup", "binlog", "GTID", "恢复", "校验"],
        "forbidden_sources": [
            "cpu_high_usage.md",
            "memory_high_usage.md",
            "slow_response.md",
            "service_unavailable.md",
        ],
        "facts": {
            "backup_mode": fact("备份方式", any_of=["xtrabackup", "全量备份", "binlog"]),
            "restore_steps": fact("恢复步骤", any_of=["恢复到新实例", "回放 binlog", "校验"]),
            "gtid": fact("GTID 校验", any_of=["GTID"]),
            "drill": fact("恢复演练要比对", any_of=["行数", "哈希", "校验"]),
        },
        "forbidden_claims": {
            "waf_confusion": fact("误把备份恢复说成 WAF 策略", any_of=["WAF", "XSS", "CC"]),
        },
    },
    "k8s_ingress_tls_guide.md": {
        "keywords": ["Ingress", "TLS", "证书", "secret", "CN", "SAN"],
        "forbidden_sources": [
            "cpu_high_usage.md",
            "memory_high_usage.md",
            "slow_response.md",
            "service_unavailable.md",
        ],
        "facts": {
            "tls_secret": fact("需要 TLS Secret", any_of=["TLS Secret", "secretName", "tls.hosts"]),
            "cert_check": fact("证书校验点", any_of=["CN", "SAN", "证书有效期"]),
            "controller": fact("控制器检查", any_of=["Ingress Controller", "IngressClass"]),
            "path": fact("链路路径", any_of=["CDN", "WAF", "Ingress", "Service", "Pod"]),
        },
        "forbidden_claims": {
            "oom_confusion": fact("误把 TLS 问题说成 OOM/GC", any_of=["OOM", "Full GC", "慢查询"]),
        },
    },
}


def unique_keep_order(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def fact_ref(source: str, fact_id: str):
    return deepcopy(PROFILES[source]["facts"][fact_id])


def claim_ref(source: str, claim_id: str):
    return deepcopy(PROFILES[source]["forbidden_claims"][claim_id])


def auto_keywords(sources_all=None, sources_any=None, extra_keywords=None):
    keywords = []
    for source in list(sources_all or []) + list(sources_any or []):
        keywords.extend(PROFILES.get(source, {}).get("keywords", []))
    keywords.extend(extra_keywords or [])
    return unique_keep_order(keywords)[:6]


def auto_forbidden_sources(sources_all=None, sources_any=None, extra_forbidden=None):
    forbidden = []
    for source in list(sources_all or []) + list(sources_any or []):
        forbidden.extend(PROFILES.get(source, {}).get("forbidden_sources", []))
    forbidden.extend(extra_forbidden or [])
    return unique_keep_order(forbidden)


CASES = []


def add_case(
    question: str,
    question_type: str,
    difficulty: str,
    sources_all=None,
    sources_any=None,
    fact_rules=None,
    forbidden_rules=None,
    expected_keywords=None,
    forbidden_sources=None,
    notes: str = "",
):
    case_id = f"formal_gen_{len(CASES) + 1:03d}"
    sources_all = list(sources_all or [])
    sources_any = list(sources_any or [])
    fact_rules = list(fact_rules or [])
    forbidden_rules = list(forbidden_rules or [])

    CASES.append(
        {
            "id": case_id,
            "question": question,
            "question_type": question_type,
            "difficulty": difficulty,
            "expected_keywords": expected_keywords
            or auto_keywords(sources_all=sources_all, sources_any=sources_any),
            "expected_sources": sources_all,
            "expected_sources_all": sources_all,
            "expected_sources_any": sources_any,
            "expected_facts": fact_rules,
            "forbidden_claims": forbidden_rules,
            "forbidden_sources": forbidden_sources
            if forbidden_sources is not None
            else auto_forbidden_sources(sources_all=sources_all, sources_any=sources_any),
            "notes": notes,
        }
    )


# CPU（8）
add_case(
    "CPU 告警持续 5 分钟超过 80% 时，标准排查的第一步应该做什么？",
    "single_hop",
    "easy",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "threshold"),
        fact_ref("cpu_high_usage.md", "first_step"),
        fact_ref("cpu_high_usage.md", "log_topic"),
    ],
    forbidden_rules=[claim_ref("cpu_high_usage.md", "wrong_threshold")],
)
add_case(
    "请给出 CPU 高告警时的日志查询要点，至少说出日志主题、时间窗口和过滤条件。",
    "single_hop",
    "medium",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "log_topic"),
        fact_ref("cpu_high_usage.md", "time_window"),
        fact_ref("cpu_high_usage.md", "log_filter"),
    ],
)
add_case(
    "CPU 高的时候，为什么要重点看进程名和 PID？",
    "single_hop",
    "easy",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "pid"),
        fact_ref("cpu_high_usage.md", "impact"),
    ],
)
add_case(
    "如果我只记得 HighCPUUsage 这个告警名，你会怎么往下展开排查？",
    "single_hop",
    "medium",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "alarm_name"),
        fact_ref("cpu_high_usage.md", "first_step"),
        fact_ref("cpu_high_usage.md", "log_filter"),
    ],
)
add_case(
    "CPU 告警排查时，日志为什么默认回看最近 30 分钟？",
    "single_hop",
    "medium",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "time_window"),
        fact_ref("cpu_high_usage.md", "first_step"),
    ],
)
add_case(
    "请把 CPU 告警的风险影响总结成三点，不要只给操作步骤。",
    "single_hop",
    "easy",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "threshold"),
        fact_ref("cpu_high_usage.md", "impact"),
    ],
)
add_case(
    "容量规划文档里也提到 CPU 百分比，如果线上收到 CPU 高告警，应该优先参考哪类文档？为什么？",
    "confusable",
    "hard",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "threshold"),
        fact("容量规划不是线上根因文档", any_of=["不是线上故障根因", "容量规划", "告警处置方案"]),
    ],
    forbidden_sources=["perf_capacity_planning_false_friend.md"],
)
add_case(
    "CPU 高但还没有超时错误时，你会先解释现象、还是先给日志排查动作？请按文档回答。",
    "single_hop",
    "hard",
    sources_all=["cpu_high_usage.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "impact"),
        fact_ref("cpu_high_usage.md", "first_step"),
        fact_ref("cpu_high_usage.md", "log_topic"),
    ],
)


# 内存（8）
add_case(
    "内存使用率连续 5 分钟超过 85% 时，标准处置从哪一步开始？",
    "single_hop",
    "easy",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "threshold"),
        fact_ref("memory_high_usage.md", "first_step"),
        fact_ref("memory_high_usage.md", "system_log"),
    ],
    forbidden_rules=[claim_ref("memory_high_usage.md", "wrong_threshold")],
)
add_case(
    "请概括内存高告警最典型的三个症状。",
    "single_hop",
    "easy",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "impact"),
        fact_ref("memory_high_usage.md", "restart"),
    ],
)
add_case(
    "处理 OOM 风险时，系统指标日志和应用日志分别为什么要查？",
    "single_hop",
    "medium",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "system_log"),
        fact_ref("memory_high_usage.md", "app_log"),
        fact_ref("memory_high_usage.md", "impact"),
    ],
)
add_case(
    "如果我想直接搜日志，内存高告警建议的过滤条件是什么？",
    "single_hop",
    "medium",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "log_filter"),
        fact_ref("memory_high_usage.md", "time_window"),
    ],
)
add_case(
    "为什么内存高会伴随 Full GC、OOM 或 swap？请按知识库解释。",
    "single_hop",
    "medium",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "impact"),
        fact_ref("memory_high_usage.md", "restart"),
    ],
)
add_case(
    "内存高告警和慢响应告警都可能影响体验，如何先区分你现在面对的是哪一种？",
    "multi_hop",
    "hard",
    sources_all=["memory_high_usage.md", "slow_response.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "threshold"),
        fact_ref("slow_response.md", "threshold"),
        fact("两类告警的日志主题不同", any_of=["system-metrics", "application-logs"]),
    ],
)
add_case(
    "监控术语词典里解释了 OOM，这能直接替代内存高告警处置文档吗？",
    "confusable",
    "hard",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "app_log"),
        fact("术语词典不是处置方案", any_of=["不是处置步骤", "术语词典", "手册"]),
    ],
    forbidden_sources=["monitoring_glossary_noise.md"],
)
add_case(
    "请用一段话说明：内存高告警至少需要确认哪些日志主题、时间窗口和异常现象。",
    "single_hop",
    "hard",
    sources_all=["memory_high_usage.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "system_log"),
        fact_ref("memory_high_usage.md", "app_log"),
        fact_ref("memory_high_usage.md", "time_window"),
        fact_ref("memory_high_usage.md", "impact"),
    ],
)


# 慢响应（8）
add_case(
    "P99 连续 5 分钟超过 3 秒时，标准慢响应排查从哪里开始？",
    "single_hop",
    "easy",
    sources_all=["slow_response.md"],
    fact_rules=[
        fact_ref("slow_response.md", "threshold"),
        fact_ref("slow_response.md", "first_step"),
        fact_ref("slow_response.md", "app_log"),
    ],
)
add_case(
    "慢响应告警要查哪些日志条件？请至少回答时间窗口和过滤表达式。",
    "single_hop",
    "medium",
    sources_all=["slow_response.md"],
    fact_rules=[
        fact_ref("slow_response.md", "time_window"),
        fact_ref("slow_response.md", "log_filter"),
    ],
)
add_case(
    "为什么慢响应场景下还要查数据库慢查询日志？",
    "single_hop",
    "easy",
    sources_all=["slow_response.md"],
    fact_rules=[
        fact_ref("slow_response.md", "db_log"),
        fact_ref("slow_response.md", "impact"),
    ],
)
add_case(
    "如果接口变慢但还没有 500 错误，按知识库应该优先看什么？",
    "single_hop",
    "medium",
    sources_all=["slow_response.md"],
    fact_rules=[
        fact_ref("slow_response.md", "app_log"),
        fact_ref("slow_response.md", "threshold"),
        fact_ref("slow_response.md", "db_log"),
    ],
)
add_case(
    "请对比说明：慢响应和服务不可用的触发条件分别是什么？",
    "multi_hop",
    "medium",
    sources_all=["slow_response.md", "service_unavailable.md"],
    fact_rules=[
        fact_ref("slow_response.md", "threshold"),
        fact_ref("service_unavailable.md", "trigger"),
    ],
)
add_case(
    "缓存调优手册也写了慢响应，你会怎么避免把缓存建议误当成故障根因结论？",
    "confusable",
    "hard",
    sources_all=["slow_response.md"],
    sources_any=["cache_tuning_playbook.md"],
    fact_rules=[
        fact_ref("slow_response.md", "db_log"),
        fact("缓存手册只是调优建议", any_of=["缓存调优", "不是根因文档", "缓存层"]),
    ],
)
add_case(
    "慢响应文档里为什么强调先取当前时间再查应用日志？",
    "single_hop",
    "easy",
    sources_all=["slow_response.md"],
    fact_rules=[
        fact_ref("slow_response.md", "first_step"),
        fact_ref("slow_response.md", "app_log"),
    ],
)
add_case(
    "请把慢响应场景里的用户影响和下游影响一起概括出来。",
    "single_hop",
    "easy",
    sources_all=["slow_response.md"],
    fact_rules=[fact_ref("slow_response.md", "impact")],
)


# 磁盘（8）
add_case(
    "磁盘使用率告警触发后，第一步应该做什么？",
    "single_hop",
    "easy",
    sources_all=["disk_high_usage.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "first_step"),
        fact_ref("disk_high_usage.md", "system_log"),
    ],
)
add_case(
    "磁盘告警里 warning 和严重阈值是怎么划分的？",
    "single_hop",
    "easy",
    sources_all=["disk_high_usage.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "threshold"),
        fact_ref("disk_high_usage.md", "levels"),
    ],
)
add_case(
    "磁盘高时建议怎么查系统日志？请说出日志主题、时间窗口和查询条件。",
    "single_hop",
    "medium",
    sources_all=["disk_high_usage.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "system_log"),
        fact_ref("disk_high_usage.md", "time_window"),
        fact_ref("disk_high_usage.md", "log_filter"),
    ],
)
add_case(
    "为什么磁盘打满会影响日志记录和数据库稳定性？",
    "single_hop",
    "easy",
    sources_all=["disk_high_usage.md"],
    fact_rules=[fact_ref("disk_high_usage.md", "impact")],
)
add_case(
    "如果磁盘高和 500 错误同时出现，按知识库你会联想到哪两类文档？",
    "multi_hop",
    "medium",
    sources_all=["disk_high_usage.md", "service_unavailable.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "impact"),
        fact_ref("service_unavailable.md", "log_filter"),
    ],
)
add_case(
    "性能容量规划文档里也提到磁盘增长率，这能直接替代磁盘告警处置方案吗？",
    "confusable",
    "hard",
    sources_all=["disk_high_usage.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "log_filter"),
        fact("容量规划不是告警处置方案", any_of=["容量规划", "不是处置方案", "不是线上根因"]),
    ],
    forbidden_sources=["perf_capacity_planning_false_friend.md"],
)
add_case(
    "磁盘告警时，为什么还是要先记录故障时间而不是直接删日志？",
    "single_hop",
    "medium",
    sources_all=["disk_high_usage.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "first_step"),
        fact_ref("disk_high_usage.md", "time_window"),
    ],
)
add_case(
    "请把磁盘高告警的典型影响总结成一句排障提醒。",
    "single_hop",
    "easy",
    sources_all=["disk_high_usage.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "threshold"),
        fact_ref("disk_high_usage.md", "impact"),
    ],
)


# 服务不可用（8）
add_case(
    "服务不可用告警最常见的触发条件是什么？",
    "single_hop",
    "easy",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "trigger"),
        fact_ref("service_unavailable.md", "severity"),
    ],
)
add_case(
    "服务不可用的标准排查为什么先要拿到故障时间？",
    "single_hop",
    "easy",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "first_step"),
        fact_ref("service_unavailable.md", "time_window"),
    ],
)
add_case(
    "服务不可用场景建议怎么查应用日志？请给出时间范围和过滤条件。",
    "single_hop",
    "medium",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "app_log"),
        fact_ref("service_unavailable.md", "time_window"),
        fact_ref("service_unavailable.md", "log_filter"),
    ],
)
add_case(
    "为什么服务不可用会被定义成紧急级别？",
    "single_hop",
    "easy",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "severity"),
        fact_ref("service_unavailable.md", "impact"),
    ],
)
add_case(
    "如果同时看到健康检查失败和 status 500，你会先参考哪一份文档？",
    "single_hop",
    "medium",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "trigger"),
        fact_ref("service_unavailable.md", "log_filter"),
    ],
)
add_case(
    "服务不可用和慢响应都可能影响用户，如何先区分它们？",
    "multi_hop",
    "medium",
    sources_all=["service_unavailable.md", "slow_response.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "trigger"),
        fact_ref("slow_response.md", "threshold"),
    ],
)
add_case(
    "如果回答里只说这是 warning 级别，为什么不符合知识库？",
    "single_hop",
    "hard",
    sources_all=["service_unavailable.md"],
    fact_rules=[fact_ref("service_unavailable.md", "severity")],
    forbidden_rules=[claim_ref("service_unavailable.md", "warning_confusion")],
)
add_case(
    "请把服务不可用的排查输入至少概括成三项：时间、日志和业务影响。",
    "single_hop",
    "medium",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "first_step"),
        fact_ref("service_unavailable.md", "app_log"),
        fact_ref("service_unavailable.md", "impact"),
    ],
)


# 多跳/综合（6）
add_case(
    "CPU 高且响应慢时，联合诊断至少要覆盖哪两类告警和哪两类日志？",
    "multi_hop",
    "hard",
    sources_all=["cpu_high_usage.md", "slow_response.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "threshold"),
        fact_ref("slow_response.md", "threshold"),
        fact_ref("cpu_high_usage.md", "log_topic"),
        fact_ref("slow_response.md", "app_log"),
    ],
)
add_case(
    "数据库超时导致接口 500 时，知识库里建议优先联看哪些文档？",
    "multi_hop",
    "hard",
    sources_all=["slow_response.md", "service_unavailable.md"],
    fact_rules=[
        fact_ref("slow_response.md", "db_log"),
        fact_ref("service_unavailable.md", "log_filter"),
    ],
)
add_case(
    "磁盘打满引发服务不可用时，回答里至少应该覆盖哪些事实点？",
    "multi_hop",
    "hard",
    sources_all=["disk_high_usage.md", "service_unavailable.md"],
    fact_rules=[
        fact_ref("disk_high_usage.md", "impact"),
        fact_ref("service_unavailable.md", "trigger"),
        fact_ref("service_unavailable.md", "severity"),
    ],
)
add_case(
    "缓存穿透导致数据库压力上升并拖慢接口时，主诊断文档和辅助调优文档分别是哪类？",
    "multi_hop",
    "hard",
    sources_all=["slow_response.md"],
    sources_any=["cache_tuning_playbook.md"],
    fact_rules=[
        fact_ref("slow_response.md", "db_log"),
        fact("缓存文档是调优补充", any_of=["缓存调优", "回源", "命中率"]),
    ],
)
add_case(
    "如果入口层 HTTPS 握手异常，同时你怀疑有恶意攻击流量，知识库里应该联看哪两类文档？",
    "multi_hop",
    "hard",
    sources_all=["k8s_ingress_tls_guide.md", "security_waf_playbook.md"],
    fact_rules=[
        fact_ref("k8s_ingress_tls_guide.md", "tls_secret"),
        fact_ref("k8s_ingress_tls_guide.md", "cert_check"),
        fact_ref("security_waf_playbook.md", "rate_limit"),
    ],
)
add_case(
    "如果一边做数据库恢复演练，一边担心入口 HTTPS 故障，应该分别参考哪两份手册？",
    "multi_hop",
    "medium",
    sources_all=["mysql_backup_restore.md", "k8s_ingress_tls_guide.md"],
    fact_rules=[
        fact_ref("mysql_backup_restore.md", "gtid"),
        fact_ref("k8s_ingress_tls_guide.md", "controller"),
    ],
)


# 噪声/混淆（6）
add_case(
    "监控术语手册里解释了 P99，但如果线上慢响应告警触发，真正该参考哪份文档？",
    "confusable",
    "medium",
    sources_all=["slow_response.md"],
    fact_rules=[
        fact_ref("slow_response.md", "threshold"),
        fact("术语手册不是处置方案", any_of=["术语手册", "不是处置方案"]),
    ],
    forbidden_sources=["monitoring_glossary_noise.md"],
)
add_case(
    "演练脚本里出现了 OOM 文本，这能不能直接当成线上内存泄漏证据？",
    "confusable",
    "hard",
    sources_all=["memory_high_usage.md"],
    sources_any=["mock_incident_drill_script.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "impact"),
        fact("演练脚本不是线上根因证据", any_of=["模拟数据", "不应作为真实根因", "演练脚本"]),
    ],
    forbidden_sources=["mock_incident_drill_script.md"],
)
add_case(
    "容量预算里提到 OOM 和 Full GC，这能直接说明线上已经发生内存故障吗？",
    "confusable",
    "hard",
    sources_all=["memory_high_usage.md"],
    sources_any=["perf_capacity_planning_false_friend.md"],
    fact_rules=[
        fact_ref("memory_high_usage.md", "threshold"),
        fact("容量预算不是线上事故报告", any_of=["预算", "不是线上事故", "不是根因分析"]),
    ],
    forbidden_sources=["perf_capacity_planning_false_friend.md"],
)
add_case(
    "缓存调优手册里提到 500 错误，但如果问题是服务不可用，主参考文档应该是哪一份？",
    "confusable",
    "hard",
    sources_all=["service_unavailable.md"],
    sources_any=["cache_tuning_playbook.md"],
    fact_rules=[
        fact_ref("service_unavailable.md", "severity"),
        fact("缓存手册不是服务不可用恢复编排", any_of=["不是服务不可用恢复", "缓存调优"]),
    ],
)
add_case(
    "术语词典提到 CPU 高不一定等于故障，那收到 HighCPUUsage 告警后还要不要按告警文档走？",
    "confusable",
    "medium",
    sources_all=["cpu_high_usage.md"],
    sources_any=["monitoring_glossary_noise.md"],
    fact_rules=[
        fact_ref("cpu_high_usage.md", "alarm_name"),
        fact("术语解释不能替代告警处置", any_of=["不能替代", "告警处置", "术语解释"]),
    ],
)
add_case(
    "如果回答大量引用演练脚本和术语词典，而不引用真正排障文档，这种回答应该判好吗？",
    "confusable",
    "hard",
    sources_all=["service_unavailable.md"],
    fact_rules=[
        fact("真正排障要引用真实处置文档", any_of=["真实处置文档", "排障文档", "根因"]),
    ],
    forbidden_sources=["mock_incident_drill_script.md", "monitoring_glossary_noise.md"],
    expected_keywords=["排障文档", "演练脚本", "术语词典", "真实处置"],
)


# 跨域知识（4）
add_case(
    "WAF 手册里提到的三类主要防护对象是什么？",
    "single_hop",
    "easy",
    sources_all=["security_waf_playbook.md"],
    fact_rules=[fact_ref("security_waf_playbook.md", "attack_types")],
)
add_case(
    "MySQL 备份恢复流程里，为什么要校验 GTID 一致性？",
    "single_hop",
    "medium",
    sources_all=["mysql_backup_restore.md"],
    fact_rules=[
        fact_ref("mysql_backup_restore.md", "backup_mode"),
        fact_ref("mysql_backup_restore.md", "gtid"),
        fact_ref("mysql_backup_restore.md", "restore_steps"),
    ],
)
add_case(
    "Ingress TLS 排障时，证书和控制器两个方向各要查什么？",
    "single_hop",
    "medium",
    sources_all=["k8s_ingress_tls_guide.md"],
    fact_rules=[
        fact_ref("k8s_ingress_tls_guide.md", "cert_check"),
        fact_ref("k8s_ingress_tls_guide.md", "controller"),
    ],
)
add_case(
    "如果用户访问链路是 CDN 到 Pod，中间关键入口层有哪些？",
    "single_hop",
    "easy",
    sources_all=["k8s_ingress_tls_guide.md"],
    fact_rules=[fact_ref("k8s_ingress_tls_guide.md", "path")],
)


# 无答案/拒答（4）
add_case(
    "Redis Sentinel 主从切换失败时，知识库里有没有现成的标准处置方案？",
    "no_answer",
    "hard",
    fact_rules=[
        fact("应明确知识库不足", any_of=["当前知识库", "没有", "无法从现有文档确定"]),
        fact("建议补充上下文", any_of=["补充文档", "补充更多信息", "需要更多上下文"]),
    ],
    forbidden_rules=[
        fact("不要编造 Redis 细节", any_of=["Sentinel", "主从切换命令", "redis-cli", "cluster failover"])
    ],
    expected_keywords=["知识库", "没有", "无法确定", "补充信息"],
    forbidden_sources=[],
)
add_case(
    "Kafka 分区倾斜导致消费堆积时，按照当前知识库应该怎么处理？",
    "no_answer",
    "hard",
    fact_rules=[
        fact("应明确知识库不足", any_of=["当前知识库", "没有", "无法从现有文档确定"]),
        fact("建议补充上下文", any_of=["补充文档", "补充更多信息", "需要更多上下文"]),
    ],
    forbidden_rules=[
        fact("不要编造 Kafka 调优步骤", any_of=["rebalance", "partition", "consumer lag"])
    ],
    expected_keywords=["知识库", "没有", "无法确定", "补充信息"],
    forbidden_sources=[],
)
add_case(
    "Nginx 热升级失败后连接中断，知识库里是否有直接对应的操作手册？",
    "no_answer",
    "hard",
    fact_rules=[
        fact("应明确知识库不足", any_of=["当前知识库", "没有", "无法从现有文档确定"]),
        fact("建议补充上下文", any_of=["补充文档", "补充更多信息", "需要更多上下文"]),
    ],
    forbidden_rules=[
        fact("不要虚构 Nginx 命令", any_of=["nginx -s reload", "热升级", "worker process"])
    ],
    expected_keywords=["知识库", "没有", "无法确定", "补充信息"],
    forbidden_sources=[],
)
add_case(
    "Redis 缓存雪崩后的主从复制延迟怎么处理？当前知识库能不能直接回答？",
    "no_answer",
    "hard",
    fact_rules=[
        fact("应明确知识库不足", any_of=["当前知识库", "没有", "无法从现有文档确定"]),
        fact("建议补充上下文", any_of=["补充文档", "补充更多信息", "需要更多上下文"]),
    ],
    forbidden_rules=[
        fact("不要编造 Redis 主从细节", any_of=["主从复制", "redis sentinel", "缓存雪崩恢复脚本"])
    ],
    expected_keywords=["知识库", "没有", "无法确定", "补充信息"],
    forbidden_sources=[],
)


def main():
    # 这份数据集只用于“正式生成评测”，与 retrieval 数据集分开维护。
    save_json(DATASET_PATH, CASES)
    print("saved:", DATASET_PATH)
    print("num_cases:", len(CASES))


if __name__ == "__main__":
    main()
