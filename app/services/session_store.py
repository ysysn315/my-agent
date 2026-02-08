# 会话存储 - 管理对话历史
# TODO: Phase 2 - 实现 SessionStore 类
# - __init__(self, max_history: int = 6)
# - add_message(self, session_id: str, role: str, content: str) -> None
# - get_history(self, session_id: str) -> List[dict]
# - clear_session(self, session_id: str) -> bool
# - get_session_count(self) -> int
# - get_all_session_ids(self) -> List[str]
# 
# 功能说明：
# - 使用字典存储所有会话的历史记录
# - 每个会话最多保留 6 轮对话（12 条消息）
# - 超过限制时自动删除最旧的消息
# - 支持清空指定会话
# - 支持查询所有会话
from typing import Dict, List
from collections import defaultdict
from loguru import logger


class SessionStore:
    def __init__(self, max_history: int = 6):
        self.max_history = max_history
        self.sessions: Dict[str, List[dict]] = defaultdict(list)
        logger.info(f"会话存储初始化完成，最大历史轮数: {max_history}")

    def add_message(self, session_id: str, role: str, content: str) -> None:
        message = {
            "role": role,
            "content": content
        }
        self.sessions[session_id].append(message)
        max_messages = 2 * self.max_history
        if len(self.sessions[session_id]) > max_messages:
            self.sessions[session_id] = self.sessions[session_id][-max_messages:]
            logger.debug(f"会话 {session_id} 历史已截断到 {max_messages} 条消息")
        logger.debug(f"会话 {session_id} 添加消息: {role} - {content[:50]}...")

    def get_history(self, session_id: str) -> List[dict]:
        history = self.sessions.get(session_id, [])
        logger.debug(f"获取会话 {session_id} 历史: {len(history)} 条消息")
        return history

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            message_count = len(self.sessions[session_id])
            del self.sessions[session_id]
            logger.debug(f"已清除对话{session_id}的历史记录")
            return True
        else:
            logger.warning(f"对话{session_id}不存在，无需清空")
            return False

    def get_session_count(self) -> int:
        return len(self.sessions)

    def get_all_session_ids(self) -> List[str]:
        return list(self.sessions.keys())
