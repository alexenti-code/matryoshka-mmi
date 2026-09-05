#!/usr/bin/env python3
"""PMI (Plastic Memory Interface, formerly MMI) — MCP server.

Reference executor of PlastFormer (see plastformer/docs/ADR-001).

Exposes the Matryoshka memory acts (TICK / WRITE / READ) as MCP tools.
Any MCP-capable agent (Claude Code, OpenCode, Prime Agent) can use them.
Executor does not decide: no scoring, no relevance, no vectors.
Append-only storage, bi-temporal records.
"""
import datetime
import json
import math
import os
import sys
import urllib.request

__version__ = "0.6.0"

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

# Friction (v0.5) — decay physics, the "layer is a speed" principle.
# Each layer is a time constant tau: the same trace fades at different
# speeds; REPEAT re-amplifies (each repeat doubles the signal, THEORY.md).
# Continuous physics, no content decisions — the temperature class.
# Owner-settable: MMI_TAU_SCALE multiplies every tau (2.0 = forgets 2x slower).
TAU_SCALE = float(os.environ.get("MMI_TAU_SCALE", "1.0") or 1.0)
if not (TAU_SCALE > 0):            # 0 / negative / NaN would break the decay math
    TAU_SCALE = 1.0
TAU = {  # seconds; factory settings, documented in SPEC.md
    "beat":    1 * 3600,        # hours
    "episode": 1 * 86400,       # a day
    "day":     7 * 86400,       # a week
    "project": 30 * 86400,      # weeks..month
    "life":    365 * 86400,     # a year scale
}

# Tick clock (v0.6.0, ADR-001 §5): MMI_CLOCK=ticks|wall, default wall.
#   wall  — weight decays in wall-clock seconds (TAU above); record_time rules.
#   ticks — weight decays in lived ticks (TAU_TICKS below); record_time and
#           valid_time stay as audited stamps and do not affect the weight.
# In ticks mode the STAND advances the counter (+1 per executed WRITE /
# REPEAT / CONNECT / RECONCILE act); the model never ticks itself — a manual
# matryoshka_tick call in ticks mode is a deprecated no-op.
# MMI_TAU_TICKS: per-layer time constants in ticks. Formats:
#   "beat=10,episode=50,day=200,project=1000,life=5000" or "10,50,200,1000,5000"
#   (layer order: beat, episode, day, project, life). Default for E1 below.
# MMI_INJECT_TOP=N: attach the N loudest traces by weight (no relevance,
#   no content search) as a <<PMI>> block to tool results. 0 = off.
TAU_TICKS_DEFAULT = {
    "beat": 10,
    "episode": 50,
    "day": 200,
    "project": 1000,
    "life": 5000,
}
_LAYER_ORDER = ("beat", "episode", "day", "project", "life")


def clock_mode() -> str:
    mode = (os.environ.get("MMI_CLOCK", "wall") or "wall").strip().lower()
    return mode if mode in ("ticks", "wall") else "wall"


def tau_ticks() -> dict:
    out = dict(TAU_TICKS_DEFAULT)
    raw = (os.environ.get("MMI_TAU_TICKS", "") or "").strip()
    if raw:
        try:
            if "=" in raw:
                for part in raw.split(","):
                    k, v = part.split("=", 1)
                    k, v = k.strip(), float(v.strip())
                    if k in out and v > 0:
                        out[k] = v
            else:
                vals = [float(x.strip()) for x in raw.split(",")]
                if len(vals) == 5 and all(v > 0 for v in vals):
                    out = dict(zip(_LAYER_ORDER, vals))
        except (ValueError, TypeError):
            pass
    scale = TAU_SCALE if TAU_SCALE > 0 else 1.0
    return {k: v * scale for k, v in out.items()}


def inject_top_n() -> int:
    try:
        return max(0, int(os.environ.get("MMI_INJECT_TOP", "0") or 0))
    except (ValueError, TypeError):
        return 0
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
            "start of a work session or when priorities change. "
            "In tick-clock mode (MMI_CLOCK=ticks) the stand counts ticks "
            "itself and this tool is a deprecated no-op."
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
    {
        "name": "matryoshka_connect",
        "description": (
            "PlastFormer act CONNECT: link existing records into one trace. "
            "Creates a NEW record (act CONNECT, refs to the linked ids) with "
            "your summary; the linked records are never modified. Use when "
            "separate memories belong together."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "refs": {"type": "array", "items": {"type": "integer"},
                         "description": "Ids of the records to link"},
                "summary": {"type": "string",
                            "description": "What the linked traces mean together"},
                "layer": {
                    "type": "string",
                    "enum": ["beat", "episode", "day", "project", "life"],
                    "description": "Memory layer for the link record",
                },
            },
            "required": ["refs", "summary"],
        },
    },
    {
        "name": "matryoshka_reconcile",
        "description": (
            "PlastFormer act RECONCILE: record a clock-biography event "
            "(e.g. a gap between lived ticks and wall-clock stamps). Creates "
            "a NEW record (act RECONCILE) in a slow layer with refs to the "
            "affected records. The past is never rewritten — the divergence "
            "itself becomes a memory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "note": {"type": "string",
                         "description": "What diverged and how it was noticed"},
                "refs": {"type": "array", "items": {"type": "integer"},
                         "description": "Ids of the affected records (may be empty)"},
                "layer": {
                    "type": "string",
                    "enum": ["beat", "episode", "day", "project", "life"],
                    "description": "Slow layer for the record (default project)",
                },
            },
            "required": ["note"],
        },
    },
    {
        "name": "matryoshka_repeat",
        "description": (
            "Matryoshka memory act REPEAT: conscious re-learning of an "
            "existing record (like learning a poem by heart). Creates a NEW "
            "record referencing the original; the original trace gains "
            "signal (doubles per repeat). Use when you decide a memory is "
            "worth keeping stronger. History is never rewritten."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "Id of the record to re-learn"},
                "note": {"type": "string", "description": "Optional: what exactly you re-learned"},
            },
            "required": ["id"],
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
            old_ids = {r.get("id") for r in old}
            _rewrite(PHI, [r for r in recs if r.get("id") not in old_ids])
            moved += len(old)
    return moved


def tick_now() -> int:
    """Lived ticks so far = number of records in TICKS.log."""
    return len(_load(TICKS))


def _auto_tick(note="stand exchange") -> dict:
    """The stand counts one lived tick per executed storing act."""
    return _append(TICKS, {
        "id": _next_id(TICKS),
        "record_time": now(),
        "act": "TICK",
        "note": note,
        "priorities": [],
    })


def act_tick(note=None, priorities=None) -> dict:
    if clock_mode() == "ticks":
        # Deprecated in ticks mode: the stand advances the counter itself,
        # the model never ticks. No record is appended.
        return {"deprecated": True, "clock": "ticks", "tick": tick_now(),
                "note": "tick is counted by the stand; this call changed nothing"}
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
        "record_time": now(),           # when the instance learned it (audit stamp)
        "valid_time": valid_time or now(),  # when it was true in the world (audit stamp)
        "record_tick": tick_now(),      # lived time: ticks so far
        "layer": layer,
        "act": "WRITE",
        "content": content,
        "source": source,
    }
    out = _append(PHI, rec)
    if clock_mode() == "ticks":
        _auto_tick("write")
    return out


def _repeats_of(rec_id) -> int:
    """REPEAT act count for a record — counted from REPEAT records
    referencing it (append-only: repeats are new records, never edits)."""
    return sum(1 for r in _load(PHI)
               if r.get("act") == "REPEAT" and rec_id_ok(r, rec_id))


def rec_id_ok(rec, rid):
    return rid in (rec.get("refs") or [])


def _weight(rec, repeats=0, n_now=None) -> float:
    """Current trace strength: (1 + repeats) * exp(-dt/tau[layer]).

    Pure friction physics shown on read. Nothing is filtered, ranked or
    dropped by it: the number only tells the model how loud the trace
    still is — like a mixture that itself reports its age (THEORY.md).
    `repeats` is passed in by the caller (counted in one journal pass);
    the standalone default keeps the function honest for single records.
    Clock: in wall mode dt is wall-clock seconds (record_time rules,
    record_tick ignored); in ticks mode dt is lived ticks
    (n_now - record_tick, wall stamps ignored)."""
    if rec.get("act") == "TICK":
        return 1.0
    n = repeats if rec.get("act") == "WRITE" else 0
    if clock_mode() == "ticks":
        if n_now is None:
            n_now = tick_now()
        try:
            dt = max(0.0, float(n_now) - float(rec.get("record_tick", 0)))
        except (ValueError, TypeError):
            dt = 0.0
        tau = tau_ticks().get(rec.get("layer", "episode"),
                              tau_ticks()["episode"])
        return round((1 + n) * math.exp(-dt / tau), 4)
    try:
        t0 = datetime.datetime.fromisoformat(rec.get("record_time", now()))
        dt = max(0.0, (datetime.datetime.now().astimezone() - t0).total_seconds())
    except (ValueError, TypeError):
        dt = 0.0
    tau = TAU.get(rec.get("layer", "episode"), TAU["episode"]) * TAU_SCALE
    return round((1 + n) * math.exp(-dt / tau), 4)


def act_repeat(rec_id, note=None) -> dict:
    """Conscious re-learning: a NEW record referencing the original.
    History is never rewritten; the original trace gains signal.
    Only an existing WRITE record can be repeated: repeating a missing
    or non-WRITE id is an error, never a silent no-op."""
    known = {r.get("id") for r in _load(PHI) + _load(ARCHIVE)
             if r.get("act") == "WRITE"}
    if rec_id not in known:
        raise ValueError(
            f"repeat: no WRITE record with id {rec_id} in the journal "
            "(repeating a missing or non-WRITE record is not possible)")
    rec = {
        "id": _next_id(PHI),
        "record_time": now(),
        "valid_time": now(),
        "record_tick": tick_now(),
        "layer": "beat",
        "act": "REPEAT",
        "refs": [rec_id],
        "content": note or "",
        "source": "repeat",
    }
    out = _append(PHI, rec)
    if clock_mode() == "ticks":
        _auto_tick("repeat")
    return out


def _known_ids():
    return {r.get("id") for r in _load(PHI) + _load(ARCHIVE)}


def act_connect(refs, summary, layer="episode") -> dict:
    """CONNECT: link existing records; sources are never touched."""
    refs = list(refs or [])
    if not refs:
        raise ValueError("connect: refs must list at least one record id")
    missing = [i for i in refs if i not in _known_ids()]
    if missing:
        raise ValueError(
            f"connect: no record(s) with id(s) {missing} in the journal")
    rec = {
        "id": _next_id(PHI),
        "record_time": now(),
        "valid_time": now(),
        "record_tick": tick_now(),
        "layer": layer,
        "act": "CONNECT",
        "refs": refs,
        "content": summary,
        "source": "connect",
    }
    out = _append(PHI, rec)
    if clock_mode() == "ticks":
        _auto_tick("connect")
    return out


def act_reconcile(note, refs=None, layer="project") -> dict:
    """RECONCILE: a clock-biography event in a slow layer; refs optional."""
    refs = list(refs or [])
    missing = [i for i in refs if i not in _known_ids()]
    if missing:
        raise ValueError(
            f"reconcile: no record(s) with id(s) {missing} in the journal")
    rec = {
        "id": _next_id(PHI),
        "record_time": now(),
        "valid_time": now(),
        "record_tick": tick_now(),
        "layer": layer,
        "act": "RECONCILE",
        "refs": refs,
        "content": note,
        "source": "reconcile",
    }
    out = _append(PHI, rec)
    if clock_mode() == "ticks":
        _auto_tick("reconcile")
    return out


def act_read(mode="last", ids=None, frm=None, to=None, last=10):
    phi = _load(PHI)
    repeats = {}
    for r in phi:                      # one pass: count REPEAT refs per id
        if r.get("act") == "REPEAT":
            for ref in (r.get("refs") or []):
                repeats[ref] = repeats.get(ref, 0) + 1
    recs = phi
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
    n_now = tick_now() if clock_mode() == "ticks" else None
    return [dict(r, weight=_weight(r, repeats.get(r.get("id"), 0), n_now))
            for r in recs]


def inject_top(n=None) -> list:
    """N loudest WRITE traces by weight only. No relevance, no content
    search, no semantic index: pure amplitude ranking for the <<PMI>>
    block (Arm C physics injection, E1 v1.1)."""
    if n is None:
        n = inject_top_n()
    if n <= 0:
        return []
    n_now = tick_now() if clock_mode() == "ticks" else None
    phi = _load(PHI)
    repeats = {}
    for r in phi:
        if r.get("act") == "REPEAT":
            for ref in (r.get("refs") or []):
                repeats[ref] = repeats.get(ref, 0) + 1
    scored = [( _weight(r, repeats.get(r.get("id"), 0), n_now), r)
              for r in phi if r.get("act") == "WRITE"]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [dict(r, weight=w) for w, r in scored[:n]]


def pmi_block(n=None) -> str:
    """Render the loudest-N traces as a <<PMI>> text block."""
    top = inject_top(n)
    lines = ["<<PMI>> loudest traces by weight (no relevance, no search)"]
    for r in top:
        lines.append(f"- [id={r.get('id')} layer={r.get('layer')} "
                     f"weight={r.get('weight')}] {r.get('content', '')}")
    lines.append("<</PMI>>")
    return "\n".join(lines)


def call_tool(name, args):
    archive_pass()
    if name == "matryoshka_tick":
        return act_tick(args.get("note"), args.get("priorities"))
    if name == "matryoshka_repeat":
        return act_repeat(args["id"], args.get("note"))
    if name == "matryoshka_connect":
        return act_connect(args["refs"], args["summary"],
                           args.get("layer", "episode"))
    if name == "matryoshka_reconcile":
        return act_reconcile(args["note"], args.get("refs", []),
                             args.get("layer", "project"))
    if name == "matryoshka_write":
        return act_write(
            args["content"], args.get("layer", "episode"),
            args.get("valid_time"), args.get("source", "dialogue"),
        )
    if name == "matryoshka_status":
        recs = _load(PHI)
        layers = {}   # WRITE records only: REPEAT records are acts, not layers
        acts = {}
        for r in recs:
            acts[r.get("act", "?")] = acts.get(r.get("act", "?"), 0) + 1
            if r.get("act") == "WRITE":
                layers[r.get("layer", "?")] = layers.get(r.get("layer", "?"), 0) + 1
        mode = clock_mode()
        st = {
            "server": "matryoshka-mmi",
            "version": __version__,
            "records": len(recs),
            "archived": len(_load(ARCHIVE)),
            "layers": layers,
            "acts": acts,
            "ticks": len(_load(TICKS)),
            "clock": mode,
            "storage": PHI,
            "append_only": True,
            "bi_temporal": True,
            "dials": {"memory_volume_mb": VOLUME_MB or "unlimited",
                      "forgetting_tempo_days": TEMPO_DAYS or "never",
                      "tau_scale": TAU_SCALE},
            "friction": {"model": "(1+repeats)*exp(-dt/tau)",
                         "tau_hours": {k: v // 3600 for k, v in TAU.items()},
                         "tau_ticks": tau_ticks(),
                         "repeats_total": sum(
                             1 for r in _load(PHI) if r.get("act") == "REPEAT")},
            "inject_top": inject_top_n(),
        }
        n = _update_notice()
        if n:
            st["_update"] = n
        return st
    if name == "matryoshka_read":
        out = act_read(
            args.get("mode", "last"), args.get("ids"),
            args.get("from"), args.get("to"), args.get("last", 10),
        )
    n_top = inject_top_n()
    if n_top > 0:
        out = {"records": out, "_pmi": pmi_block(n_top)}
    return out


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
