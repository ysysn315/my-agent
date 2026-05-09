from app.services.session_store import SessionStore


class FakeRedis:
    def __init__(self, *args, **kwargs):
        self.lists = {}
        self.values = {}
        self.sets = {}

    def rpush(self, key, value):
        self.lists.setdefault(key, []).append(value)

    def expire(self, key, seconds):
        return True

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def lrange(self, key, start, end):
        items = self.lists.get(key, [])
        if end == -1:
            end = len(items) - 1
        return items[start : end + 1]

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def delete(self, key):
        self.lists.pop(key, None)
        self.values.pop(key, None)
        self.sets.pop(key, None)

    def ltrim(self, key, start, end):
        items = self.lists.get(key, [])
        if start < 0:
            start = max(len(items) + start, 0)
        if end < 0:
            end = len(items) + end
        self.lists[key] = items[start : end + 1]

    def exists(self, key):
        return int(key in self.lists or key in self.values)

    def srem(self, key, value):
        if key in self.sets:
            self.sets[key].discard(value)

    def scard(self, key):
        return len(self.sets.get(key, set()))

    def smembers(self, key):
        return self.sets.get(key, set())


class FakeSettings:
    redis_host = "localhost"
    redis_port = 6379
    redis_db = 0
    redis_password = ""
    session_expire_seconds = 3600


def test_session_store_summary_compacts_older_messages(monkeypatch):
    import app.services.session_store as session_store_module

    monkeypatch.setattr(session_store_module.redis, "Redis", FakeRedis)

    store = SessionStore(FakeSettings(), max_history=2)
    session_id = "session-1"

    store.add_message(session_id, "user", "问题 1")
    store.add_message(session_id, "assistant", "回答 1")
    store.add_message(session_id, "user", "问题 2")
    store.add_message(session_id, "assistant", "回答 2")
    store.add_message(session_id, "user", "问题 3")
    store.add_message(session_id, "assistant", "回答 3")

    messages_to_summarize = store.get_messages_to_summarize(session_id)

    assert [msg["content"] for msg in messages_to_summarize] == ["问题 1", "回答 1"]

    store.apply_summary_and_trim(session_id, "用户已经讨论过问题 1 和回答 1")

    assert store.get_summary(session_id) == "用户已经讨论过问题 1 和回答 1"
    assert [msg["content"] for msg in store.get_history(session_id)] == [
        "问题 2",
        "回答 2",
        "问题 3",
        "回答 3",
    ]
