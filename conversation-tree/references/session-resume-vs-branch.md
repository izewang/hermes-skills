# Session Resume vs Branch — 代码级参考

## Schema

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    parent_session_id TEXT REFERENCES sessions(id),
    started_at REAL,
    ended_at REAL,
    end_reason TEXT,          -- NULL = 进行中, 'compression', 'resumed_other', etc.
    message_count INTEGER DEFAULT 0,
    title TEXT,
    ...
);
```

## `/resume` 代码路径

### CLI 模式 (`cli.py:_handle_resume_command`)

```python
# 1. 结束当前会话
self._session_db.end_session(self.session_id, "resumed_other")
# → UPDATE sessions SET ended_at=?, end_reason=? WHERE id=? AND ended_at IS NULL

# 2. 切换到目标会话
self.session_id = target_id
self._session_db.reopen_session(target_id)
# → UPDATE sessions SET ended_at=NULL, end_reason=NULL WHERE id=?

# 3. 后续消息直接写入 target_id 对应的 session row
```

### 网关模式 (`tui_gateway/server.py` session.resume RPC)

```python
db.reopen_session(target)                    # 清除结束标记
agent = _make_agent(sid, target, session_id=target)  # agent 用目标 ID
# 新消息归入 target session
```

## `/branch` 代码路径 (`cli.py:_handle_branch_command`)

```python
# 创建新 session_id，复制全部历史消息作为新记录
new_session_id = uuid.uuid4().hex[:8]
self._session_db.create_session(new_session_id, ...)  # 新 row
# 逐条复制 conversation_history 中的消息
for msg in self.conversation_history:
    self._session_db.add_message(...)
```

## Session 创建机制 (`run_agent.py:_ensure_db_session`)

```python
def _ensure_db_session(self):
    if self._session_db_created or not self._session_db:
        return
    self._session_db.create_session(
        session_id=self.session_id,
        source=...,
        parent_session_id=self._parent_session_id,
    )
    self._session_db_created = True
```

`create_session` → `_insert_session_row` 使用 **`INSERT OR IGNORE`**：
- 新 session 不存在 → 正常插入
- 已存在（如 resume 场景） → 静默跳过，保留原 row

## 分支点检测（session-branch-tree.py）

```python
# 对于每个有 parent 的 session S：
c.execute(
    "SELECT COUNT(*) FROM messages WHERE session_id=? AND timestamp>?",
    (parent_id, S.started_at)
)
if count > 0:
    # parent 在 S 分支后有新消息 → 插入虚拟节点
    promoted[S["id"]] = (parent_id, pre_msg_count)
```

虚拟节点表现为 `⚪  N条`，其中 N 是分支发生时 parent 已积累的消息数（`timestamp <= child.started_at` 的 count）。

## 关键结论

| 场景 | 新 session? | 树结构变化 |
|------|------------|-----------|
| `/resume <A>` 后发消息 | ❌ | A 的 message_count +1, end_reason 变 NULL |
| `/branch [name]` | ✅ | 新 B 挂为 A 的子节点, A 的 end_reason 保留 |
| A 有子 B 且 A 继续发消息后 | — | 脚本插入虚拟节点, A 和 B 成姐妹 |

**核心规则：** resume = 原地继续 / branch = fork 副本。
