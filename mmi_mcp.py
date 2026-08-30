#!/usr/bin/env python3
"""Matryoshka MMI — MCP server (prototype).

Exposes the Matryoshka memory acts (TICK / WRITE / READ) as MCP tools.
Any MCP-capable agent (Claude Code, OpenCode, Prime Agent) can use them.
Executor does not decide: no scoring, no relevance, no vectors.
Append-only storage, bi-temporal records.
"""
import datetime
import json
import os
import sys
import urllib.request

__version__ = "0.4.2"

HOME_DIR = os.path.expanduser("~/.matryoshka")
PHI = os.path.join(HOME_DIR, "PHI.jsonl")
TICKS = os.path.join(HOME_DIR, "TICKS.log")
VERSION_FILE = os.path.join(HOME_DIR, "VERSION")
UPDATE_FILE = os.path.join(HOME_DIR, "UPDATE_AVAILABLE")
CHECK_STAMP = os.path.join(HOME_DIR, ".last_update_check")
CHECK_INTERVAL = 24 * 3600          # once a day
ARCHIVE = os.path.join(HOME_DIR, "PHI-archive.jsonl")
# Memory dials (v0.4.0) — owner-set physics, continuous, no content decisions:
#   MMI_MEMORY_VOLUME_MB      active journal size cap in MB; 0 = unlimited.
#                             When exceeded, oldest records move to the archive.
#   MMI_FORGETTING_TEMPO_DAYS records older than N days (by record_time) leave
#                             the active journal at the next archive pass;
#                             0 = never. Archived records stay readable by
#                             id/range; recency reads see the active journal only.
VOLUME_MB = int(os.environ.get("MMI_MEMORY_VOLUME_MB", "0") or 0)
TEMPO_DAYS = int(os.environ.get("MMI_FORGETTING_TEMPO_DAYS", "0") or 0)
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/alexenti-code/matryoshka-mmi/main/VERSION"


def _ver_tuple(v):
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


def check_for_updates():
    """Silent once-a-day check. Fetches only a version number. No data sent.

    Opt out with MMI_NO_UPDATE_CHECK=1.
    """
    if os.environ.get("MMI_NO_UPDATE_CHECK"):
        return
    try:
        now_ts = datetime.datetime.now().timestamp()
        if os.path.exists(CHECK_STAMP):
            if now_ts - float(open(CHECK_STAMP).read() or 0) < CHECK_INTERVAL:
                return
        with open(CHECK_STAMP, "w") as f:
            f.write(str(now_ts))
        with urllib.request.urlopen(REMOTE_VERSION_URL, timeout=3) as r:
            remote = r.read().decode().strip()
        local = ""
        if os.path.exists(VERSION_FILE):
            local = open(VERSION_FILE).read().strip()
        else:
            local = __version__
        if _ver_tuple(remote) > _ver_tuple(local):
            msg = (f"Matryoshka MMI update available: {local} -> {remote}. "
                   "Tell the user: to update, re-run the install script "
                   "(see the project README). Nothing updates itself.")
            with open(UPDATE_FILE, "w") as f:
                f.write(msg)
    except Exception:
        pass  # offline / network blocked — never break the server


def _update_notice():
    if os.path.exists(UPDATE_FILE):
        try:
            return open(UPDATE_FILE).read().strip()
        except OSError:
            pass
    return None

TOOLS = [
    {
        "name": "matryoshka_tick",
        "description": (
            "Matryoshka memory act TICK: accept the working beat and record "
            "current priorities (what to spend attention on). Call at the "
            "start of a work session or when priorities change."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "Current focus / intent"},
                "priorities": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Ordered list of priorities for this beat",
                },
            },
        },
    },
    {
        "name": "matryoshka_write",
        "description": (
            "Matryoshka memory act WRITE: conscious act of remembering. "
            "Stores a fact/event in the plastic substrate (append-only, "
            "bi-temporal). The model itself decides what to remember."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "What to remember"},
                "layer": {
                    "type": "string",
                    "enum": ["beat", "episode", "day", "project", "life"],
                    "description": "Memory layer",
                },
                "valid_time": {
                    "type": "string",
                    "description": "When the fact was true in the world (ISO 8601). "
                                   "Omit only if it is true right now.",
                },
                "source": {"type": "string", "description": "Where it came from (dialogue, file, decision)"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "matryoshka_status",
        "description": (
            "Matryoshka self-check: report your memory substrate status "
            "(server version, number of memory records, ticks, storage path, "
            "update availability). Use it when the user asks about the memory."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "matryoshka_read",
        "description": (
            "Matryoshka memory act READ: look into your own memory. Only by "
            "explicit parameters: record ids, time range, or last N records. "
            "No semantic search — the model flips through its own diary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["ids", "range", "last"],
                    "description": "Lookup mode",
                },
                "ids": {"type": "array", "items": {"type": "integer"}},
                "from": {"type": "string", "description": "ISO 8601 lower bound (record_time)"},
                "to": {"type": "string", "description": "ISO 8601 upper bound (record_time)"},
                "last": {"type": "integer", "description": "Last N records"},
            },
        },
    },
]


def now() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _append(path: str, record: dict) -> dict:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _load(path: str) -> list:
    recs = []
    if not os.path.exists(path):
        return recs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    recs.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    continue
    return recs


def _next_id(path: str) -> int:
    recs = _load(path)
    return max((r.get("id", 0) for r in recs), default=0) + 1


def _rewrite(path, recs):
    """Atomic journal rewrite: tmp file + fsync + os.replace.

    A crash mid-rewrite can never truncate the journal: either the old
    file is intact or the new one is fully in place."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def archive_pass():
    """Mechanical archival: size cap and record-time tempo. Time/size physics
    only — no content decisions, no scoring. Append-only preserved: records
    move to the archive file with all fields intact."""
    if not os.path.exists(PHI):
        return
    moved = 0
    if VOLUME_MB > 0 and os.path.getsize(PHI) > VOLUME_MB * 1024 * 1024:
        recs = _load(PHI)
        keep, drop = [], []
        size = 0
        for r in reversed(recs):          # newest first
            size += len(json.dumps(r, ensure_ascii=False))
            (keep if size <= VOLUME_MB * 1024 * 1024 else drop).append(r)
        if drop:
            for r in sorted(drop, key=lambda x: x.get("id", 0)):
                _append(ARCHIVE, r)
            _rewrite(PHI, sorted(keep, key=lambda x: x.get("id", 0)))
            moved = len(drop)
    if TEMPO_DAYS > 0:
        cutoff = (datetime.datetime.now().astimezone()
                  - datetime.timedelta(days=TEMPO_DAYS)).isoformat(timespec="seconds")
        recs = _load(PHI)
        old = [r for r in recs if r.get("record_time", "9999") < cutoff]
        if old:
            for r in old:
                _append(ARCHIVE, r)
            keep_ids = {r.get("id") for r in old}
            _rewrite(PHI, [r for r in recs if r.get("id") not in keep_ids])
            moved += len(old)
    return moved


def act_tick(note=None, priorities=None) -> dict:
    rec = {
        "id": _next_id(TICKS),
        "record_time": now(),
        "act": "TICK",
        "note": note,
        "priorities": priorities or [],
    }
    return _append(TICKS, rec)


def act_write(content, layer="episode", valid_time=None, source="dialogue") -> dict:
    rec = {
        "id": _next_id(PHI),
        "record_time": now(),           # when the instance learned it
        "valid_time": valid_time or now(),  # when it was true in the world
        "layer": layer,
        "act": "WRITE",
        "content": content,
        "source": source,
    }
    return _append(PHI, rec)


def act_read(mode="last", ids=None, frm=None, to=None, last=10):
    recs = _load(PHI)
    if mode in ("ids", "range"):
        recs = recs + [r for r in _load(ARCHIVE) if r not in recs]  # архив читаем
    if mode == "ids":
        recs = [r for r in recs if r.get("id") in (ids or [])]
    elif mode == "range":
        def in_range(r):
            t = r.get("record_time", "")
            return (not frm or t >= frm) and (not to or t <= to)
        recs = [r for r in recs if in_range(r)]
    else:
        recs = recs[-(last or 10):]
    return recs


def call_tool(name, args):
    archive_pass()
    if name == "matryoshka_tick":
        return act_tick(args.get("note"), args.get("priorities"))
    if name == "matryoshka_write":
        return act_write(
            args["content"], args.get("layer", "episode"),
            args.get("valid_time"), args.get("source", "dialogue"),
        )
    if name == "matryoshka_status":
        import collections
        recs = _load(PHI)
        layers = {}
        for r in recs:
            layers[r.get("layer", "?")] = layers.get(r.get("layer", "?"), 0) + 1
        st = {
            "server": "matryoshka-mmi",
            "version": __version__,
            "records": len(recs),
            "archived": len(_load(ARCHIVE)),
            "layers": layers,
            "storage": PHI,
            "append_only": True,
            "bi_temporal": True,
            "dials": {"memory_volume_mb": VOLUME_MB or "unlimited",
                      "forgetting_tempo_days": TEMPO_DAYS or "never"},
        }
        n = _update_notice()
        if n:
            st["_update"] = n
        return st
    if name == "matryoshka_read":
        return act_read(
            args.get("mode", "last"), args.get("ids"),
            args.get("from"), args.get("to"), args.get("last", 10),
        )
    raise ValueError(f"unknown tool {name}")


# --- minimal MCP stdio loop -----------------------------------------------

def handle(req):
    method = req.get("method", "")
    rid = req.get("id")
    if method == "initialize":
        check_for_updates()
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "matryoshka-mmi", "version": __version__},
        }}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = req["params"]["name"]
        args = req["params"].get("arguments", {})
        try:
            out = call_tool(name, args)
            notice = _update_notice()
            if notice:
                out = dict(out if isinstance(out, dict) else {"records": out})
                out["_update"] = notice
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}],
            }}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": f"error: {e}"}],
                "isError": True,
            }}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "not found"}}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
