# Matryoshka MMI — Specification v0.3

**Product type:** local memory server (MCP stdio application) for coding agents.
**License:** Apache-2.0. **Runtime:** Python 3.10+, stdlib only, zero dependencies.
**Single source of truth for behaviour:** this document.

## 1. What it is

A long-lived local process (`mmi_mcp.py`) exposing the Matryoshka memory acts
to any MCP-capable agent (Claude Code, OpenCode, Prime Agent, etc.). The model
is the only semantic subject: it decides what to remember and what to recall.
The server executes acts and decides nothing (no scoring, no relevance, no
vectors, no semantic search).

Architecture roles (per Matryoshka MANIFEST):

| Role | Component |
|---|---|
| Stable core K | the user's model (any provider) |
| Plastic substrate Φ(t) | `~/.matryoshka/PHI.jsonl` (append-only journal) |
| Executor (hand) | `mmi_mcp.py` |
| Instance time | `~/.matryoshka/TICKS.log` |

## 2. Distribution and verification

- **Source of truth:** GitHub repository `alexenti-code/matryoshka-mmi`,
  tagged releases (`v*`), each release = a git tag + GitHub Release.
- **Verification:** every release carries its version in `VERSION` (repo root)
  and `__version__` (server). The installer stamps `~/.matryoshka/VERSION`.
  Users verify provenance by the git tag; researchers cite the Zenodo DOI of
  the matching release.
- **Transport:** stdio, JSON-lines per MCP protocol version 2024-11-05.
  No network listeners, no open ports. Outbound: one version-string check per
  day (see §6), disabled with `MMI_NO_UPDATE_CHECK=1`.

## 3. Acts (tools)

| Tool | Act | Semantics |
|---|---|---|
| `matryoshka_tick` | TICK | accept the working beat; record priorities |
| `matryoshka_write` | WRITE | conscious remembering; fields: content (required), layer, valid_time, source |
| `matryoshka_read` | READ | explicit lookup only: `ids`, or `from/to` time range, or `last N` |
| `matryoshka_status` | STATUS | self-report: version, record counts per layer, storage path |


## 3.1. Memory dials (v0.4.0)

Owner-set physics, same constitutional class as sampling `temperature`:
continuous, no thresholds on content, no scoring, no triggers.

| Dial | Env var | Default | Meaning |
|---|---|---|---|
| memory_volume | `MMI_MEMORY_VOLUME_MB` | 0 (unlimited) | active journal size cap, MB; overflow moves oldest records to `PHI-archive.jsonl` |
| forgetting_tempo | `MMI_FORGETTING_TEMPO_DAYS` | 0 (never) | records older than N days (by `record_time`) move to the archive |

- Archival is mechanical time/size physics: records move with all fields intact
  (append-only preserved); archived records stay readable by `ids`/`range`;
  recency reads (`last`) see the active journal only.
- Factory settings (not exposed in the journal server): `write_gain`,
  `curiosity_gain`, `recall_sharpness`, `repeat_gain` — require the plastic
  parameter body (research scope, private repo). Do not expose or emulate.
- Dial semantics: `forgetting_tempo` does not decide *what* to forget — only
  *when*, by `record_time`; exactly as `temperature` does not decide *what* to
  say.

## 4. Record format (PHI.jsonl, one JSON object per line)

```json
{
  "id": 1,
  "record_time": "2026-08-29T21:00:00+03:00",
  "valid_time": "2026-08-29T21:00:00+03:00",
  "layer": "episode",
  "act": "WRITE",
  "content": "the fact to remember",
  "source": "dialogue"
}
```

Invariants:

1. **Append-only.** Records are never modified or deleted; new information is
   a new record.
2. **Bi-temporal.** `valid_time` (when it was true in the world) vs
   `record_time` (when the instance learned it).
3. **Layers.** `beat` < `episode` < `day` < `project` < `life`.
4. **No semantic index.** Reads are by id, time, or recency. The model reads
   its own diary.

## 5. Update signaling (never auto-update)

- Daily: server fetches `VERSION` from GitHub (only a version string).
- If newer than the stamped local version, a notice is stored and attached as
  an `_update` field to tool results until the user applies the update.
- The agent informs the user; the user applies by re-running `install.sh`.
- Opt-out: `MMI_NO_UPDATE_CHECK=1`.

## 6. Out of scope for MMI v0.3

- Vector/semantic retrieval (the model reads, it does not query an index).
- Consolidation of regions, rank-1 writes inside the model graph (research
  scope, stays in the research repository).
- Multi-user or network operation: single user, single machine, by design.
