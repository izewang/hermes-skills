#!/usr/bin/env python3
"""Hermes 会话分支树查看工具"""

import sqlite3, os, argparse
from datetime import datetime


def get_sessions(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, title, end_reason, parent_session_id, started_at, ended_at,
               message_count, source
        FROM sessions ORDER BY started_at
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def build_tree(sessions, db_path):
    nodes = {s["id"]: s for s in sessions}
    raw_p = {s["id"]: s.get("parent_session_id") for s in sessions}
    all_nodes = dict(nodes)
    children, roots = {}, []
    assigned = set()
    def add(p, c):
        children.setdefault(p, []).append(c)

    # Promotion detection: parent had messages after child branched off
    promoted = {}
    conn = sqlite3.connect(db_path) if os.path.isfile(db_path) else None
    if conn:
        c = conn.cursor()
        for s in sessions:
            pid = raw_p.get(s["id"])
            if not pid or not s.get("started_at"):
                continue
            ts = s["started_at"]
            c.execute("SELECT COUNT(*) FROM messages WHERE session_id=? AND timestamp>?", (pid, ts))
            if c.fetchone()[0] > 0:
                c.execute("SELECT COUNT(*) FROM messages WHERE session_id=? AND timestamp<=?", (pid, ts))
                promoted[s["id"]] = (pid, c.fetchone()[0])
        conn.close()

    prom_cids = set(promoted.keys())
    prom_pars = set(p for _, (p, _) in promoted.items())
    chain = prom_cids & prom_pars  # sessions that are both promoted child AND parent of promoted children

    # Build tree with virtual nodes
    for s in sessions:
        sid, pid = s["id"], raw_p.get(s["id"])
        if sid in chain:
            assigned.add(sid); continue
        if sid in prom_cids:
            assigned.add(sid); continue
        if sid in prom_pars:
            v_id = f"@{sid[-8:]}"
            pre = next((v for c_, (p_, v) in promoted.items() if p_ == sid), 0)
            v_node = {"id": v_id, "_virtual": True, "_pre_msgs": pre}
            if not raw_p.get(sid):
                v_node["_origin"] = sid  # root virtual node: records original session ID
            all_nodes[v_id] = v_node
            assigned.add(v_id)
            vp = raw_p.get(sid)
            if vp:
                add(vp, v_id)
            else:
                roots.append(all_nodes[v_id])
            add(v_id, sid)
            assigned.add(sid)
            for cid in prom_cids:
                if promoted[cid][0] == sid:
                    add(v_id, cid)
                    assigned.add(cid)
            continue
        if not pid:
            roots.append(s); assigned.add(sid); continue
        add(pid, sid); assigned.add(sid)

    # Chain session handling: promoted sessions that also have promoted children
    for sid in chain:
        v_id = f"@{sid[-8:]}"
        if v_id in all_nodes: continue
        pre = next((v for c_, (p_, v) in promoted.items() if p_ == sid), 0)
        all_nodes[v_id] = {"id": v_id, "_virtual": True, "_pre_msgs": pre}
        add(sid, v_id); assigned.add(v_id)
        for cid in prom_cids:
            if promoted[cid][0] == sid:
                add(v_id, cid); assigned.add(cid)

    # Orphan cleanup
    for s in sessions:
        if s["id"] in assigned: continue
        pid = raw_p.get(s["id"])
        if pid: add(pid, s["id"])
        else: roots.append(s)

    # Sort by started_at (real nodes) or pre_msgs (virtual nodes)
    def sort_key(sid):
        n = all_nodes.get(sid)
        if not n: return 0
        return n.get("_pre_msgs", 0) if n.get("_virtual") else (n.get("started_at", 0) or 0)
    roots.sort(key=lambda r: sort_key(r["id"]))
    for k in children:
        children[k] = sorted(set(children[k]), key=sort_key)
    return all_nodes, children, roots



def render(all_nodes, children, roots, cur_id=None):
    for i, root in enumerate(roots):
        if i > 0: print()
        _render_root(all_nodes, children, root, cur_id)


def _render_root(all_nodes, children, root, cur_id=None):
    rid = root["id"]
    if root.get("_virtual"):
        pre = root.get("_pre_msgs", 0)
        origin_sid = root.get("_origin")
        name = origin_sid if origin_sid else root["id"].lstrip("@")[-8:]
        print(f"📄 {name} 💬 {int(pre)} 条")
    else:
        title = root.get("title") or root["id"]
        msgs = root.get("message_count", 0)
        emoji = "🟢" if rid == cur_id else ""
        line = f"📄 {title} 💬 {msgs} 条"
        if emoji:
            line += f" {emoji}"
        print(line)

    cids = children.get(rid, [])
    if cids:
        print("│")
        for j, cid in enumerate(cids):
            _render_node(all_nodes, children, cid, "", j == len(cids) - 1, 1, cur_id)
            if j < len(cids) - 1:
                print("│")


def _render_node(all_nodes, children, node_id, prefix, is_last, depth=1, cur_id=None):
    node = all_nodes.get(node_id)
    if not node: return
    cids = children.get(node_id, [])
    spacer = "    " if is_last else "│   "
    effective_spacer = spacer if depth < 1 else "  " + spacer
    connector = "└── " if is_last else "├── "

    if node.get("_virtual"):
        pre = node.get("_pre_msgs", 0)
        print(f"{prefix}{connector}◆ 💬 {int(pre)} 条")
    else:
        title = node.get("title") or node["id"]
        msgs = node.get("message_count", 0)
        real_id = node["id"]
        emoji = "🟢" if real_id == cur_id else ""
        line = f"{prefix}{connector}🌿 {title} 💬 {msgs} 条"
        if emoji:
            line += f" {emoji}"
        print(line)

    if cids:
        print(f"{prefix}{effective_spacer}│")
        for j, cid in enumerate(cids):
            _render_node(all_nodes, children, cid, prefix + effective_spacer, j == len(cids) - 1, depth + 1, cur_id)
            if j < len(cids) - 1:
                print(f"{prefix}{effective_spacer}│")


def main():
    p = argparse.ArgumentParser()
    dh = os.environ.get("HERMES_HOME")
    if not dh:
        dh = os.path.expanduser("~/.hermes")
    p.add_argument("--db", default=os.path.join(dh, "state.db"))
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if not os.path.isfile(args.db):
        print(f"❌ 找不到: {args.db}"); return 1
    try:
        sessions = get_sessions(args.db)
    except sqlite3.Error as e:
        print(f"❌ 读取失败: {e}"); return 1
    if not sessions:
        print("📭 无记录"); return 0
    all_nodes, children, roots = build_tree(sessions, args.db)
    total = len(sessions)
    act = sum(1 for s in sessions if s.get("end_reason") is None)
    # 找到当前活跃 session：最后一条消息所在的 session
    cur_id = None
    try:
        conn = sqlite3.connect(args.db)
        c = conn.cursor()
        c.execute("SELECT session_id FROM messages ORDER BY timestamp DESC LIMIT 1")
        row = c.fetchone()
        if row:
            cur_id = row[0]
        conn.close()
    except sqlite3.Error:
        pass
    vc = sum(1 for n in all_nodes.values() if n.get("_virtual"))
    print(f"🌳 Hermes 会话分支树")
    print(f"   总计 {total} 个会话  |  活跃 {act}")
    if vc: print(f"   🔄 {vc} 个分支点")
    print()
    render(all_nodes, children, roots, cur_id)
    return 0


if __name__ == "__main__":
    exit(main())
