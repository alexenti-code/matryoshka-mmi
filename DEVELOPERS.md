# For agent-developers (our own agents)

Read this before touching anything.

## What this project is (30 seconds)

A local MCP memory server for coding agents. One Python file (`mmi_mcp.py`),
stdlib only. The model decides what to remember; the server only executes
acts (TICK/WRITE/READ/STATUS) over an append-only bi-temporal journal
(`~/.matryoshka/PHI.jsonl`). Distributed via GitHub, Apache-2.0.

## Where everything lives

| Path | What |
|---|---|
| `mmi_mcp.py` | the whole server: MCP stdio loop, 4 tools, update check. Read it fully before editing |
| `install.sh` | installer: stamps `~/.matryoshka/`, registers the server in detected agents (claude/opencode/prime-agent), injects the instruction block. Asks confirmation when interactive |
| `uninstall.sh` | full removal. Keep it in sync with install.sh changes |
| `VERSION` | root version file; the daily update check fetches exactly this |
| `SPEC.md` | canonical behaviour spec. Code and spec change together |
| `RECOMMENDED-AGENTS.md` | supported agents; **empirical model minimum: 12B+** |
| `MONETIZATION.md` | proposals only. Do NOT implement any of it without the owner's explicit instruction |
| `NAME.md` | name/trademark/patent analysis (decision: keep the name, no patent) |

## Hard rules

1. **No push without the owner's explicit consent** (owner's standing rule).
2. **Never auto-update.** The server may only notify (`_update` field);
   the user applies updates by re-running install.sh.
3. **Model minimum 12B** (empirical, owner's testing). Do not soften.
4. **Privacy invariant:** outbound traffic = one version-string check per day,
   nothing else, ever. No telemetry.
5. **Research scope:** consolidation and the Rust daemon (mmid) stay in the
   private research repo (`/Users/alex/AURA-Retrieval/MMI/`). Do not disclose.
6. Test in a sandbox HOME (`/tmp/...`), never in the owner's real HOME.
7. Russian communication with the owner; direct, no fluff.

## Release procedure

1. Bump `__version__` in `mmi_mcp.py` and root `VERSION` (keep equal).
2. Sandbox test: install → protocol handshake → uninstall (all clean).
3. Commit → tag `vX.Y.Z` → push → `gh release create vX.Y.Z`.

## Developer-to-developer hand-off

`.dev-exchange/` (git-ignored, local only) is our service-message folder.
If you leave unfinished work, drop a short `<topic>.md` there: what was done,
what is pending, where you stopped. The next agent-developer session reads
it first. Never commit or push it.
