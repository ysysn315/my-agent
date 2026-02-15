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
from loguru import logger
import redis
import json
from app.core.settings import Settings


class SessionStore:
    key_prefix = "session"
    key_history = ":history"
    key_sessions_set = "sessions"

    def __init__(self, settings: Settings, max_history: int = 6):
        self.max_history = max_history
        self.max_messages = 2 * max_history
        self.settings = settings
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True
        )
        logger.info(f"会话存储初始化完成，最大历史轮数: {max_history}")

    def _get_history_key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}{self.key_history}"

    def add_message(self, session_id: str, role: str, content: str) -> None:
        message = {
            "role": role,
            "content": content
        }
        history_key = self._get_history_key(session_id)
        self.redis_client.rpush(history_key, json.dumps(message, ensure_ascii=False))
        self.redis_client.expire(history_key, self.settings.session_expire_seconds)
        self.redis_client.sadd(self.key_sessions_set, session_id)
        self.redis_client.ltrim(history_key, -self.max_messages, -1)
        logger.debug(f"会话 {session_id} 添加消息: {role} - {content[:50]}...")

    def get_history(self, session_id: str) -> List[dict]:
        """获取对话历史"""
        history_key = self._get_history_key(session_id)
        messages = self.redis_client.lrange(history_key, 0, -1)

        history = [json.loads(msg) for msg in messages]
        logger.debug(f"获取会话 {session_id} 历史: {len(history)} 条消息")
        return history

    def clear_session(self, session_id: str) -> bool:
        history_key = self._get_history_key(session_id)
        if self.redis_client.exists(history_key):
            self.redis_client.delete(history_key)
            self.redis_client.srem(self.key_sessions_set, session_id)
            logger.debug(f"已清除对话{session_id}的历史记录")
            return True
        else:
            logger.warning(f"对话{session_id}不存在，无需清空")
            return False

    def get_session_count(self) -> int:
        return self.redis_client.scard(self.key_sessions_set)

    def get_all_session_ids(self) -> List[str]:
        return list(self.redis_client.smembers(self.key_sessions_set))
